"""Main screen for Textual TUI."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer

from ..widgets import (
    HostListWidget,
    ContainerTableWidget,
    StatusBarWidget,
    StatsPanelWidget,
)
from ...i18n import get_translator


class MainScreen(Screen):
    """Main monitoring screen."""

    BINDINGS = [
        ("h", "show_help", "Help"),
        ("r", "refresh", "Refresh"),
        ("f", "filter", "Filter"),
        ("s", "sort", "Sort"),
        ("l", "switch_language", "Language"),
        ("q", "quit", "Quit"),
        ("/", "search", "Search"),
    ]

    def __init__(self, *args, **kwargs):
        """Initialize main screen."""
        super().__init__(*args, **kwargs)
        self._host_statuses = []

    def compose(self) -> ComposeResult:
        """Compose the main screen."""
        yield Header(show_clock=True)

        with Container(id="main-container"):
            # Statistics panel at top
            yield StatsPanelWidget(id="stats-panel")

            # Main content area
            with Horizontal(id="content-area"):
                # Left sidebar - host list
                yield HostListWidget(id="host-list")

                # Right content - container table
                with Vertical(id="main-content"):
                    yield ContainerTableWidget(id="container-table")

        # Status bar at bottom
        yield StatusBarWidget(id="status-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Handle screen mount."""
        # Set initial focus to container table
        self.query_one("#container-table").focus()

    def update_data(self, host_statuses: list) -> None:
        """
        Update all widgets with new data.

        Args:
            host_statuses: List of HostStatus objects.
        """
        self._host_statuses = host_statuses

        # Update host list
        host_list = self.query_one("#host-list", HostListWidget)
        host_list.update_hosts(host_statuses)

        # Update stats panel
        stats_panel = self.query_one("#stats-panel", StatsPanelWidget)
        stats_panel.update_stats(host_statuses)

        # Collect all containers
        all_containers = []
        for host_status in host_statuses:
            all_containers.extend(host_status.containers)

        # Update container table (show all containers initially)
        container_table = self.query_one("#container-table", ContainerTableWidget)
        container_table.update_containers(all_containers)

        # Update status bar
        self._update_status_bar()

    def _update_status_bar(self) -> None:
        """Update status bar with current statistics."""
        status_bar = self.query_one("#status-bar", StatusBarWidget)
        container_table = self.query_one("#container-table", ContainerTableWidget)
        host_list = self.query_one("#host-list", HostListWidget)

        status_bar.update_stats(
            total_hosts=host_list.get_host_count(),
            connected_hosts=host_list.get_connected_count(),
            total_containers=container_table.get_container_count(),
            running_containers=container_table.get_running_count(),
        )

    def on_host_list_widget_host_selected(
        self, message: HostListWidget.HostSelected
    ) -> None:
        """Handle host selection from host list."""
        # Filter containers by selected host
        container_table = self.query_one("#container-table", ContainerTableWidget)

        # Collect all containers
        all_containers = []
        for host_status in self._host_statuses:
            all_containers.extend(host_status.containers)

        # Update with filter
        container_table.update_containers(all_containers, host_name=message.host_name)
        self._update_status_bar()

    def on_container_table_widget_container_selected(
        self, message: ContainerTableWidget.ContainerSelected
    ) -> None:
        """Handle container selection - show detail screen."""
        # Import here to avoid circular dependency
        from .detail_screen import DetailScreen

        # Find the container in our data
        container_data = None
        for host_status in self._host_statuses:
            for container in host_status.containers:
                if container.id == message.container_id:
                    # Convert ContainerInfo to detail dict
                    container_data = {
                        "Id": container.id,
                        "Name": container.name,
                        "Image": container.image,
                        "Status": container.status,
                        "State": {"Status": container.state, "Running": container.is_running()},
                        "Created": container.created,
                        "Host": container.host,
                        "Config": {
                            "Image": container.image,
                        },
                        "NetworkSettings": {
                            "Ports": container.ports,
                        },
                        "Stats": {
                            "CPUPerc": container.cpu_percent,
                            "MemUsage": container.memory_usage,
                            "MemPerc": container.memory_percent,
                            "NetIO": container.net_io,
                            "BlockIO": container.block_io,
                        }
                    }
                    break
            if container_data:
                break

        # Create and push detail screen
        detail_screen = DetailScreen(
            container_id=message.container_id,
            container_name=message.container_name,
            container_details=container_data or {},
        )
        self.app.push_screen(detail_screen)

    def action_show_help(self) -> None:
        """Show help screen."""
        from .help_screen import HelpScreen
        self.app.push_screen(HelpScreen())

    def action_refresh(self) -> None:
        """Refresh data."""
        from ...utils.logger import get_logger
        logger = get_logger()
        logger.info("*** action_refresh() called in MainScreen ***")

        t = get_translator()
        status_bar = self.query_one("#status-bar", StatusBarWidget)
        status_bar.set_message(t.get("messages.refreshing"))

        # Directly call app's public refresh API
        logger.info("*** Calling app.request_refresh() ***")
        self.app.request_refresh()
        logger.info("*** app.request_refresh() returned ***")

    def action_filter(self) -> None:
        """Show filter dialog."""
        t = get_translator()
        # TODO: Implement filter dialog
        status_bar = self.query_one("#status-bar", StatusBarWidget)
        status_bar.set_message(t.get("messages.filter_not_implemented"))

    def action_sort(self) -> None:
        """Cycle through sort options."""
        t = get_translator()
        container_table = self.query_one("#container-table", ContainerTableWidget)

        # Cycle through sort columns
        sort_columns = ["name", "image", "status", "state", "cpu", "memory"]
        current = container_table.sort_column
        try:
            current_idx = sort_columns.index(current)
            next_idx = (current_idx + 1) % len(sort_columns)
            next_column = sort_columns[next_idx]
        except ValueError:
            next_column = "name"

        container_table.set_sort_column(next_column)

        status_bar = self.query_one("#status-bar", StatusBarWidget)
        status_bar.set_message(t.get("messages.sorted_by", column=next_column))

    def action_search(self) -> None:
        """Show search/filter input."""
        t = get_translator()
        # TODO: Implement search input
        status_bar = self.query_one("#status-bar", StatusBarWidget)
        status_bar.set_message(t.get("messages.search_not_implemented"))

    def action_switch_language(self) -> None:
        """Switch language."""
        self.app.switch_language()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
