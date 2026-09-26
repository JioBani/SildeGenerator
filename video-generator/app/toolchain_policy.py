from __future__ import annotations

from typing import Any


VERSION = "astra-toolchain-policy-1.0"

TOOLS: dict[str, dict[str, str]] = {
    "classic-slide": {"role": "stable_runtime", "status": "production", "purpose": "static_image_voice_subtitle"},
    "hyperframes": {"role": "deterministic_runtime", "status": "explicit_selection", "purpose": "editable_web_motion"},
    "gsap": {"role": "motion_choreography", "status": "allowlisted", "purpose": "timeline_easing_stagger"},
    "opentoonz-plastic": {"role": "gold_reference", "status": "manual_benchmark", "purpose": "2d_mesh_rigidity_stacking"},
    "blender-armature": {"role": "gold_authoring", "status": "offline_only", "purpose": "bone_weight_hidden_region_authoring"},
    "astra-mesh-evidence": {"role": "geometry_qc", "status": "experiment", "purpose": "stretch_area_flip_seam_neutral"},
    "playwright": {"role": "visual_review", "status": "planned", "purpose": "baseline_candidate_diff"},
    "scikit-image": {"role": "image_qc", "status": "planned", "purpose": "ssim_hausdorff_psnr"},
    "libigl": {"role": "solver_benchmark", "status": "research_only", "purpose": "arap_slim_comparator"},
    "synfig": {"role": "authoring_comparator", "status": "research_only", "purpose": "raster_bone_deformation"},
}


def plan_scene_toolchain(renderer_requirements: dict[str, Any], *, selected_harness: str) -> dict[str, Any]:
    requirements = renderer_requirements if isinstance(renderer_requirements, dict) else {}
    experimental = requirements.get("experimental_capabilities", [])
    names = {
        row.get("capability") for row in experimental
        if isinstance(row, dict) and isinstance(row.get("capability"), str)
    } if isinstance(experimental, list) else set()

    runtime = ["classic-slide"]
    reason_codes = ["stable_default"]
    if selected_harness == "astra-motion":
        runtime = ["hyperframes", "gsap"]
        reason_codes = ["user_selected_astra_motion", "deterministic_frame_seek", "safe_effect_allowlist"]

    authoring: list[str] = []
    qc: list[str] = []
    if "limited_mesh" in names:
        authoring = ["opentoonz-plastic", "blender-armature"]
        qc = ["astra-mesh-evidence"]
        reason_codes.extend(["limited_mesh_requires_gold_reference", "geometry_evidence_required"])
    if names & {"actor_reaction", "grasp_and_retain", "interaction_ready"}:
        if "blender-armature" not in authoring:
            authoring.append("blender-armature")
        reason_codes.append("authored_actor_rig_required")

    return {
        "version": VERSION,
        "runtime": runtime,
        "authoring": authoring,
        "quality_control": qc,
        "human_review": bool(names) or selected_harness == "astra-motion",
        "reason_codes": reason_codes,
        "tools": {name: TOOLS[name] for name in runtime + authoring + qc},
        "automatic_external_tool_execution": False,
    }
