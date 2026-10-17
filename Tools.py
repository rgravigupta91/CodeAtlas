import random, subprocess, tempfile, os, base64, uuid
from langchain_core.tools import tool
import streamlit as st

OUTPUT_DIR = "./Diagrams"
@tool
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

        filename = f"diagram_{uuid.uuid4().hex}.{fmt}"
        output_file = os.path.join(OUTPUT_DIR, filename)

        # Write mermaid code to file
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Call mmdc (Mermaid CLI)
        subprocess.run(
            ["mmdc", "-i", input_file, "-o", output_file, "-w", "2000", "-H", "1500"],
            check=True,
            shell=True
        )

        # Read the rendered output
        with open(output_file, "rb") as f:
            data = f.read()
        
        # Return public URL (or local path if running only locally)
        return {
        "format": fmt,
        "url": f"{OUTPUT_DIR}/{filename}"   # for serving via web
    }
"""   output = {
        "tool": "render_mermaid",
        "result": {
            "format": "png",
            "image_base64": base64.b64encode(data).decode("utf-8")
        }
    }
    return output"""