#!/usr/bin/env python3
"""Debug script to see tool names from servers."""

import asyncio

from mcp.client.streamable_http import StreamableHTTPTransport


async def debug_tools():
    """Debug tool names from invoicing server."""
    print("🔍 Conectando ao servidor invoicing...")

    transport = StreamableHTTPTransport(base_url="http://127.0.0.1:9101", path="/mcp")

    try:
        await transport.connect()

        # List tools
        tools = await transport.list_tools()
        print(f"📋 Tools encontradas ({len(tools.tools)}):")

        for tool in tools.tools:
            print(f"  - {tool.name}")
            if hasattr(tool, "description"):
                print(f"    Description: {tool.description}")

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        await transport.close()


if __name__ == "__main__":
    asyncio.run(debug_tools())
