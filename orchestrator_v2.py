#!/usr/bin/env python3
"""
Orchestrator simplificado com filtragem direta
"""
import asyncio
import logging

from fastmcp import Client, Context, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Domain servers configuration
DOMAINS = {
    "invoicing": "http://127.0.0.1:9101/mcp",
    "products": "http://127.0.0.1:9102/mcp",
    "users": "http://127.0.0.1:9103/mcp",
}

# Session domain tracking
SESSION_DOMAIN = {}

# Domain proxy clients (will be populated during setup)
DOMAIN_CLIENTS = {}

# Create main orchestrator server
main = FastMCP("Orchestrator")


@main.tool(name="list_domains", tags={"orchestrator"})
def list_domains() -> list[str]:
    """List available domain servers that can be selected for this session."""
    return sorted(DOMAINS.keys())


@main.tool(name="get_session_status", tags={"orchestrator"})
def get_session_status(ctx: Context) -> dict[str, str | list[str] | None]:
    """Get the current session status and selected domain."""
    session_id = ctx.session_id or ctx.client_id or "default"
    selected_domain = SESSION_DOMAIN.get(session_id)

    return {
        "session_id": session_id,
        "selected_domain": selected_domain,
        "available_domains": sorted(DOMAINS.keys()),
        "status": "active" if selected_domain else "no_domain_selected",
    }


@main.tool(name="select_domain", tags={"orchestrator"})
async def select_domain(domain: str, ctx: Context) -> dict[str, str]:
    """Select the active domain for this session."""
    if domain not in DOMAINS:
        return {"status": "error", "message": f"Unknown domain: {domain}"}

    session_id = ctx.session_id or ctx.client_id or "default"
    SESSION_DOMAIN[session_id] = domain
    logger.info(f"Session {session_id} selected domain: {domain}")

    return {
        "status": "success",
        "session_id": session_id,
        "selected_domain": domain,
        "message": f"Domain '{domain}' is now active for this session",
    }


@main.tool(name="list_available_tools", tags={"orchestrator"})
async def list_available_tools(ctx: Context) -> dict[str, list[str]]:
    """List all available tools for the current session."""
    session_id = ctx.session_id or ctx.client_id or "default"
    selected_domain = SESSION_DOMAIN.get(session_id)

    result = {
        "session_id": session_id,
        "selected_domain": selected_domain,
        "orchestrator_tools": [
            "list_domains",
            "get_session_status",
            "select_domain",
            "list_available_tools",
        ],
        "domain_tools": [],
    }

    if selected_domain and selected_domain in DOMAIN_CLIENTS:
        try:
            client = DOMAIN_CLIENTS[selected_domain]
            async with client:
                tools = await client.list_tools()
                domain_tool_names = [f"{selected_domain}_{t.name}" for t in tools]
                result["domain_tools"] = domain_tool_names
        except Exception as e:
            logger.warning(f"Failed to get tools from {selected_domain}: {e}")
            result["error"] = str(e)

    return result


def setup_domain_clients() -> None:
    """Setup domain client connections."""
    logger.info("Setting up domain clients...")

    for domain_name, server_url in DOMAINS.items():
        try:
            # Create HTTP client for the domain server with explicit transport
            transport = StreamableHttpTransport(url=server_url)
            client = Client(transport)
            DOMAIN_CLIENTS[domain_name] = client

            logger.info(f"✓ Setup client for {domain_name} domain at {server_url}")

        except Exception as e:
            logger.warning(f"⚠ Failed to setup client for {domain_name} domain: {e}")


def setup_domain_servers() -> None:
    """Setup domain server proxies."""
    logger.info("Setting up domain server proxies...")

    for domain_name, server_url in DOMAINS.items():
        try:
            # Create HTTP client for the domain server with explicit transport
            transport = StreamableHttpTransport(url=server_url)
            client = Client(transport)

            # Create proxy server from the client
            proxy_server = FastMCP.as_proxy(client)

            # Mount the proxy with domain prefix
            main.mount(proxy_server, prefix=domain_name)

            logger.info(f"✓ Mounted {domain_name} domain from {server_url}")

        except Exception as e:
            logger.warning(f"⚠ Failed to mount {domain_name} domain: {e}")
            logger.info(f"Domain {domain_name} will be available when server starts")


if __name__ == "__main__":
    # Setup domain servers and clients on startup
    setup_domain_clients()
    setup_domain_servers()

    # Start the orchestrator server
    logger.info("Starting orchestrator server on http://127.0.0.1:9100")
    main.run(transport="http", host="127.0.0.1", port=9100)
