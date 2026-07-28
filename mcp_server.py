import sys
import yfinance as yf
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

app = Server("finance_server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_revenue_multiple",
            description="Get the approximate revenue multiple (P/S ratio) for a public company using its ticker symbol.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g., AAPL, MSFT, SNOW)"
                    }
                },
                "required": ["ticker"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name != "get_revenue_multiple":
        raise ValueError(f"Unknown tool: {name}")

    ticker = arguments.get("ticker")
    if not ticker:
        return [TextContent(type="text", text="Error: Ticker symbol is required.")]

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        ps_ratio = info.get("priceToSalesTrailing12Months")
        
        if ps_ratio:
            return [TextContent(type="text", text=f"The current Price-to-Sales (revenue multiple) for {ticker} is approximately {ps_ratio:.2f}x.")]
        else:
            return [TextContent(type="text", text=f"Could not find Price-to-Sales ratio for {ticker}. They may not be public or data is missing.")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error fetching data for {ticker}: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
