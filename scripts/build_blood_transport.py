"""Integrate measured per-pair displacement without replacing it by median velocity."""
import argparse
import json
from pathlib import Path


def integrate(rows):
    if not rows:
        raise ValueError('Empty flow evidence')
    points = [[0, 0]]
    origin = rows[0]['start']
    end = origin
    distance = 0
    for row in rows:
        if abs(row['start']-end) > 1e-6 or row['end'] <= row['start']:
            raise ValueError('Noncontiguous flow intervals')
        if row['measurement'] is None:
            raise ValueError('Missing displacement must not become zero')
        distance += row['measurement']['dx']
        end = row['end']
        points.append([end-origin, distance])
    return points


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve previous transport evidence')
    source = json.loads(args.source.read_text(encoding='utf-8'))
    points = integrate(source['rows'])
    args.output.write_text('window.bloodTransport='+json.dumps(points)+';', encoding='utf-8')
    print(json.dumps({'points':len(points),'end':points[-1]}))


if __name__ == '__main__':
    main()
