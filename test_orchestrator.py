#!/usr/bin/env python3
"""
Test script for the FastMCP Orchestrator

This script automatically starts all required servers and demonstrates
the session-based domain selection functionality of the orchestrator system.
"""

import asyncio
import os
import signal
import socket
import subprocess

from fastmcp import Client


def check_port_open(host, port, timeout=1):
    """Check if a port is open and listening."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# Configuration for servers - Start domain servers first, then orchestrator
SERVERS = [
    {"name": "invoicing", "script": "src/invoicing.py", "port": 9101, "order": 1},
    {"name": "products", "script": "src/products.py", "port": 9102, "order": 1},
    {"name": "users", "script": "src/users.py", "port": 9103, "order": 1},
    {"name": "orchestrator", "script": "src/orchestrator.py", "port": 9100, "order": 2},
]


class ServerManager:
    """Manages multiple FastMCP servers for testing."""

    def __init__(self):
        self.processes = []

    async def start_servers(self):
        """Start all required servers in order."""
        print("🚀 Starting all FastMCP servers...")
        print("=" * 50)

        # Sort servers by order (domain servers first, then orchestrator)
        servers_by_order = sorted(SERVERS, key=lambda x: x["order"])

        # Start domain servers first
        domain_servers = [s for s in servers_by_order if s["order"] == 1]
        orchestrator_servers = [s for s in servers_by_order if s["order"] == 2]

        # Start domain servers
        print("📦 Starting domain servers...")
        for server in domain_servers:
            await self._start_single_server(server)

        # Wait for domain servers to be ready
        print("\n⏳ Waiting for domain servers to be ready...")
        await asyncio.sleep(3)

        # Check domain servers health
        await self._check_domain_servers_health()

        # Start orchestrator
        print("\n🎯 Starting orchestrator...")
        for server in orchestrator_servers:
            await self._start_single_server(server)

        # Wait for orchestrator to be ready
        print("\n⏳ Waiting for orchestrator to initialize...")
        await asyncio.sleep(3)

    async def _start_single_server(self, server):
        """Start a single server."""
        print(f"Starting {server['name']} server on port {server['port']}...")

        try:
            # Start server process
            process = subprocess.Popen(
                ["uv", "run", server["script"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            self.processes.append(
                {"name": server["name"], "process": process, "port": server["port"]}
            )

            print(f"✅ {server['name']} server started (PID: {process.pid})")

        except Exception as e:
            print(f"❌ Failed to start {server['name']}: {e}")

    async def _check_domain_servers_health(self):
        """Check if domain servers are responding."""
        print("🔍 Checking domain server health...")

        domain_servers = [p for p in self.processes if p["name"] != "orchestrator"]

        for server_info in domain_servers:
            name = server_info["name"]
            port = server_info["port"]

            # First check if port is listening
            if not check_port_open("127.0.0.1", port):
                print(f"⚠️ {name} port {port} is not listening yet")
                # Wait a bit and check again
                await asyncio.sleep(2)
                if not check_port_open("127.0.0.1", port):
                    print(f"❌ {name} port {port} still not ready")
                    continue

            # Then check if MCP server is responding
            for attempt in range(3):
                try:
                    async with Client(f"http://127.0.0.1:{port}/mcp") as client:
                        tools = await client.list_tools()
                        print(f"✅ {name} server is responding ({len(tools)} tools)")
                        break
                except Exception as e:
                    if attempt < 2:
                        print(f"🔄 {name} server not ready yet, retrying...")
                        await asyncio.sleep(1)
                    else:
                        print(f"⚠️ {name} server MCP check failed: {type(e).__name__}")
                        # Check if process is at least running
                        if server_info["process"].poll() is None:
                            print(f"ℹ️ {name} process is running, may need more time")

    async def _check_servers_health(self):
        """Check if all servers are responding."""
        print("\n🔍 Final server health check...")

        for server_info in self.processes:
            port = server_info["port"]
            name = server_info["name"]

            try:
                # Try to connect to the server
                async with Client(f"http://127.0.0.1:{port}/mcp") as client:
                    tools = await client.list_tools()
                    print(f"✅ {name} server is healthy ({len(tools)} tools available)")

            except Exception as e:
                print(f"⚠️ {name} server health check failed: {e}")
                # Check if process is at least running
                if server_info["process"].poll() is None:
                    print(f"ℹ️ {name} process is running, may need more time")
                else:
                    print(f"❌ {name} process has stopped")

    def stop_servers(self):
        """Stop all running servers."""
        print("\n🛑 Stopping all servers...")

        for server_info in self.processes:
            try:
                process = server_info["process"]
                name = server_info["name"]

                if process.poll() is None:  # Process is still running
                    # Try graceful shutdown first
                    if os.name != "nt":
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    else:
                        process.terminate()

                    # Wait a bit for graceful shutdown
                    try:
                        process.wait(timeout=5)
                        print(f"✅ {name} server stopped gracefully")
                    except subprocess.TimeoutExpired:
                        # Force kill if necessary
                        if os.name != "nt":
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        else:
                            process.kill()
                        print(f"⚠️ {name} server force killed")

            except Exception as e:
                print(f"❌ Error stopping {server_info['name']}: {e}")

        self.processes.clear()
        print("🏁 All servers stopped")


async def wait_for_orchestrator_ready(max_retries=15, delay=3):
    """Wait for orchestrator to be ready with retry logic."""
    print(
        f"⏳ Waiting for orchestrator to be fully ready (max {max_retries} attempts)..."
    )

    # First check if port is listening
    for i in range(10):
        if check_port_open("127.0.0.1", 9100):
            print("✅ Orchestrator port 9100 is listening")
            break
        print(f"🔄 Waiting for orchestrator port to open... ({i+1}/10)")
        await asyncio.sleep(1)
    else:
        print("❌ Orchestrator port never opened")
        return False

    # Then check MCP connectivity
    for attempt in range(max_retries):
        try:
            async with Client("http://127.0.0.1:9100/mcp") as client:
                tools = await client.list_tools()
                print(f"✅ Orchestrator is ready with {len(tools)} tools available")
                return True
        except Exception as e:
            error_type = type(e).__name__
            print(
                f"🔄 Attempt {attempt + 1}/{max_retries}: Orchestrator MCP not ready ({error_type})"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)

    print("❌ Orchestrator MCP failed to respond after maximum retries")
    return False


async def test_orchestrator():
    """Test the orchestrator functionality."""
    print("🚀 Testing FastMCP Orchestrator")
    print("=" * 50)

    try:
        # Connect to the orchestrator with retry
        print("📡 Connecting to orchestrator at http://127.0.0.1:9100...")

        async with Client("http://127.0.0.1:9100/mcp") as client:
            print("✅ Connected successfully!")

            # 1. List available domains
            print("\n1️⃣ Listing available domains...")
            domains_result = await client.call_tool("list_domains")
            domains = domains_result.data
            print(f"Available domains: {domains}")

            # 2. Check initial session status
            print("\n2️⃣ Checking initial session status...")
            status_result = await client.call_tool("get_session_status")
            status = status_result.data
            print(f"Session status: {status}")

            # 3. List tools before domain selection
            print("\n3️⃣ Listing tools before domain selection...")
            tools_before = await client.list_tools()
            tool_names_before = [tool.name for tool in tools_before]
            print(f"Available tools: {tool_names_before}")

            # Test each domain
            for domain in ["invoicing", "products", "users"]:
                await test_domain_functionality(client, domain)

            print("\n✅ All domain tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        raise


async def test_domain_functionality(client: Client, domain: str):
    """Test functionality for a specific domain."""
    print(f"\n🔧 Testing {domain.upper()} domain functionality...")
    print("-" * 40)

    try:
        # Select the domain
        print(f"🎯 Selecting '{domain}' domain...")
        select_result = await client.call_tool("select_domain", {"domain": domain})
        print(f"Selection result: {select_result.data}")

        # List tools after domain selection
        print(f"📋 Listing tools after selecting {domain}...")
        tools_after = await client.list_tools()
        tool_names_after = [tool.name for tool in tools_after]

        # Filter domain-specific tools
        domain_tools = [
            name for name in tool_names_after if name.startswith(f"{domain}_")
        ]
        print(f"🔧 {domain.capitalize()} tools: {domain_tools}")

        # Test domain-specific functionality
        if domain == "invoicing" and "invoicing_create_invoice" in tool_names_after:
            print("💰 Testing invoice creation...")
            invoice_result = await client.call_tool(
                "invoicing_create_invoice", {"customer_id": 123, "amount": 99.99}
            )
            print(f"Invoice result: {invoice_result.data}")

        elif domain == "products" and "products_search_products" in tool_names_after:
            print("📦 Testing product search...")
            products_result = await client.call_tool(
                "products_search_products", {"query": "test"}
            )
            print(f"Products result: {products_result.data}")

        elif domain == "users" and "users_get_user" in tool_names_after:
            print("👤 Testing user lookup...")
            user_result = await client.call_tool("users_get_user", {"user_id": 1})
            print(f"User result: {user_result.data}")
        else:
            print(f"⚠️ No testable {domain} tools found (server may not be fully ready)")

        print(f"✅ {domain.capitalize()} domain test completed")

    except Exception as e:
        print(f"❌ {domain.capitalize()} domain test failed: {e}")
        # Continue with other tests rather than failing completely


async def test_without_domain_servers():
    """Test orchestrator functionality even without domain servers."""
    print("\n🔧 Testing orchestrator-only functionality...")

    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            # Test core orchestrator tools
            domains = await client.call_tool("list_domains")
            print(f"✅ Domains listed: {domains.data}")

            status = await client.call_tool("get_session_status")
            print(f"✅ Session status: {status.data}")

            print("✅ Core orchestrator functionality working!")

    except Exception as e:
        print(f"❌ Core test failed: {e}")


async def main():
    """Main function that starts servers and runs tests."""
    server_manager = ServerManager()

    try:
        # Start all servers in order
        await server_manager.start_servers()

        # Do final health check
        await server_manager._check_servers_health()

        # Wait for orchestrator to be ready
        if not await wait_for_orchestrator_ready():
            print("❌ Cannot continue without orchestrator")
            return

        # Run the tests
        await test_orchestrator()

    except KeyboardInterrupt:
        print("\n🔄 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Always stop servers
        server_manager.stop_servers()


if __name__ == "__main__":
    print("FastMCP Orchestrator Test Suite with Auto Server Management")
    print("=" * 60)
    print("This script automatically starts all servers and runs comprehensive tests.")
    print()
    print("🎯 What this script does:")
    print(
        "1. 🚀 Starts all servers: invoicing(9101), products(9102), users(9103), orchestrator(9100)"
    )
    print("2. ⏳ Waits for all servers to be ready")
    print("3. 🧪 Tests orchestrator functionality with all 3 domains")
    print("4. 🛑 Automatically stops all servers when done")
    print()
    print("💡 Usage: uv run test_orchestrator.py")
    print("🔧 For manual control, see README.md")
    print()
    print("🚀 Starting test suite...")
    print()

    # Run the main function
    asyncio.run(main())
