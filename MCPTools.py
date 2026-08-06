import tempfile, os, subprocess

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

print(render_mermaid(code="flowchart TD; A-->B; B-->C;"))