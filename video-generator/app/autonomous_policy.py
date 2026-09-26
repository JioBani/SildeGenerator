"""Fail-closed adoption policy; does not produce or replace independent evaluations.

Only the orchestrator's verified observations belong here. Model self-scores and
user-submitted assertions must never be passed as trusted evaluator evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import re


VERSION = "unattended-adoption-0.1"
REPAIR_LIMITS = {"plan": 3, "scene": 3, "candidate": 5, "consecutive_same_cause": 2}
CHECKS = (
    "technical", "script_meaning", "route_selection", "output_frames",
    "design_typography", "source_rights", "motion_semantics_quantities_units",
    "voice_subtitle_sync", "camera", "tone_identity",
)
HELD_OUT_TYPES = {
    "personal_choice", "historical_sources", "scientific_causality",
    "quantity_comparison", "observational_without_protagonist",
}
NEGATIVE_TYPES = {
    "drama_as_infographic", "explanation_as_atmosphere", "duplicate_cut",
    "random_order", "missing_choice_cost", "effect_before_cause", "mixed_units",
    "modern_source_as_historical", "subtitle_outside_frame", "identity_style_drift",
    "generated_text_as_information", "abrupt_repeated_zoom",
}


def _ratio(value, threshold):
    if not isinstance(value, dict):
        return False
    passed, total = value.get("passed"), value.get("total")
    return (type(passed) is int and type(total) is int and total > 0 and
            0 <= passed <= total and Fraction(passed, total) >= Fraction(str(threshold)))


def adoption_decision(evidence, *, candidate_hash, baseline_hash, verified_report_hashes):
    """Aggregate verified reports, leaving absent/unknown dimensions unaccepted.

    verified_report_hashes is supplied by the evidence collector, never the model.
    This aggregator cannot establish semantic correctness or evaluator independence
    by itself. Those remain separate required reports, including benchmark data.
    """
    failures = []
    if any(not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value) for value in (candidate_hash, baseline_hash)):
        failures.append("invalid_artifact_hash")
    if candidate_hash == baseline_hash:
        failures.append("candidate_identical_to_baseline")
    if evidence.get("candidate_sha256") != candidate_hash or evidence.get("baseline_sha256") != baseline_hash:
        failures.append("comparison_hash_mismatch")
    reports = evidence.get("checks", {})
    for name in CHECKS:
        report = reports.get(name)
        if not isinstance(report, dict):
            failures.append(f"missing_evaluation:{name}")
            continue
        if report.get("report_sha256") not in verified_report_hashes:
            failures.append(f"unverified_report:{name}")
        if report.get("candidate_sha256") != candidate_hash:
            failures.append(f"stale_evaluation:{name}")
        if report.get("status") != "PASS" or report.get("critical_failures") != 0:
            failures.append(f"evaluation_failed:{name}")
    exact_metrics = ("meaning_unit_coverage", "source_rights_hash_coverage",
                     "motion_quantity_unit_coverage", "typography_role_coverage", "safe_area_coverage")
    metrics = evidence.get("metrics", {})
    for metric in exact_metrics:
        if not _ratio(metrics.get(metric), 1):
            failures.append(f"coverage_not_complete:{metric}")
    targets = {"held_out_route_accuracy": .95, "misrouting_detection": .98,
               "evaluator_agreement": .9, "negative_control_detection": .95,
               "held_out_superiority": .7}
    for metric, threshold in targets.items():
        if not _ratio(metrics.get(metric), threshold):
            failures.append(f"benchmark_target_not_met:{metric}")
    benchmark = evidence.get("benchmark", {})
    if benchmark.get("report_sha256") not in verified_report_hashes:
        failures.append("benchmark_evidence_unverified")
    if not HELD_OUT_TYPES.issubset(set(benchmark.get("held_out_types", []))):
        failures.append("held_out_types_missing")
    if not NEGATIVE_TYPES.issubset(set(benchmark.get("negative_types", []))):
        failures.append("negative_control_types_missing")
    development = set(benchmark.get("development_script_hashes", []))
    withheld = set(benchmark.get("held_out_script_hashes", []))
    if development & withheld:
        failures.append("held_out_data_leakage")
    if len(withheld) < len(HELD_OUT_TYPES):
        failures.append("insufficient_distinct_held_out_scripts")
    if benchmark.get("critical_regressions") != 0:
        failures.append("regression_evidence_missing_or_failed")
    comparison = evidence.get("blind_comparison", {})
    if comparison.get("report_sha256") not in verified_report_hashes:
        failures.append("blind_comparison_unverified")
    if comparison.get("generator_run_id") == comparison.get("evaluator_run_id") or not comparison.get("evaluator_run_id"):
        failures.append("independent_evaluator_missing")
    if comparison.get("orders") != ["AB", "BA"] or comparison.get("preferred_hashes") != [candidate_hash, candidate_hash]:
        failures.append("candidate_not_superior_in_both_orders")
    concepts = evidence.get("concept_selection", {})
    if concepts.get("report_sha256") not in verified_report_hashes:
        failures.append("concept_comparison_unverified")
    if len(set(concepts.get("candidate_hashes", []))) < 3 or concepts.get("names_hidden") is not True:
        failures.append("three_anonymous_concepts_required")
    if concepts.get("critical_failures") != 0:
        failures.append("concept_critical_checks_missing_or_failed")
    return {"policy_version": VERSION, "status": "GOAL_NOT_MET" if failures else "AUTO_VALIDATED",
            "failures": failures, "candidate_sha256": candidate_hash, "baseline_sha256": baseline_hash,
            "human_approval": None, "production_deployment_authorized": False,
            "does_not_establish": ["measured_human_emotion", "commercial_quality_guarantee"]}


@dataclass
class RepairBudget:
    plan_repairs: int = 0
    candidates: int = 0
    scene_repairs: dict | None = None
    previous_cause: str | None = None
    cause_streak: int = 0

    def __post_init__(self):
        self.scene_repairs = dict(self.scene_repairs or {})

    def next_action(self, kind, *, cause, scene_id=None):
        if kind not in {"plan", "scene", "candidate"}:
            raise ValueError("unknown_repair_kind")
        if kind == "scene" and not scene_id:
            raise ValueError("scene_id_required")
        self.cause_streak = self.cause_streak + 1 if self.previous_cause == cause else 1
        self.previous_cause = cause
        if self.cause_streak >= REPAIR_LIMITS["consecutive_same_cause"]:
            return "FIX_CAPABILITY_OR_EVALUATOR"
        count = self.plan_repairs if kind == "plan" else self.candidates if kind == "candidate" else self.scene_repairs.get(scene_id, 0)
        if count >= REPAIR_LIMITS[kind]:
            return "GOAL_NOT_MET_CONTINUE_OTHER_SAFE_WORK"
        if kind == "plan":
            self.plan_repairs += 1
        elif kind == "candidate":
            self.candidates += 1
        else:
            self.scene_repairs[scene_id] = count + 1
        return "REPAIR_TARGET_ONLY"
