"""Compare decoded output and isolated layers without changing acceptance gates."""
import argparse
import json
from pathlib import Path

import cv2

from measure_blood_bulge import lumen_support


def compare_support(expected, observed):
    expected = {p[0]: p[1:] for p in expected}
    observed = {p[0]: p[1:] for p in observed}
    common = sorted(expected.keys() & observed.keys())
    return {
        'matched_columns': len(common),
        'missing_columns': sorted(expected.keys() - observed.keys()),
        'columns': [
            {'x': x, 'expected': expected[x], 'observed': observed[x],
             'max_edge_error': max(abs(a-b) for a, b in zip(expected[x], observed[x]))}
            for x in common
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('layers', type=Path)
    parser.add_argument('video', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError('Preserve previous diagnostic report')
    cap = cv2.VideoCapture(str(args.video))
    rows = []
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if abs(fps - 30) > 0.01:
            raise ValueError('This diagnostic expects 30 fps')
        for second in (0, 4):
            layers = {}
            for mode in ('full', 'no-particles', 'no-edges', 'geometry'):
                image = cv2.imread(str(args.layers / f'{second}-{mode}.png'))
                if image is None:
                    raise ValueError(f'Missing {second}-{mode} layer')
                layers[mode] = lumen_support(cv2.resize(image, (640, 360)))
            cap.set(cv2.CAP_PROP_POS_FRAMES, second * 30)
            ok, image = cap.read()
            if not ok:
                raise ValueError('Missing decoded frame')
            encoded = lumen_support(cv2.resize(image, (640, 360)))
            rows.append({
                'second': second,
                'geometry_to_full': compare_support(layers['geometry'], layers['full']),
                'geometry_to_no_particles': compare_support(layers['geometry'], layers['no-particles']),
                'full_to_encoded': compare_support(layers['full'], encoded),
            })
    finally:
        cap.release()
    report = {
        'status': 'DIAGNOSTIC_ONLY', 'rows': rows,
        'limitations': 'Two sampled frames. Color support is not a geometric boundary. '
                        'No acceptance threshold is changed; source fidelity and acting remain unapproved.',
    }
    args.report.write_text(json.dumps(report, indent=2), encoding='utf-8')
    for row in rows:
        print(json.dumps({'second': row['second'], **{
            key: next((c for c in row[key]['columns'] if c['x'] == 320), None)
            for key in ('geometry_to_full', 'geometry_to_no_particles', 'full_to_encoded')
        }}))


if __name__ == '__main__':
    main()
