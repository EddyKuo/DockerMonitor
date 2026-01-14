"""Container table widget for Textual TUI."""

from typing import List, Optional
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text

from ...i18n import get_translator


class ContainerTableWidget(Widget):
    """Widget displaying Docker containers in a table."""

    DEFAULT_CSS = """
    ContainerTableWidget {
        height: 100%;
    }

    ContainerTableWidget > DataTable {
        height: 100%;
    }

    ContainerTableWidget .running {
        color: $success;
    }

    ContainerTableWidget .exited {
        color: $error;
    }

    ContainerTableWidget .paused {
        color: $warning;
    }
    """

    current_host: reactive[Optional[str]] = reactive(None)
    filter_text: reactive[str] = reactive("")
    sort_column: reactive[str] = reactive("name")

    class ContainerSelected(Message):
        """Message sent when a container is selected."""

        def __init__(self, container_id: str, container_name: str):
            """Initialize message."""
            super().__init__()
            self.container_id = container_id
            self.container_name = container_name

    def __init__(self, *args, **kwargs):
        """Initialize container table widget."""
        super().__init__(*args, **kwargs)
        self._containers = []
        self._all_containers = []

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        t = get_translator()
        yield Static(
            f"[bold]{t.get('container_table.title')}[/bold] - [dim]Press Enter for details[/dim]",
            classes="widget-title",
        )
        yield DataTable(id="container-table", cursor_type="row")

    def on_mount(self) -> None:
        """Initialize the table when mounted."""
        t = get_translator()
        table = self.query_one("#container-table", DataTable)

        # Add columns
        table.add_column(t.get("container_table.column_name"), key="name", width=20)
        table.add_column(t.get("container_table.column_image"), key="image", width=25)
        table.add_column(t.get("container_table.column_status"), key="status", width=15)
        table.add_column(t.get("container_table.column_state"), key="state", width=10)
        table.add_column(t.get("container_table.column_cpu"), key="cpu", width=8)
        table.add_column(t.get("container_table.column_memory"), key="memory", width=12)
        table.add_column(t.get("container_table.column_ports"), key="ports", width=20)

        # Enable cursor
        table.cursor_type = "row"
        table.zebra_stripes = True

    def update_containers(self, containers: List, host_name: Optional[str] = None) -> None:
        """
        Update the container list.

        Args:
            containers: List of ContainerInfo objects.
            host_name: Optional host name to filter by.
        """
        self._all_containers = containers

        # Filter by host if specified
        if host_name:
            self._containers = [c for c in containers if c.host == host_name]
            self.current_host = host_name
        else:
            self._containers = containers
            self.current_host = None

        self._refresh_table()

    def _refresh_table(self) -> None:
        """Refresh the table display."""
        table = self.query_one("#container-table", DataTable)
        table.clear()

        # Apply filter
        containers = self._containers
        if self.filter_text:
            filter_lower = self.filter_text.lower()
            containers = [
                c
                for c in containers
                if filter_lower in c.name.lower()
                or filter_lower in c.image.lower()
                or filter_lower in c.state.lower()
            ]

        # Sort containers
        containers = self._sort_containers(containers)

        # Add rows
        for container in containers:
            # Determine state color
            state_color = self._get_state_color(container.state)

            # Format row
            row = [
                Text(container.name[:18] if len(container.name) > 18 else container.name),
                Text(container.image[:23] if len(container.image) > 23 else container.image),
                Text(container.status[:13] if len(container.status) > 13 else container.status),
                Text(container.state, style=state_color),
                Text(f"{container.cpu_percent:.1f}" if container.cpu_percent else "-"),
                Text(container.memory_usage or "-"),
                Text(container.ports[:18] if container.ports and len(container.ports) > 18 else (container.ports or "-")),
            ]

            table.add_row(*row, key=container.id)

    def _sort_containers(self, containers: List) -> List:
        """Sort containers by the current sort column."""
        sort_key = self.sort_column

        if sort_key == "name":
            return sorted(containers, key=lambda c: c.name.lower())
        elif sort_key == "image":
            return sorted(containers, key=lambda c: c.image.lower())
        elif sort_key == "status":
            return sorted(containers, key=lambda c: c.status.lower())
        elif sort_key == "state":
            return sorted(containers, key=lambda c: c.state.lower())
        elif sort_key == "cpu":
            return sorted(
                containers, key=lambda c: c.cpu_percent or 0, reverse=True
            )
        elif sort_key == "memory":
            return sorted(
                containers, key=lambda c: c.memory_percent or 0, reverse=True
            )
        else:
            return containers

    def _get_state_color(self, state: str) -> str:
        """Get color for container state."""
        state_lower = state.lower()
        if state_lower == "running":
            return "green"
        elif state_lower in ("exited", "dead"):
            return "red"
        elif state_lower == "paused":
            return "yellow"
        elif state_lower in ("created", "restarting"):
            return "cyan"
        else:
            return "white"

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle container selection."""
        container_id = event.row_key.value
        container = next((c for c in self._containers if c.id == container_id), None)

        if container:
            self.post_message(
                self.ContainerSelected(
                    container_id=container.id,
                    container_name=container.name,
                )
            )

    def set_filter(self, text: str) -> None:
        """
        Set filter text.

        Args:
            text: Filter text to apply.
        """
        self.filter_text = text
        self._refresh_table()

    def set_sort_column(self, column: str) -> None:
        """
        Set sort column.

        Args:
            column: Column name to sort by.
        """
        self.sort_column = column
        self._refresh_table()

    def get_container_count(self) -> int:
        """Get total number of containers displayed."""
        return len(self._containers)

    def get_running_count(self) -> int:
        """Get number of running containers."""
        return sum(1 for c in self._containers if c.is_running())

    def get_stopped_count(self) -> int:
        """Get number of stopped containers."""
        return sum(1 for c in self._containers if not c.is_running())

    def get_total_cpu(self) -> float:
        """Get total CPU usage."""
        return sum(c.cpu_percent or 0 for c in self._containers if c.is_running())

    def clear(self) -> None:
        """Clear the table."""
        table = self.query_one("#container-table", DataTable)
        table.clear()
        self._containers = []
