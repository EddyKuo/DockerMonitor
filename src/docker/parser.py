"""Docker CLI output parser."""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..utils.logger import get_logger


@dataclass
class ContainerInfo:
    """Parsed Docker container information."""

    id: str
    name: str
    image: str
    status: str
    state: str  # running, exited, paused, etc.
    created: Optional[str] = None
    ports: Optional[str] = None
    command: Optional[str] = None
    host: Optional[str] = None

    # Resource usage (from docker stats)
    cpu_percent: Optional[float] = None
    memory_usage: Optional[str] = None
    memory_percent: Optional[float] = None
    net_io: Optional[str] = None
    block_io: Optional[str] = None

    def is_running(self) -> bool:
        """Check if container is running."""
        return self.state.lower() == "running"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "status": self.status,
            "state": self.state,
            "created": self.created,
            "ports": self.ports,
            "command": self.command,
            "host": self.host,
            "cpu_percent": self.cpu_percent,
            "memory_usage": self.memory_usage,
            "memory_percent": self.memory_percent,
            "net_io": self.net_io,
            "block_io": self.block_io,
        }


class DockerOutputParser:
    """
    Parses Docker CLI JSON output.

    Supports parsing output from:
    - docker ps (container list)
    - docker stats (resource usage)
    - docker inspect (detailed info)
    """

    def __init__(self):
        """Initialize parser."""
        self.logger = get_logger()

    def parse_ps_output(self, output: str, host: str = "unknown") -> List[ContainerInfo]:
        """
        Parse 'docker ps' JSON output.

        Args:
            output: JSON output from 'docker ps --format "{{json .}}"'.
            host: Host identifier for tagging containers.

        Returns:
            List of ContainerInfo objects.
        """
        containers = []

        if not output or not output.strip():
            self.logger.debug(f"Empty docker ps output from {host}")
            return containers

        # Docker ps outputs one JSON object per line
        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                # Parse container info
                container = ContainerInfo(
                    id=data.get("ID", ""),
                    name=data.get("Names", data.get("Name", "")),
                    image=data.get("Image", ""),
                    status=data.get("Status", ""),
                    state=data.get("State", "unknown"),
                    created=data.get("CreatedAt", data.get("Created")),
                    ports=data.get("Ports", ""),
                    command=data.get("Command", ""),
                    host=host,
                )

                containers.append(container)

            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse docker ps line from {host}: {e}")
                self.logger.debug(f"Problematic line: {line[:100]}")
            except Exception as e:
                self.logger.error(f"Unexpected error parsing docker ps from {host}: {e}")

        self.logger.debug(f"Parsed {len(containers)} containers from {host}")
        return containers

    def parse_stats_output(
        self, output: str, host: str = "unknown"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Parse 'docker stats' JSON output.

        Args:
            output: JSON output from 'docker stats --no-stream --format "{{json .}}"'.
            host: Host identifier.

        Returns:
            Dictionary mapping container ID/name to stats data.
        """
        stats = {}

        if not output or not output.strip():
            self.logger.debug(f"Empty docker stats output from {host}")
            return stats

        # Docker stats outputs one JSON object per line
        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            try:
                data = json.loads(line)

                container_id = data.get("Container", data.get("ID", ""))
                container_name = data.get("Name", container_id)

                stats[container_name] = {
                    "id": container_id,
                    "name": container_name,
                    "cpu_percent": self._parse_percentage(data.get("CPUPerc", "0%")),
                    "memory_usage": data.get("MemUsage", ""),
                    "memory_percent": self._parse_percentage(data.get("MemPerc", "0%")),
                    "net_io": data.get("NetIO", ""),
                    "block_io": data.get("BlockIO", ""),
                    "pids": data.get("PIDs", ""),
                }

            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse docker stats line from {host}: {e}")
            except Exception as e:
                self.logger.error(f"Unexpected error parsing docker stats from {host}: {e}")

        self.logger.debug(f"Parsed stats for {len(stats)} containers from {host}")
        return stats

    def merge_ps_and_stats(
        self, containers: List[ContainerInfo], stats: Dict[str, Dict[str, Any]]
    ) -> List[ContainerInfo]:
        """
        Merge container list with stats data.

        Args:
            containers: List of containers from docker ps.
            stats: Stats dictionary from docker stats.

        Returns:
            Updated list of ContainerInfo with stats included.
        """
        for container in containers:
            # Try to find stats by name or ID
            container_stats = stats.get(container.name) or stats.get(container.id)

            if container_stats:
                container.cpu_percent = container_stats.get("cpu_percent")
                container.memory_usage = container_stats.get("memory_usage")
                container.memory_percent = container_stats.get("memory_percent")
                container.net_io = container_stats.get("net_io")
                container.block_io = container_stats.get("block_io")

        return containers

    def _parse_percentage(self, percent_str: str) -> Optional[float]:
        """
        Parse percentage string to float.

        Args:
            percent_str: String like "45.67%" or "0.00%".

        Returns:
            Float value or None if parsing fails.
        """
        try:
            # Remove % sign and convert to float
            return float(percent_str.rstrip("%"))
        except (ValueError, AttributeError):
            return None

    def parse_inspect_output(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Parse 'docker inspect' JSON output.

        Args:
            output: JSON output from 'docker inspect <container>'.

        Returns:
            Dictionary with detailed container information, or None if parsing fails.
        """
        try:
            # docker inspect returns a JSON array
            data = json.loads(output)

            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
            else:
                self.logger.warning("Unexpected docker inspect output format")
                return None

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse docker inspect output: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error parsing docker inspect: {e}")
            return None

    def containers_to_dict_list(self, containers: List[ContainerInfo]) -> List[Dict[str, Any]]:
        """
        Convert list of ContainerInfo to list of dictionaries.

        Args:
            containers: List of ContainerInfo objects.

        Returns:
            List of dictionaries.
        """
        return [c.to_dict() for c in containers]
