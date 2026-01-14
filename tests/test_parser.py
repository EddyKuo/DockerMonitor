"""Tests for DockerOutputParser."""

import pytest
from src.docker.parser import DockerOutputParser, ContainerInfo


@pytest.fixture
def parser():
    """Create a parser instance."""
    return DockerOutputParser()


@pytest.fixture
def sample_ps_output():
    """Sample docker ps JSON output."""
    return """{"Command":"\\"docker-entrypoint.s\u2026\\"","CreatedAt":"2024-01-10 10:00:00 +0000 UTC","ID":"abc123def456","Image":"nginx:latest","Labels":"","LocalVolumes":"0","Mounts":"","Names":"web-server","Networks":"bridge","Ports":"80/tcp, 443/tcp","RunningFor":"2 days ago","Size":"0B","State":"running","Status":"Up 2 days"}
{"Command":"\\"redis-server\\"","CreatedAt":"2024-01-09 09:00:00 +0000 UTC","ID":"def456ghi789","Image":"redis:6","Labels":"","LocalVolumes":"1","Mounts":"/data","Names":"cache","Networks":"bridge","Ports":"6379/tcp","RunningFor":"3 days ago","Size":"0B","State":"running","Status":"Up 3 days"}
{"Command":"\\"postgres\\"","CreatedAt":"2024-01-08 08:00:00 +0000 UTC","ID":"ghi789jkl012","Image":"postgres:13","Labels":"","LocalVolumes":"1","Mounts":"/var/lib/postgresql/data","Names":"database","Networks":"bridge","Ports":"5432/tcp","RunningFor":"4 days ago","Size":"0B","State":"exited","Status":"Exited (0) 1 hour ago"}"""


@pytest.fixture
def sample_stats_output():
    """Sample docker stats JSON output."""
    return """{"BlockIO":"0B / 0B","CPUPerc":"2.45%","Container":"abc123def456","ID":"abc123def456","MemPerc":"1.23%","MemUsage":"128MiB / 4GiB","Name":"web-server","NetIO":"1.2kB / 3.4kB","PIDs":"10"}
{"BlockIO":"0B / 0B","CPUPerc":"0.50%","Container":"def456ghi789","ID":"def456ghi789","MemPerc":"0.80%","MemUsage":"64MiB / 4GiB","Name":"cache","NetIO":"500B / 800B","PIDs":"5"}"""


def test_parse_ps_output(parser, sample_ps_output):
    """Test parsing docker ps output."""
    containers = parser.parse_ps_output(sample_ps_output, host="test-host")

    assert len(containers) == 3
    assert all(isinstance(c, ContainerInfo) for c in containers)

    # Check first container
    web = containers[0]
    assert web.name == "web-server"
    assert web.image == "nginx:latest"
    assert web.state == "running"
    assert web.host == "test-host"
    assert web.is_running() is True

    # Check exited container
    db = containers[2]
    assert db.name == "database"
    assert db.state == "exited"
    assert db.is_running() is False


def test_parse_empty_ps_output(parser):
    """Test parsing empty output."""
    containers = parser.parse_ps_output("", host="test-host")
    assert containers == []


def test_parse_stats_output(parser, sample_stats_output):
    """Test parsing docker stats output."""
    stats = parser.parse_stats_output(sample_stats_output, host="test-host")

    assert len(stats) == 2
    assert "web-server" in stats
    assert "cache" in stats

    web_stats = stats["web-server"]
    assert web_stats["cpu_percent"] == 2.45
    assert web_stats["memory_percent"] == 1.23
    assert web_stats["memory_usage"] == "128MiB / 4GiB"


def test_parse_percentage(parser):
    """Test percentage parsing."""
    assert parser._parse_percentage("45.67%") == 45.67
    assert parser._parse_percentage("0.00%") == 0.0
    assert parser._parse_percentage("100%") == 100.0
    assert parser._parse_percentage("invalid") is None


def test_merge_ps_and_stats(parser, sample_ps_output, sample_stats_output):
    """Test merging container list with stats."""
    containers = parser.parse_ps_output(sample_ps_output, host="test-host")
    stats = parser.parse_stats_output(sample_stats_output, host="test-host")

    merged = parser.merge_ps_and_stats(containers, stats)

    # Check that stats were merged
    web = next(c for c in merged if c.name == "web-server")
    assert web.cpu_percent == 2.45
    assert web.memory_percent == 1.23
    assert web.memory_usage == "128MiB / 4GiB"

    # Container without stats should have None values
    db = next(c for c in merged if c.name == "database")
    assert db.cpu_percent is None
    assert db.memory_percent is None


def test_container_info_to_dict():
    """Test ContainerInfo to dict conversion."""
    container = ContainerInfo(
        id="abc123",
        name="test-container",
        image="nginx:latest",
        status="Up 2 days",
        state="running",
        host="test-host",
    )

    data = container.to_dict()

    assert data["id"] == "abc123"
    assert data["name"] == "test-container"
    assert data["image"] == "nginx:latest"
    assert data["state"] == "running"
    assert data["host"] == "test-host"


def test_parse_invalid_json(parser):
    """Test parsing invalid JSON."""
    invalid_output = "not json\n{incomplete"
    containers = parser.parse_ps_output(invalid_output, host="test-host")

    # Should handle errors gracefully and skip invalid lines
    assert containers == []
