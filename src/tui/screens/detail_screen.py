"""Container detail screen for Textual TUI."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static, Button
from rich.table import Table as RichTable
from rich.panel import Panel
from rich.syntax import Syntax
from rich.console import Group
import json

from ...i18n import get_translator


class DetailScreen(Screen):
    """Screen showing detailed container information."""

    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("q", "dismiss", "Back"),
    ]

    def __init__(
        self,
        container_id: str,
        container_name: str,
        container_details: dict = None,
        *args,
        **kwargs,
    ):
        """
        Initialize detail screen.

        Args:
            container_id: Container ID.
            container_name: Container name.
            container_details: Optional detailed container info.
        """
        super().__init__(*args, **kwargs)
        self.container_id = container_id
        self.container_name = container_name
        self.container_details = container_details or {}

    def compose(self) -> ComposeResult:
        """Compose the detail screen."""
        t = get_translator()
        yield Header(show_clock=True)

        with Container(id="detail-outer-container"):
            with VerticalScroll(id="detail-container"):
                yield Static(
                    f"[bold cyan]{t.get('detail.title')}: {self.container_name}[/bold cyan]",
                    id="detail-title",
                )
                yield Static("", id="detail-content")
                yield Button(t.get("detail.back_button"), id="back-button", variant="primary")

        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount."""
        self._update_content()

    def _update_content(self) -> None:
        """Update the detail content."""
        t = get_translator()
        if not self.container_details:
            content = Panel(
                f"[yellow]{t.get('detail.no_info')}[/yellow]",
                title=t.get("detail.notice_title"),
                border_style="yellow",
            )
        else:
            content = self._create_detail_display()

        try:
            self.query_one("#detail-content", Static).update(content)
        except Exception as e:
            # Fallback if update fails
            pass

    def _create_detail_display(self) -> Panel:
        """Create detailed information display."""
        t = get_translator()
        details = self.container_details

        # Create tables for different sections
        output = []

        # Basic information
        basic_table = RichTable(show_header=False, box=None, padding=(0, 1))
        basic_table.add_column("Property", style="cyan", width=20)
        basic_table.add_column("Value", style="white")

        basic_table.add_row(t.get("detail.basic_info.id"), details.get("Id", "N/A")[:12])
        basic_table.add_row(t.get("detail.basic_info.name"), details.get("Name", "N/A").lstrip("/"))
        basic_table.add_row(t.get("detail.basic_info.host"), details.get("Host", "N/A"))
        basic_table.add_row(t.get("detail.basic_info.image"), details.get("Image", details.get("Config", {}).get("Image", "N/A")))
        basic_table.add_row(t.get("detail.basic_info.status"), details.get("Status", "N/A"))

        if details.get("Created"):
            basic_table.add_row(t.get("detail.basic_info.created"), details.get("Created"))

        state = details.get("State", {})
        if isinstance(state, dict):
            basic_table.add_row(
                t.get("detail.basic_info.state"),
                state.get("Status", "N/A")
            )
            basic_table.add_row(
                t.get("detail.basic_info.running"),
                t.get("detail.basic_info.yes") if state.get("Running") else t.get("detail.basic_info.no")
            )

        output.append(Panel(basic_table, title=f"[bold]{t.get('detail.basic_info.title')}[/bold]", border_style="cyan"))
        output.append("\n")

        # Resource usage stats
        stats = details.get("Stats", {})
        if stats and any(stats.values()):
            stats_table = RichTable(show_header=False, box=None, padding=(0, 1))
            stats_table.add_column("Metric", style="cyan", width=20)
            stats_table.add_column("Value", style="white")

            if stats.get("CPUPerc") is not None:
                stats_table.add_row(t.get("detail.resource_usage.cpu_usage"), f"{stats.get('CPUPerc'):.1f}%")
            if stats.get("MemUsage"):
                stats_table.add_row(t.get("detail.resource_usage.memory_usage"), stats.get("MemUsage"))
            if stats.get("MemPerc") is not None:
                stats_table.add_row(t.get("detail.resource_usage.memory_percent"), f"{stats.get('MemPerc'):.1f}%")
            if stats.get("NetIO"):
                stats_table.add_row(t.get("detail.resource_usage.network_io"), stats.get("NetIO"))
            if stats.get("BlockIO"):
                stats_table.add_row(t.get("detail.resource_usage.block_io"), stats.get("BlockIO"))

            output.append(Panel(stats_table, title=f"[bold]{t.get('detail.resource_usage.title')}[/bold]", border_style="green"))
            output.append("\n")

        # Network settings
        network_settings = details.get("NetworkSettings", {})
        if network_settings:
            network_table = RichTable(show_header=False, box=None, padding=(0, 1))
            network_table.add_column("Property", style="cyan", width=20)
            network_table.add_column("Value", style="white")

            if network_settings.get("IPAddress"):
                network_table.add_row(t.get("detail.network.ip_address"), network_settings.get("IPAddress"))
            if network_settings.get("Gateway"):
                network_table.add_row(t.get("detail.network.gateway"), network_settings.get("Gateway"))

            # Handle ports - can be string or dict
            ports = network_settings.get("Ports")
            if ports:
                if isinstance(ports, str):
                    network_table.add_row(t.get("detail.network.ports"), ports)
                elif isinstance(ports, dict):
                    port_list = []
                    for container_port, host_bindings in ports.items():
                        if host_bindings:
                            for binding in host_bindings:
                                host_port = binding.get("HostPort", "")
                                port_list.append(f"{host_port} -> {container_port}")
                        else:
                            port_list.append(container_port)
                    if port_list:
                        network_table.add_row(t.get("detail.network.ports"), ", ".join(port_list))

            if network_table.row_count > 0:
                output.append(Panel(network_table, title=f"[bold]{t.get('detail.network.title')}[/bold]", border_style="blue"))
                output.append("\n")

        # Mounts/Volumes
        mounts = details.get("Mounts", [])
        if mounts:
            mounts_table = RichTable(show_header=True, box=None, padding=(0, 1))
            mounts_table.add_column(t.get("detail.volumes.type"), style="cyan")
            mounts_table.add_column(t.get("detail.volumes.source"), style="white")
            mounts_table.add_column(t.get("detail.volumes.destination"), style="white")

            for mount in mounts[:5]:  # Show first 5
                mounts_table.add_row(
                    mount.get("Type", ""),
                    mount.get("Source", "")[:40],
                    mount.get("Destination", "")
                )

            output.append(Panel(mounts_table, title=f"[bold]{t.get('detail.volumes.title')}[/bold]", border_style="yellow"))
            output.append("\n")

        # Environment variables
        env = details.get("Config", {}).get("Env", [])
        if env:
            env_content = "\n".join(env[:10])  # Show first 10
            env_panel = Panel(
                env_content,
                title=f"[bold]{t.get('detail.environment.title')}[/bold]",
                border_style="magenta",
            )
            output.append(env_panel)
            output.append("\n")

        # Combine all output in a main panel
        group = Group(*output)
        return Panel(
            group,
            title=f"[bold cyan]{t.get('detail.title')}: {self.container_name}[/bold cyan]",
            border_style="bright_blue",
            padding=(1, 2),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "back-button":
            self.dismiss()

    def action_dismiss(self) -> None:
        """Dismiss the detail screen."""
        self.app.pop_screen()

    def set_container_details(self, details: dict) -> None:
        """
        Set container details and update display.

        Args:
            details: Container details dictionary.
        """
        self.container_details = details
        self._update_content()
