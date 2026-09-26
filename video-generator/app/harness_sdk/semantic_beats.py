"""Opt-in pre-design meaning contract; structural checks are not semantic approval."""
from typing import Annotated, Literal
import hashlib
import json
import re
from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1,max_length=1600,pattern=r"\S")]
Route = Literal["cinematic","diagram","source"]


class BeatModel(BaseModel):
    model_config=ConfigDict(extra="forbid",allow_inf_nan=False)


class RejectedRoute(BeatModel):
    route: Route
    reason: Text


class EvidenceNeed(BeatModel):
    claim_quote: Text
    source_id: str | None
    acceptance_criteria: list[Text] = Field(min_length=1,max_length=5)


class BeatContent(BeatModel):
    literal_content: str = Field(min_length=1,max_length=20000)
    story_function: Text
    information_function: Text
    viewer_state_before: Text
    viewer_state_after: Text
    primary_purpose: Literal["feel","understand","verify"]
    route: Route
    route_reason: Text
    rejected_routes: list[RejectedRoute] = Field(min_length=2,max_length=2)
    new_information: Text
    emotional_change: Text | None
    research_need: Literal["none","factual","visual","historical","geographic","quantitative"]
    required_evidence: list[EvidenceNeed] = Field(max_length=10)
    grammar: Literal["cause_change_result","step_sequence","quantitative_comparison","cumulative_change","transport_track",
                     "whole_detail","before_after","decompose_recombine","evidence_judgment","map_spatial"] | None
    transition_to_next: Text
    confidence: float = Field(ge=0,le=1)

    @model_validator(mode="after")
    def coherent(self):
        expected={"feel":"cinematic","understand":"diagram","verify":"source"}[self.primary_purpose]
        if self.route!=expected: raise ValueError("purpose_route_mismatch")
        if {r.route for r in self.rejected_routes}!={"cinematic","diagram","source"}-{self.route}:
            raise ValueError("rejected_routes_incomplete")
        if (self.grammar is not None)!=(self.route=="diagram"):
            raise ValueError("semantic_grammar_route_mismatch")
        if self.viewer_state_before.strip()==self.viewer_state_after.strip():
            raise ValueError("beat_has_no_viewer_change")
        if self.route=="source" and not self.required_evidence:
            raise ValueError("source_requires_evidence_claim")
        if self.route=="source" and len({e.source_id for e in self.required_evidence})>1:
            raise ValueError("multiple_sources_require_adjacent_beats")
        if not self.literal_content.strip(): raise ValueError("empty_semantic_beat")
        for evidence in self.required_evidence:
            if evidence.claim_quote not in self.literal_content: raise ValueError("evidence_claim_not_in_beat")
        return self


class SemanticBeat(BeatContent):
    cause_beat_numbers: list[int] = Field(max_length=10)


class BeatRelation(BeatModel):
    from_beat_number: int = Field(ge=1, le=10, strict=True)
    kind: Literal["event_cause", "motivation", "context", "sequence"]
    source_quote: Text
    target_quote: Text
    grounding: Literal["explicit", "inferred"]
    explanation: Text


class RelatedBeat(BeatContent):
    relations: list[BeatRelation] = Field(max_length=10)


class ScriptAnalysis(BeatModel):
    version: Literal["semantic-beats-0.1"]
    script_type: Literal["character_story","history_documentary","science_explanation","quantitative_comparison","observational_essay","mixed"]
    central_idea: Text
    beats: list[SemanticBeat] = Field(min_length=1,max_length=10)


class RelatedScriptAnalysis(ScriptAnalysis):
    version: Literal["semantic-beats-0.2"]
    beats: list[RelatedBeat] = Field(min_length=1,max_length=10)


def analysis_model(version):
    if version == "semantic-beats-0.1": return ScriptAnalysis
    if version == "semantic-beats-0.2": return RelatedScriptAnalysis
    raise ValueError("unsupported_semantic_analysis_version")


RELATION_RULES = [
    "event_cause: a prior event brings about the target event, not merely its presentation in the story.",
    "motivation: a goal, reason or information motivates a person's action or choice; it does not cause a pre-existing number or fact.",
    "context: background helps interpret the target, without claiming it brings that target about.",
    "sequence: only order is supported; before/after alone does not prove causation.",
    "Each relation requires exact source and target quotations from the two stated beats and an explicit/inferred grounding label.",
    "Quotations ground endpoints, not the truth of a relation. Independent review must check the actual relation and inferred claims.",
    "Do not add a link just because two beats are adjacent. An empty relations list is valid. No causes are inferred automatically from legacy numbers."]


def semantic_planning_extension(version="semantic-beats-0.1", *, report_missing=False):
    analysis_model(version)
    result={"version":version,"max_beats":10,"max_repairs":3,"repeated_failure_limit":2,
        "minimum_confidence":.75,"rules":[
            "Analyze script meaning before scene design, not by sentence length or topic keywords.",
            "Concatenate literal_content exactly to the original, including whitespace. Split mixed purposes within a sentence when needed.",
            "One beat describes one intended viewer change. Feel uses cinematic; understand uses diagram; verify uses registered source.",
            "Choose no fixed route ratio and invent no protagonist, dilemma, number or historical claim.",
            "Consider both other routes and explain rejection. " + (
                "Name the grammar required by the meaning, even if the runtime does not support it."
                if report_missing else "Name a supported grammar for diagram beats."),
            "Confidence is not approval. Below threshold requires independent alternatives, never arbitrary confident fallback.",
            "Each accepted beat is one source unit and one scene in this first contract. Keep narration and route fixed during design.",
            "Unsupported grammar or absent source stops production; never replace with a still or generic zoom."]}
    if version == "semantic-beats-0.2": result["relation_rules"] = list(RELATION_RULES)
    if report_missing:
        result["capability_reporting"] = "required-grammar-0.1"
        result["rules"].append(
            "For an unsupported diagram, keep route=diagram and name its required grammar from the schema; "
            "never use null, invent a supported substitute, or split the disclaimer off. "
            "Core reports grammar_not_supported before assets. A valid requirement is not execution approval.")
    return result


def semantic_enabled(contract):
    extension=(contract or {}).get("semantic_analysis")
    if extension is None: return False
    if extension!=semantic_planning_extension(extension.get("version"),
            report_missing=extension.get("capability_reporting") is not None):
        raise ValueError("unsupported_semantic_analysis_contract")
    return True


def semantic_review_extension(*, evidence_ids=False):
    return {"version": "semantic-sufficiency-0.2" if evidence_ids else "semantic-sufficiency-0.1", "model": "gpt-5.6-terra",
            "effort": "low", "scope": "pre_render_only", "shared_repairs": 3}


def semantic_review_enabled(contract):
    policy = (contract or {}).get("semantic_review")
    if policy is None:
        return False
    if policy != semantic_review_extension(evidence_ids=policy.get('version')=='semantic-sufficiency-0.2') or not semantic_enabled(contract):
        raise ValueError("unsupported_semantic_review_contract")
    return True


def relation_alternatives_extension():
    return {'version': 'inferred-relation-alternatives-0.1', 'candidate_count': 2,
            'scope': 'one_inferred_relation_only', 'shared_repair_cost': 2}


def inspect_analysis(analysis,scenario,contract):
    findings=[]
    if analysis.version != contract.get("semantic_analysis", {}).get("version"):
        findings.append("semantic_analysis_version_mismatch")
    if ''.join(b.literal_content for b in analysis.beats)!=scenario:
        findings.append("semantic_source_coverage_not_exact")
    grammars=set(contract.get("hybrid_direction",{}).get("grammars",[]))
    source_ids={i["id"] for i in contract.get("trusted_source_catalog",[])}
    for index,beat in enumerate(analysis.beats,1):
        prefix=f"beat-{index:03d}:"
        if any(n<1 or n>=index for n in getattr(beat, "cause_beat_numbers", [])): findings.append(prefix+"cause_not_earlier")
        seen=set()
        for relation in getattr(beat, "relations", []):
            number=relation.from_beat_number
            if number>=index:
                findings.append(prefix+"relation_not_earlier")
            elif relation.source_quote not in analysis.beats[number-1].literal_content:
                findings.append(prefix+"relation_source_quote_not_grounded")
            if relation.target_quote not in beat.literal_content:
                findings.append(prefix+"relation_target_quote_not_grounded")
            key=(number,relation.source_quote,relation.target_quote)
            if key in seen: findings.append(prefix+"duplicate_or_conflicting_relation")
            seen.add(key)
        if beat.grammar and beat.grammar not in grammars: findings.append(prefix+"grammar_not_supported")
        if analysis.version == "semantic-beats-0.2" and beat.grammar in {"quantitative_comparison","cumulative_change","before_after"}:
            # This is only a lower bound on executable data, not quantity semantics.
            # Detailed node quotes, units and arithmetic are checked downstream.
            numbers=re.findall(r"(?<![\d.])\d+(?:\.\d+)?",beat.literal_content)
            if len(numbers)<2:
                findings.append(prefix+"numeric_grammar_needs_two_items_keep_connected_context")
        if beat.confidence<.75: findings.append(prefix+"independent_route_comparison_required")
        if beat.route=="source" and any(e.source_id not in source_ids for e in beat.required_evidence):
            findings.append(prefix+"SOURCE_NOT_AVAILABLE")
    return findings


def bind_and_check_beats(scenes,analysis):
    """Core-owned binding prevents the design model from approving its own route."""
    findings=[]
    by_unit={f"unit-{i:03d}": (i,b) for i,b in enumerate(analysis.beats,1)}
    covered=[]
    for scene in scenes:
        if len(scene.source_unit_ids)!=1 or scene.source_unit_ids[0] not in by_unit:
            findings.append(f"{scene.id}:semantic_beat_merge_or_missing")
            continue
        unit=scene.source_unit_ids[0]
        number,beat=by_unit[unit]
        covered.append(unit)
        expected=beat.model_dump(mode="json")
        scene.layout["semantic_beat"]={"beat_id":f"beat-{number:03d}","source_unit_ids":[unit],"analysis_sha256":analysis_sha256(analysis),**expected}
        if analysis.version=="semantic-beats-0.2":
            declared_cause=(scene.layout.get("direction") or {}).get("cause_scene_number")
            actual_causes={r.from_beat_number for r in beat.relations if r.kind in {"event_cause","motivation"}}
            if declared_cause is not None and declared_cause != number and declared_cause not in actual_causes:
                findings.append(f"{scene.id}:context_promoted_to_cause")
        actual=scene.layout.get("hybrid") or {}
        if actual.get("route")!=beat.route: findings.append(f"{scene.id}:semantic_route_changed")
        if beat.grammar and (actual.get("diagram") or {}).get("grammar")!=beat.grammar:
            findings.append(f"{scene.id}:semantic_grammar_changed")
        if scene.narration!=beat.literal_content: findings.append(f"{scene.id}:semantic_narration_changed")
        if beat.route=="source" and actual.get("source_id") not in {e.source_id for e in beat.required_evidence}:
            findings.append(f"{scene.id}:semantic_evidence_changed")
    if covered!=list(by_unit): findings.append("semantic_scene_coverage_not_exact")
    return findings


def analysis_sha256(analysis):
    value=analysis.model_dump(mode="json")
    if analysis.version=="semantic-beats-0.1":
        # Preserve hashes from the original public field order after factoring common fields.
        for index,beat in enumerate(value["beats"]):
            causes=beat.pop("cause_beat_numbers")
            ordered={}
            for key,item in beat.items():
                ordered[key]=item
                if key=="emotional_change": ordered["cause_beat_numbers"]=causes
            value["beats"][index]=ordered
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(",", ":")).encode("utf-8")).hexdigest()
