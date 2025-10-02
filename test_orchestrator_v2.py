#!/usr/bin/env python3
"""
Teste do orchestrator v2
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

    print("🎯 Iniciando orchestrator v2...")
    orchestrator_process = subprocess.Popen(
        ["uv", "run", "python", "orchestrator_v2.py"],
        cwd="/home/willams/fastmcp-playground",
    )
    time.sleep(5)

    print("🧪 Testando orchestrator v2...")
    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            print("=== 1. Ferramentas iniciais ===")
            tools = await client.list_tools()
            print(f"Ferramentas: {[t.name for t in tools]}")

            print("=== 2. Lista de ferramentas disponíveis (antes) ===")
            available = await client.call_tool("list_available_tools")
            print(f"Disponíveis: {available.content[0].text}")

            print("=== 3. Selecionando domínio ===")
            result = await client.call_tool("select_domain", {"domain": "invoicing"})
            print(f"Resultado: {result.content[0].text}")

            print("=== 4. Lista de ferramentas disponíveis (depois) ===")
            available = await client.call_tool("list_available_tools")
            print(f"Disponíveis: {available.content[0].text}")

            print("=== 5. Ferramentas finais ===")
            tools = await client.list_tools()
            print(f"Ferramentas: {[t.name for t in tools]}")

            # Procurar ferramentas do invoicing
            invoicing_tools = [t.name for t in tools if t.name.startswith("invoicing_")]
            print(f"Ferramentas do invoicing: {invoicing_tools}")

            if invoicing_tools:
                print("=== 6. Testando ferramenta do invoicing ===")
                tool_name = invoicing_tools[0]
                print(f"Testando: {tool_name}")
                if "create" in tool_name:
                    try:
                        result = await client.call_tool(
                            tool_name, {"customer_id": 123, "amount": 100.0}
                        )
                        print(f"Resultado: {result.content[0].text}")
                    except Exception as e:
                        print(f"Erro: {e}")

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
