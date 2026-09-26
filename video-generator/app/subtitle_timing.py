"""Derive short subtitle cues from measured character alignment when available."""

from __future__ import annotations

import math


def cues_from_alignment(narration: str, alignment: dict | None, duration: float, max_chars: int = 32) -> list[dict]:
    if not isinstance(alignment, dict):
        return []
    characters = alignment.get("characters")
    starts = alignment.get("character_start_times_seconds")
    ends = alignment.get("character_end_times_seconds")
    if not all(isinstance(item, list) for item in (characters, starts, ends)):
        return []
    if not characters or not (len(characters) == len(starts) == len(ends)):
        return []
    spoken = "".join(str(char) for char in characters)
    if "".join(spoken.split()) != "".join(narration.split()):
        return []
    cues = []
    begin = 0
    while begin < len(characters):
        while begin < len(characters) and str(characters[begin]).isspace():
            begin += 1
        if begin >= len(characters):
            break
        limit = min(len(characters), begin + max_chars)
        stop = limit
        if limit < len(characters):
            punctuation = next((index + 1 for index in range(limit - 1, begin + max_chars // 2 - 1, -1)
                if str(characters[index]) in ".!?。！？,，;；"), None)
            whitespace = next((index + 1 for index in range(limit - 1, begin + max_chars // 2 - 1, -1)
                if str(characters[index]).isspace()), None)
            stop = punctuation or whitespace or limit
        text = "".join(str(char) for char in characters[begin:stop]).strip()
        try:
            start = max(0.0, float(starts[begin]))
            end = min(duration, float(ends[stop - 1]))
        except (TypeError, ValueError):
            return []
        if not text or not math.isfinite(start) or not math.isfinite(end) or end <= start or (cues and start < cues[-1]["end"] - .1):
            return []
        cues.append({"text": text, "start": start, "end": end, "source": "elevenlabs_alignment"})
        begin = stop
    return cues
