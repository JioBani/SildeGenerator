"""Versioned, provider-free preproduction planning policy."""


def preproduction_extension(*, research_tasks=False, scene_design=False):
    return {"version": "preproduction-brief-0.3" if scene_design else "preproduction-brief-0.2" if research_tasks else "preproduction-brief-0.1",
            "scope": "accepted_beats_to_scene_design"}


def preproduction_enabled(contract):
    value = (contract or {}).get("preproduction_brief")
    if value is None:
        return False
    if value not in (preproduction_extension(), preproduction_extension(research_tasks=True),
                     preproduction_extension(scene_design=True)):
        raise ValueError("unsupported_preproduction_brief")
    if not (contract.get("semantic_analysis") and contract.get("visual_grammar_library")):
        raise ValueError("preproduction_requires_semantics_and_grammar_library")
    return True
