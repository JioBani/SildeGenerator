from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    if len(sys.argv) not in (3, 4):
        raise SystemExit("usage: reference_contact_sheet.py <capture-directory> <output.png> [interval-seconds]")
    capture_directory = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    capture_manifest = capture_directory / "capture-manifest.json"
    if capture_manifest.is_file():
        manifest = json.loads(capture_manifest.read_text(encoding="utf-8"))
        captures = manifest["captures"]
        frame_root = capture_directory
    else:
        analysis = json.loads((capture_directory / "analysis.json").read_text(encoding="utf-8"))
        interval = int(sys.argv[3]) if len(sys.argv) == 4 else 10
        captures = [
            {"seconds": row["second"], "filename": row["frame"]}
            for row in analysis["per_second"]
            if row["second"] % interval == 0
        ]
        frame_root = capture_directory / "frames-1fps"
    columns = 4 if len(captures) > 16 else 2
    cell_width = 480 if columns == 4 else 720
    image_height = 270 if columns == 4 else 405
    label_height = 34 if columns == 4 else 42
    rows = (len(captures) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * (image_height + label_height)), "#111820")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=18 if columns == 4 else 24)
    for index, capture in enumerate(captures):
        row, column = divmod(index, columns)
        x = column * cell_width
        y = row * (image_height + label_height)
        with Image.open(frame_root / capture["filename"]) as frame:
            frame = frame.convert("RGB")
            frame.thumbnail((cell_width, image_height))
            offset_x = x + (cell_width - frame.width) // 2
            offset_y = y + (image_height - frame.height) // 2
            sheet.paste(frame, (offset_x, offset_y))
        seconds = float(capture["seconds"])
        draw.text((x + 16, y + image_height + 8), f"{seconds // 60:02.0f}:{seconds % 60:04.1f}", fill="white", font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


if __name__ == "__main__":
    main()
