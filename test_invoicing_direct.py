#!/usr/bin/env python3
"""
Teste direto do servidor invoicing
"""
import asyncio

from fastmcp import Client


async def test_invoicing_direct():
    """Testa o servidor invoicing diretamente"""
    try:
        async with Client("http://127.0.0.1:9101/mcp") as client:
            print("=== Conectado ao servidor invoicing diretamente ===")

            # Listar ferramentas
            tools = await client.list_tools()
            print(f"Ferramentas disponíveis: {[t.name for t in tools]}")

            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")

    except Exception as e:
        print(f"❌ Erro ao testar: {e}")


if __name__ == "__main__":
    asyncio.run(test_invoicing_direct())
