"""
FastMCP Orchestrator - Domain Gateway Server

This orchestrator provides a gateway to multiple domain-specific MCP servers,
allowing session-based domain selection and tool filtering.

Architecture:
- Orchestrator tools: Always available for domain management
- Domain tools: Available only after domain selection
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from fastmcp import Client, Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# -------------------------------
# Configuration
# -------------------------------

# Remote domain server configurations
DOMAINS: dict[str, str] = {
    "invoicing": "http://127.0.0.1:9101/mcp",
    "products": "http://127.0.0.1:9102/mcp",
    "users": "http://127.0.0.1:9103/mcp",
}  # Session to domain mapping (in production, use Redis or database)
SESSION_DOMAIN: dict[str, str] = {}

# -------------------------------
# Main Orchestrator Server
# -------------------------------

main = FastMCP(
    name="Orchestrator",
    instructions=(
        "Gateway orchestrator for domain-specific MCP servers. "
        "Use 'list_domains' to see available domains and 'select_domain' "
        "to activate domain-specific tools for your session."
    ),
)


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
        "available_domains": list(DOMAINS.keys()),
        "status": "active" if selected_domain else "no_domain_selected",
    }


@main.tool(name="select_domain", tags={"orchestrator"})
async def select_domain(
    domain: Literal["invoicing", "products", "users"], ctx: Context
) -> dict[str, str]:
    """
    Select the active domain for this session.

    Args:
        domain: The domain to activate (invoicing, products, or users)
        ctx: FastMCP context

    Returns:
        Confirmation with session and domain information
    """
    # Get session identifier
    session_id = ctx.session_id or ctx.client_id or "default"

    # Validate domain
    if domain not in DOMAINS:
        raise ToolError(f"Invalid domain: {domain}. Available: {list(DOMAINS.keys())}")

    # Store domain selection for this session
    SESSION_DOMAIN[session_id] = domain
    logger.info(f"Session {session_id} selected domain: {domain}")

    # Notify clients to refresh their tool/resource lists
    await ctx.send_tool_list_changed()
    await ctx.send_resource_list_changed()
    await ctx.send_prompt_list_changed()

    return {
        "status": "success",
        "session_id": session_id,
        "selected_domain": domain,
        "message": f"Domain '{domain}' is now active for this session",
    }


# -------------------------------
# Domain Scoping Middleware
# -------------------------------


class DomainScopeMiddleware(Middleware):
    """
    Session-based domain scoping middleware.

    This middleware ensures that:
    1. Orchestrator tools (listed in ORCHESTRATOR_TOOLS) are always available
    2. Domain tools are only available after domain selection
    3. Each session can have different domain selections
    4. Tool names are properly prefixed by domain
    """

    # Define orchestrator tools explicitly
    ORCHESTRATOR_TOOLS = {"list_domains", "get_session_status", "select_domain"}

    def _is_allowed_tool(self, tool_name: str, session_id: str | None) -> bool:
        """
        Check if a tool is allowed for the current session.

        Args:
            tool_name: Name of the tool
            session_id: Current session identifier

        Returns:
            True if tool is allowed, False otherwise
        """
        # Always allow orchestrator tools
        if tool_name in self.ORCHESTRATOR_TOOLS:
            logger.debug(f"Allowing orchestrator tool: {tool_name}")
            return True

        # For domain tools, check session selection
        if not session_id:
            logger.debug(f"Denying tool {tool_name}: no session_id")
            return False  # No session means no domain access

        selected_domain = SESSION_DOMAIN.get(session_id)
        if not selected_domain:
            logger.debug(
                f"Denying tool {tool_name}: no domain selected for session {session_id}"
            )
            return False  # No domain selected yet

        # Check if tool name matches selected domain prefix
        matches = tool_name.startswith(f"{selected_domain}_")
        logger.debug(
            f"Tool {tool_name}, session {session_id}, domain {selected_domain}: {'ALLOW' if matches else 'DENY'}"
        )
        return matches

    async def on_list_tools(self, ctx: MiddlewareContext, call_next):
        """Filter tools based on session domain selection."""
        # Get all tools from downstream
        tools = await call_next(ctx)
        logger.debug(f"Total tools from downstream: {len(tools)}")

        # Get session ID
        session_id = (
            getattr(ctx.fastmcp_context, "session_id", None)
            if ctx.fastmcp_context
            else None
        )
        logger.debug(f"Session ID: {session_id}")

        # Filter tools based on session and domain
        filtered_tools = [
            tool for tool in tools if self._is_allowed_tool(tool.name, session_id)
        ]

        logger.debug(
            f"Session {session_id}: filtered {len(tools)} tools to {len(filtered_tools)}"
        )
        logger.debug(f"Final tools: {[t.name for t in filtered_tools]}")

        return filtered_tools

    async def on_call_tool(self, ctx: MiddlewareContext, call_next):
        """Validate tool access before execution."""
        tool_name = ctx.message.name
        session_id = (
            getattr(ctx.fastmcp_context, "session_id", None)
            if ctx.fastmcp_context
            else None
        )

        # Check if tool is allowed
        if not self._is_allowed_tool(tool_name, session_id):
            selected_domain = SESSION_DOMAIN.get(session_id or "", "none")
            raise ToolError(
                f"Tool '{tool_name}' is not available for this session. "
                f"Current domain: {selected_domain}. "
                f"Use 'select_domain' to choose a domain first."
            )

        # Tool is allowed, proceed with execution
        return await call_next(ctx)


# Add middleware to the main server
main.add_middleware(DomainScopeMiddleware())


# -------------------------------
# Server Setup and Proxy Mounting
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
            from fastmcp.client.transports import StreamableHttpTransport

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

    # Setup domain server proxies (non-blocking)
    setup_domain_servers()

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
    # Run async setup in background
    try:
        asyncio.run(main_async())
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        logger.info(
            "Starting orchestrator anyway (domains will be available when ready)"
        )

    # Start the orchestrator HTTP server
    start_orchestrator()
