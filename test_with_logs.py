#!/usr/bin/env python3
"""
Teste com logging detalhado
"""
import asyncio
import logging
import subprocess
import time

from fastmcp import Client

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


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
    )
    time.sleep(5)

    print("🧪 Testando com logging...")
    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            print("=== Listando ferramentas iniciais ===")
            tools = await client.list_tools()
            print(f"Ferramentas: {[t.name for t in tools]}")

            print("=== Selecionando domínio ===")
            result = await client.call_tool("select_domain", {"domain": "invoicing"})
            print(f"Resultado: {result.content[0].text}")

            print("=== Listando ferramentas após seleção ===")
            tools_after = await client.list_tools()
            print(f"Ferramentas: {[t.name for t in tools_after]}")

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
