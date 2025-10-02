#!/usr/bin/env python3
"""
Teste final do orchestrator
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

    print("🎯 Iniciando orchestrator final...")
    orchestrator_process = subprocess.Popen(
        ["uv", "run", "python", "orchestrator_final.py"],
        cwd="/home/willams/fastmcp-playground",
    )
    time.sleep(5)

    print("🧪 Testando orchestrator final...")
    try:
        async with Client("http://127.0.0.1:9100/mcp") as client:
            print("=== 1. Ferramentas iniciais (antes da seleção) ===")
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            print(f"Ferramentas: {tool_names}")
            print(
                f'Ferramentas do orchestrator: {[t for t in tool_names if not t.startswith("invoicing_")]}'
            )
            print(
                f'Ferramentas do invoicing: {[t for t in tool_names if t.startswith("invoicing_")]}'
            )

            print("\n=== 2. Selecionando domínio invoicing ===")
            result = await client.call_tool("select_domain", {"domain": "invoicing"})
            print(f"Resultado: {result.content[0].text}")

            print("\n=== 3. Ferramentas após seleção ===")
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            print(f"Ferramentas: {tool_names}")
            print(
                f'Ferramentas do orchestrator: {[t for t in tool_names if not t.startswith("invoicing_")]}'
            )
            print(
                f'Ferramentas do invoicing: {[t for t in tool_names if t.startswith("invoicing_")]}'
            )

            # Verificar se as ferramentas do invoicing apareceram
            invoicing_tools = [t for t in tool_names if t.startswith("invoicing_")]
            if invoicing_tools:
                print(
                    f"\n✅ Sucesso! {len(invoicing_tools)} ferramentas do invoicing disponíveis"
                )

                print("\n=== 4. Testando ferramenta do invoicing ===")
                try:
                    result = await client.call_tool(
                        "invoicing_create_invoice",
                        {"customer_id": 123, "amount": 250.75},
                    )
                    print(f"Resultado da criação de invoice: {result.content[0].text}")
                    print("✅ Ferramenta do invoicing funcionando!")
                except Exception as e:
                    print(f"❌ Erro ao chamar ferramenta do invoicing: {e}")
            else:
                print(
                    "\n❌ Falha! Nenhuma ferramenta do invoicing apareceu após seleção"
                )

            print("\n=== 5. Verificando status da sessão ===")
            status = await client.call_tool("get_session_status")
            print(f"Status: {status.content[0].text}")

    except Exception as e:
        print(f"❌ Erro geral: {e}")
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
