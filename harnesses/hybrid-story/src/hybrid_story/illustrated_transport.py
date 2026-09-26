"""Generated plate + editable route + independent alpha sprite."""
import hashlib
import html
import shutil
from pathlib import Path

from PIL import Image


def composition_markup(scene, hybrid, assets, index, duration, cursor, width, height):
    spec = hybrid.composition
    text_color = hybrid.design.palette.text if hybrid.design else "white"
    text_back = hybrid.design.palette.background if hybrid.design else "#152e32"
    proof = scene.layout.get("hybrid_illustration") or {}
    if proof.get("prepared_by") != "trusted_illustration_registry" or proof.get("id") != spec.asset_pack_id:
        raise ValueError("illustration_runtime_provenance_required")
    if duration * (spec.end_at - spec.start_at) < 1.8 or duration * (1 - spec.end_at) < 1:
        raise ValueError("illustration_measured_motion_or_hold_too_short")
    for role in ("background", "subject"):
        path = Path(proof[f"{role}_path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != proof[f"{role}_sha256"]:
            raise ValueError("illustration_runtime_hash_mismatch")
        shutil.copy2(path, assets / f"composition-{index}-{role}.png")
    with Image.open(proof["subject_path"]) as image:
        sprite_width = width * spec.subject_width
        sprite_height = sprite_width * image.height / image.width
    points = [(p.x * width, p.y * height) for p in spec.points]
    path_data = f'M{points[0][0]},{points[0][1]} C' + ' '.join(f'{x},{y}' for x, y in points[1:])
    path_id, ship_id = f"route-{index}", f"subject-{index}"
    # The plate and SVG have identical aspect and coordinates, without cover crop.
    content = f'<img class="composition-plate" src="assets/composition-{index}-background.png" alt="">'
    content += f'<svg class="composition-overlay" viewBox="0 0 {width} {height}" aria-label="{html.escape(hybrid.diagram.title)}">'
    content += f'<path id="{path_id}" d="{path_data}" fill="none" stroke="{spec.route_color}" stroke-width="4" stroke-dasharray="9 9"/>'
    state_actions = []
    for node in hybrid.diagram.nodes:
        x, y = node.x * width, node.y * height
        text = html.escape(node.label)
        content += f'<circle cx="{x}" cy="{y}" r="7" fill="{spec.route_color}" stroke="{text_back}" stroke-width="3"/>'
        content += f'<text x="{x}" y="{y+sprite_height/2+38}" text-anchor="middle" fill="{text_color}" stroke="{text_back}" stroke-width="6" paint-order="stroke" font-size="26">{text}</text>'
        for phase, value in [("before", node.before), ("after", node.after)]:
            content += f'<text id="{phase}-{index}-{node.id}" opacity="{1 if phase == "before" else 0}" x="{x}" y="{y+sprite_height/2+70}" text-anchor="middle" fill="{text_color}" stroke="{text_back}" stroke-width="6" paint-order="stroke" font-size="22">{html.escape(value)}</text>'
        state_actions += [
            f"tl.to('#before-{index}-{node.id}',{{opacity:0,duration:.15}},{cursor+duration*node.change_at});",
            f"tl.to('#after-{index}-{node.id}',{{opacity:1,duration:.15}},{cursor+duration*node.change_at});",
        ]
    content += f'<image id="{ship_id}" href="assets/composition-{index}-subject.png" width="{sprite_width}" height="{sprite_height}"/>'
    content += '</svg><div class="source-label">AI 제작 삽화 · 개념 항로</div>'
    motion = f"{{path:'#{path_id}',align:'#{path_id}',alignOrigin:[.5,.5],autoRotate:true}}"
    actions = [
        f"tl.set('#{ship_id}',{{motionPath:{{path:'#{path_id}',align:'#{path_id}',alignOrigin:[.5,.5],autoRotate:true,start:0,end:0}}}},{cursor});",
        f"tl.to('#{ship_id}',{{motionPath:{motion},duration:{duration*(spec.end_at-spec.start_at)},ease:'power2.inOut'}},{cursor+duration*spec.start_at});",
    ]
    return content, actions + state_actions
