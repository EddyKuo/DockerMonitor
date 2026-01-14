"""Host list widget for Textual TUI."""

from typing import List, Optional
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, ListView, ListItem, Label
from textual.reactive import reactive
from textual.message import Message

from ...i18n import get_translator


class HostListItem(ListItem):
    """A single host item in the list."""

    def __init__(
        self,
        host_name: str,
        hostname: str,
        connected: bool = False,
        container_count: int = 0,
        running_count: int = 0,
        *args,
        **kwargs,
    ):
        """
        Initialize host list item.

        Args:
            host_name: Display name of the host.
            hostname: IP address or hostname.
            connected: Whether host is connected.
            container_count: Total number of containers.
            running_count: Number of running containers.
        """
        super().__init__(*args, **kwargs)
        self.host_name = host_name
        self.hostname = hostname
        self.connected = connected
        self.container_count = container_count
        self.running_count = running_count

    def compose(self) -> ComposeResult:
        """Compose the host item."""
        t = get_translator()
        status_icon = "●" if self.connected else "○"
        status_color = "green" if self.connected else "red"

        yield Label(
            f"[{status_color}]{status_icon}[/{status_color}] "
            f"[bold]{self.host_name}[/bold]\n"
            f"  [dim]{self.hostname}[/dim]\n"
            f"  [cyan]{self.running_count}[/cyan]/{self.container_count} {t.get('container_table.title').lower()}"
        )


class HostListWidget(Widget):
    """Widget displaying list of monitored hosts."""

    DEFAULT_CSS = """
    HostListWidget {
        width: 30;
        border: solid $primary;
    }

    HostListWidget > ListView {
        background: $surface;
        height: 100%;
    }

    HostListWidget ListItem {
        padding: 1;
    }

    HostListWidget ListItem:hover {
        background: $boost;
    }

    HostListWidget ListItem.-selected {
        background: $accent;
    }
    """

    selected_host: reactive[Optional[str]] = reactive(None)

    class HostSelected(Message):
        """Message sent when a host is selected."""

        def __init__(self, host_name: str, hostname: str):
            """Initialize message."""
            super().__init__()
            self.host_name = host_name
            self.hostname = hostname

    def __init__(self, *args, **kwargs):
        """Initialize host list widget."""
        super().__init__(*args, **kwargs)
        self._hosts = []

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        t = get_translator()
        yield Static(f"[bold]{t.get('host_list.title')}[/bold]", classes="widget-title")
        yield ListView(id="host-list")

    def update_hosts(self, host_statuses: List) -> None:
        """
        Update the list of hosts.

        Args:
            host_statuses: List of HostStatus objects.
        """
        self._hosts = host_statuses

        # Get the ListView
        list_view = self.query_one("#host-list", ListView)
        list_view.clear()

        # Add host items
        for host_status in host_statuses:
            item = HostListItem(
                host_name=host_status.host_name,
                hostname=host_status.hostname,
                connected=host_status.connected,
                container_count=host_status.container_count,
                running_count=host_status.running_count,
            )
            list_view.append(item)

        # Select first host by default
        if host_statuses:
            self.selected_host = host_statuses[0].host_name

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle host selection."""
        if isinstance(event.item, HostListItem):
            self.selected_host = event.item.host_name
            self.post_message(
                self.HostSelected(
                    host_name=event.item.host_name,
                    hostname=event.item.hostname,
                )
            )

    def get_selected_host(self) -> Optional[str]:
        """Get currently selected host name."""
        return self.selected_host

    def get_host_count(self) -> int:
        """Get total number of hosts."""
        return len(self._hosts)

    def get_connected_count(self) -> int:
        """Get number of connected hosts."""
        return sum(1 for h in self._hosts if h.connected)
