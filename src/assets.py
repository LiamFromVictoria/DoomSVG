"""Rasterise the SVG art sheets into PNG atlases with headless Chrome (build-time only).

The game samples textures one texel-column at a time, so the atlases must be bitmaps;
authoring them as SVG keeps every asset in the same format as the game itself.
"""
import asyncio
import base64
import hashlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
CACHE = ROOT / "build" / "cache"


async def _rasterise(svg_path, width, height):
    from cdp import Browser, file_url

    b = await Browser().start()
    try:
        await b.viewport(width, height, 1)
        await b.send("Emulation.setDefaultBackgroundColorOverride", {"color": {"r": 0, "g": 0, "b": 0, "a": 0}})
        await b.goto(file_url(svg_path), settle=0.3)
        res = await b.send(
            "Page.captureScreenshot",
            {"format": "png", "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1}},
        )
        return base64.b64decode(res["data"])
    finally:
        await b.close()


def rasterise(svg_path, width, height):
    """PNG bytes of svg_path rendered at width x height, cached by content hash."""
    svg_path = pathlib.Path(svg_path)
    key = hashlib.sha256(svg_path.read_bytes() + f"{width}x{height}".encode()).hexdigest()[:16]
    CACHE.mkdir(parents=True, exist_ok=True)
    hit = CACHE / f"{svg_path.stem}-{key}.png"
    if not hit.exists():
        hit.write_bytes(asyncio.run(_rasterise(svg_path, width, height)))
    return hit.read_bytes()


def data_uri(png):
    return "data:image/png;base64," + base64.b64encode(png).decode()
