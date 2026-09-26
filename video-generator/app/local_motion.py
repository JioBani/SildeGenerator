"""Limited, provider-free motion artwork for the isolated production pilot.

This is an authored visual vocabulary, not an AI image or acting approval.
"""
from __future__ import annotations

from typing import Any

from .models import ScenePlan


def _primitive(object_id: str, role: str) -> str:
    value = f"{object_id} {role}".lower()
    if any(word in value for word in ("frame-stack", "frame-triptych", "frame stack", "프레임 묶음")):
        return "frame_set"
    if any(word in value for word in ("crosshair", "control-axis", "십자가 가이드", "교차 기준선")):
        return "crosshair"
    if any(word in value for word in ("unstable-frame", "uneasy-frame", "tilt-frame", "tiltframe", "기울어진 프레임", "기울어지는 프레임")):
        return "tilted_frame"
    if any(word in value for word in ("stable-frame", "balance-frame", "수평 프레임", "안정 구도 프레임")):
        return "level_frame"
    if any(word in value for word in ("balance-weights", "균형추", "균형 무게")):
        return "weights"
    if any(word in value for word in ("dialogue-symbol", "대사 상징", "대화 상징")):
        return "wave"
    if any(word in value for word in ("peripheral-shapes", "주변 형상", "주변 정보")):
        return "dots"
    if any(word in value for word in ("gaze-path", "viewer-path", "시선 경로")):
        return "path"
    if any(word in value for word in ("actor-position", "protagonist-marker", "인물 위치")):
        return "figure"
    if any(word in value for word in ("eye-marker", "eye-guide", "gaze-marker", "시선 포인터", "눈 위치")):
        return "eye"
    if any(word in value for word in ("controls", "조종선")):
        return "path"
    if any(word in value for word in ("phoneguide", "phone-guide", "frame-guides", "스마트폰 내부")):
        return "grid"
    if any(word in value for word in ("phone", "smartphone", "스마트폰")):
        return "phone"
    if any(word in value for word in ("frame-set", "filmframes", "프레임 묶음", "영화 프레임")):
        return "frame_set"
    if any(word in value for word in ("eye-line", "eyeline", "눈선", "시선선", "thirdline", "leftgaze", "rightgaze")):
        return "eye_line"
    if any(word in value for word in ("eye-symbol", "eyepointer", "eye-marker", "눈 표식", "눈 모양", "시선 표식")):
        return "eye"
    if any(word in value for word in ("calmframe", "balanced-panel", "안정 구도", "대칭 패널")):
        return "balanced_panel"
    if any(word in value for word in ("uneasyframe", "offset-panel", "불안 구도", "비대칭 패널")):
        return "offset_panel"
    if any(word in value for word in ("uncertainty-cloud", "불확실", "흐릿한 구름")):
        return "cloud"
    if any(word in value for word in ("grid", "격자", "screen-guide")):
        return "grid"
    if any(word in value for word in ("upper-third", "thirds-line", "horizon-guide", "stableguide", "balance-line", "outertiltguide", "수평 가이드", "수평선", "기준선")):
        return "thirds_line"
    if any(word in value for word in ("lock-pin", "fixationpoint", "fixation-point", "target-point", "고정 핀", "고정점", "목표점")):
        return "pin"
    if any(word in value for word in ("figure-frame", "subject-token", "protagonistmarker", "인물 실루엣", "주인공 실루엣", "인물 위치")):
        return "figure"
    if any(word in value for word in ("travel-path", "이동 경로", "이동선")):
        return "path"
    if any(word in value for word in ("attention-dots", "periphery", "주의점", "시선 점", "주변 시각")):
        return "dots"
    if any(word in value for word in ("speech-wave", "dialoguewave", "dialogue-wave", "대사 파형", "음성 파형", "상징하는 파동")):
        return "wave"
    if any(word in value for word in ("warning-mark", "imbalance-accent", "imbalancecue", "경고 표식", "불균형 강조", "코랄 표시")):
        return "accent"
    if any(word in value for word in ("tilting-frame", "tiltframe", "기울어진 프레임", "기울어지는", "틸트 프레임")):
        return "tilted_frame"
    if any(word in value for word in ("level-frame", "안정 프레임", "수평 프레임")):
        return "level_frame"
    if any(word in value for word in ("frame", "프레임")):
        return "frame"
    if any(word in value for word in ("ocean", "globe", "earth-curve", "earth-horizon", "지구 곡면", "남태평양")):
        return "world"
    if any(word in value for word in ("land", "육지")):
        return "land"
    if any(word in value for word in ("marker", "위치 마커", "위치 기준점")):
        return "marker"
    if object_id == "iss" or any(word in value for word in ("space-station", "satellite", "우주정거장")):
        return "satellite"
    if any(word in value for word in ("orbit", "궤도")):
        return "orbit"
    if "vertical-distance" in value or "수직" in value:
        return "vertical_distance"
    if any(word in value for word in ("distance", "-link", "연결선", "거리선")):
        return "distance"
    if any(word in value for word in ("person", "people", "human", "인물", "사람")):
        return "people"
    return "unsupported"


def author_directed_local_motion(plan: ScenePlan, style: dict[str, Any]) -> ScenePlan:
    """Adapt an actual director plan to editable local graphics, without replacing its story."""
    result = plan.model_copy(deep=True)
    if not result.scenes:
        raise ValueError("Motion direction has no scenes")
    film_framing = any(word in f"{result.title} {result.core_question}" for word in ("영화", "프레임", "구도", "시선"))
    for scene in result.scenes:
        objects = [item for item in scene.object_states if isinstance(item, dict)
                   and item.get("object_id") not in {None, "", "scene", "scene-image",
                                                      "scene-title", "evidence-card", "progress-line", "accent-orbit"}]
        if not objects:
            raise ValueError(f"{scene.id}: motion scene has no directed visual objects")
        if len(objects) > 8:
            raise ValueError(f"{scene.id}: local renderer supports at most eight visual objects")
        primitives = [_primitive(str(item["object_id"]), str(item.get("role") or "")) for item in objects]
        if "unsupported" in primitives:
            missing = [str(item["object_id"]) for item, primitive in zip(objects, primitives)
                       if primitive == "unsupported"]
            raise ValueError(f"{scene.id}: local graphics need authored assets for {', '.join(missing)}")
        labels = [str(item.get("text") or "").strip() for item in scene.layout.get("visual_labels", [])
                  if isinstance(item, dict)]
        if not labels or not all(item.get("role") for item in objects):
            raise ValueError(f"{scene.id}: directed objects need descriptive roles and visual labels")
        if style["id"] == "narrative" and not any(item.get("role") == "subject" for item in objects):
            raise ValueError(f"{scene.id}: narrative motion scene has no subject")
        object_ids = {str(item["object_id"]) for item in objects}
        unsupported = [item.get("kind") for item in scene.motion if isinstance(item, dict)
                       and item.get("object_id") in object_ids
                       and item.get("kind") not in {"reveal", "path_follow", "state_change", "group_split", "pulse", "hold"}]
        if unsupported:
            raise ValueError(f"{scene.id}: local renderer cannot execute {', '.join(map(str, unsupported))}")
        motions = [item for item in scene.motion if isinstance(item, dict)
                   and item.get("object_id") in object_ids
                   and item.get("kind") in {"reveal", "path_follow", "state_change", "group_split", "pulse", "hold"}]
        if not motions:
            raise ValueError(f"{scene.id}: no executable object motion in director plan")
        scene.layout = {
            **scene.layout,
            "local_visual": {
                "mode": "directed",
                "theme": "film_framing" if film_framing else "general",
                "scene_function": scene.scene_function,
                "layout_mode": scene.layout.get("mode", "focus"),
                "heading": scene.viewer_takeaway[:72],
                "objects": [{
                    "id": str(item["object_id"]),
                    "label": str(item["role"])[:48],
                    "role": str(item.get("role") or "object"),
                    "initial": str(item.get("initial") or "")[:50],
                    "final": str(item.get("final") or "")[:50],
                    "primitive": primitives[position],
                    "bounds": item.get("region_hint"),
                } for position, item in enumerate(objects)],
                "labels": labels[:8],
                "motions": [{"id": str(item["object_id"]), "kind": str(item["kind"])}
                            for item in motions],
            },
        }
        scene.renderer_requirements = {
            "preferred": "hyperframes",
            "capabilities": ["editable_dom", "directed_objects"],
            "asset_route": "local_directed_graphic_v1",
        }
    return result


THEMES: tuple[tuple[str, tuple[str, ...], tuple[str, str, str]], ...] = (
    ("spotlight", ("스포트라이트 효과", "남 눈치", "나만 쳐다", "차림새", "옷에 작은 자국"),
     ("내가 느낀 시선", "실제 타인의 주의", "달라진 행동")),
    ("attention", ("뇌", "빈도 환각", "바더", "필터", "관심"), ("주변 정보", "관심 대상", "선택적 주의")),
    ("light", ("빛 공해", "가로등", "밤하늘", "별빛"), ("인공 조명", "밤의 환경", "영향")),
    ("temperature", ("절대영도", "극저온", "온도", "차가운"), ("온도", "입자 운동", "극저온")),
    ("compute", ("GPU", "CPU", "계산", "병렬"), ("입력", "동시 계산", "결과")),
    ("history", ("문명", "역사", "침략", "멸망"), ("사건", "연쇄 변화", "결과")),
)

BEATS: dict[str, dict[str, tuple[str, tuple[str, str, str]]]] = {
    "spotlight": {
        "experience": ("모두가 나를 볼까?", ("작은 옷 자국", "상상 속 시선", "불안")),
        "explanation": ("실제 관심은 다르다", ("내가 느낀 주목", "타인의 관심", "차이")),
        "reflection": ("시선에서 벗어나다", ("자국은 그대로", "시선은 줄어듦", "가벼운 행동")),
    },
    "attention": {
        "experience": ("왜 자꾸 눈에 띌까?", ("평소 거리", "관심 대상", "반복 발견")),
        "explanation": ("뇌가 정보를 고른다", ("정보 유입", "중요 태그", "주의 집중")),
        "reflection": ("환경은 그대로, 인식은 달라진다", ("같은 환경", "인지 필터", "달라진 체감")),
    },
    "light": {
        "experience": ("밤을 밝히는 빛", ("밤하늘", "인공 조명", "시야 변화")),
        "explanation": ("빛은 밤에도 작용한다", ("야간 조명", "생체 리듬", "생태 영향")),
        "reflection": ("밤의 모습을 다시 보다", ("불필요한 빛", "줄이기", "어두운 밤")),
    },
    "temperature": {
        "experience": ("차가움의 기준", ("온도", "입자 운동", "극저온")),
        "explanation": ("운동이 느려진다", ("열 에너지", "운동 변화", "낮은 온도")),
        "reflection": ("극한의 조건", ("실험 조건", "관찰", "새 현상")),
    },
    "compute": {
        "experience": ("계산은 어디서 일어날까?", ("입력", "연산", "출력")),
        "explanation": ("계산을 나누어 처리한다", ("많은 작업", "병렬 계산", "결과 결합")),
        "reflection": ("보이는 결과 뒤의 과정", ("요청", "동시 처리", "화면 결과")),
    },
    "history": {
        "experience": ("사건의 시작", ("문명", "변화", "의문")),
        "explanation": ("원인이 이어지다", ("원인", "연쇄 변화", "결과")),
        "reflection": ("남은 흔적", ("사건", "기록", "해석")),
    },
}


def spotlight_mode(narration: str, index: int, total: int) -> str:
    if index == 0 or "자국" in narration:
        return "incident"
    if "스포트라이트 효과" in narration:
        return "definition"
    if "조명" in narration or "주목" in narration:
        return "imagined_gaze"
    if "실험" in narration or "절반" in narration:
        return "evidence"
    if "이유" in narration:
        return "question"
    if "저마다" in narration or "자기 삶" in narration:
        return "others_busy"
    if index == total - 1 or "나답게" in narration:
        return "release"
    return "realization"


def author_local_motion(plan: ScenePlan, style: dict[str, Any], scenario: str) -> ScenePlan:
    result = plan.model_copy(deep=True)
    theme, labels = next(
        ((name, words) for name, cues, words in THEMES if any(cue.lower() in scenario.lower() for cue in cues)),
        ("general", ("상황", "변화", "결과")),
    )
    total = len(result.scenes)
    for index, scene in enumerate(result.scenes):
        beat = "experience" if index < total / 3 else "explanation" if index < total * 2 / 3 else "reflection"
        heading, beat_labels = BEATS.get(theme, {}).get(beat, (scene.viewer_takeaway[:54], labels))
        mode = spotlight_mode(scene.narration, index, total) if theme == "spotlight" else beat
        scene.layout = {
            **scene.layout,
            "continuity_group": "local-guide-v1" if style["id"] == "narrative" else None,
            "local_visual": {"theme": theme, "beat": beat, "index": index, "total": total,
                             "mode": mode, "heading": heading, "labels": list(beat_labels)},
        }
        if style["id"] == "narrative":
            scene.object_states = [{
                "object_id": "local-guide-v1", "role": "subject", "initial": "observing",
                "final": "noticing" if beat != "reflection" else "understanding",
                "isolation": "not_needed", "asset_route": "authored_vector_presenter_v1",
            }]
            if theme == "spotlight":
                scene.object_states.extend([
                    {"object_id": "shirt-mark-v1", "role": "story-object", "initial": "noticed",
                     "final": "unchanged", "asset_route": "editable_dom"},
                    {"object_id": "other-people-v1", "role": "context", "initial": "present",
                     "final": "occupied_elsewhere", "asset_route": "editable_dom"},
                ])
            scene.layout["visual_labels"] = []
        else:
            scene.object_states = [
                {"object_id": f"local-node-{position}", "role": "diagram-node",
                 "initial": "inactive", "final": "active", "asset_route": "editable_dom"}
                for position in range(3)
            ]
            scene.layout["visual_labels"] = [
                {"text": label, "x": (.2, .5, .8)[position], "y": .45}
                for position, label in enumerate(beat_labels)
            ]
        # The local renderer executes the explicitly authored beat. It does not
        # claim an unapproved character rig, grasp, or image-layer motion.
        scene.motion = []
        scene.renderer_requirements = {
            "preferred": "hyperframes", "capabilities": ["editable_dom", "local_vector_art"],
            "asset_route": "authored_vector_presenter_v1" if style["id"] == "narrative" else "editable_dom",
        }
    return result
