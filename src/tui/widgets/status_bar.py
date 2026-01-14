"""Status bar widget for Textual TUI."""

from datetime import datetime
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static
from textual.reactive import reactive

from ...i18n import get_translator


class StatusBarWidget(Widget):
    """Widget displaying status information at the bottom."""

    DEFAULT_CSS = """
    StatusBarWidget {
        height: 3;
        dock: bottom;
        background: $panel;
        border-top: solid $primary;
    }

    StatusBarWidget > Static {
        padding: 0 1;
        height: 100%;
        content-align: left middle;
    }

    StatusBarWidget .status-left {
        dock: left;
        width: 1fr;
    }

    StatusBarWidget .status-right {
        dock: right;
        width: auto;
    }
    """

    total_hosts: reactive[int] = reactive(0)
    connected_hosts: reactive[int] = reactive(0)
    total_containers: reactive[int] = reactive(0)
    running_containers: reactive[int] = reactive(0)
    last_update: reactive[str] = reactive("")
    status_message: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        yield Static("", id="status-left", classes="status-left")
        yield Static("", id="status-right", classes="status-right")

    def watch_total_hosts(self, value: int) -> None:
        """React to total_hosts change."""
        self._update_display()

    def watch_connected_hosts(self, value: int) -> None:
        """React to connected_hosts change."""
        self._update_display()

    def watch_total_containers(self, value: int) -> None:
        """React to total_containers change."""
        self._update_display()

    def watch_running_containers(self, value: int) -> None:
        """React to running_containers change."""
        self._update_display()

    def watch_last_update(self, value: str) -> None:
        """React to last_update change."""
        self._update_display()

    def watch_status_message(self, value: str) -> None:
        """React to status_message change."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the status bar display."""
        t = get_translator()

        # Left side - statistics
        left_text = (
            f"[bold cyan]{t.get('status_bar.hosts')}:[/bold cyan] {self.connected_hosts}/{self.total_hosts}  "
            f"[bold green]{t.get('status_bar.containers')}:[/bold green] {self.running_containers}/{self.total_containers}  "
        )

        if self.status_message:
            left_text += f"[yellow]{self.status_message}[/yellow]"

        # Right side - shortcuts and time
        right_text = (
            f"[dim]Last update: {self.last_update}[/dim]  "
            f"{t.get('status_bar.shortcuts')}"
        )

        # Update widgets
        try:
            self.query_one("#status-left", Static).update(left_text)
            self.query_one("#status-right", Static).update(right_text)
        except Exception:
            # Widgets might not be mounted yet
            pass

    def update_stats(
        self,
        total_hosts: int,
        connected_hosts: int,
        total_containers: int,
        running_containers: int,
    ) -> None:
        """
        Update statistics.

        Args:
            total_hosts: Total number of hosts.
            connected_hosts: Number of connected hosts.
            total_containers: Total number of containers.
            running_containers: Number of running containers.
        """
        self.total_hosts = total_hosts
        self.connected_hosts = connected_hosts
        self.total_containers = total_containers
        self.running_containers = running_containers
        self.last_update = datetime.now().strftime("%H:%M:%S")

    def set_message(self, message: str) -> None:
        """
        Set status message.

        Args:
            message: Message to display.
        """
        self.status_message = message

    def clear_message(self) -> None:
        """Clear status message."""
        self.status_message = ""
