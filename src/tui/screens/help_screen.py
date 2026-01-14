"""Help screen for Textual TUI."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll, Container
from textual.widgets import Header, Footer, Static, Button, Markdown

from ...i18n import get_translator


HELP_TEXT = """
# DockerMonitor - Help

## Overview

DockerMonitor is a terminal-based monitoring tool for Docker containers across multiple hosts.
It connects through an SSH jump host to monitor containers in your private network.

## Keyboard Shortcuts

### Main Screen

| Key | Action | Description |
|-----|--------|-------------|
| `h` | Help | Show this help screen |
| `r` | Refresh | Manually refresh container data |
| `f` | Filter | Filter containers (coming soon) |
| `s` | Sort | Cycle through sort columns |
| `/` | Search | Search containers (coming soon) |
| `q` | Quit | Exit the application |
| `Tab` | Focus | Switch focus between widgets |
| `↑/↓` | Navigate | Move selection up/down in lists |
| `Enter` | Details | View detailed container information |

### Detail Screen

| Key | Action | Description |
|-----|--------|-------------|
| `Esc` | Back | Return to main screen |
| `q` | Back | Return to main screen |

## Widget Overview

### Host List (Left Sidebar)

Shows all configured hosts with:
- **●** Green circle = Connected
- **○** Red circle = Disconnected
- Container count for each host

Click or use arrow keys to select a host and filter containers.

### Container Table (Main Area)

Displays all containers with:
- **Name**: Container name
- **Image**: Docker image
- **Status**: Human-readable status
- **State**: Running, Exited, etc. (color-coded)
- **CPU %**: CPU usage percentage
- **Memory**: Memory usage
- **Ports**: Exposed ports

### Statistics Panel (Top)

Shows summary information:
- Total hosts and connection status
- Container counts by state
- Top images by usage
- Average CPU usage

### Status Bar (Bottom)

Displays:
- Current statistics
- Last update time
- Available keyboard shortcuts

## Configuration

Configuration is loaded from:
- `config/hosts.yaml` - Host definitions
- `.env` - Environment variables

See README.md for detailed configuration instructions.

## Troubleshooting

### Connection Issues

1. Verify SSH keys are properly configured
2. Check jump host connectivity: `ssh user@jumphost`
3. Enable debug logging: `python -m src.main --debug tui`
4. Check logs in `logs/` directory

### No Containers Showing

1. Ensure Docker is running on target hosts
2. Verify user has Docker permissions
3. Check that hosts are marked as `enabled: true` in config

### Performance Issues

1. Reduce number of monitored hosts
2. Increase refresh interval
3. Disable resource stats collection

## About

**DockerMonitor** v0.1.0

Built with:
- Python 3.8+
- Textual (TUI framework)
- AsyncSSH (SSH client)
- Rich (terminal formatting)

For more information, see README.md or CLAUDE.md in the project root.

---

Press ESC or Q to close this help screen.
"""


class HelpScreen(Screen):
    """Screen showing help and keyboard shortcuts."""

    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("q", "dismiss", "Back"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        t = get_translator()
        yield Header(show_clock=True)

        with VerticalScroll(id="help-container"):
            yield Markdown(HELP_TEXT, id="help-content")
            yield Button(t.get("help.close_button"), id="close-button", variant="primary")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-button":
            self.dismiss()

    def action_dismiss(self) -> None:
        """Dismiss the help screen."""
        self.app.pop_screen()
