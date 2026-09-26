"""Compile accepted meaning into an executable, traceable scene-design brief."""
import hashlib
from .harness_sdk.preproduction import preproduction_enabled
from .harness_sdk.semantic_beats import analysis_sha256
from .semantic_review import digest


VISUAL_OBLIGATIONS = {
    "cause_change_result": ("show_cause", "show_relation_arrival", "change_affected_target", "hold_result"),
    "step_sequence": ("show_ordered_steps", "show_completion_order", "hold_final_step"),
    "quantitative_comparison": ("show_same_unit_values", "show_common_zero_scale", "hold_comparison"),
    "cumulative_change": ("show_individual_increments", "show_running_totals", "hold_total"),
    "transport_track": ("show_origin_and_destination", "move_identifiable_token", "hold_arrival"),
    "before_after": ("show_one_entity_and_metric", "retain_first_measurement", "show_second_on_common_scale"),
    "map_spatial": ("show_fixed_named_places", "reveal_quoted_relations", "show_not_to_scale"),
}

PRIMARY_SOURCE_PREFERENCES = {
    "fact": ["original study or issuing institution", "dated primary document"],
    "design": ["original creator or collecting institution", "licensed visual archive"],
    "source": ["original archive or issuing institution", "dated original record"],
}

DIAGRAM_DESIGN_OPTIONS = {
    "quantitative_comparison": ["rows", "columns", "dot_tracks"],
    "before_after": ["columns", "rows", "dot_tracks"],
    "cumulative_change": ["stacked_increments"],
    "step_sequence": ["ordered_nodes"],
    "cause_change_result": ["causal_nodes"],
    "transport_track": ["bounded_path"],
    "map_spatial": ["relative_north_up"],
}


def research_task(beat, beat_id, catalog):
    needed_for = "source" if beat.route == "source" else "design" if beat.research_need == "visual" else "fact"
    registered = sorted({e.source_id for e in beat.required_evidence if e.source_id in catalog})
    candidate_records = [{key: catalog[source_id][key] for key in
                          ("id", "title", "source_url", "date_label", "meaning_limit", "origin")
                          if key in catalog[source_id]}
                         for source_id in registered]
    criteria = [criterion for evidence in beat.required_evidence for criterion in evidence.acceptance_criteria]
    if not criteria:
        criteria = ["Directly supports or depicts the quoted claim in its actual time and scope"]
    return {
        "beat_id": beat_id,
        "needed_for": needed_for,
        "research_need": beat.research_need,
        "research_question": f"Which primary material directly supports or depicts this exact script passage: {beat.literal_content.strip()}",
        "source_excerpt": beat.literal_content,
        "preferred_primary_sources": PRIMARY_SOURCE_PREFERENCES[needed_for],
        "acceptance_criteria": criteria,
        "rights_requirements": (["explicit reuse or quotation basis", "required attribution", "allowed transformations"]
                                if needed_for in {"source", "design"} else []),
        "registered_source_ids": registered,
        "candidate_records": candidate_records,
        "status": "REGISTERED_CANDIDATE" if registered else "DISCOVERY_REQUIRED",
        "rights_review": "REQUIRED_BEFORE_VIDEO_USE" if needed_for in {"source", "design"} else "NOT_APPLICABLE_UNTIL_MEDIA_SELECTED",
        "fact_verified": False,
    }


def compile_preproduction_brief(analysis, contract):
    if not preproduction_enabled(contract):
        raise ValueError("preproduction_brief_opt_in_required")
    library = contract["visual_grammar_library"]
    recipes = {r["id"]: r for r in library["recipes"]}
    catalog = {item["id"]: item for item in contract.get("trusted_source_catalog", [])}
    research_tasks = []
    beats = []
    for index, beat in enumerate(analysis.beats, 1):
        item = {
            "beat_id": f"beat-{index:03d}",
            "source_sha256": hashlib.sha256(beat.literal_content.encode("utf-8")).hexdigest(),
            "route": beat.route,
            "grammar": beat.grammar,
            "viewer_change": {"from": beat.viewer_state_before, "to": beat.viewer_state_after},
            "story_function": beat.story_function,
            "information_function": beat.information_function,
            "new_information": beat.new_information,
        }
        version = contract["preproduction_brief"]["version"]
        if version in {"preproduction-brief-0.2", "preproduction-brief-0.3"}:
            item["transition_intent"] = beat.transition_to_next
            if beat.research_need != "none" or beat.required_evidence:
                task = research_task(beat, item["beat_id"], catalog)
                research_tasks.append(task)
                item["research_task_id"] = item["beat_id"]
        if beat.route == "diagram":
            if beat.grammar not in contract["hybrid_direction"]["grammars"] or beat.grammar not in recipes or beat.grammar not in VISUAL_OBLIGATIONS:
                raise ValueError(f"beat-{index:03d}:diagram_grammar_not_executable")
            recipe = recipes[beat.grammar]
            item["execution"] = {
                "route": "editable_diagram",
                "required_visual_events": list(VISUAL_OBLIGATIONS[beat.grammar]),
                "runtime_requires": recipe["runtime_requires"],
                "do_not_use_when": recipe["do_not_use_when"],
                "implementation_limit": recipe["implementation_limit"],
            }
            if version == "preproduction-brief-0.3":
                item["scene_design"] = {
                    "viewer_start": beat.viewer_state_before,
                    "viewer_end": beat.viewer_state_after,
                    "attention_target": beat.new_information,
                    "visual_events": list(VISUAL_OBLIGATIONS[beat.grammar]),
                    "executable_layouts": DIAGRAM_DESIGN_OPTIONS[beat.grammar],
                    "reading_hold_required": True,
                    "evidence_status": "RESEARCH_PENDING" if item.get("research_task_id") else "NO_RESEARCH_TASK",
                }
        elif beat.route == "source":
            ids = {e.source_id for e in beat.required_evidence}
            if len(ids) != 1 or None in ids or not ids <= catalog.keys():
                raise ValueError(f"beat-{index:03d}:source_not_registered")
            source_id = next(iter(ids))
            item["execution"] = {
                "route": "registered_source",
                "source_id": source_id,
                "claims": [e.claim_quote for e in beat.required_evidence],
                "catalog_entry": catalog[source_id],
                "visual_boundary": "Show the registered observation with date and attribution; do not turn it into evidence for a different event.",
            }
            if version == "preproduction-brief-0.3":
                item["scene_design"] = {
                    "viewer_start": beat.viewer_state_before,
                    "viewer_end": beat.viewer_state_after,
                    "attention_target": beat.new_information,
                    "evidence_source_id": source_id,
                    "evidence_status": "REGISTERED_NOT_FACT_VERIFIED",
                    "reading_hold_required": True,
                }
        elif beat.route == "cinematic":
            item["execution"] = {
                "route": "cinematic_still",
                "emotional_change": beat.emotional_change,
                "visual_boundary": "Stage one visible instant grounded in this beat; no invented later outcome or articulated acting.",
            }
            if version == "preproduction-brief-0.3":
                item["scene_design"] = {
                    "viewer_start": beat.viewer_state_before,
                    "viewer_end": beat.viewer_state_after,
                    "attention_target": beat.story_function,
                    "visible_instant": beat.literal_content,
                    "evidence_status": "RESEARCH_PENDING" if item.get("research_task_id") else "NO_RESEARCH_TASK",
                    "reading_hold_required": False,
                }
        else:
            raise ValueError(f"beat-{index:03d}:route_not_supported")
        beats.append(item)
    result = {
        "version": contract["preproduction_brief"]["version"],
        "analysis_sha256": analysis_sha256(analysis),
        "grammar_library_sha256": library["sha256"],
        "source_catalog_sha256": digest(contract.get("trusted_source_catalog", [])),
        "beats": beats,
        "approval": "STRUCTURAL_ONLY",
    }
    if result["version"] in {"preproduction-brief-0.2", "preproduction-brief-0.3"}:
        result["research_tasks"] = research_tasks
        result["research_status"] = ("DISCOVERY_REQUIRED" if any(t["status"] == "DISCOVERY_REQUIRED" for t in research_tasks)
                                     else "CANDIDATES_ONLY" if research_tasks else "NO_RESEARCH_REQUESTED")
    return result


def require_matching_concept_brief(selection, brief):
    if (selection.get("status") != "PRE_RENDER_CONCEPT_SELECTED"
            or selection.get("preproduction_brief_sha256") != digest(brief)):
        raise ValueError("preproduction_concept_brief_mismatch")


def scene_brief_findings(scenes, brief):
    """Check the few meaning obligations not already covered by diagram schemas."""
    findings = []
    if len(scenes) != len(brief["beats"]):
        return ["preproduction_scene_count_mismatch"]
    for scene, beat in zip(scenes, brief["beats"]):
        hybrid = scene.layout.get("hybrid") or {}
        if hybrid.get("route") != beat["route"]:
            findings.append(f"{scene.id}:preproduction_route_drift")
            continue
        if beat["route"] == "source" and hybrid.get("source_id") != beat["execution"]["source_id"]:
            findings.append(f"{scene.id}:preproduction_source_drift")
        if beat["route"] != "diagram":
            continue
        diagram = hybrid.get("diagram") or {}
        if diagram.get("grammar") != beat["grammar"]:
            findings.append(f"{scene.id}:preproduction_grammar_drift")
            continue
        if beat["grammar"] == "cause_change_result":
            nodes = {n["id"]: n for n in diagram.get("nodes", []) if isinstance(n, dict) and "id" in n}
            edges = diagram.get("edges", [])
            if not any(e.get("target") in nodes and nodes[e["target"]].get("before") != nodes[e["target"]].get("after")
                       for e in edges if isinstance(e, dict)):
                findings.append(f"{scene.id}:cause_target_has_no_visible_change")
    return findings
