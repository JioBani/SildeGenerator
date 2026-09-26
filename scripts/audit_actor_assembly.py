"""Read-only artifact audit. Reports are new files; approved evidence is never overwritten."""
import argparse
import json
from pathlib import Path

from actor_assembly_gate import audit, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = audit(contract, args.root)
    result["contract_sha256"] = digest(args.contract)
    with args.report.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({key:value for key,value in result.items() if key != "probe_series"}, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
