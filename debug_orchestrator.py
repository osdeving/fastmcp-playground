#!/usr/bin/env python3
"""
Teste completo do orchestrator para debug
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

    print("🎯 Iniciando orchestrator...")
    orchestrator_process = subprocess.Popen(
        ["uv", "run", "python", "src/orchestrator.py"],
        cwd="/home/willams/fastmcp-playground",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(orchestrator_process)
    time.sleep(5)

    print("🧪 Testando orchestrator...")
    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            print("=== Conectado ao orchestrator ===")

            # 1. Listar ferramentas iniciais
            tools = await client.list_tools()
            print(f"1. Ferramentas iniciais: {[t.name for t in tools]}")

            # 2. Verificar se há ferramentas com prefixo invoicing antes da seleção
            invoicing_tools_before = [
                t.name for t in tools if t.name.startswith("invoicing_")
            ]
            print(
                f"2. Ferramentas invoicing antes da seleção: {invoicing_tools_before}"
            )

            # 3. Selecionar domínio invoicing
            print("3. Selecionando domínio invoicing...")
            result = await client.call_tool("select_domain", {"domain": "invoicing"})
            selection_result = result.content[0].text
            print(f"   Resultado da seleção: {selection_result}")

            # 4. Listar ferramentas após seleção
            tools_after = await client.list_tools()
            print(f"4. Ferramentas após seleção: {[t.name for t in tools_after]}")

            # 5. Verificar ferramentas com prefixo invoicing após seleção
            invoicing_tools_after = [
                t.name for t in tools_after if t.name.startswith("invoicing_")
            ]
            print(f"5. Ferramentas invoicing após seleção: {invoicing_tools_after}")

            # 6. Verificar se a quantidade de ferramentas mudou
            print(
                f"6. Quantidade de ferramentas: antes={len(tools)}, depois={len(tools_after)}"
            )

            # 7. Tentar listar todas as ferramentas do orchestrator com debug
            print("7. Analisando ferramentas disponíveis...")
            for tool in tools_after:
                print(f"   - {tool.name}: {tool.description}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()

    cleanup()


if __name__ == "__main__":
    asyncio.run(main())
