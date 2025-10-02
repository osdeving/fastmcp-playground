from fastmcp import FastMCP
import math

mcp = FastMCP(name="Calculator", instructions="This MCP can perform basic arithmetic operations.",
              include_tags={"add", "sub"})

@mcp.tool(tags={"add"})
def add(a : int, b : int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool(tags={"sub"})
def subtract(a : int, b : int) -> int:
    """Subtract two numbers"""
    return a - b



from starlette.requests import Request
from starlette.responses import PlainTextResponse
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


if __name__ == '__main__':
    mcp.run()

