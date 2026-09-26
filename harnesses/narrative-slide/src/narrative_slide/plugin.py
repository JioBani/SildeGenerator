from __future__ import annotations
import math

from app.harness_sdk import HarnessValidation, PipelineGraph, ResourceRequest, TaskNode, TaskResult
from app.harness_sdk.direction import direction_planning_extension, evaluate_direction
from .effects.media import assemble_video, concatenate_audio, render_segment, write_subtitles
from .effects.camera import camera_filter
from .effects.transitions import transition_kind


class ClassicSlideHarness:
    manifest = None
    transition = "fade"

    def describe_planning_contract(self, config):
        return {
            "version": "narrative-slide-0.1",
            "engine_family": "slide",
            "supported_layouts": ["focus", "reaction", "evidence", "comparison"],
            "supported_transitions": ["cut", "crossfade", "dissolve"],
            "supported_rhythms": ["read_then_move_then_hold", "anticipation_action_consequence"],
            "supported_effects": ["hold", "camera_push", "camera_pull"],
            "independent_effects": [],
            "asset_routes": {"cinematic_still": "One designed image per shot with explicit framing and visible action"},
            "constraints": ["Use camera hold for continuity groups", "No articulated actor or diagram animation in a still slide"],
            "narrative_direction": direction_planning_extension(),
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
        findings = list(evaluate_direction(scenes)["findings"])
        for scene in scenes:
            try:
                camera_filter(scene, 2, float(config.get('zoom_strength', .045)))
            except (ValueError, TypeError) as error:
                findings.append(f'{scene.id}:camera_contract:{error}')
            try:
                transition_kind(scene)
            except ValueError as error:
                findings.append(f'{scene.id}:transition_contract:{error}')
        return findings

    async def build_pipeline(self, context):
        operation = context.metadata["operation"]; graph = PipelineGraph(); prefix = context.metadata.get("task_prefix", operation)
        if operation == "render_segment":
            scenes, subtitles, output, config = context.metadata["scenes"], context.metadata["subtitles"], context.metadata["output"], context.metadata["config"]
            async def subtitles_task(_): write_subtitles(scenes, subtitles, context.settings, config); return TaskResult((subtitles,))
            async def render_task(_): await render_segment(scenes, subtitles, output, context.settings, config, context.process, self.transition); return TaskResult((output,))
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
            raise ValueError(f"unsupported classic-slide operation: {operation}")
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
