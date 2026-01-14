"""Main entry point for DockerMonitor."""

import asyncio
import sys
from pathlib import Path

import click

from .utils.config import ConfigManager
from .utils.logger import setup_logger, get_logger
from .ssh.tunnel import SSHTunnelManager
from .ssh.executor import RemoteExecutor
from .docker.monitor import DockerMonitor
from .aggregator.data import DataAggregator


async def monitor_hosts(config: ConfigManager, tags: list = None) -> list:
    """
    Monitor all configured hosts.

    Args:
        config: ConfigManager instance.
        tags: Optional list of tags to filter hosts.

    Returns:
        List of HostStatus objects.
    """
    logger = get_logger()

    # Get configuration
    jump_host_config = config.get_jump_host()
    target_hosts = config.get_target_hosts(tags=tags, enabled_only=True)
    monitoring_config = config.get_monitoring_config()
    docker_config = config.get_docker_config()

    if not target_hosts:
        logger.error("No target hosts found in configuration")
        return []

    logger.info(f"Monitoring {len(target_hosts)} hosts through jump host {jump_host_config['hostname']}")

    # Create SSH tunnel manager
    tunnel = SSHTunnelManager(
        jump_host=jump_host_config["hostname"],
        jump_port=jump_host_config.get("port", 22),
        jump_user=jump_host_config["username"],
        jump_key_file=jump_host_config.get("key_file"),
        jump_password=jump_host_config.get("password"),
        timeout=monitoring_config["command_timeout"],
    )

    host_statuses = []

    try:
        # Connect to jump host
        await tunnel.connect_to_jump_host()
        logger.info("Connected to jump host")

        # Monitor each target host
        semaphore = asyncio.Semaphore(monitoring_config["max_concurrent_connections"])

        async def monitor_single_host(host_config):
            async with semaphore:
                logger.info(f"[{host_config['name']}] Starting monitoring...")

                try:
                    # Connect to target host
                    logger.info(f"[{host_config['name']}] Connecting to {host_config['hostname']}...")

                    target_conn = await asyncio.wait_for(
                        tunnel.connect_to_target(
                            target_host=host_config["hostname"],
                            target_port=host_config.get("port", 22),
                            target_user=host_config["username"],
                            target_key_file=host_config.get("key_file"),
                            target_password=host_config.get("password"),
                        ),
                        timeout=60  # 60 second timeout for connection
                    )

                    logger.info(f"[{host_config['name']}] Connected successfully")

                    # Create executor and monitor
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
                    logger.info(f"[{host_config['name']}] Fetching container status...")
                    host_status = await monitor.get_host_status(include_containers=True)
                    logger.info(
                        f"[{host_config['name']}] ✓ {host_status.container_count} containers "
                        f"({host_status.running_count} running, {host_status.stopped_count} stopped)"
                    )

                    return host_status

                except asyncio.TimeoutError:
                    logger.error(f"[{host_config['name']}] ✗ Connection timeout")
                    from .docker.monitor import HostStatus
                    return HostStatus(
                        host_name=host_config["name"],
                        hostname=host_config["hostname"],
                        connected=False,
                        docker_available=False,
                        error="Connection timeout",
                    )
                except Exception as e:
                    logger.error(f"[{host_config['name']}] ✗ Error: {type(e).__name__}: {e}")
                    import traceback
                    logger.debug(f"[{host_config['name']}] Traceback:\n{traceback.format_exc()}")
                    from .docker.monitor import HostStatus
                    return HostStatus(
                        host_name=host_config["name"],
                        hostname=host_config["hostname"],
                        connected=False,
                        docker_available=False,
                        error=str(e),
                    )

        # Monitor all hosts concurrently
        tasks = [monitor_single_host(host) for host in target_hosts]
        host_statuses = await asyncio.gather(*tasks)

    finally:
        # Clean up connections
        await tunnel.close_all()
        logger.info("Closed all connections")

    return host_statuses


@click.group()
@click.option("--config", type=click.Path(exists=True), help="Path to hosts.yaml config file")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, config, debug):
    """DockerMonitor - Monitor Docker containers across multiple hosts via jump host."""
    # Setup logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logger(level=log_level)

    # Load configuration
    try:
        config_manager = ConfigManager(config_path=config)
        config_manager.validate()
        ctx.obj = {"config": config_manager}
    except Exception as e:
        click.echo(f"Error: Failed to load configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--tags", help="Filter hosts by tags (comma-separated)")
@click.option("--format", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")
@click.option("--output", type=click.Path(), help="Save output to file")
@click.pass_context
def status(ctx, tags, format, output):
    """Get current status of all containers."""
    config = ctx.obj["config"]
    logger = get_logger()

    # Parse tags
    tag_list = tags.split(",") if tags else None

    # Run monitoring
    try:
        host_statuses = asyncio.run(monitor_hosts(config, tags=tag_list))

        if not host_statuses:
            click.echo("No hosts monitored", err=True)
            return

        # Aggregate and format data
        aggregator = DataAggregator()

        if format == "json":
            output_data = aggregator.to_json(host_statuses, pretty=True)
            if output:
                Path(output).write_text(output_data, encoding="utf-8")
                click.echo(f"JSON output saved to {output}")
            else:
                click.echo(output_data)

        elif format == "csv":
            output_data = aggregator.to_csv(host_statuses)
            if output:
                Path(output).write_text(output_data, encoding="utf-8")
                click.echo(f"CSV output saved to {output}")
            else:
                click.echo(output_data)

        else:  # table
            output_data = aggregator.to_table(host_statuses)
            click.echo(output_data)

            if output:
                Path(output).write_text(output_data, encoding="utf-8")
                click.echo(f"Table output saved to {output}")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error during monitoring: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--tags", help="Filter hosts by tags (comma-separated)")
@click.option("--interval", type=int, default=60, help="Auto-refresh interval in seconds")
@click.pass_context
def tui(ctx, tags, interval):
    """Launch Textual TUI interface."""
    config = ctx.obj["config"]
    
    # Reconfigure logger with console output disabled for TUI mode
    # This prevents log output from corrupting the terminal display
    setup_logger(level="DEBUG" if ctx.parent.params.get("debug") else "INFO", console_enabled=False)
    logger = get_logger()

    # Parse tags
    tag_list = tags.split(",") if tags else None

    try:
        # Import TUI app
        from .tui.app import run_tui

        # Run TUI
        logger.info("Starting TUI interface...")
        asyncio.run(run_tui(config, refresh_interval=interval, tags=tag_list))

    except KeyboardInterrupt:
        logger.info("TUI interrupted by user")
    except Exception as e:
        logger.exception(f"Error running TUI: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
