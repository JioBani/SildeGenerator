"""Measure a manually selected red balloon ROI; not a general object tracker."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def measure(image):
    image = image.convert('RGB')
    if image.size != (640, 360):
        raise ValueError('Expected the existing 640x360 native-frame analysis')
    ys = []
    for y in range(115, 246):
        hits = 0
        for x in range(312, 329):
            r, g, b = image.getpixel((x, y))
            hits += r > 150 and g < 65 and b < 55
        if hits >= 10:
            ys.append(y)
    # Ignore disconnected red lining above/below the balloon.
    accepted = set(ys)
    if 180 not in accepted:
        return 0
    top = bottom = 180
    while top-1 in accepted:
        top -= 1
    while bottom+1 in accepted:
        bottom += 1
    return bottom-top+1


def main():
    p = argparse.ArgumentParser()
    p.add_argument('analysis', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists():
        p.error('Use a new output to preserve evidence')
    data = json.loads(a.analysis.read_text(encoding='utf-8'))
    rows = []
    for frame in data['frames']:
        if 214.5 <= frame['source_second'] <= 217.5:
            file = a.analysis.parent/'frames'/frame['file']
            with Image.open(file) as image:
                height = measure(image)
            rows.append({'frame_index': frame['frame_index'], 'source_second': frame['source_second'],
                         'file': frame['file'], 'frame_sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                         'red_height_px': height})
    if not rows:
        raise ValueError('No frames in the required intervention event window')
    peak = max(r['red_height_px'] for r in rows)
    expanded = [r for r in rows if r['red_height_px'] >= peak*.9]
    result = {'source_sha256': data['source_sha256'], 'analysis_sha256': hashlib.sha256(a.analysis.read_bytes()).hexdigest(),
              'method': 'Manually isolated central red-color strip, 10 of 17 pixels; source PTS preserved',
              'limitations': 'ROI-specific proxy; wire and other objects must be excluded by visual review. Not full silhouette or optical flow.',
              'roi': [312, 115, 329, 246], 'peak_height_px': peak,
              'expanded_first': expanded[0]['source_second'], 'expanded_last': expanded[-1]['source_second'], 'rows': rows}
    a.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}))


if __name__ == '__main__':
    main()
