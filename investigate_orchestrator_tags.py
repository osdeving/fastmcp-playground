#!/usr/bin/env python3
"""
Investigar tags das ferramentas do orchestrator
"""
import asyncio
import subprocess
import time

from fastmcp import Client


async def main():
    print("🚀 Iniciando servidor invoicing...")
    invoicing_process = subprocess.Popen(
        ["uv", "run", "python", "src/invoicing.py"],
        cwd="/home/willams/fastmcp-playground",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)

    print("🎯 Iniciando orchestrator...")
    orchestrator_process = subprocess.Popen(
        ["uv", "run", "python", "src/orchestrator.py"],
        cwd="/home/willams/fastmcp-playground",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(5)

    print("🧪 Investigando tags do orchestrator...")

    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            tools = await client.list_tools()
            print(f"Total de ferramentas: {len(tools)}")

            for tool in tools:
                print(f"\nFerramenta: {tool.name}")
                print(f"  Meta: {getattr(tool, 'meta', 'N/A')}")

                # Check for tags in meta
                if hasattr(tool, "meta") and tool.meta:
                    print(f"  Meta exists: {tool.meta}")
                    if "_fastmcp" in tool.meta:
                        fastmcp_meta = tool.meta["_fastmcp"]
                        print(f"  FastMCP meta: {fastmcp_meta}")
                        if "tags" in fastmcp_meta:
                            tags = fastmcp_meta["tags"]
                            print(f"  Tags: {tags}")
                        else:
                            print(f"  No tags in FastMCP meta")
                    else:
                        print(f"  No _fastmcp in meta")
                else:
                    print(f"  No meta")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            invoicing_process.terminate()
            orchestrator_process.terminate()
            invoicing_process.wait(timeout=2)
            orchestrator_process.wait(timeout=2)
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
