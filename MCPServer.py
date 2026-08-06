import uvicorn, subprocess, tempfile, os
from fastapi import FastAPI
from pydantic import BaseModel
import base64

# --- Your tool logic here ---
def render_mermaid(code: str, fmt: str = "png") -> bytes:
    """
    Render Mermaid code to PNG or SVG using mermaid-cli (mmdc).
    Requires: npm install -g @mermaid-js/mermaid-cli
    """
    # Ensure format is supported
    fmt = fmt.lower()
    if fmt not in {"png", "svg"}:
        raise ValueError("Format must be 'png' or 'svg'")

    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "diagram.mmd")
        output_file = os.path.join(tmpdir, f"diagram.{fmt}")

        # Write mermaid code to file
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Call mmdc (Mermaid CLI)
        subprocess.run(
            ["mmdc", "-i", input_file, "-o", output_file],
            check=True,
        )

        # Read the rendered output
        with open(output_file, "rb") as f:
            return f.read()

# --- MCP schema ---
class ToolRequest(BaseModel):
    code: str
    format: str = "png"
    theme: str | None = None

class ToolResponse(BaseModel):
    success: bool
    image_base64: str | None = None
    error: str | None = None

# --- FastAPI app ---
app = FastAPI(title="Mermaid MCP Server")

@app.post("/tools/render", response_model=ToolResponse)
async def render_tool(req: ToolRequest):
    try:
        result_bytes = render_mermaid(req.code, req.format)
        return ToolResponse(
            success=True,
            image_base64=base64.b64encode(result_bytes).decode("utf-8"),
        )
    except Exception as e:
        return ToolResponse(success=False, error=str(e))

# --- Entry point ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3033)