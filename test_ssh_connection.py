"""Test SSH connection through jump host."""

import asyncio
import asyncssh
import sys


async def test_connection():
    """Test SSH connection."""
    # Jump host credentials
    jump_host = "152.101.26.116"
    jump_user = "pv5"
    jump_key = "~/.ssh/id_rsa"

    # Target host credentials
    target_host = "192.168.195.10"
    target_user = "pv5"
    target_password = input("Enter password for target host: ")

    print(f"[1/3] Connecting to jump host {jump_user}@{jump_host}...")
    try:
        # Connect to jump host
        jump_conn = await asyncssh.connect(
            jump_host,
            username=jump_user,
            client_keys=[jump_key],
            known_hosts=None,
        )
        print(f"[1/3] ✓ Connected to jump host")

        print(f"[2/3] Connecting to target {target_user}@{target_host} through jump host...")

        # Connect to target through jump host
        target_conn = await asyncio.wait_for(
            jump_conn.connect_ssh(
                target_host,
                username=target_user,
                password=target_password,
                client_keys=[],
                known_hosts=None,
                preferred_auth=["password"],
            ),
            timeout=30,
        )
        print(f"[2/3] ✓ Connected to target host")

        print(f"[3/3] Testing command execution...")
        result = await target_conn.run("echo 'Connection test successful'", check=True)
        print(f"[3/3] ✓ Command output: {result.stdout.strip()}")

        # Cleanup
        target_conn.close()
        jump_conn.close()

        print("\n✓ All tests passed!")
        return True

    except asyncio.TimeoutError:
        print("✗ Connection timed out after 30 seconds")
        return False
    except asyncssh.PermissionDenied as e:
        print(f"✗ Permission denied: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("SSH Connection Test")
    print("=" * 50)

    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
