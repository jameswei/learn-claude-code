#!/usr/bin/env python3
"""MCP Sum Calculator Server - A simple MCP server with sum functionality"""

from mcp.server.fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP("mcp-sum-calculator")


@mcp.tool()
def sum_numbers(a: int, b: int) -> str:
    """Sum two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of the two numbers as a string
    """
    result = a + b
    return f"The sum of {a} and {b} is {result}"


if __name__ == "__main__":
    mcp.run()