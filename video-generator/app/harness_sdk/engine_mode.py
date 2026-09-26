"""Explicit product boundaries; shared infrastructure does not merge render modes."""


def evaluate_engine_mode(scenes, contract):
    mode = (contract or {}).get("engine_family")
    if mode is None:
        return []  # Legacy harness contracts keep their behavior.
    if mode not in {"slide", "hybrid"}:
        raise ValueError("unsupported_engine_family")
    findings = []
    for scene in scenes:
        route = (getattr(scene, "layout", {}) or {}).get("hybrid")
        if mode == "slide" and route is not None:
            findings.append(f"{scene.id}:slide_engine_rejects_hybrid_route")
        elif mode == "hybrid" and not isinstance(route, dict):
            findings.append(f"{scene.id}:hybrid_engine_requires_explicit_route")
    return findings
