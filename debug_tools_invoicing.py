#!/usr/bin/env python3
"""Debug script to see tool names from invoicing server."""

import asyncio
import json

from mcp.client import ClientSession, StdioServerParameters
from mcp.client.streamable_http import StreamableHTTPTransport


async def debug_invoicing_tools():
    """Connect to invoicing server and list tools."""
    print("🔍 Conectando ao servidor invoicing...")

    # Create transport
    transport = StreamableHTTPTransport("http://127.0.0.1:9101/mcp")

    # Create client session
    session = ClientSession(transport)

    try:
        # Initialize connection
        await session.initialize()

        # List tools
        result = await session.list_tools()
        print(f"📋 Tools encontradas ({len(result.tools)}):")

        for tool in result.tools:
            print(f"  ✅ {tool.name}")
            print(f"     📝 {tool.description}")
            if hasattr(tool, "inputSchema"):
                print(f"     📊 Schema: {json.dumps(tool.inputSchema, indent=2)}")
            print()

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            await session.close()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(debug_invoicing_tools())
