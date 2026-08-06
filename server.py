# server.py
import base64
from fastmcp import FastMCP
from typing import Optional

# import your render function (the implementation you already created)
# def render_mermaid(code: str, fmt: str = "png") -> bytes: ...
from MCPTools import render_mermaid

mcp = FastMCP("MermaidRenderer")

@mcp.tool()
def render(code: str, fmt: str = "png", theme: Optional[str] = None) -> dict:
    """
    Input:
      - code: mermaid code string
      - fmt: 'png' or 'svg'
      - theme: optional theme name (ignored unless you wire it into mmdc flags)
    Returns a JSON-like object with base64 data (clients can decode).
    """
    # call your underlying renderer
    img_bytes = render_mermaid(code, fmt=fmt)
    return {"image_base64": base64.b64encode(img_bytes).decode("utf-8")}

if __name__ == "__main__":
    # Run as Streamable HTTP MCP server on port 3033 (mounted at /mcp)
    mcp.run(transport="http", host="127.0.0.1", port=3033)