"""Non-provider assets for the explicitly selected hybrid scene route."""
from pathlib import Path
from .harness_sdk.hybrid import HybridScene
from .rendered_review import file_sha256
from .source_media import prepare_source


def prepare_local_asset(scene, harness, source_root: Path, output: Path, settings):
    route = HybridScene.model_validate(scene.layout["hybrid"])
    if route.route == "cinematic":
        raise ValueError("cinematic_route_requires_image_provider")
    if route.route == "source":
        proof = prepare_source(source_root, route.source_id, output, (settings.width, settings.height))
        scene.layout = {**scene.layout, "hybrid_source": proof, "asset_origin": "registered_source", "asset_provenance": proof}
        return proof
    if route.composition is not None:
        from .illustration_assets import prepare_illustration
        root = getattr(settings, "illustration_assets_dir", None)
        if root is None:
            raise ValueError("illustration_registry_not_configured")
        proof = prepare_illustration(root, route.composition, output, (settings.width, settings.height))
        scene.layout = {**scene.layout, "hybrid_illustration": proof, "asset_origin": "generated_illustration", "asset_provenance": proof}
        return proof
    hook = getattr(harness.instance, "prepare_local_scene_asset", None)
    if hook is None:
        raise ValueError("hybrid_diagram_poster_not_supported")
    hook(scene, output, settings)
    proof = {"origin": "authored_graphic", "provider": "local_diagram", "sha256": file_sha256(output),
             "grammar": route.diagram.grammar, "image_generation_calls": 0}
    scene.layout = {**scene.layout, "asset_origin": "authored_graphic", "asset_provenance": proof}
    return proof
