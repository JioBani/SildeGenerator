from __future__ import annotations
import math

from app.harness_sdk import HarnessValidation, PipelineGraph, ResourceRequest, TaskNode, TaskResult
from app.harness_sdk.direction import direction_planning_extension, evaluate_direction
from app.harness_sdk.hybrid import hybrid_planning_extension, evaluate_hybrid
from app.harness_sdk.semantic_beats import semantic_planning_extension, semantic_review_extension, relation_alternatives_extension
from app.harness_sdk.concept_design import concept_extension
from app.harness_sdk.locked_scene_design import locked_scene_extension
from app.harness_sdk.visible_text import visible_text_extension
from app.harness_sdk.preproduction import preproduction_extension
from .effects.media import assemble_video, concatenate_audio, render_segment, write_subtitles
from .effects.camera import camera_filter
from .effects.transitions import transition_kind
from .hybrid_renderer import render_hybrid, diagram_poster
from .grammar import grammar_brief
from .graphic_type import validate_semantic_labels


class HybridStoryHarness:
    manifest = None
    transition = "fade"

    def describe_planning_contract(self, config):
        return {
            "version": "hybrid-story-0.18.1",
            "engine_family": "hybrid",
            "supported_layouts": ["focus", "reaction", "evidence", "comparison"],
            "supported_transitions": ["cut"],
            "supported_rhythms": ["read_then_move_then_hold", "anticipation_action_consequence"],
            "supported_effects": ["hold", "camera_push", "camera_pull"],
            "independent_effects": ["illustrated_transport"],
            "asset_routes": {"cinematic": "still", "diagram": "editable", "source": "registered"},
            "constraints": ["No rigs", "No fallback"],
            "narrative_direction": direction_planning_extension("narrative-direction-0.2"),
            "hybrid_direction": hybrid_planning_extension("hybrid-scene-0.6"),
            "semantic_analysis": semantic_planning_extension("semantic-beats-0.2", report_missing=True),
            "semantic_review": semantic_review_extension(evidence_ids=True),
            "relation_alternatives": relation_alternatives_extension(),
            "preproduction_brief": preproduction_extension(scene_design=True),
            "concept_selection": concept_extension(directed_graphics=True),
            "locked_scene_design": locked_scene_extension(),
            "visible_text_review": visible_text_extension(),
            "rendered_observation_gate": "rendered-observations-0.2",
            "visual_grammar_library": grammar_brief(),
        }

    def plan_segments(self, scenes, preferred_size, config):
        # Final assembly is concat-only: never split an outgoing dissolve.
        ranges = []
        start = 0
        for index, scene in enumerate(scenes):
            boundary_is_cut = transition_kind(scene) == 'cut' or config.get('crossfade_seconds') == 0
            if index == len(scenes) - 1 or (index + 1 - start >= preferred_size and boundary_is_cut):
                ranges.append((start, index + 1))
                start = index + 1
        return ranges

    def validate_plan(self, scenes, config):
        findings = list(evaluate_direction(scenes)["findings"]) + evaluate_hybrid(scenes)
        for scene in scenes:
            hybrid = (scene.layout or {}).get("hybrid") or {}
            diagram = hybrid.get("diagram") or {}
            if diagram.get("grammar") in {"quantitative_comparison", "cumulative_change", "step_sequence"}:
                try:
                    from app.harness_sdk.hybrid import Diagram
                    validate_semantic_labels(Diagram.model_validate(diagram))
                except ValueError as error:
                    findings.append(f'{scene.id}:graphic_typography:{error}')
            try:
                camera_filter(scene, 2, float(config.get('zoom_strength', .045)))
            except (ValueError, TypeError) as error:
                findings.append(f'{scene.id}:camera_contract:{error}')
            try:
                transition_kind(scene)
            except ValueError as error:
                findings.append(f'{scene.id}:transition_contract:{error}')
        return findings

    def prepare_local_scene_asset(self, scene, output, settings):
        diagram_poster(scene, output, settings.width, settings.height)

    async def build_pipeline(self, context):
        operation = context.metadata["operation"]; graph = PipelineGraph(); prefix = context.metadata.get("task_prefix", operation)
        if operation == "render_segment":
            scenes, subtitles, output, config = context.metadata["scenes"], context.metadata["subtitles"], context.metadata["output"], context.metadata["config"]
            async def subtitles_task(_): write_subtitles(scenes, subtitles, context.settings, config); return TaskResult((subtitles,))
            async def render_task(_): await render_hybrid(scenes, subtitles, output, context.settings, config, context.process); return TaskResult((output,))
            graph.add(TaskNode(f"{prefix}-subtitles", subtitles_task, resource=ResourceRequest("cpu"), expected_outputs=(subtitles,)))
            graph.add(TaskNode(f"{prefix}-render", render_task, dependencies=(f"{prefix}-subtitles",), resource=ResourceRequest("ffmpeg"), expected_outputs=(output,)))
        elif operation == "subtitles":
            scenes, output, config = context.metadata["scenes"], context.metadata["output"], context.metadata["config"]
            async def task(_): write_subtitles(scenes, output, context.settings, config); return TaskResult((output,))
            graph.add(TaskNode(f"{prefix}-write", task, resource=ResourceRequest("cpu"), expected_outputs=(output,)))
        elif operation == "audio_assembly":
            scenes, work = context.metadata["scenes"], context.metadata["work"]
            output = work / "narration.m4a"
            async def task(_): await concatenate_audio(scenes, work, context.process); return TaskResult((output,))
            graph.add(TaskNode(f"{prefix}-concat", task, resource=ResourceRequest("ffmpeg"), expected_outputs=(output,)))
        elif operation == "video_assembly":
            segments, audio, output = context.metadata["segments"], context.metadata["audio"], context.metadata["output"]
            async def task(_): await assemble_video(segments, audio, output, context.process); return TaskResult((output,))
            graph.add(TaskNode(f"{prefix}-concat", task, resource=ResourceRequest("ffmpeg"), expected_outputs=(output,)))
        else:
            raise ValueError(f"unsupported hybrid-story operation: {operation}")
        return graph

    async def validate_result(self, context, result):
        checks = ("video-stream", "audio-stream", "dimensions", "fps", "duration")
        try:
            duration = float(result.get('duration_seconds', 0))
            fps = float(result.get('fps', 0))
            passed = bool(result.get('video_codec') and result.get('audio_codec')) and (
                result.get('width') == context.settings.width and
                result.get('height') == context.settings.height and
                math.isfinite(fps) and abs(fps - context.settings.fps) <= .05 and
                math.isfinite(duration) and 0 < duration <= 60.05)
        except (TypeError, ValueError):
            passed = False
        return HarnessValidation(passed, checks, "Technical streams only; visual and narrative evaluation are separate, not human approval")
