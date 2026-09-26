"""Bound experimental planning output without editing or salvaging its meaning."""
from copy import deepcopy
import re


REPEATED_BLOCK = re.compile(r"(.{24,512}?)\1{3}", re.DOTALL)


def bounded_phase_schema(schema):
    result = deepcopy(schema)
    def walk(value):
        if isinstance(value, dict):
            phases = value.get("properties", {}).get("phases")
            if isinstance(phases, dict) and phases.get("type") == "array":
                phases["items"]["maxLength"] = 240
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(result)
    return result


class PlanningStreamGuard:
    def __init__(self, *, max_chars=128000, max_string_chars=8000):
        self.max_chars = max_chars
        self.max_string_chars = max_string_chars
        self.total = 0
        self.in_string = False
        self.escaped = False
        self.string = []

    def feed(self, delta):
        for char in delta:
            self.total += 1
            if self.total > self.max_chars:
                raise RuntimeError("planning_stream_limit:total_characters")
            if not self.in_string:
                if char == '"':
                    self.in_string = True
                    self.string = []
                continue
            if char == '"' and not self.escaped:
                self.in_string = False
                self.string = []
                continue
            self.string.append(char)
            if len(self.string) > self.max_string_chars:
                raise RuntimeError("planning_stream_limit:single_string")
            if len(self.string) % 128 == 0 and REPEATED_BLOCK.search(''.join(self.string[-4096:])):
                raise RuntimeError("planning_stream_limit:repeated_string_block")
            self.escaped = char == '\\' and not self.escaped
