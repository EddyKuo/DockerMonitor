"""Statistics panel widget for Textual TUI."""

from typing import Dict, List
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Vertical
from rich.table import Table as RichTable
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn

from ...i18n import get_translator


class StatsPanelWidget(Widget):
    """Widget displaying statistics and summary information."""

    DEFAULT_CSS = """
    StatsPanelWidget {
        height: auto;
        max-height: 15;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }

    StatsPanelWidget > Vertical {
        height: auto;
    }

    StatsPanelWidget Static {
        height: auto;
    }
    """

    def __init__(self, *args, **kwargs):
        """Initialize stats panel widget."""
        super().__init__(*args, **kwargs)
        self._stats = {}

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        t = get_translator()
        with Vertical():
            yield Static(f"[bold]{t.get('stats_panel.title')}[/bold]", id="stats-title")
            yield Static("", id="stats-content")

    def update_stats(self, host_statuses: List) -> None:
        """
        Update statistics from host statuses.

        Args:
            host_statuses: List of HostStatus objects.
        """
        # Calculate statistics
        total_hosts = len(host_statuses)
        connected_hosts = sum(1 for h in host_statuses if h.connected)
        failed_hosts = total_hosts - connected_hosts

        total_containers = sum(h.container_count for h in host_statuses)
        running_containers = sum(h.running_count for h in host_statuses)
        stopped_containers = sum(h.stopped_count for h in host_statuses)

        # Collect all containers for analysis
        all_containers = []
        for host in host_statuses:
            all_containers.extend(host.containers)

        # Count by state
        states = {}
        for container in all_containers:
            state = container.state
            states[state] = states.get(state, 0) + 1

        # Count by image
        images = {}
        for container in all_containers:
            image = container.image.split(":")[0]  # Remove tag
            images[image] = images.get(image, 0) + 1

        # Top images
        top_images = sorted(images.items(), key=lambda x: x[1], reverse=True)[:5]

        # Calculate CPU/Memory stats for running containers
        running_with_stats = [
            c for c in all_containers
            if c.is_running() and c.cpu_percent is not None
        ]

        total_cpu = sum(c.cpu_percent for c in running_with_stats)
        avg_cpu = total_cpu / len(running_with_stats) if running_with_stats else 0

        # Create rich table for display
        content = self._create_stats_display(
            total_hosts=total_hosts,
            connected_hosts=connected_hosts,
            failed_hosts=failed_hosts,
            total_containers=total_containers,
            running_containers=running_containers,
            stopped_containers=stopped_containers,
            states=states,
            top_images=top_images,
            avg_cpu=avg_cpu,
        )

        # Update display
        try:
            self.query_one("#stats-content", Static).update(content)
        except Exception:
            pass

    def _create_stats_display(
        self,
        total_hosts: int,
        connected_hosts: int,
        failed_hosts: int,
        total_containers: int,
        running_containers: int,
        stopped_containers: int,
        states: Dict[str, int],
        top_images: List,
        avg_cpu: float,
    ) -> RichTable:
        """Create statistics display table."""
        t = get_translator()

        # Create main table
        table = RichTable(show_header=False, box=None, padding=(0, 1))
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="bold")

        # Host stats
        table.add_row(t.get("stats_panel.total_hosts"), f"{total_hosts}")
        table.add_row(
            t.get("stats_panel.connected_hosts"),
            f"[green]{connected_hosts}[/green]" if connected_hosts > 0 else "0"
        )
        if failed_hosts > 0:
            table.add_row("Failed", f"[red]{failed_hosts}[/red]")

        table.add_row("", "")  # Spacer

        # Container stats
        table.add_row(t.get("stats_panel.total_containers"), f"{total_containers}")
        table.add_row(
            t.get("stats_panel.running_containers"),
            f"[green]{running_containers}[/green]" if running_containers > 0 else "0"
        )
        table.add_row(
            t.get("stats_panel.stopped_containers"),
            f"[red]{stopped_containers}[/red]" if stopped_containers > 0 else "0"
        )

        # Other states
        for state, count in states.items():
            if state.lower() not in ("running", "exited"):
                table.add_row(f"{state.capitalize()}", f"{count}")

        table.add_row("", "")  # Spacer

        # Performance
        if avg_cpu > 0:
            table.add_row(t.get("stats_panel.cpu_usage"), f"{avg_cpu:.1f}%")

        table.add_row("", "")  # Spacer

        # Top images
        if top_images:
            table.add_row("[bold]Top Images[/bold]", "")
            for image, count in top_images[:3]:
                # Truncate long image names
                display_name = image if len(image) <= 18 else image[:15] + "..."
                table.add_row(f"  {display_name}", f"{count}")

        return table

    def clear(self) -> None:
        """Clear statistics."""
        try:
            self.query_one("#stats-content", Static).update("")
        except Exception:
            pass
