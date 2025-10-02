#!/usr/bin/env python3
"""
Teste simples do orchestrator
"""
import asyncio
import atexit
import signal
import subprocess
import time

from fastmcp import Client

# Variáveis globais para os processos
processes = []


def cleanup():
    """Limpa os processos ao sair"""
    for process in processes:
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            pass


atexit.register(cleanup)


def signal_handler(signum, frame):
    cleanup()
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


async def test_orchestrator():
    """Testa o orchestrator step by step"""

    # 1. Iniciar apenas o servidor invoicing
    print("🚀 Iniciando servidor invoicing...")
    invoicing_process = subprocess.Popen(
        ["uv", "run", "python", "src/invoicing.py"],
        cwd="/home/willams/fastmcp-playground",
    )
    processes.append(invoicing_process)
    time.sleep(2)

    # 2. Iniciar o orchestrator
    print("🎯 Iniciando orchestrator...")
    orchestrator_process = subprocess.Popen(
        ["uv", "run", "python", "src/orchestrator.py"],
        cwd="/home/willams/fastmcp-playground",
    )
    processes.append(orchestrator_process)
    time.sleep(3)

    # 3. Testar o orchestrator
    print("🧪 Testando orchestrator...")
    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            print("=== Conectado ao orchestrator ===")

            # Listar ferramentas iniciais
            tools = await client.list_tools()
            print(f"Ferramentas iniciais: {[t.name for t in tools]}")

            # Selecionar domínio invoicing
            print("Selecionando domínio invoicing...")
            result = await client.call_tool("select_domain", {"domain": "invoicing"})
            print(f"Resultado da seleção: {result.content[0].text}")

            # Listar ferramentas após seleção
            tools = await client.list_tools()
            print(f"Ferramentas após seleção: {[t.name for t in tools]}")

            # Se temos ferramentas de invoicing, testar uma
            invoicing_tools = [t for t in tools if t.name.startswith("invoicing_")]
            if invoicing_tools:
                tool_name = invoicing_tools[0].name
                print(f"Testando ferramenta: {tool_name}")
                if "create" in tool_name:
                    result = await client.call_tool(
                        tool_name,
                        {"amount": 100.0, "description": "Teste via orchestrator"},
                    )
                    print(f"Resultado: {result.content[0].text}")
            else:
                print("❌ Nenhuma ferramenta de invoicing encontrada")

    except Exception as e:
        print(f"❌ Erro ao testar: {e}")

    finally:
        print("🛑 Limpando processos...")
        cleanup()


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
