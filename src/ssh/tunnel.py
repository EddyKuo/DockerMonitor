"""SSH Tunnel Manager for connecting through jump host."""

import asyncio
from typing import Optional, Dict, Any
import asyncssh
from pathlib import Path

from ..utils.logger import get_logger


class SSHTunnelManager:
    """
    Manages SSH connections through a jump host (bastion server).

    This class handles:
    - Connection to jump host
    - Creating tunneled connections to target hosts
    - Connection pooling and reuse
    - Automatic reconnection
    """

    def __init__(
        self,
        jump_host: str,
        jump_port: int = 22,
        jump_user: str = None,
        jump_key_file: str = None,
        jump_password: str = None,
        timeout: int = 30,
    ):
        """
        Initialize SSH Tunnel Manager.

        Args:
            jump_host: Jump host hostname or IP.
            jump_port: Jump host SSH port.
            jump_user: Username for jump host.
            jump_key_file: Path to SSH private key file.
            jump_password: Password (not recommended, use key instead).
            timeout: Connection timeout in seconds.
        """
        self.jump_host = jump_host
        self.jump_port = jump_port
        self.jump_user = jump_user
        self.jump_key_file = jump_key_file
        self.jump_password = jump_password
        self.timeout = timeout

        self._jump_connection: Optional[asyncssh.SSHClientConnection] = None
        self._target_connections: Dict[str, asyncssh.SSHClientConnection] = {}
        self._lock = asyncio.Lock()

        self.logger = get_logger()

    async def connect_to_jump_host(self) -> asyncssh.SSHClientConnection:
        """
        Establish connection to jump host.

        Returns:
            SSH connection to jump host.

        Raises:
            asyncssh.Error: If connection fails.
        """
        async with self._lock:
            # Return existing connection if still alive
            if self._jump_connection and not self._jump_connection.is_closed():
                return self._jump_connection

            self.logger.info(
                f"Connecting to jump host: {self.jump_user}@{self.jump_host}:{self.jump_port}"
            )

            try:
                # Prepare connection options
                connect_kwargs = {
                    "host": self.jump_host,
                    "port": self.jump_port,
                    "username": self.jump_user,
                    "connect_timeout": self.timeout,
                    "known_hosts": None,  # Disable host key checking (use with caution)
                }

                # Add authentication method
                if self.jump_key_file:
                    key_path = Path(self.jump_key_file).expanduser()
                    if not key_path.exists():
                        raise FileNotFoundError(
                            f"SSH key file not found: {self.jump_key_file}"
                        )
                    connect_kwargs["client_keys"] = [str(key_path)]
                elif self.jump_password:
                    connect_kwargs["password"] = self.jump_password
                else:
                    raise ValueError(
                        "Either jump_key_file or jump_password must be provided"
                    )

                # Connect
                self._jump_connection = await asyncssh.connect(**connect_kwargs)
                self.logger.info("Successfully connected to jump host")

                return self._jump_connection

            except asyncssh.Error as e:
                self.logger.error(f"Failed to connect to jump host: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error connecting to jump host: {e}")
                raise

    async def connect_to_target(
        self,
        target_host: str,
        target_port: int = 22,
        target_user: str = None,
        target_key_file: str = None,
        target_password: str = None,
    ) -> asyncssh.SSHClientConnection:
        """
        Connect to target host through jump host.

        Args:
            target_host: Target hostname or IP.
            target_port: Target SSH port.
            target_user: Username for target host.
            target_key_file: Path to SSH private key file.
            target_password: Password (not recommended).

        Returns:
            SSH connection to target host.

        Raises:
            asyncssh.Error: If connection fails.
        """
        connection_id = f"{target_user}@{target_host}:{target_port}"

        # Check for existing connection (with lock)
        async with self._lock:
            if connection_id in self._target_connections:
                conn = self._target_connections[connection_id]
                if not conn.is_closed():
                    return conn
                else:
                    # Remove dead connection
                    del self._target_connections[connection_id]

        self.logger.info(f"Connecting to target host: {connection_id}")

        # Ensure jump host connection is alive (WITHOUT lock to avoid deadlock)
        jump_conn = await self.connect_to_jump_host()
        self.logger.info(f"Jump connection ready, connecting to {target_host}...")

        # Now acquire lock for the actual connection
        async with self._lock:
            try:

                # Prepare connection options
                connect_kwargs = {
                    "host": target_host,
                    "port": target_port,
                    "username": target_user,
                    "connect_timeout": self.timeout,
                    "known_hosts": None,
                }

                # Add authentication method (prefer password over key if both provided)
                if target_password:
                    self.logger.info(f"Using password authentication for {connection_id}")
                    connect_kwargs["password"] = target_password
                    # Only use password, no keys
                    connect_kwargs["client_keys"] = []
                    connect_kwargs["preferred_auth"] = ["password"]
                elif target_key_file:
                    self.logger.info(f"Using key authentication for {connection_id}")
                    key_path = Path(target_key_file).expanduser()
                    if not key_path.exists():
                        raise FileNotFoundError(
                            f"SSH key file not found: {target_key_file}"
                        )
                    connect_kwargs["client_keys"] = [str(key_path)]
                else:
                    raise ValueError(
                        "Either target_key_file or target_password must be provided"
                    )

                # Connect through jump host (tunneling)
                self.logger.info(f"Initiating SSH tunnel to {target_host}:{target_port}...")

                try:
                    target_conn = await asyncio.wait_for(
                        jump_conn.connect_ssh(**connect_kwargs),
                        timeout=self.timeout
                    )
                    self.logger.info(f"SSH tunnel established to {connection_id}")
                except asyncio.TimeoutError:
                    self.logger.error(f"Connection to {connection_id} timed out after {self.timeout}s")
                    raise
                except asyncssh.PermissionDenied as e:
                    self.logger.error(f"Permission denied for {connection_id}: {e}")
                    raise
                except asyncssh.ConnectionLost as e:
                    self.logger.error(f"Connection lost to {connection_id}: {e}")
                    raise
                except Exception as e:
                    self.logger.error(f"SSH connection error to {connection_id}: {type(e).__name__}: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                    raise

                # Store connection
                self._target_connections[connection_id] = target_conn
                self.logger.info(f"Successfully connected to target: {connection_id}")

                return target_conn

            except asyncssh.Error as e:
                self.logger.error(f"Failed to connect to target host {connection_id}: {e}")
                raise
            except Exception as e:
                self.logger.error(
                    f"Unexpected error connecting to target host {connection_id}: {e}"
                )
                raise

    async def close_target_connection(self, target_host: str, target_port: int = 22, target_user: str = None):
        """
        Close connection to specific target host.

        Args:
            target_host: Target hostname.
            target_port: Target SSH port.
            target_user: Username.
        """
        connection_id = f"{target_user}@{target_host}:{target_port}"

        async with self._lock:
            if connection_id in self._target_connections:
                conn = self._target_connections[connection_id]
                if not conn.is_closed():
                    conn.close()
                    await conn.wait_closed()
                del self._target_connections[connection_id]
                self.logger.info(f"Closed connection to {connection_id}")

    async def close_all(self):
        """Close all connections (target hosts and jump host)."""
        async with self._lock:
            # Close all target connections
            for connection_id, conn in list(self._target_connections.items()):
                if not conn.is_closed():
                    conn.close()
                    await conn.wait_closed()
                self.logger.info(f"Closed connection to {connection_id}")

            self._target_connections.clear()

            # Close jump host connection
            if self._jump_connection and not self._jump_connection.is_closed():
                self._jump_connection.close()
                await self._jump_connection.wait_closed()
                self.logger.info("Closed connection to jump host")

            self._jump_connection = None

    def is_jump_connected(self) -> bool:
        """
        Check if jump host connection is alive.

        Returns:
            True if connected, False otherwise.
        """
        return self._jump_connection is not None and not self._jump_connection.is_closed()

    def is_target_connected(self, target_host: str, target_port: int = 22, target_user: str = None) -> bool:
        """
        Check if target host connection is alive.

        Args:
            target_host: Target hostname.
            target_port: Target port.
            target_user: Username.

        Returns:
            True if connected, False otherwise.
        """
        connection_id = f"{target_user}@{target_host}:{target_port}"
        if connection_id in self._target_connections:
            conn = self._target_connections[connection_id]
            return not conn.is_closed()
        return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect_to_jump_host()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_all()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SSHTunnelManager(jump_host={self.jump_host}, "
            f"connected_targets={len(self._target_connections)})"
        )
