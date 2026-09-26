"""Evidence-checked research hints, separate from approved director rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .tracking import atomic_json, sha256_file


REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = Path("/app/research-root") if Path("/app/research-root").is_dir() else REPO_ROOT
MAX_CANDIDATES = 2

# These are retrieval cues for a bounded experiment, not learned production rules.
TRIGGERS = {
    "transport-preserve-time-series": ("흐름", "이동", "운반", "전달", "흘러", "수송", "flow", "transport"),
    "shape-aware-spacing": ("입자", "군집", "여러 개체", "많은 사람", "분산", "particles", "units"),
    "light-pollution-split-clip-region": ("비교", "대비", "양쪽", "두 세계", "contrast", "compare"),
    "light-pollution-parent-local-motion": ("이동", "경로", "따라", "움직", "항해", "route", "move"),
}


def _verified_evidence(case: dict[str, Any], root: Path) -> bool:
    items = case.get("evidence")
    if not isinstance(items, list) or not items:
        return False
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            return False
        path = (root / item["path"]).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            return False
        if sha256_file(path) != item.get("sha256"):
            return False
    return True


def select_research_candidates(
    scenario: str, harness_id: str, *, root: Path = RESEARCH_ROOT,
    planning_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return observed risks only; never authorize an effect or an asset."""
    path = root / "docs" / "director-learning-ledger.json"
    if harness_id != "astra-motion" or not path.is_file():
        return {"status": "UNAVAILABLE", "ledger_sha256": None, "candidates": []}
    ledger = json.loads(path.read_text(encoding="utf-8"))
    if ledger.get("schema_version") != 1 or not isinstance(ledger.get("cases"), list):
        raise ValueError("Invalid research ledger")
    supported = set((planning_contract or {}).get("supported_effects", []))
    candidates = []
    for case in ledger["cases"]:
        if not isinstance(case, dict):
            continue
        case_id = case.get("id")
        terms = TRIGGERS.get(case_id)
        matched_terms = [term for term in terms or () if term.casefold() in scenario.casefold()]
        if not matched_terms:
            continue
        if not _verified_evidence(case, root):
            continue
        effects = case.get("required_effects")
        if not isinstance(effects, list) or not all(isinstance(item, str) for item in effects):
            continue
        candidates.append({
            "id": case_id,
            "matched_terms": matched_terms,
            "reference_id": case.get("reference_id"),
            "scene_functions": case.get("scene_functions", []),
            "observed_failure": str(case.get("failure", ""))[:500],
            "observed_correction": str(case.get("correction", ""))[:500],
            "conditions": case.get("conditions", [])[:3],
            "counterexamples": case.get("counterexamples", [])[:3],
            "required_effects": effects,
            "unsupported_effects": sorted(set(effects) - supported),
            "evidence": case["evidence"],
            "transfer_status": case.get("transfer_status", "NOT_REVIEWED"),
            "production_authorized": False,
        })
        if len(candidates) == MAX_CANDIDATES:
            break
    return {
        "status": "RESEARCH_ONLY" if candidates else "NO_VERIFIED_MATCH",
        "ledger_sha256": sha256_file(path),
        "candidates": candidates,
    }


def research_prompt(brief: dict[str, Any]) -> str:
    if not brief["candidates"]:
        return ""
    observations = [{key: row[key] for key in (
        "id", "matched_terms", "scene_functions", "observed_failure", "observed_correction",
        "conditions", "counterexamples", "unsupported_effects",
    )} for row in brief["candidates"]]
    return (
        "\n--- runtime/research-risk-questions.json ---\n"
        "These are unvalidated research observations, not approved director rules. "
        "You have not inspected the source frames; the observations and evidence hashes are recorded separately. "
        "Use only as questions to check against this script. Do not copy reference "
        "artwork, claim transfer, or request an unsupported effect as executable. "
        "The harness contract and preflight remain authoritative.\n"
        + json.dumps(observations, ensure_ascii=False, sort_keys=True)
    )


def record_research_brief(work_dir: Path, brief: dict[str, Any], *, mode: str, used_in_prompt: bool) -> None:
    atomic_json(work_dir / "director-research-brief.json", {
        **brief,
        "mode": mode,
        "used_in_prompt": used_in_prompt and bool(brief["candidates"]),
        "quality_reviewed": False,
    })
