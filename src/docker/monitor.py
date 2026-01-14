"""Docker container monitoring via SSH and CLI commands."""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..ssh.executor import RemoteExecutor, CommandResult
from .parser import DockerOutputParser, ContainerInfo
from ..utils.logger import get_logger


@dataclass
class HostStatus:
    """Status of a monitored host."""

    host_name: str
    hostname: str
    connected: bool
    docker_available: bool
    docker_version: Optional[str] = None
    error: Optional[str] = None
    containers: List[ContainerInfo] = None

    def __post_init__(self):
        """Initialize containers list if not provided."""
        if self.containers is None:
            self.containers = []

    @property
    def container_count(self) -> int:
        """Total number of containers."""
        return len(self.containers)

    @property
    def running_count(self) -> int:
        """Number of running containers."""
        return sum(1 for c in self.containers if c.is_running())

    @property
    def stopped_count(self) -> int:
        """Number of stopped containers."""
        return sum(1 for c in self.containers if not c.is_running())


class DockerMonitor:
    """
    Monitors Docker containers on remote hosts.

    Uses SSH to execute Docker CLI commands (Method A).
    """

    def __init__(
        self,
        executor: RemoteExecutor,
        host_name: str,
        hostname: str,
        docker_bin: str = "/usr/bin/docker",
    ):
        """
        Initialize DockerMonitor.

        Args:
            executor: RemoteExecutor instance for this host.
            host_name: Friendly name of the host (e.g., "prod-web-01").
            hostname: Actual hostname/IP of the host.
            docker_bin: Path to docker binary on remote host.
        """
        self.executor = executor
        self.host_name = host_name
        self.hostname = hostname
        self.docker_bin = docker_bin

        self.parser = DockerOutputParser()
        self.logger = get_logger()

        self._docker_available = False
        self._docker_version: Optional[str] = None

    async def check_docker(self) -> bool:
        """
        Check if Docker is available on this host.

        Returns:
            True if Docker is available and accessible.
        """
        is_available, version = await self.executor.check_docker_available()

        self._docker_available = is_available
        self._docker_version = version

        return is_available

    async def get_containers(
        self,
        all_containers: bool = True,
        with_stats: bool = False,
    ) -> List[ContainerInfo]:
        """
        Get list of containers on this host.

        Args:
            all_containers: If True, include stopped containers. If False, only running.
            with_stats: If True, also fetch resource usage stats.

        Returns:
            List of ContainerInfo objects.

        Raises:
            RuntimeError: If Docker is not available.
        """
        if not self._docker_available:
            await self.check_docker()
            if not self._docker_available:
                raise RuntimeError(
                    f"Docker is not available on {self.host_name} ({self.hostname})"
                )

        # Build docker ps command
        if all_containers:
            ps_command = f"{self.docker_bin} ps -a --format '{{{{json .}}}}'"
        else:
            ps_command = f"{self.docker_bin} ps --format '{{{{json .}}}}'"

        # Execute docker ps
        result = await self.executor.execute(ps_command)

        if not result.success:
            self.logger.error(
                f"Failed to get containers from {self.host_name}: {result.stderr}"
            )
            return []

        # Parse output
        containers = self.parser.parse_ps_output(result.stdout, host=self.host_name)

        # Fetch stats if requested
        if with_stats and containers:
            stats = await self.get_stats()
            containers = self.parser.merge_ps_and_stats(containers, stats)

        return containers

    async def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get resource usage statistics for all running containers.

        Returns:
            Dictionary mapping container name/ID to stats.
        """
        if not self._docker_available:
            await self.check_docker()
            if not self._docker_available:
                return {}

        # Build docker stats command
        stats_command = f"{self.docker_bin} stats --no-stream --format '{{{{json .}}}}'"

        # Execute command
        result = await self.executor.execute(stats_command, timeout=60)

        if not result.success:
            self.logger.warning(
                f"Failed to get stats from {self.host_name}: {result.stderr}"
            )
            return {}

        # Parse output
        stats = self.parser.parse_stats_output(result.stdout, host=self.host_name)

        return stats

    async def get_container_details(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific container.

        Args:
            container_id: Container ID or name.

        Returns:
            Dictionary with detailed container info, or None if not found.
        """
        if not self._docker_available:
            await self.check_docker()
            if not self._docker_available:
                return None

        # Build docker inspect command
        inspect_command = f"{self.docker_bin} inspect {container_id}"

        # Execute command
        result = await self.executor.execute(inspect_command)

        if not result.success:
            self.logger.warning(
                f"Failed to inspect container {container_id} on {self.host_name}: {result.stderr}"
            )
            return None

        # Parse output
        details = self.parser.parse_inspect_output(result.stdout)

        return details

    async def get_host_status(self, include_containers: bool = True) -> HostStatus:
        """
        Get overall status of this host.

        Args:
            include_containers: If True, fetch container list.

        Returns:
            HostStatus object.
        """
        # Test connection
        is_connected = await self.executor.test_connection()

        if not is_connected:
            return HostStatus(
                host_name=self.host_name,
                hostname=self.hostname,
                connected=False,
                docker_available=False,
                error="Connection failed",
            )

        # Check Docker
        docker_ok = await self.check_docker()

        if not docker_ok:
            return HostStatus(
                host_name=self.host_name,
                hostname=self.hostname,
                connected=True,
                docker_available=False,
                error="Docker not available",
            )

        # Get containers if requested
        containers = []
        if include_containers:
            try:
                containers = await self.get_containers(all_containers=True, with_stats=True)
            except Exception as e:
                self.logger.error(f"Failed to get containers from {self.host_name}: {e}")

        return HostStatus(
            host_name=self.host_name,
            hostname=self.hostname,
            connected=True,
            docker_available=True,
            docker_version=self._docker_version,
            containers=containers,
        )

    async def execute_docker_command(self, command: str) -> CommandResult:
        """
        Execute a custom Docker command.

        Args:
            command: Docker command to execute (without 'docker' prefix).

        Returns:
            CommandResult object.
        """
        full_command = f"{self.docker_bin} {command}"
        return await self.executor.execute(full_command)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DockerMonitor(host={self.host_name}, "
            f"docker_available={self._docker_available})"
        )
