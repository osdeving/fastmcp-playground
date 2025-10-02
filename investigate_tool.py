#!/usr/bin/env python3
"""
Investigar atributos do Tool
"""
import asyncio
import subprocess
import time

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport


async def main():
    print("🚀 Iniciando servidor invoicing...")
    invoicing_process = subprocess.Popen(
        ["uv", "run", "python", "src/invoicing.py"],
        cwd="/home/willams/fastmcp-playground",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)

    print("🧪 Investigando atributos do Tool...")

    # Criar servidor de teste
    test_server = FastMCP("TestServer")

    # Ferramenta com tags
    @test_server.tool(tags={"test", "orchestrator"})
    def test_tool():
        """Test tool"""
        return "test"

    # Criar proxy
    transport = StreamableHttpTransport(url="http://127.0.0.1:9101/mcp")
    client = Client(transport)
    proxy_server = FastMCP.as_proxy(client)
    test_server.mount(proxy_server, prefix="invoicing")

    # Investigar
    async with Client(test_server) as test_client:
        tools = await test_client.list_tools()
        print(f"Total de ferramentas: {len(tools)}")

        for tool in tools:
            print(f"\nFerramenta: {tool.name}")
            print(f"  Tipo: {type(tool)}")
            print(f"  Atributos: {dir(tool)}")
            print(f"  Dict: {tool.__dict__ if hasattr(tool, '__dict__') else 'N/A'}")

            # Tentar acessar propriedades específicas
            for attr in ["tags", "metadata", "extra", "_tags"]:
                try:
                    value = getattr(tool, attr, None)
                    print(f"  {attr}: {value}")
                except:
                    print(f"  {attr}: ERROR")

            break  # Só analisar a primeira ferramenta

    try:
        invoicing_process.terminate()
        invoicing_process.wait(timeout=2)
    except:
        pass


if __name__ == "__main__":
    asyncio.run(main())
