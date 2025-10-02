#!/usr/bin/env python3
"""
FastMCP Orchestrator - Versão Final
Gateway para servidores MCP de domínios específicos.
"""
import logging

from fastmcp import Client, Context, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError as ToolExecutionError
from fastmcp.server.middleware import Middleware, MiddlewareContext

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
SESSION_DOMAIN: dict[str, str] = {}

# Create main orchestrator server
main = FastMCP("Orchestrator")

# -------------------------------
# Orchestrator Core Tools
# -------------------------------


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
    """
    Select the active domain for this session.

    Args:
        domain: The domain to activate (invoicing, products, or users)
        ctx: FastMCP context

    Returns:
        Confirmation with session and domain information
    """
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


# -------------------------------
# Simple Domain Filtering Middleware
# -------------------------------


class SimpleDomainMiddleware(Middleware):
    """Simple middleware that allows orchestrator tools + selected domain tools."""

    ORCHESTRATOR_TOOLS = {"list_domains", "get_session_status", "select_domain"}

    # Map domain to its tools (with FastMCP prefixes)
    DOMAIN_TOOLS = {
        "invoicing": {
            "invoicing_create_invoice",
            "invoicing_get_invoice",
            "invoicing_pay_invoice",
        },
        "products": {
            "products_create_product",
            "products_get_product",
            "products_list_products",
        },
        "users": {"users_create_user", "users_get_user", "users_list_users"},
    }

    async def on_list_tools(self, ctx: MiddlewareContext, call_next):
        """Filter tools based on session domain selection."""
        # Get all tools from downstream
        all_tools = await call_next(ctx)

        # Get session ID
        session_id = (
            getattr(ctx.fastmcp_context, "session_id", None)
            if ctx.fastmcp_context
            else None
        )

        logger.info(f"🔍 Middleware debug - Session: {session_id}")
        logger.info(f"🔍 All tools ({len(all_tools)}): {[t.name for t in all_tools]}")
        logger.info(f"🔍 Session domains: {SESSION_DOMAIN}")

        # Always include orchestrator tools
        filtered_tools = [
            tool for tool in all_tools if tool.name in self.ORCHESTRATOR_TOOLS
        ]

        # If domain is selected, include its tools
        if session_id and session_id in SESSION_DOMAIN:
            selected_domain = SESSION_DOMAIN[session_id]
            logger.info(f"🔍 Selected domain: {selected_domain}")
            if selected_domain in self.DOMAIN_TOOLS:
                domain_tool_names = self.DOMAIN_TOOLS[selected_domain]
                logger.info(f"🔍 Expected domain tools: {domain_tool_names}")
                domain_tools = [
                    tool for tool in all_tools if tool.name in domain_tool_names
                ]
                logger.info(f"🔍 Found domain tools: {[t.name for t in domain_tools]}")
                filtered_tools.extend(domain_tools)

        logger.info(f"🔍 Final filtered tools: {[t.name for t in filtered_tools]}")
        logger.debug(
            f"Session {session_id}: {len(all_tools)} -> {len(filtered_tools)} tools"
        )
        return filtered_tools

    async def on_call_tool(self, ctx: MiddlewareContext, call_next):
        """Validate tool access before execution."""
        tool_name = ctx.message.name
        session_id = (
            getattr(ctx.fastmcp_context, "session_id", None)
            if ctx.fastmcp_context
            else None
        )

        # Allow orchestrator tools
        if tool_name in self.ORCHESTRATOR_TOOLS:
            return await call_next(ctx)

        # For domain tools, check session selection
        if not session_id or session_id not in SESSION_DOMAIN:
            raise ToolExecutionError(f"No domain selected. Use select_domain first.")

        selected_domain = SESSION_DOMAIN[session_id]

        # Check if tool belongs to selected domain
        if selected_domain in self.DOMAIN_TOOLS:
            allowed_tools = self.DOMAIN_TOOLS[selected_domain]
            if tool_name not in allowed_tools:
                raise ToolExecutionError(
                    f"Tool '{tool_name}' not available in domain '{selected_domain}'. "
                    f"Available tools: {', '.join(sorted(allowed_tools))}"
                )

        return await call_next(ctx)


# Add middleware to the main server
main.add_middleware(SimpleDomainMiddleware())

# -------------------------------
# Domain Server Setup
# -------------------------------


def setup_domain_servers() -> None:
    """
    Set up proxy connections to remote domain servers.

    Each domain server is mounted with a prefix that matches the domain name,
    so tools become available as:
    - invoicing_create_invoice, invoicing_get_invoice, invoicing_pay_invoice
    - products_search_products, products_get_product, products_check_stock
    - users_get_user, users_update_email, users_list_dependents
    """
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
            # Continue with other domains even if one fails


async def check_domain_servers() -> dict[str, bool]:
    """Check which domain servers are available."""
    status = {}
    for domain_name, server_url in DOMAINS.items():
        try:
            async with Client(server_url) as client:
                await client.list_tools()
                status[domain_name] = True
                logger.info(f"✓ Domain server {domain_name} is available")
        except Exception as e:
            status[domain_name] = False
            logger.warning(f"⚠ Domain server {domain_name} not available: {e}")
    return status


# -------------------------------
# Main Entry Point
# -------------------------------


async def main_async() -> None:
    """Main async setup function."""
    logger.info("Starting FastMCP Orchestrator...")

    # Check initial status of domain servers
    status = await check_domain_servers()
    available_domains = [name for name, available in status.items() if available]
    unavailable_domains = [name for name, available in status.items() if not available]

    if available_domains:
        logger.info(f"✓ Available domains: {', '.join(available_domains)}")
    if unavailable_domains:
        logger.info(
            f"⚠ Unavailable domains: {', '.join(unavailable_domains)} (will retry on demand)"
        )

    logger.info("Orchestrator setup complete!")


def start_orchestrator():
    """Start the orchestrator server."""
    logger.info("Starting orchestrator server on http://127.0.0.1:9100")
    main.run(transport="http", host="127.0.0.1", port=9100)


if __name__ == "__main__":
    # Setup domain servers on startup
    setup_domain_servers()

    # Start the orchestrator server
    start_orchestrator()
