"""Tests for DataAggregator."""

import pytest
import json
from src.aggregator.data import DataAggregator
from src.docker.monitor import HostStatus
from src.docker.parser import ContainerInfo


@pytest.fixture
def aggregator():
    """Create aggregator instance."""
    return DataAggregator()


@pytest.fixture
def sample_host_statuses():
    """Create sample host statuses."""
    containers_host1 = [
        ContainerInfo(
            id="abc123",
            name="web",
            image="nginx:latest",
            status="Up 2 days",
            state="running",
            host="host1",
            cpu_percent=2.5,
            memory_usage="128MB / 4GB",
            memory_percent=3.2,
        ),
        ContainerInfo(
            id="def456",
            name="app",
            image="python:3.9",
            status="Up 1 day",
            state="running",
            host="host1",
            cpu_percent=5.0,
            memory_usage="256MB / 4GB",
            memory_percent=6.4,
        ),
    ]

    containers_host2 = [
        ContainerInfo(
            id="ghi789",
            name="db",
            image="postgres:13",
            status="Exited (0) 1 hour ago",
            state="exited",
            host="host2",
        ),
    ]

    host1 = HostStatus(
        host_name="host1",
        hostname="192.168.1.10",
        connected=True,
        docker_available=True,
        docker_version="Docker version 20.10.0",
        containers=containers_host1,
    )

    host2 = HostStatus(
        host_name="host2",
        hostname="192.168.1.11",
        connected=True,
        docker_available=True,
        docker_version="Docker version 20.10.0",
        containers=containers_host2,
    )

    host3 = HostStatus(
        host_name="host3",
        hostname="192.168.1.12",
        connected=False,
        docker_available=False,
        error="Connection timeout",
    )

    return [host1, host2, host3]


def test_aggregate_hosts(aggregator, sample_host_statuses):
    """Test host aggregation."""
    result = aggregator.aggregate_hosts(sample_host_statuses)

    assert "timestamp" in result
    assert "summary" in result
    assert "hosts" in result
    assert "containers" in result
    assert "failures" in result

    summary = result["summary"]
    assert summary["total_hosts"] == 3
    assert summary["connected_hosts"] == 2
    assert summary["failed_hosts"] == 1
    assert summary["total_containers"] == 3
    assert summary["running_containers"] == 2
    assert summary["stopped_containers"] == 1

    # Check failures
    failures = result["failures"]
    assert len(failures) == 1
    assert failures[0]["host"] == "host3"
    assert failures[0]["error"] == "Connection timeout"


def test_to_json(aggregator, sample_host_statuses):
    """Test JSON output."""
    json_output = aggregator.to_json(sample_host_statuses, pretty=True)

    # Should be valid JSON
    data = json.loads(json_output)

    assert data["summary"]["total_hosts"] == 3
    assert len(data["containers"]) == 3
    assert len(data["hosts"]) == 3


def test_to_csv(aggregator, sample_host_statuses):
    """Test CSV output."""
    csv_output = aggregator.to_csv(sample_host_statuses)

    lines = csv_output.strip().split("\n")

    # Check header
    assert "host,name,id,image,status,state" in lines[0]

    # Check data rows
    assert len(lines) == 4  # header + 3 containers


def test_get_statistics(aggregator, sample_host_statuses):
    """Test statistics calculation."""
    stats = aggregator.get_statistics(sample_host_statuses)

    assert "summary" in stats
    assert "images" in stats
    assert "states" in stats
    assert "top_images" in stats

    # Check image counts
    images = stats["images"]
    assert "nginx" in images
    assert "python" in images
    assert "postgres" in images

    # Check states
    states = stats["states"]
    assert states["running"] == 2
    assert states["exited"] == 1


def test_to_table(aggregator, sample_host_statuses):
    """Test table output."""
    table_output = aggregator.to_table(sample_host_statuses)

    # Should contain summary information
    assert "Docker Monitoring Summary" in table_output
    assert "Host Status" in table_output
    assert "Total Hosts" in table_output
    assert "3" in table_output  # Total hosts count


def test_empty_hosts(aggregator):
    """Test with no hosts."""
    result = aggregator.aggregate_hosts([])

    summary = result["summary"]
    assert summary["total_hosts"] == 0
    assert summary["total_containers"] == 0
    assert len(result["containers"]) == 0
