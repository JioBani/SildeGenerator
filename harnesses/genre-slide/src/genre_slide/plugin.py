from __future__ import annotations

from app.harness_sdk import HarnessValidation, PipelineGraph, ResourceRequest, TaskNode, TaskResult

from .renderer import assemble_video, concatenate_audio, render_segment, write_subtitles


class AstraMotionHarness:
    manifest = None

    async def build_pipeline(self, context):
        operation = context.metadata["operation"]
        prefix = context.metadata.get("task_prefix", operation)
        graph = PipelineGraph()
        if operation == "render_segment":
            scenes = context.metadata["scenes"]
            output = context.metadata["output"]
            config = context.metadata["config"]

            async def render_task(_):
                await render_segment(scenes, output, context.settings, config, context.process)
                return TaskResult((output,))

            graph.add(TaskNode(
                f"{prefix}-hyperframes",
                render_task,
                resource=ResourceRequest("ffmpeg"),
                expected_outputs=(output,),
            ))
        elif operation == "subtitles":
            scenes, output, config = context.metadata["scenes"], context.metadata["output"], context.metadata["config"]

            async def subtitle_task(_):
                write_subtitles(scenes, output, context.settings, config)
                return TaskResult((output,))

            graph.add(TaskNode(f"{prefix}-write", subtitle_task, resource=ResourceRequest("cpu"), expected_outputs=(output,)))
        elif operation == "audio_assembly":
            scenes, work = context.metadata["scenes"], context.metadata["work"]
            output = work / "narration.m4a"

            async def audio_task(_):
                await concatenate_audio(scenes, work, context.process)
                return TaskResult((output,))

            graph.add(TaskNode(f"{prefix}-concat", audio_task, resource=ResourceRequest("ffmpeg"), expected_outputs=(output,)))
        elif operation == "video_assembly":
            segments, audio, output = context.metadata["segments"], context.metadata["audio"], context.metadata["output"]

            async def assembly_task(_):
                await assemble_video(segments, audio, output, context.process)
                return TaskResult((output,))

            graph.add(TaskNode(f"{prefix}-concat", assembly_task, resource=ResourceRequest("ffmpeg"), expected_outputs=(output,)))
        else:
            raise ValueError(f"unsupported genre-slide operation: {operation}")
        return graph

    async def validate_result(self, context, result):
        valid = bool(
            result.get("video_codec")
            and result.get("audio_codec")
            and result.get("width") == context.settings.width
            and result.get("height") == context.settings.height
            and 0 < float(result.get("duration_seconds") or 0) <= 60.05
            and abs(float(result.get("fps") or 0) - context.settings.fps) <= .05
        )
        return HarnessValidation(
            valid,
            ("video-stream", "audio-stream", "dimensions", "fps", "episode-60", "human-gold-pending"),
            "Genre slide technical QC; design and genre approval remain human gates",
        )
