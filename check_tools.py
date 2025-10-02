#!/usr/bin/env python3
"""
Teste para verificar ferramentas dos servidores individuais
"""
import asyncio
import atexit
import signal
import subprocess
import time

from fastmcp import Client

processes = []


def cleanup():
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=2)
        except Exception:
            pass


atexit.register(cleanup)


def signal_handler(signum, frame):
    cleanup()
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


async def main():
    print("🚀 Iniciando servidor invoicing...")
    invoicing_process = subprocess.Popen(
        ["uv", "run", "python", "src/invoicing.py"],
        cwd="/home/willams/fastmcp-playground",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(invoicing_process)
    time.sleep(3)

    print("🧪 Testando servidor invoicing...")
    try:
        async with Client("http://127.0.0.1:9101/mcp") as client:
            tools = await client.list_tools()
            print(f"Ferramentas do invoicing: {[t.name for t in tools]}")

            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
                print(f"    Tags: {tool.tags}")
    except Exception as e:
        print(f"❌ Erro: {e}")

    cleanup()


if __name__ == "__main__":
    asyncio.run(main())
