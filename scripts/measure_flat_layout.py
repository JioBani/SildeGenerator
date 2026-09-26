"""Compare silhouettes against a flat background; output is framing evidence only."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops


def bounds(file):
    with Image.open(file) as im:
        im = im.convert('RGB')
        bg = im.getpixel((0, 0))
        diff = ImageChops.difference(im, Image.new('RGB', im.size, bg))
        r, g, b = diff.split()
        mask = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v > 45 else 0)
        box = mask.getbbox()
        if box is None:
            raise ValueError('No foreground detected')
        return {'size': im.size, 'bbox': box, 'background': bg}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('candidate', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists():
        p.error('Output must be new')
    src, dst = bounds(a.source), bounds(a.candidate)
    factor = dst['size'][0]/src['size'][0]
    target = [v*factor for v in src['bbox']]
    box = dst['bbox']
    scale = (target[3]-target[1])/(box[3]-box[1])
    shift = [target[0]-box[0]*scale, target[1]-box[1]*scale]
    report = {'source': src, 'candidate': dst, 'target_bbox': target,
              'height_fit_scale': scale, 'top_left_fit_translation': shift,
              'limitations': 'Single flat-background fixture only. Uniform framing fit does not repair anatomy, proportions or timing.'}
    a.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
