"""Validated camera intent. Coordinates refer to the normalized 16:9 crop."""
import math


def camera_filter(scene, frames, default_zoom):
    layout = getattr(scene, 'layout', {}) or {}
    camera = layout.get('camera', {})
    if camera is None:
        camera = {}
    if not isinstance(camera, dict):
        raise ValueError('layout.camera must be an object')
    mode = camera.get('mode', 'hold')
    if mode not in ('hold', 'push', 'pull'):
        raise ValueError('unsupported cinematic camera mode')
    group = layout.get('continuity_group')
    if group is not None:
        if not isinstance(group, str) or not group.strip():
            raise ValueError('continuity_group must be a nonempty string')
        if mode != 'hold':
            raise ValueError('matched-state continuity groups require hold camera')
    strength = camera.get('strength', default_zoom)
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= .08:
        raise ValueError('camera strength must be finite in [0,0.08]')
    focus = camera.get('focus', [.5, .5])
    if not isinstance(focus, (list, tuple)) or len(focus) != 2:
        raise ValueError('camera focus requires normalized x,y')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in focus):
        raise ValueError('camera focus must be finite in [0,1]')
    progress = f'min(on/{max(1, frames - 1)},1)'
    ease = f'({progress})*({progress})*(3-2*({progress}))'
    zoom = '1' if mode == 'hold' else f'1+{strength}*' + (f'({ease})' if mode == 'push' else f'(1-({ease}))')
    # Anchor the selected focus in screen space, rather than shifting toward a corner.
    x = f'(iw-iw/zoom)*{focus[0]}'
    y = f'(ih-ih/zoom)*{focus[1]}'
    return zoom, x, y
