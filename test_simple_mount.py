#!/usr/bin/env python3
"""
Teste simples de mount proxy
"""
import asyncio
import atexit
import signal
import subprocess
import time

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

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

    print("🧪 Testando mount proxy simples...")

    # Criar um servidor simples para testar mount
    test_server = FastMCP("TestServer")

    # Criar proxy do servidor invoicing
    print("Criando proxy...")
    transport = StreamableHttpTransport(url="http://127.0.0.1:9101/mcp")
    client = Client(transport)
    proxy_server = FastMCP.as_proxy(client)

    # Montar o proxy
    print("Montando proxy...")
    test_server.mount(proxy_server, prefix="invoicing")

    # Testar o servidor
    print("Testando servidor com proxy montado...")
    async with Client(test_server) as test_client:
        tools = await test_client.list_tools()
        print(f"Ferramentas disponíveis: {[t.name for t in tools]}")

        # Procurar ferramentas com prefixo
        invoicing_tools = [t.name for t in tools if t.name.startswith("invoicing_")]
        print(f"Ferramentas do invoicing: {invoicing_tools}")

        if invoicing_tools:
            print("✅ Proxy mount funcionou!")
            # Testar uma ferramenta
            tool_name = invoicing_tools[0]
            print(f"Testando ferramenta: {tool_name}")
            if "create" in tool_name:
                result = await test_client.call_tool(
                    tool_name, {"amount": 100.0, "description": "Teste do proxy"}
                )
                print(f"Resultado: {result.content[0].text}")
        else:
            print("❌ Proxy mount falhou - nenhuma ferramenta encontrada")

    cleanup()


if __name__ == "__main__":
    asyncio.run(main())
