"""Rebuild the block diagram SVG, the design page and the PNG export.

Usage (from the project root):  python3 tools/build.py
Requires Node with playwright installed for the PNG/screenshots step.
"""
import pathlib, subprocess, sys

here = pathlib.Path(__file__).resolve().parent
root = here.parent
sys.path.insert(0, str(here))
import diagram  # noqa: E402  (builds the SVG string on import)

page = (here / "template.html").read_text(encoding="utf-8").replace("{{SVG}}", diagram.svg)
out = root / "design" / "power-path-v2.html"
out.write_text(page, encoding="utf-8")
print("wrote", out)
try:
    subprocess.run(["node", str(here / "shot.js")], check=True)
    print("wrote design/power-block-diagram-v2.png")
except (FileNotFoundError, subprocess.CalledProcessError) as e:
    print("PNG step skipped:", e)
