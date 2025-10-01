import asyncio
from fastmcp import Client

async def main():
    async with Client('https://gofastmcp.com/mcp') as client:
        result = await client.call_tool(name='SearchFastMcp', arguments={'query': 'how to test'})
        print(result)

asyncio.run(main())
