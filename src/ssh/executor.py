"""Remote command executor for SSH connections."""

import asyncio
from typing import Optional, Tuple
from dataclasses import dataclass
import asyncssh

from ..utils.logger import get_logger, LoggerAdapter


@dataclass
class CommandResult:
    """Result of a remote command execution."""

    command: str
    exit_status: int
    stdout: str
    stderr: str
    success: bool
    host: str

    @property
    def output(self) -> str:
        """Get combined output (stdout + stderr)."""
        return self.stdout + self.stderr

    def __repr__(self) -> str:
        """String representation."""
        status = "SUCCESS" if self.success else f"FAILED (exit={self.exit_status})"
        return f"CommandResult(host={self.host}, status={status}, command={self.command[:50]}...)"


class RemoteExecutor:
    """
    Executes commands on remote hosts via SSH.

    This class handles:
    - Command execution with timeout
    - Output capture (stdout/stderr)
    - Error handling and retry logic
    """

    def __init__(
        self,
        connection: asyncssh.SSHClientConnection,
        host_identifier: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        """
        Initialize RemoteExecutor.

        Args:
            connection: Active SSH connection.
            host_identifier: Host identifier for logging (e.g., "prod-web-01").
            timeout: Command execution timeout in seconds.
            max_retries: Maximum number of retry attempts.
            retry_delay: Delay between retries in seconds.
        """
        self.connection = connection
        self.host_identifier = host_identifier
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        base_logger = get_logger()
        self.logger = LoggerAdapter(base_logger, {"host": host_identifier})

    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        retry: bool = True,
    ) -> CommandResult:
        """
        Execute a command on the remote host.

        Args:
            command: Command to execute.
            timeout: Override default timeout for this command.
            retry: Enable retry on failure.

        Returns:
            CommandResult containing execution details.

        Raises:
            asyncssh.Error: If command execution fails after all retries.
            asyncio.TimeoutError: If command times out.
        """
        timeout = timeout or self.timeout
        retries = self.max_retries if retry else 1

        for attempt in range(1, retries + 1):
            try:
                self.logger.debug(
                    f"Executing command (attempt {attempt}/{retries}): {command[:100]}"
                )

                # Execute command with timeout
                result = await asyncio.wait_for(
                    self.connection.run(command, check=False),
                    timeout=timeout,
                )

                # Parse result
                exit_status = result.exit_status
                stdout = result.stdout if result.stdout else ""
                stderr = result.stderr if result.stderr else ""
                success = exit_status == 0

                if success:
                    self.logger.debug(f"Command succeeded: {command[:100]}")
                else:
                    self.logger.warning(
                        f"Command failed with exit code {exit_status}: {command[:100]}"
                    )
                    if stderr:
                        self.logger.warning(f"Error output: {stderr[:200]}")

                return CommandResult(
                    command=command,
                    exit_status=exit_status,
                    stdout=stdout,
                    stderr=stderr,
                    success=success,
                    host=self.host_identifier,
                )

            except asyncio.TimeoutError:
                self.logger.error(
                    f"Command timed out after {timeout}s (attempt {attempt}/{retries}): {command[:100]}"
                )

                if attempt < retries:
                    self.logger.info(f"Retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise

            except asyncssh.Error as e:
                self.logger.error(
                    f"SSH error executing command (attempt {attempt}/{retries}): {e}"
                )

                if attempt < retries:
                    self.logger.info(f"Retrying in {self.retry_delay}s...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise

            except Exception as e:
                self.logger.error(f"Unexpected error executing command: {e}")
                raise

        # Should not reach here, but just in case
        raise RuntimeError(f"Failed to execute command after {retries} attempts")

    async def execute_multiple(
        self,
        commands: list[str],
        timeout: Optional[int] = None,
        sequential: bool = False,
    ) -> list[CommandResult]:
        """
        Execute multiple commands.

        Args:
            commands: List of commands to execute.
            timeout: Override default timeout.
            sequential: If True, execute sequentially. If False, execute in parallel.

        Returns:
            List of CommandResults.
        """
        if sequential:
            # Execute one by one
            results = []
            for cmd in commands:
                result = await self.execute(cmd, timeout=timeout)
                results.append(result)
            return results
        else:
            # Execute in parallel
            tasks = [self.execute(cmd, timeout=timeout) for cmd in commands]
            return await asyncio.gather(*tasks, return_exceptions=False)

    async def test_connection(self) -> bool:
        """
        Test if connection is alive by running a simple command.

        Returns:
            True if connection is alive and working.
        """
        try:
            result = await self.execute("echo 'connection_test'", timeout=10, retry=False)
            return result.success and "connection_test" in result.stdout
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    async def check_docker_available(self) -> Tuple[bool, Optional[str]]:
        """
        Check if Docker is installed and accessible on remote host.

        Returns:
            Tuple of (is_available, version_string).
        """
        try:
            result = await self.execute("docker --version", timeout=10, retry=False)

            if result.success:
                version = result.stdout.strip()
                self.logger.info(f"Docker available: {version}")
                return True, version
            else:
                self.logger.warning("Docker command failed")
                return False, None

        except Exception as e:
            self.logger.error(f"Failed to check Docker availability: {e}")
            return False, None

    def __repr__(self) -> str:
        """String representation."""
        return f"RemoteExecutor(host={self.host_identifier}, timeout={self.timeout}s)"
