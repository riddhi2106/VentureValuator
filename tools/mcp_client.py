import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def fetch_comps_via_mcp(ticker: str) -> str:
    # Path to the MCP server we created
    server_script = os.path.join(os.path.dirname(__file__), "..", "mcp_server.py")
    
    server_params = StdioServerParameters(
        command=sys.executable,  # Use same venv Python as the calling process
        args=[server_script],
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("get_revenue_multiple", arguments={"ticker": ticker})
                
                # result.content is a list of TextContent objects
                return result.content[0].text
    except Exception as e:
        return f"MCP server error: {e}"

def get_public_comps(ticker: str) -> str:
    """Synchronous wrapper for the MCP client"""
    return asyncio.run(fetch_comps_via_mcp(ticker))
