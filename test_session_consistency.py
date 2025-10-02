#!/usr/bin/env python3
"""
Teste de consistência de sessão
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

    print("🧪 Testando consistência de sessão...")
    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            # 1. Primeira chamada - listar ferramentas
            print("=== 1. Primeira chamada ===")
            tools1 = await client.list_tools()
            print(f"Ferramentas: {[t.name for t in tools1]}")

            # 2. Selecionar domínio
            print("=== 2. Selecionando domínio ===")
            result = await client.call_tool("select_domain", {"domain": "invoicing"})
            print(f"Resultado: {result.content[0].text}")

            # 3. Segunda chamada - listar ferramentas
            print("=== 3. Segunda chamada (mesma sessão) ===")
            tools2 = await client.list_tools()
            print(f"Ferramentas: {[t.name for t in tools2]}")

            # 4. Verificar status
            print("=== 4. Verificando status ===")
            status = await client.call_tool("get_session_status")
            print(f"Status: {status.content[0].text}")

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
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
