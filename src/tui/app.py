"""Main Textual application for DockerMonitor."""

import asyncio
from typing import List, Optional
from textual.app import App
from textual.message import Message
from textual.css.query import NoMatches

from .screens import MainScreen
from ..utils.config import ConfigManager
from ..utils.logger import get_logger
from ..ssh.tunnel import SSHTunnelManager
from ..ssh.executor import RemoteExecutor
from ..docker.monitor import DockerMonitor, HostStatus
from ..i18n import get_translator


class DockerMonitorApp(App):
    """Textual application for monitoring Docker containers."""

    CSS_PATH = "styles.css"
    TITLE = "DockerMonitor - Docker Container Monitoring"

    class RefreshRequested(Message):
        """Message requesting data refresh."""
        pass

    def __init__(
        self,
        config: ConfigManager,
        refresh_interval: int = 60,
        tags: Optional[List[str]] = None,
        *args,
        **kwargs,
    ):
        """
        Initialize DockerMonitor app.

        Args:
            config: ConfigManager instance.
            refresh_interval: Auto-refresh interval in seconds.
            tags: Optional list of tags to filter hosts.
        """
        super().__init__(*args, **kwargs)
        self.config = config
        self.refresh_interval = refresh_interval
        self.tags = tags

        # Initialize translator with locale from config
        locale = config.get_locale()
        self.translator = get_translator(locale)

        self.logger = get_logger()
        self._host_statuses: List[HostStatus] = []
        self._tunnel: Optional[SSHTunnelManager] = None
        self._monitors = {}
        self._refresh_timer = None
        self._is_monitoring = False

    def on_mount(self) -> None:
        """Handle app mount."""
        self.logger.info(f"### App.on_mount() called, refresh_interval={self.refresh_interval} ###")

        # Push main screen directly
        self.push_screen(MainScreen())

        # Start monitoring
        asyncio.create_task(self._start_monitoring())

        # Set up auto-refresh timer
        if self.refresh_interval > 0:
            self._refresh_timer = self.set_interval(
                self.refresh_interval, self._auto_refresh
            )
            self.logger.info(f"### Auto-refresh timer set: every {self.refresh_interval} seconds ###")
        else:
            self.logger.warning(f"### Auto-refresh disabled (interval={self.refresh_interval}) ###")

    async def _start_monitoring(self) -> None:
        """Start monitoring hosts."""
        try:
            self._is_monitoring = True
            await self._refresh_data()
        except Exception as e:
            self.logger.exception(f"Error starting monitoring: {e}")
            self.notify(f"Error: {str(e)}", severity="error", timeout=10)

    async def _refresh_data(self) -> None:
        """Refresh monitoring data."""
        # === 診斷日誌 ===
        self.logger.info("=" * 60)
        self.logger.info("=== _refresh_data() CALLED ===")
        self.logger.info(f"_is_monitoring = {self._is_monitoring}")
        self.logger.info(f"_tunnel exists = {self._tunnel is not None}")
        self.logger.info(f"_monitors count = {len(self._monitors)}")
        self.logger.info(f"_host_statuses count = {len(self._host_statuses)}")
        self.logger.info("=" * 60)

        if not self._is_monitoring:
            self.logger.warning("!!! _is_monitoring is False, skipping refresh !!!")
            self.notify("監控已停止，無法更新", severity="warning", timeout=5)
            return

        t = self.translator
        tunnel = None  # Use local tunnel variable

        try:
            # Get configuration
            jump_host_config = self.config.get_jump_host()
            target_hosts = self.config.get_target_hosts(tags=self.tags, enabled_only=True)
            monitoring_config = self.config.get_monitoring_config()
            docker_config = self.config.get_docker_config()

            if not target_hosts:
                self.notify(t.get("messages.no_hosts"), severity="warning")
                return

            # Show initial progress
            self.notify(t.get("messages.refreshing"), timeout=1)

            # Always close old connections before creating new ones
            if self._tunnel is not None:
                self.logger.info("Closing previous connections...")
                await self._tunnel.close_all()
                self._tunnel = None
                self._monitors.clear()  # Clear old monitors with stale connections

            # Create NEW tunnel for this refresh
            self.notify(t.get("messages.connecting"), timeout=2)
            tunnel = SSHTunnelManager(
                jump_host=jump_host_config["hostname"],
                jump_port=jump_host_config.get("port", 22),
                jump_user=jump_host_config["username"],
                jump_key_file=jump_host_config.get("key_file"),
                jump_password=jump_host_config.get("password"),
                timeout=monitoring_config["command_timeout"],
            )

            # Connect to jump host
            await tunnel.connect_to_jump_host()
            self.logger.info("Connected to jump host")
            self.notify(t.get("messages.connected"), timeout=1)

            # Monitor each host
            semaphore = asyncio.Semaphore(monitoring_config["max_concurrent_connections"])

            # Show monitoring progress
            host_names = [h["name"] for h in target_hosts]
            self.notify(
                t.get("messages.monitoring_hosts", hosts=", ".join(host_names)),
                timeout=2
            )

            async def monitor_single_host(host_config):
                async with semaphore:
                    host_name = host_config["name"]
                    try:
                        # Notify which host we're connecting to
                        self.logger.info(f"Connecting to {host_name}...")

                        # Connect to target host using local tunnel
                        target_conn = await tunnel.connect_to_target(
                            target_host=host_config["hostname"],
                            target_port=host_config.get("port", 22),
                            target_user=host_config["username"],
                            target_key_file=host_config.get("key_file"),
                            target_password=host_config.get("password"),
                        )

                        self.logger.info(f"Connected to {host_name}, collecting data...")

                        # Create NEW monitor (don't reuse old ones)
                        executor = RemoteExecutor(
                            connection=target_conn,
                            host_identifier=host_config["name"],
                            timeout=monitoring_config["command_timeout"],
                            max_retries=monitoring_config["max_retries"],
                            retry_delay=monitoring_config["retry_delay"],
                        )

                        monitor = DockerMonitor(
                            executor=executor,
                            host_name=host_config["name"],
                            hostname=host_config["hostname"],
                            docker_bin=docker_config["docker_bin"],
                        )

                        # Get host status
                        host_status = await monitor.get_host_status(include_containers=True)
                        return host_status

                    except Exception as e:
                        self.logger.error(f"Failed to monitor {host_config['name']}: {e}")
                        return HostStatus(
                            host_name=host_config["name"],
                            hostname=host_config["hostname"],
                            connected=False,
                            docker_available=False,
                            error=str(e),
                        )

            # Monitor all hosts concurrently
            tasks = [monitor_single_host(host) for host in target_hosts]
            self._host_statuses = await asyncio.gather(*tasks)

            # Update UI
            self._update_main_screen()

            self.notify(t.get("messages.refreshed", count=len(self._host_statuses)), timeout=2)

        except Exception as e:
            self.logger.exception(f"Error refreshing data: {e}")
            self.notify(t.get("messages.error", error=str(e)), severity="error", timeout=10)

        finally:
            # ALWAYS close connections after refresh completes
            if tunnel is not None:
                try:
                    self.logger.info("Closing all SSH connections after refresh...")
                    await tunnel.close_all()
                    self.logger.info("All connections closed")
                except Exception as e:
                    self.logger.error(f"Error closing connections: {e}")

    def _update_main_screen(self) -> None:
        """Update main screen with latest data."""
        try:
            # Get main screen
            main_screen = self.screen

            if isinstance(main_screen, MainScreen):
                main_screen.update_data(self._host_statuses)
                # Clear the status bar message after update
                try:
                    from .widgets import StatusBarWidget
                    status_bar = main_screen.query_one("#status-bar", StatusBarWidget)
                    status_bar.clear_message()
                except Exception:
                    pass  # Status bar might not be mounted
        except Exception as e:
            self.logger.error(f"Error updating main screen: {e}")

    def _auto_refresh(self) -> None:
        """Auto-refresh timer callback."""
        if self._is_monitoring:
            asyncio.create_task(self._refresh_data())

    def request_refresh(self) -> None:
        """
        Request a data refresh (public API for screens).

        This method can be called from any screen to trigger a data refresh.
        """
        self.logger.info(">>> request_refresh() called, creating async task")
        task = asyncio.create_task(self._refresh_data())
        self.logger.info(f">>> Task created: {task}")

    def on_refresh_requested(self, message: RefreshRequested) -> None:
        """Handle refresh request from UI (fallback for message system)."""
        self.logger.info(">>> on_refresh_requested() called via message")
        self.request_refresh()

    async def on_unmount(self) -> None:
        """Handle app unmount - cleanup resources."""
        self._is_monitoring = False

        if self._refresh_timer:
            self._refresh_timer.stop()

        # No need to close tunnel here since we close it after each refresh
        # But just in case there's a stale reference
        if self._tunnel:
            try:
                await self._tunnel.close_all()
            except Exception:
                pass  # Ignore errors during cleanup
            finally:
                self._tunnel = None

    def switch_language(self) -> None:
        """Switch between available languages."""
        # Get current locale
        current_locale = self.translator.locale

        # Toggle between en and zh_TW
        new_locale = "zh_TW" if current_locale == "en" else "en"

        # Update translator
        self.translator.set_locale(new_locale)

        # Get language name
        language_key = "language_en" if new_locale == "en" else "language_zh_tw"
        language_name = self.translator.get(f"messages.{language_key}")

        # Notify user
        self.notify(
            self.translator.get("messages.language_switched", language=language_name),
            timeout=3
        )

        # Reload the main screen to apply new language
        self._reload_main_screen()

    def _reload_main_screen(self) -> None:
        """Reload the main screen to apply language changes."""
        try:
            self.logger.info("### _reload_main_screen() called ###")
            self.logger.info(f"Before reload: _is_monitoring = {self._is_monitoring}")

            # Pop current screen
            self.pop_screen()

            # Push new main screen
            new_main_screen = MainScreen()
            self.push_screen(new_main_screen)

            # Update with existing data if available
            if self._host_statuses:
                new_main_screen.update_data(self._host_statuses)

            self.logger.info(f"After reload: _is_monitoring = {self._is_monitoring}")
            self.logger.info("### _reload_main_screen() completed ###")

        except Exception as e:
            self.logger.error(f"Error reloading main screen: {e}")

    def action_quit(self) -> None:
        """Quit the application."""
        self._is_monitoring = False
        self.exit()


async def run_tui(
    config: ConfigManager,
    refresh_interval: int = 60,
    tags: Optional[List[str]] = None,
) -> None:
    """
    Run the TUI application.

    Args:
        config: ConfigManager instance.
        refresh_interval: Auto-refresh interval in seconds.
        tags: Optional list of tags to filter hosts.
    """
    app = DockerMonitorApp(
        config=config,
        refresh_interval=refresh_interval,
        tags=tags,
    )
    await app.run_async()
