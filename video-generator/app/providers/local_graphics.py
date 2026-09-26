"""Authored backgrounds for the no-API motion pilot."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


def draw_background(scene: Any, path: Path, width: int, height: int) -> None:
    layout = getattr(scene, "layout", {}) or {}
    visual = layout.get("local_visual", {})
    narrative = layout.get("motion_style_id") == "narrative"
    if visual.get("mode") == "directed":
        film_framing = visual.get("theme") == "film_framing"
        image = Image.new("RGB", (width, height), "#13242f" if film_framing else "#eaf2ef")
        draw = ImageDraw.Draw(image)
        mode = visual.get("layout_mode", "focus")
        line = max(3, width // 480)
        guide = "#52727b" if film_framing else "#9dbab5"
        if mode in {"route", "process"}:
            y = int(height * .51)
            draw.line((int(width * .1), y, int(width * .9), y), fill=guide, width=line * 2)
            for x in (.15, .5, .85):
                cx = int(width * x)
                draw.ellipse((cx - line * 3, y - line * 3, cx + line * 3, y + line * 3), fill="#da7258")
        elif mode in {"split", "comparison"}:
            draw.line((width // 2, int(height * .26), width // 2, int(height * .75)),
                      fill=guide, width=line)
        else:
            if film_framing:
                draw.rectangle((int(width * .08), int(height * .16), int(width * .92), int(height * .72)),
                               outline="#385865", width=line)
            else:
                draw.ellipse((int(width * .58), int(height * .2), int(width * .85), int(height * .68)),
                             outline="#c4dad4", width=line * 2)
        draw.rectangle((0, 0, width, int(height * .015)), fill="#e4ad5d" if film_framing else "#dc7356")
    elif narrative and visual.get("theme") == "spotlight":
        image = Image.new("RGB", (width, height), "#e8eee9")
        draw = ImageDraw.Draw(image)
        horizon = int(height * .72)
        draw.rectangle((0, horizon, width, height), fill="#c7d5cb")
        for x in (.05, .26, .72, .91):
            left = int(width * x)
            draw.rectangle((left, 0, left + max(12, int(width * .015)), horizon), fill="#d3dfd7")
        draw.rounded_rectangle((int(width * .58), int(height * .1), int(width * .93), int(height * .55)),
                               radius=max(12, width // 80), fill="#f5f7ef", outline="#9db7ac", width=max(3, width // 400))
        draw.line((0, horizon, width, horizon), fill="#9db7ac", width=max(3, height // 230))
        for x in (.15, .45, .78):
            draw.line((int(width * x), horizon, int(width * (x - .09)), height), fill="#b5c9be", width=2)
    elif narrative:
        image = Image.new("RGB", (width, height), "#183b43")
        draw = ImageDraw.Draw(image)
        horizon = int(height * .68)
        draw.rectangle((0, horizon, width, height), fill="#d3b994")
        draw.polygon([(0, horizon), (width, horizon), (width, horizon + height * .055), (0, horizon + height * .14)], fill="#f3d7a8")
        for index, x in enumerate((.04, .19, .66, .81)):
            left = int(width * x)
            right = left + int(width * (.18 if index % 2 else .12))
            top = int(height * (.21 + .07 * (index % 2)))
            draw.rectangle((left, top, right, horizon), fill="#28515a" if index % 2 else "#204650")
            for row in range(2):
                for column in range(2):
                    px = left + 24 + column * 58
                    py = top + 38 + row * 76
                    if px + 28 < right:
                        draw.rectangle((px, py, px + 28, py + 38), fill="#e5b566" if (row + column + index) % 2 else "#3d6d71")
        draw.ellipse((int(width * .72), int(height * .07), int(width * .8), int(height * .21)), fill="#f4c97b")
    else:
        image = Image.new("RGB", (width, height), "#edf3f1")
        draw = ImageDraw.Draw(image)
        step = max(30, width // 24)
        for x in range(0, width, step):
            draw.line((x, 0, x, height), fill="#dce8e5", width=1)
        for y in range(0, height, step):
            draw.line((0, y, width, y), fill="#dce8e5", width=1)
        draw.rectangle((0, 0, width, int(height * .018)), fill="#e77154")
        draw.ellipse((int(width * .76), int(height * .12), int(width * .98), int(height * .52)), outline="#c5dcd5", width=8)
    if visual.get("theme") == "temperature" and narrative:
        draw.polygon([(0, height * .68), (width * .27, height * .52), (width * .48, height * .68)], fill="#d7e9e4")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)
