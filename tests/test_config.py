"""Tests for ConfigManager."""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.utils.config import ConfigManager


@pytest.fixture
def sample_config():
    """Create a sample configuration file."""
    config_data = {
        "jump_host": {
            "hostname": "jump.example.com",
            "port": 22,
            "username": "test_user",
            "key_file": "~/.ssh/id_rsa",
        },
        "target_hosts": [
            {
                "name": "test-host-01",
                "hostname": "192.168.1.10",
                "port": 22,
                "username": "docker_user",
                "key_file": "~/.ssh/id_rsa",
                "tags": ["production", "web"],
                "enabled": True,
            },
            {
                "name": "test-host-02",
                "hostname": "192.168.1.11",
                "port": 22,
                "username": "docker_user",
                "key_file": "~/.ssh/id_rsa",
                "tags": ["development"],
                "enabled": False,
            },
        ],
        "monitoring": {
            "default_interval": 60,
            "command_timeout": 30,
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        return f.name


def test_config_load(sample_config):
    """Test loading configuration file."""
    config = ConfigManager(sample_config)
    assert config is not None
    assert config.config_path == Path(sample_config)


def test_get_jump_host(sample_config):
    """Test getting jump host configuration."""
    config = ConfigManager(sample_config)
    jump_host = config.get_jump_host()

    assert jump_host["hostname"] == "jump.example.com"
    assert jump_host["port"] == 22
    assert jump_host["username"] == "test_user"


def test_get_target_hosts_enabled_only(sample_config):
    """Test getting only enabled target hosts."""
    config = ConfigManager(sample_config)
    hosts = config.get_target_hosts(enabled_only=True)

    assert len(hosts) == 1
    assert hosts[0]["name"] == "test-host-01"


def test_get_target_hosts_all(sample_config):
    """Test getting all target hosts."""
    config = ConfigManager(sample_config)
    hosts = config.get_target_hosts(enabled_only=False)

    assert len(hosts) == 2


def test_get_target_hosts_by_tags(sample_config):
    """Test filtering hosts by tags."""
    config = ConfigManager(sample_config)
    hosts = config.get_target_hosts(tags=["production"], enabled_only=True)

    assert len(hosts) == 1
    assert "production" in hosts[0]["tags"]


def test_get_monitoring_config(sample_config):
    """Test getting monitoring configuration."""
    config = ConfigManager(sample_config)
    monitoring = config.get_monitoring_config()

    assert monitoring["default_interval"] == 60
    assert monitoring["command_timeout"] == 30


def test_validate_config(sample_config):
    """Test configuration validation."""
    config = ConfigManager(sample_config)
    assert config.validate() is True


def test_get_host_by_name(sample_config):
    """Test getting host by name."""
    config = ConfigManager(sample_config)
    host = config.get_host_by_name("test-host-01")

    assert host is not None
    assert host["name"] == "test-host-01"
    assert host["hostname"] == "192.168.1.10"


def test_get_host_by_name_not_found(sample_config):
    """Test getting non-existent host."""
    config = ConfigManager(sample_config)
    host = config.get_host_by_name("non-existent")

    assert host is None


@pytest.fixture(autouse=True)
def cleanup(sample_config):
    """Clean up temporary files after tests."""
    yield
    Path(sample_config).unlink(missing_ok=True)
