from pathlib import Path
from types import SimpleNamespace

from experimental_stable_zoom.effects.media import _camera_focus, video_filter


def scene(*, focus=None):
    layout = {} if focus is None else {"camera": {"focus": focus}}
    return SimpleNamespace(duration_seconds=4.0, layout=layout)


def settings():
    return SimpleNamespace(width=1920, height=1080, fps=24, crossfade_seconds=0.35, subtitles_enabled=False)


def test_zoom_keeps_one_focus_and_uses_oversampled_coordinates():
    filters, label = video_filter([scene()], Path("subtitles.ass"), settings(), {
        "crossfade_seconds": 0.35,
        "zoom_strength": 0.045,
        "camera_focus": [0.5, 0.5],
        "camera_oversample": 4,
    }, "fade")

    assert label == "video"
    assert "scale=7680:4320" in filters
    assert "x='(iw-iw/zoom)*0.500000'" in filters
    assert "y='(ih-ih/zoom)*0.500000'" in filters
    assert "1-on" not in filters


def test_scene_can_select_a_single_bounded_focus_point():
    assert _camera_focus(scene(focus=[0.3, 0.7]), {}) == (0.3, 0.7)
    assert _camera_focus(scene(focus=[-2, 4]), {}) == (0.0, 1.0)
    assert _camera_focus(scene(focus="invalid"), {}) == (0.5, 0.5)
