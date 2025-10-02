#!/usr/bin/env python3
"""
Teste isolado do middleware
"""
import asyncio
import logging
import subprocess
import time

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport


# Simular o middleware
class TestDomainScopeMiddleware:
    def __init__(self):
        self.SESSION_DOMAIN = {}

    def _is_allowed_tool(
        self, tool_name: str, tool_tags: set | None, session_id: str | None
    ) -> bool:
        print(
            f"DEBUG: Checking tool {tool_name}, tags={tool_tags}, session={session_id}"
        )

        # Always allow orchestrator tools
        if tool_tags and "orchestrator" in tool_tags:
            print(f"DEBUG: Allowing orchestrator tool: {tool_name}")
            return True

        # For domain tools, check session selection
        if not session_id:
            print(f"DEBUG: Denying tool {tool_name}: no session_id")
            return False

        selected_domain = self.SESSION_DOMAIN.get(session_id)
        if not selected_domain:
            print(
                f"DEBUG: Denying tool {tool_name}: no domain selected for session {session_id}"
            )
            return False

        # Check if tool name matches selected domain prefix
        matches = tool_name.startswith(f"{selected_domain}_")
        print(
            f"DEBUG: Tool {tool_name}, session {session_id}, domain {selected_domain}: {'ALLOW' if matches else 'DENY'}"
        )
        return matches


async def main():
    print("🚀 Iniciando servidor invoicing...")
    invoicing_process = subprocess.Popen(
        ["uv", "run", "python", "src/invoicing.py"],
        cwd="/home/willams/fastmcp-playground",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)

    print("🧪 Testando middleware isoladamente...")

    # Criar servidor de teste
    test_server = FastMCP("TestWithMiddleware")

    # Ferramentas do orchestrator
    @test_server.tool(tags={"orchestrator"})
    def select_domain(domain: str, session_id: str):
        """Select domain"""
        middleware.SESSION_DOMAIN[session_id] = domain
        return f"Selected {domain}"

    # Criar proxy do invoicing
    transport = StreamableHttpTransport(url="http://127.0.0.1:9101/mcp")
    client = Client(transport)
    proxy_server = FastMCP.as_proxy(client)

    # Montar proxy
    test_server.mount(proxy_server, prefix="invoicing")

    # Inicializar middleware
    middleware = TestDomainScopeMiddleware()

    # Testar servidor
    async with Client(test_server) as test_client:
        # 1. Listar ferramentas iniciais
        print("=== 1. Ferramentas iniciais ===")
        tools = await test_client.list_tools()
        all_tools = [t.name for t in tools]
        print(f"Todas as ferramentas: {all_tools}")

        # Simular filtragem do middleware (sem session)
        print("=== 2. Simulando filtragem sem session ===")
        filtered_no_session = []
        for tool in tools:
            if middleware._is_allowed_tool(tool.name, tool.tags, None):
                filtered_no_session.append(tool.name)
        print(f"Ferramentas filtradas (sem session): {filtered_no_session}")

        # Simular seleção de domínio
        print("=== 3. Simulando seleção de domínio ===")
        session_id = "test-session-123"
        middleware.SESSION_DOMAIN[session_id] = "invoicing"
        print(f"Domínio selecionado: invoicing para session {session_id}")

        # Simular filtragem com session e domínio
        print("=== 4. Simulando filtragem com session e domínio ===")
        filtered_with_session = []
        for tool in tools:
            if middleware._is_allowed_tool(tool.name, tool.tags, session_id):
                filtered_with_session.append(tool.name)
        print(f"Ferramentas filtradas (com session e domínio): {filtered_with_session}")

    try:
        invoicing_process.terminate()
        invoicing_process.wait(timeout=2)
    except:
        pass


if __name__ == "__main__":
    asyncio.run(main())
