"""Data aggregator for multi-host Docker monitoring."""

import json
import csv
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from ..docker.monitor import HostStatus
from ..docker.parser import ContainerInfo
from ..utils.logger import get_logger


class DataAggregator:
    """
    Aggregates and formats data from multiple hosts.

    Supports multiple output formats:
    - JSON
    - CSV
    - Table (for display)
    - Dictionary (for TUI)
    """

    def __init__(self):
        """Initialize DataAggregator."""
        self.logger = get_logger()

    def aggregate_hosts(self, host_statuses: List[HostStatus]) -> Dict[str, Any]:
        """
        Aggregate data from multiple hosts.

        Args:
            host_statuses: List of HostStatus objects.

        Returns:
            Aggregated data dictionary.
        """
        total_containers = 0
        total_running = 0
        total_stopped = 0
        connected_hosts = 0
        failed_hosts = []
        all_containers = []

        for host_status in host_statuses:
            if host_status.connected and host_status.docker_available:
                connected_hosts += 1
                total_containers += host_status.container_count
                total_running += host_status.running_count
                total_stopped += host_status.stopped_count
                all_containers.extend(host_status.containers)
            else:
                failed_hosts.append(
                    {
                        "host": host_status.host_name,
                        "error": host_status.error or "Unknown error",
                    }
                )

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_hosts": len(host_statuses),
                "connected_hosts": connected_hosts,
                "failed_hosts": len(failed_hosts),
                "total_containers": total_containers,
                "running_containers": total_running,
                "stopped_containers": total_stopped,
            },
            "hosts": [self._host_status_to_dict(hs) for hs in host_statuses],
            "containers": [c.to_dict() for c in all_containers],
            "failures": failed_hosts,
        }

    def _host_status_to_dict(self, host_status: HostStatus) -> Dict[str, Any]:
        """Convert HostStatus to dictionary."""
        return {
            "host_name": host_status.host_name,
            "hostname": host_status.hostname,
            "connected": host_status.connected,
            "docker_available": host_status.docker_available,
            "docker_version": host_status.docker_version,
            "container_count": host_status.container_count,
            "running_count": host_status.running_count,
            "stopped_count": host_status.stopped_count,
            "error": host_status.error,
        }

    def to_json(
        self, host_statuses: List[HostStatus], pretty: bool = True
    ) -> str:
        """
        Export data to JSON format.

        Args:
            host_statuses: List of HostStatus objects.
            pretty: If True, format with indentation.

        Returns:
            JSON string.
        """
        data = self.aggregate_hosts(host_statuses)

        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(data, ensure_ascii=False)

    def to_csv(
        self, host_statuses: List[HostStatus], output_file: str = None
    ) -> str:
        """
        Export container data to CSV format.

        Args:
            host_statuses: List of HostStatus objects.
            output_file: Optional file path to save CSV.

        Returns:
            CSV string.
        """
        # Collect all containers
        all_containers = []
        for host_status in host_statuses:
            all_containers.extend(host_status.containers)

        if not all_containers:
            return ""

        # Define CSV fields
        fieldnames = [
            "host",
            "name",
            "id",
            "image",
            "status",
            "state",
            "created",
            "ports",
            "cpu_percent",
            "memory_usage",
            "memory_percent",
        ]

        # Write CSV
        import io

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for container in all_containers:
            row = {
                "host": container.host or "",
                "name": container.name,
                "id": container.id[:12],  # Short ID
                "image": container.image,
                "status": container.status,
                "state": container.state,
                "created": container.created or "",
                "ports": container.ports or "",
                "cpu_percent": container.cpu_percent or "",
                "memory_usage": container.memory_usage or "",
                "memory_percent": container.memory_percent or "",
            }
            writer.writerow(row)

        csv_data = output.getvalue()
        output.close()

        # Save to file if specified
        if output_file:
            try:
                Path(output_file).write_text(csv_data, encoding="utf-8")
                self.logger.info(f"CSV data saved to {output_file}")
            except Exception as e:
                self.logger.error(f"Failed to save CSV to {output_file}: {e}")

        return csv_data

    def to_table(self, host_statuses: List[HostStatus]) -> str:
        """
        Format data as a text table for console display.

        Args:
            host_statuses: List of HostStatus objects.

        Returns:
            Formatted table string.
        """
        from rich.console import Console
        from rich.table import Table
        from rich import box
        import io

        console = Console(file=io.StringIO(), width=120)

        # Summary table
        summary = self.aggregate_hosts(host_statuses)["summary"]

        summary_table = Table(title="Docker Monitoring Summary", box=box.ROUNDED)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="magenta")

        summary_table.add_row("Total Hosts", str(summary["total_hosts"]))
        summary_table.add_row("Connected Hosts", str(summary["connected_hosts"]))
        summary_table.add_row("Total Containers", str(summary["total_containers"]))
        summary_table.add_row("Running", str(summary["running_containers"]))
        summary_table.add_row("Stopped", str(summary["stopped_containers"]))

        console.print(summary_table)
        console.print()

        # Host details table
        host_table = Table(title="Host Status", box=box.ROUNDED)
        host_table.add_column("Host", style="cyan")
        host_table.add_column("IP", style="white")
        host_table.add_column("Connected", style="green")
        host_table.add_column("Docker", style="blue")
        host_table.add_column("Containers", style="magenta")
        host_table.add_column("Running", style="green")
        host_table.add_column("Stopped", style="red")

        for host_status in host_statuses:
            connected_str = "✓" if host_status.connected else "✗"
            docker_str = "✓" if host_status.docker_available else "✗"

            host_table.add_row(
                host_status.host_name,
                host_status.hostname,
                connected_str,
                docker_str,
                str(host_status.container_count),
                str(host_status.running_count),
                str(host_status.stopped_count),
            )

        console.print(host_table)

        # Get output
        output = console.file.getvalue()
        return output

    def save_to_file(
        self,
        host_statuses: List[HostStatus],
        output_dir: str = "output",
        format: str = "json",
    ) -> str:
        """
        Save aggregated data to file.

        Args:
            host_statuses: List of HostStatus objects.
            output_dir: Output directory.
            format: Output format (json, csv).

        Returns:
            Path to saved file.
        """
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"docker_monitor_{timestamp}.{format}"
        file_path = output_path / filename

        # Generate and save data
        if format == "json":
            data = self.to_json(host_statuses, pretty=True)
            file_path.write_text(data, encoding="utf-8")
        elif format == "csv":
            data = self.to_csv(host_statuses)
            file_path.write_text(data, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported format: {format}")

        self.logger.info(f"Data saved to {file_path}")
        return str(file_path)

    def get_statistics(self, host_statuses: List[HostStatus]) -> Dict[str, Any]:
        """
        Calculate statistics across all hosts.

        Args:
            host_statuses: List of HostStatus objects.

        Returns:
            Dictionary with statistical data.
        """
        aggregated = self.aggregate_hosts(host_statuses)

        # Calculate additional statistics
        containers = aggregated["containers"]

        # Group by image
        images = {}
        for container in containers:
            image = container.get("image", "unknown")
            images[image] = images.get(image, 0) + 1

        # Group by state
        states = {}
        for container in containers:
            state = container.get("state", "unknown")
            states[state] = states.get(state, 0) + 1

        return {
            "summary": aggregated["summary"],
            "images": images,
            "states": states,
            "top_images": sorted(images.items(), key=lambda x: x[1], reverse=True)[:10],
        }
