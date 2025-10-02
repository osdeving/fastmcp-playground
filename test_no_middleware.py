#!/usr/bin/env python3
"""
Teste do orchestrator sem middleware
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

    print("🎯 Iniciando orchestrator sem middleware...")
    orchestrator_process = subprocess.Popen(
        ["uv", "run", "python", "orchestrator_no_middleware.py"],
        cwd="/home/willams/fastmcp-playground",
    )
    time.sleep(5)

    print("🧪 Testando orchestrator sem middleware...")
    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            print("=== Listando ferramentas ===")
            tools = await client.list_tools()
            print(f"Ferramentas disponíveis: {[t.name for t in tools]}")

            # Buscar ferramentas específicas
            orchestrator_tools = [
                t.name for t in tools if not t.name.startswith("invoicing_")
            ]
            invoicing_tools = [t.name for t in tools if t.name.startswith("invoicing_")]

            print(f"Ferramentas do orchestrator: {orchestrator_tools}")
            print(f"Ferramentas do invoicing: {invoicing_tools}")

            if "select_domain" in [t.name for t in tools]:
                print("=== Testando select_domain ===")
                result = await client.call_tool(
                    "select_domain", {"domain": "invoicing"}
                )
                print(f"Resultado: {result.content[0].text}")

            if invoicing_tools:
                print("=== Testando ferramenta do invoicing ===")
                tool_name = invoicing_tools[0]
                print(f"Testando: {tool_name}")
                if "create" in tool_name:
                    try:
                        result = await client.call_tool(
                            tool_name, {"customer_id": 123, "amount": 100.0}
                        )
                        print(f"Resultado: {result.content[0].text}")
                    except Exception as e:
                        print(f"Erro esperado (pode precisar de mais parâmetros): {e}")

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
