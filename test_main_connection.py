"""Test connection using main.py logic."""

import asyncio
import sys
sys.path.insert(0, 'D:\\code\\DockerMonitor')

from src.utils.config import ConfigManager
from src.utils.logger import setup_logger
from src.ssh.tunnel import SSHTunnelManager


async def test_main_logic():
    """Test using main.py connection logic."""
    setup_logger(level="DEBUG")

    print("Loading configuration...")
    config = ConfigManager()

    jump_config = config.get_jump_host()
    target_hosts = config.get_target_hosts(enabled_only=True)
    monitoring_config = config.get_monitoring_config()

    print(f"Jump host: {jump_config['hostname']}")
    print(f"Target hosts: {[h['name'] for h in target_hosts]}")
    print(f"Timeout: {monitoring_config['command_timeout']}s")
    print()

    # Create tunnel
    tunnel = SSHTunnelManager(
        jump_host=jump_config["hostname"],
        jump_port=jump_config.get("port", 22),
        jump_user=jump_config["username"],
        jump_key_file=jump_config.get("key_file"),
        timeout=monitoring_config["command_timeout"],
    )

    try:
        # Connect to jump host
        print("Connecting to jump host...")
        await tunnel.connect_to_jump_host()
        print("✓ Connected to jump host\n")

        # Test first target host
        host = target_hosts[0]
        print(f"Testing connection to {host['name']} ({host['hostname']})...")

        try:
            target_conn = await asyncio.wait_for(
                tunnel.connect_to_target(
                    target_host=host["hostname"],
                    target_port=host.get("port", 22),
                    target_user=host["username"],
                    target_key_file=host.get("key_file"),
                    target_password=host.get("password"),
                ),
                timeout=60
            )
            print(f"✓ Connected to {host['name']}\n")

            # Test command
            print("Testing command execution...")
            result = await target_conn.run("docker ps --format '{{.Names}}'")
            print(f"✓ Docker containers found:")
            if result.stdout:
                for line in result.stdout.strip().split('\n')[:5]:
                    print(f"  - {line}")
            else:
                print("  (no containers)")

        except asyncio.TimeoutError:
            print(f"✗ Connection to {host['name']} timed out")
        except Exception as e:
            print(f"✗ Error connecting to {host['name']}: {e}")
            import traceback
            traceback.print_exc()

    finally:
        await tunnel.close_all()
        print("\nClosed all connections")


if __name__ == "__main__":
    asyncio.run(test_main_logic())
