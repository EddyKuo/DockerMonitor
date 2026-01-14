"""Configuration management for DockerMonitor."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv


class ConfigManager:
    """Manages configuration from YAML files and environment variables."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize ConfigManager.

        Args:
            config_path: Path to hosts.yaml configuration file.
                        If None, uses default path: config/hosts.yaml
        """
        # Load environment variables from .env file
        load_dotenv()

        # Determine config file path
        if config_path is None:
            # Default to config/hosts.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "hosts.yaml"
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create a hosts.yaml file in the config directory."
            )

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")

    def get_jump_host(self) -> Dict[str, Any]:
        """
        Get jump host configuration.

        Returns:
            Dictionary containing jump host connection details.

        Raises:
            KeyError: If jump_host configuration is missing.
        """
        if "jump_host" not in self._config:
            raise KeyError("Missing 'jump_host' configuration in hosts.yaml")

        jump_host = self._config["jump_host"].copy()

        # Override with environment variables if present
        jump_host["hostname"] = os.getenv("JUMP_HOST", jump_host.get("hostname"))
        jump_host["port"] = int(os.getenv("JUMP_PORT", jump_host.get("port", 22)))
        jump_host["username"] = os.getenv("JUMP_USER", jump_host.get("username"))
        jump_host["key_file"] = os.getenv("JUMP_KEY_PATH", jump_host.get("key_file"))

        # Expand ~ in key_file path
        if jump_host.get("key_file"):
            jump_host["key_file"] = os.path.expanduser(jump_host["key_file"])

        return jump_host

    def get_target_hosts(
        self, tags: Optional[List[str]] = None, enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get list of target hosts to monitor.

        Args:
            tags: Filter hosts by tags. If None, return all hosts.
            enabled_only: If True, only return hosts with enabled=True.

        Returns:
            List of host configuration dictionaries.
        """
        if "target_hosts" not in self._config:
            raise KeyError("Missing 'target_hosts' configuration in hosts.yaml")

        hosts = self._config["target_hosts"]

        # Filter by enabled status
        if enabled_only:
            hosts = [h for h in hosts if h.get("enabled", True)]

        # Filter by tags
        if tags:
            hosts = [
                h
                for h in hosts
                if any(tag in h.get("tags", []) for tag in tags)
            ]

        # Expand ~ in key_file paths
        for host in hosts:
            if host.get("key_file"):
                host["key_file"] = os.path.expanduser(host["key_file"])

        return hosts

    def get_monitoring_config(self) -> Dict[str, Any]:
        """
        Get monitoring configuration.

        Returns:
            Dictionary containing monitoring settings.
        """
        default_config = {
            "default_interval": 60,
            "command_timeout": 30,
            "max_concurrent_connections": 5,
            "max_retries": 3,
            "retry_delay": 5,
        }

        config = self._config.get("monitoring", {})

        # Override with environment variables
        config["default_interval"] = int(
            os.getenv("MONITOR_INTERVAL", config.get("default_interval", 60))
        )
        config["command_timeout"] = int(
            os.getenv("TIMEOUT", config.get("command_timeout", 30))
        )
        config["max_concurrent_connections"] = int(
            os.getenv("MAX_WORKERS", config.get("max_concurrent_connections", 5))
        )

        return {**default_config, **config}

    def get_docker_config(self) -> Dict[str, Any]:
        """
        Get Docker command configuration.

        Returns:
            Dictionary containing Docker settings and commands.
        """
        default_config = {
            "docker_bin": "/usr/bin/docker",
            "commands": [
                {
                    "name": "ps_all",
                    "command": "docker ps -a --format '{{json .}}'",
                    "description": "List all containers",
                },
                {
                    "name": "ps_running",
                    "command": "docker ps --format '{{json .}}'",
                    "description": "List running containers",
                },
                {
                    "name": "stats",
                    "command": "docker stats --no-stream --format '{{json .}}'",
                    "description": "Container resource usage",
                },
            ],
        }

        config = self._config.get("docker", {})
        return {**default_config, **config}

    def get_output_config(self) -> Dict[str, Any]:
        """
        Get output configuration.

        Returns:
            Dictionary containing output settings.
        """
        default_config = {
            "default_format": "table",
            "output_dir": "./output",
            "save_history": True,
            "history_retention_days": 30,
        }

        config = self._config.get("output", {})

        # Override with environment variables
        config["default_format"] = os.getenv(
            "OUTPUT_FORMAT", config.get("default_format", "table")
        )
        config["output_dir"] = os.getenv(
            "OUTPUT_DIR", config.get("output_dir", "./output")
        )

        return {**default_config, **config}

    def get_log_level(self) -> str:
        """
        Get logging level from environment.

        Returns:
            Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        """
        return os.getenv("LOG_LEVEL", "INFO").upper()

    def is_debug_mode(self) -> bool:
        """
        Check if debug mode is enabled.

        Returns:
            True if debug mode is enabled.
        """
        debug = os.getenv("DEBUG", "false").lower()
        return debug in ("true", "1", "yes", "on")

    def get_locale(self) -> str:
        """
        Get application locale/language setting.

        Returns:
            Locale string (e.g., 'en', 'zh_TW'). Defaults to 'en'.
        """
        # Try environment variable first
        locale = os.getenv("LOCALE")
        if locale:
            return locale

        # Then check config file
        app_config = self._config.get("app", {})
        return app_config.get("locale", "en")

    def validate(self) -> bool:
        """
        Validate configuration completeness.

        Returns:
            True if configuration is valid.

        Raises:
            ValueError: If configuration is invalid.
        """
        # Check jump host
        jump_host = self.get_jump_host()
        required_jump_fields = ["hostname", "username", "key_file"]
        for field in required_jump_fields:
            if not jump_host.get(field):
                raise ValueError(f"Missing required jump_host field: {field}")

        # Check target hosts
        target_hosts = self.get_target_hosts(enabled_only=False)
        if not target_hosts:
            raise ValueError("No target hosts configured")

        for host in target_hosts:
            required_host_fields = ["name", "hostname", "username", "key_file"]
            for field in required_host_fields:
                if not host.get(field):
                    raise ValueError(
                        f"Missing required field '{field}' in host: {host.get('name', 'unknown')}"
                    )

        return True

    def get_host_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific host configuration by name.

        Args:
            name: Host name to search for.

        Returns:
            Host configuration dictionary or None if not found.
        """
        hosts = self.get_target_hosts(enabled_only=False)
        for host in hosts:
            if host.get("name") == name:
                return host
        return None

    def __repr__(self) -> str:
        """String representation of ConfigManager."""
        return (
            f"ConfigManager(config_path='{self.config_path}', "
            f"hosts={len(self.get_target_hosts(enabled_only=False))})"
        )
