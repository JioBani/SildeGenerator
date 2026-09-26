"""Outgoing shot transition contract; no model strings reach FFmpeg directly."""
import math


def transition_kind(scene):
    value = getattr(scene, 'transition', None)
    if value is None:
        return 'crossfade'
    if value not in ('cut', 'crossfade', 'dissolve'):
        raise ValueError(f'unsupported cinematic transition: {value}')
    return value


def boundary_fades(scenes, seconds):
    seconds = float(seconds)
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError('crossfade_seconds must be finite and nonnegative')
    return [0.0 if transition_kind(left) == 'cut' else
            min(seconds, left.duration_seconds / 3, right.duration_seconds / 3)
            for left, right in zip(scenes, scenes[1:])]
