from __future__ import annotations

from app.harness_sdk import HarnessValidation, PipelineGraph, ResourceRequest, TaskNode, TaskResult

from .renderer import assemble_video, concatenate_audio, render_segment, write_subtitles
from .scene_program import EFFECTS, LAYOUTS, PLANNABLE_EFFECTS, RHYTHMS, TRANSITIONS


INDEPENDENT_EFFECTS = {"path_follow", "state_change", "group_split", "reaction"}
ACTOR_ROLES = ("actor", "person", "character", "human", "인물", "배우", "캐릭터")
RIG_CAPABILITIES = {"actor_reaction", "grasp_and_retain", "interaction_ready", "limited_mesh"}


class AstraMotionHarness:
    manifest = None

    def describe_planning_contract(self, config):
        return {
            "version": "astra-motion-planning-0.1",
            "supported_layouts": sorted(LAYOUTS),
            "supported_transitions": sorted(TRANSITIONS),
            "supported_rhythms": sorted(RHYTHMS),
            "supported_effects": sorted(PLANNABLE_EFFECTS),
            "independent_effects": sorted(INDEPENDENT_EFFECTS),
            "asset_routes": {
                "static_scene": "whole_image; no independent subject motion",
                "information_graphic": "editable shapes, labels, and paths",
                "moving_illustration": "separate RGBA subject, repaired background, covered regions, pivot, draw order, and full-path review",
                "actor_performance": "separate head, face states, torso and needed limbs; reviewed rig and human acting approval",
            },
            "constraints": [
                "Independent motion requires isolation=required and a normalized region_hint.",
                "A flat image or successful segmentation is not an approved actor rig.",
                "Actor expression, limb contact, and mesh deformation require authored assets and external review; do not replace them with generic reaction or camera motion.",
                "For an unavailable action, name the needed capability in renderer_requirements.capabilities; this records a need, not approval, and the preflight must stop before asset generation.",
            ],
        }

    def validate_plan(self, scenes, config):
        findings = []
        for scene in scenes:
            scene_id = scene.id
            layout = scene.layout if isinstance(scene.layout, dict) else {}
            if layout.get("mode") not in LAYOUTS:
                findings.append(f"{scene_id}:unsupported_motion_layout")
            if scene.transition not in TRANSITIONS:
                findings.append(f"{scene_id}:unsupported_motion_transition")
            if scene.rhythm not in RHYTHMS:
                findings.append(f"{scene_id}:unsupported_motion_rhythm")

            objects = {item.get("object_id"): item for item in scene.object_states if isinstance(item, dict)}
            requirements = scene.renderer_requirements if isinstance(scene.renderer_requirements, dict) else {}
            capabilities = requirements.get("capabilities", [])
            requests = requirements.get("experimental_capabilities", [])
            requested = {item.get("capability") for item in requests if isinstance(item, dict)} if isinstance(requests, list) else set()
            if isinstance(capabilities, list):
                for capability in sorted(RIG_CAPABILITIES.intersection(capabilities)):
                    if capability not in requested:
                        findings.append(f"{scene_id}:capability_requires_external_review:{capability}")

            for action in scene.motion:
                if not isinstance(action, dict):
                    findings.append(f"{scene_id}:motion_action_invalid")
                    continue
                kind = action.get("kind")
                if kind not in EFFECTS:
                    findings.append(f"{scene_id}:unsupported_motion_effect:{kind}")
                    continue
                subject = objects.get(action.get("object_id"))
                if kind not in INDEPENDENT_EFFECTS or not subject:
                    continue
                object_id = action["object_id"]
                if subject.get("isolation") == "not_needed":
                    findings.append(f"{scene_id}:{object_id}:independent_motion_not_isolated")
                if not subject.get("region_hint"):
                    findings.append(f"{scene_id}:{object_id}:region_hint_required")
                role = str(subject.get("role") or "").lower()
                if kind == "reaction" and any(token in role for token in ACTOR_ROLES) and "actor_reaction" not in requested:
                    findings.append(f"{scene_id}:{object_id}:actor_reaction_requires_external_review")
        return findings

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
            raise ValueError(f"unsupported astra-motion operation: {operation}")
        return graph

    async def validate_result(self, context, result):
        valid = bool(
            result.get("video_codec")
            and result.get("audio_codec")
            and result.get("width") == context.settings.width
            and result.get("height") == context.settings.height
            and float(result.get("duration_seconds") or 0) <= 60.05
        )
        return HarnessValidation(
            valid,
            ("video-stream", "audio-stream", "dimensions", "fps", "episode-60", "human-gold-pending"),
            "Astra motion technical QC; design and Gold approval remain human gates",
        )
