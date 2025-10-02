from fastmcp import FastMCP
import time

mcp = FastMCP()


@mcp.tool()
def async_tool() -> str:
    """Async tool demo."""
    time.sleep(5)
    return "Finished!"


if __name__ == "__main__":
    mcp.run()
