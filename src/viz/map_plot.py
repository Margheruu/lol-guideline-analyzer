"""Plot the player's kills/deaths on the Summoner's Rift map (Pillow-based).

Pillow is used instead of matplotlib because matplotlib's Agg renderer crashes
in this conda env (see CLAUDE.md / toolchain notes). Pillow renders reliably
and the output is a PIL Image (easy to show in Streamlit via st.image).

Coordinate system: timeline positions are game units ~0..14870 with origin at
the bottom-left (y up). Image pixels have origin top-left (y down), so y is
flipped in `to_pixel`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from src.analysis.combat import takedowns_for
from src.analysis.deaths import deaths_for
from src.ingest.ddragon import sr_map_image

MAP_MAX = 14870  # approximate Summoner's Rift max coordinate

_KILL = (60, 200, 60, 255)
_ASSIST = (240, 200, 40, 255)
_DEATH = (235, 30, 30, 255)


def to_pixel(pos: dict[str, float], w: int, h: int) -> tuple[float, float]:
    """Game (x, y) -> image pixel (x, y), flipping y to match image origin."""
    x = pos.get("x", 0) / MAP_MAX * w
    y = (1 - pos.get("y", 0) / MAP_MAX) * h
    return x, y


def render_combat_map(ctx: Any, map_path: Path | None = None,
                      scale: int = 2) -> Image.Image:
    """Return a PIL image of the map with the player's takedowns and deaths."""
    img = Image.open(map_path or sr_map_image()).convert("RGBA")
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    w, h = img.size
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    r = max(4, w // 110)  # marker radius

    for t in takedowns_for(ctx):
        x, y = to_pixel(t.position, w, h)
        color = _KILL if t.kind == "kill" else _ASSIST
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color,
                     outline=(0, 0, 0, 255), width=2)

    for d in deaths_for(ctx):
        x, y = to_pixel(d.position, w, h)
        if d.is_frontmost:  # highlight: died as the most-forward ally
            R = r * 2.4
            draw.ellipse([x - R, y - R, x + R, y + R],
                         outline=_DEATH, width=3)
        s = r * 1.3  # red X
        draw.line([x - s, y - s, x + s, y + s], fill=_DEATH, width=4)
        draw.line([x - s, y + s, x + s, y - s], fill=_DEATH, width=4)
        draw.text((x + s + 2, y - s - 2), f"{d.timestamp_ms // 60000}'",
                  fill=_DEATH, font=font)

    return img


def save_combat_map(ctx: Any, out_path: str | Path,
                    map_path: Path | None = None) -> Path:
    """Render and save the combat map PNG; returns the output path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    render_combat_map(ctx, map_path=map_path).save(out_path)
    return out_path
