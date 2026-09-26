"""Small explicit library: select by meaning, never by an unverified score."""
import hashlib
import json
from pathlib import Path


def grammar_brief():
    path = Path(__file__).resolve().parents[2] / "knowledge/visual-grammar.json"
    data = path.read_bytes()
    ledger = json.loads(data)
    if ledger["version"] != "hybrid-grammar-ledger-0.4":
        raise ValueError("unsupported_visual_grammar_ledger")
    ids = [item["id"] for item in ledger["recipes"]]
    if set(ids) != {"cause_change_result", "quantitative_comparison", "transport_track", "cumulative_change", "step_sequence", "before_after", "map_spatial"} or len(ids) != 7:
        raise ValueError("visual_grammar_runtime_mismatch")
    # Keep detailed observations in the hash-bound ledger. The planning packet
    # carries applicability, exclusions and limits without repeating provenance.
    keys=('id','use_when','do_not_use_when','runtime_requires','implementation_limit','quality_status')
    return {'version':ledger['version'],'scope':ledger['scope'],
            'sha256':hashlib.sha256(data).hexdigest(),
            'recipes':[{k:v for k,v in recipe.items() if k in keys} for recipe in ledger['recipes']]}
