from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .tracking import atomic_json


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CodexTranscript:
    """Durable, append-only capture of one streamed Codex request attempt."""

    def __init__(
        self,
        work_dir: Path,
        attempt: int,
        request: dict[str, Any],
        *,
        model: str,
        effort: str,
        fast_mode: bool,
    ) -> None:
        self.directory = work_dir / "codex" / f"attempt-{attempt}"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.request_path = self.directory / "request.json"
        self.events_path = self.directory / "events.jsonl"
        self.output_path = self.directory / "output.txt"
        self.final_path = self.directory / "final-response.json"
        self.summary_path = self.directory / "summary.json"
        self.event_count = 0
        self.event_counts: dict[str, int] = {}
        self.started_at = _now()
        self.first_event_at: str | None = None
        self.first_output_at: str | None = None
        self.completed_at: str | None = None
        self.last_event_at: str | None = None
        self.request_id: str | None = None
        self.actual_service_tier: str | None = None
        self.model = model
        self.effort = effort
        self.fast_mode = fast_mode
        self.status = "streaming"
        self.error: str | None = None
        atomic_json(self.request_path, request)
        self.events_path.write_text("", encoding="utf-8")
        self.output_path.write_text("", encoding="utf-8")
        self._write_summary()

    def record(self, event_name: str | None, raw_data: str, payload: dict[str, Any]) -> str:
        received_at = _now()
        event_type = str(payload.get("type") or event_name or "message")
        self.event_count += 1
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
        self.first_event_at = self.first_event_at or received_at
        self.last_event_at = received_at
        response = payload.get("response") if isinstance(payload.get("response"), dict) else None
        self.request_id = str(
            payload.get("response_id")
            or payload.get("id")
            or (response or {}).get("id")
            or self.request_id
            or ""
        ) or None
        tier = (response or {}).get("service_tier") or payload.get("service_tier")
        if tier:
            self.actual_service_tier = str(tier)
        line = json.dumps({
            "received_at": received_at,
            "event": event_name,
            "type": event_type,
            "data": raw_data,
        }, ensure_ascii=False, separators=(",", ":"))
        with self.events_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line + "\n")
            stream.flush()
        self._write_summary()
        return event_type

    def append_output(self, delta: str) -> None:
        if not delta:
            return
        self.first_output_at = self.first_output_at or _now()
        with self.output_path.open("a", encoding="utf-8", newline="") as stream:
            stream.write(delta)
            stream.flush()
        self._write_summary()

    def replace_output(self, text: str) -> None:
        self.first_output_at = self.first_output_at or (_now() if text else None)
        self.output_path.write_text(text, encoding="utf-8", newline="")
        self._write_summary()

    def complete(self, response: dict[str, Any]) -> None:
        self.status = str(response.get("status") or "completed")
        self.completed_at = _now()
        self.request_id = str(response.get("id") or self.request_id or "") or None
        self.actual_service_tier = str(response.get("service_tier") or self.actual_service_tier or "") or None
        atomic_json(self.final_path, response)
        self._write_summary()

    def fail(self, error: Exception | str) -> None:
        self.status = "failed"
        self.error = str(error)[:4000]
        self.completed_at = _now()
        self._write_summary()

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "model": self.model,
            "effort": self.effort,
            "fast_mode_requested": self.fast_mode,
            "service_tier_requested": "priority" if self.fast_mode else "default",
            "service_tier_actual": self.actual_service_tier,
            "request_id": self.request_id,
            "started_at": self.started_at,
            "first_event_at": self.first_event_at,
            "first_output_at": self.first_output_at,
            "last_event_at": self.last_event_at,
            "completed_at": self.completed_at,
            "event_count": self.event_count,
            "event_counts": self.event_counts,
            "error": self.error,
        }

    def _write_summary(self) -> None:
        atomic_json(self.summary_path, self.summary())

    def paths(self) -> list[tuple[Path, str]]:
        return [
            (self.request_path, "codex_request"),
            (self.events_path, "codex_stream_events"),
            (self.output_path, "codex_output"),
            (self.final_path, "codex_final_response"),
            (self.summary_path, "codex_transcript_summary"),
        ]
