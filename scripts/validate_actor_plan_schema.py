"""Offline JSON Schema evidence check (development environment with jsonschema)."""
import argparse
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


def validate(folder):
    receipt = json.loads((folder / 'receipt.json').read_text(encoding='utf-8'))
    hashes = {}
    for name in ('requested-schema.json', 'model-proposal-fixture.json'):
        hashes[name] = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        if hashes[name] != receipt['artifacts'][name]:
            raise ValueError('planner artifact hash changed')
    schema = json.loads((folder / 'requested-schema.json').read_text(encoding='utf-8'))
    proposal = json.loads((folder / 'model-proposal-fixture.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(proposal)
    path = folder / 'schema-validation.json'
    if path.exists():
        raise ValueError('Do not replace schema validation evidence')
    report = {'status': 'PASS', 'artifacts': hashes,
              'scope': 'Offline JSON Schema structural validity, not provider acceptance or director quality'}
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    validate(parser.parse_args().folder)
