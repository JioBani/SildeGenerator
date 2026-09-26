from __future__ import annotations

from app.harness_sdk import HarnessValidation, PipelineGraph, ResourceRequest, TaskNode, TaskResult
from .effects.media import assemble_video, concatenate_audio, render_segment, write_subtitles


class ExperimentalStableZoomHarness:
    manifest = None
    transition = "fade"

    async def build_pipeline(self, context):
        operation = context.metadata["operation"]
        graph = PipelineGraph()
        prefix = context.metadata.get("task_prefix", operation)
        if operation == "render_segment":
            scenes = context.metadata["scenes"]
            subtitles = context.metadata["subtitles"]
            output = context.metadata["output"]
            config = context.metadata["config"]

            async def subtitles_task(_):
                write_subtitles(scenes, subtitles, context.settings, config)
                return TaskResult((subtitles,))

            async def render_task(_):
                await render_segment(scenes, subtitles, output, context.settings, config, context.process, self.transition)
                return TaskResult((output,))

            graph.add(TaskNode(f"{prefix}-subtitles", subtitles_task, resource=ResourceRequest("cpu"), expected_outputs=(subtitles,)))
            graph.add(TaskNode(f"{prefix}-render", render_task, dependencies=(f"{prefix}-subtitles",), resource=ResourceRequest("ffmpeg"), expected_outputs=(output,)))
        elif operation == "subtitles":
            scenes = context.metadata["scenes"]
            output = context.metadata["output"]
            config = context.metadata["config"]

            async def task(_):
                write_subtitles(scenes, output, context.settings, config)
                return TaskResult((output,))

            graph.add(TaskNode(f"{prefix}-write", task, resource=ResourceRequest("cpu"), expected_outputs=(output,)))
        elif operation == "audio_assembly":
            scenes = context.metadata["scenes"]
            work = context.metadata["work"]
            output = work / "narration.m4a"

            async def task(_):
                await concatenate_audio(scenes, work, context.process)
                return TaskResult((output,))

            graph.add(TaskNode(f"{prefix}-concat", task, resource=ResourceRequest("ffmpeg"), expected_outputs=(output,)))
        elif operation == "video_assembly":
            segments = context.metadata["segments"]
            audio = context.metadata["audio"]
            output = context.metadata["output"]

            async def task(_):
                await assemble_video(segments, audio, output, context.process)
                return TaskResult((output,))

            graph.add(TaskNode(f"{prefix}-concat", task, resource=ResourceRequest("ffmpeg"), expected_outputs=(output,)))
        else:
            raise ValueError(f"unsupported experimental-stable-zoom operation: {operation}")
        return graph

    async def validate_result(self, context, result):
        checks = ("video-stream", "audio-stream", "dimensions", "fps", "duration")
        return HarnessValidation(bool(result.get("video_codec") and result.get("audio_codec")), checks, "stable zoom deterministic QC")
