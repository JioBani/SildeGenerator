"""Compile director-authored scene designs without genre frame templates."""
import html
import hashlib
import json
import math
import re
import shutil
from pathlib import Path

GENRES = {'knowledge','history','tutorial','character','cartoon','documentary'}
DESIGN_VERSION = 'scene-design-1'
CSS = """
@font-face{font-family:'Noto Sans CJK KR';src:local('Noto Sans CJK KR');font-style:normal;font-weight:100 900}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;font-family:'Noto Sans CJK KR',Arial,sans-serif;letter-spacing:0}
.scene{position:absolute;inset:0;overflow:hidden;opacity:0;background:var(--background);color:var(--foreground)}
.region{position:absolute;overflow:hidden}.media img{width:100%;height:100%;object-fit:var(--image-fit)}
.media.line{border:var(--border-width) solid var(--accent)}.media.matte{background:var(--matte);padding:var(--media-padding)}
.title{margin:0;font-size:var(--title-size);line-height:1.18;font-weight:var(--title-weight);word-break:keep-all;overflow-wrap:anywhere}
.caption{padding:16px 22px;background:var(--caption-background);color:var(--caption-foreground);font-size:var(--caption-size);line-height:1.35;overflow-wrap:anywhere}
.credit{position:absolute;left:2%;bottom:2%;font-size:20px;padding:7px 10px;background:rgba(255,255,255,.92);color:#24363b;max-width:54%;overflow-wrap:anywhere}
.visual-label{position:absolute;width:28%;min-height:64px;transform:translateX(-50%);text-align:center;font-size:30px;font-weight:700;line-height:1.25;color:var(--foreground);overflow-wrap:anywhere;background:rgba(255,255,255,.92)}
"""


def _color(value, field):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
        raise ValueError(f'Invalid authored design color: {field}')
    return value


def _number(value, low, high, field):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'Invalid authored design number: {field}')
    return float(value)


def _box(value, field):
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f'Invalid authored design box: {field}')
    x, y, width, height = (_number(item, 0, 1, field) for item in value)
    if width < .12 or height < .08 or x + width > 1 or y + height > 1:
        raise ValueError(f'Authored design box outside frame: {field}')
    return x, y, width, height


def _box_style(box):
    x, y, width, height = box
    return f'left:{x*100:.3f}%;top:{y*100:.3f}%;width:{width*100:.3f}%;height:{height*100:.3f}%'


def _design(layout):
    design = layout.get('authored_design') if isinstance(layout, dict) else None
    if not isinstance(design, dict) or design.get('version') != DESIGN_VERSION:
        raise ValueError('Scene Design Contract required; fixed genre frames are disabled')
    rationale = design.get('rationale')
    if not isinstance(rationale, str) or not 12 <= len(rationale) <= 600:
        raise ValueError('Authored design requires a concrete rationale')
    image_fit = design.get('image_fit')
    treatment = design.get('media_treatment')
    motion = design.get('entry_motion')
    if image_fit not in ('contain', 'cover') or treatment not in ('none', 'line', 'matte'):
        raise ValueError('Invalid authored media treatment')
    if motion not in ('fade', 'rise', 'push', 'scale'):
        raise ValueError('Invalid authored entry motion')
    return {
        'version': DESIGN_VERSION, 'rationale': rationale,
        'background': _color(design.get('background'), 'background'),
        'foreground': _color(design.get('foreground'), 'foreground'),
        'accent': _color(design.get('accent'), 'accent'),
        'caption_background': _color(design.get('caption_background'), 'caption_background'),
        'caption_foreground': _color(design.get('caption_foreground'), 'caption_foreground'),
        'media_box': _box(design.get('media_box'), 'media_box'),
        'title_box': _box(design.get('title_box'), 'title_box'),
        'caption_box': _box(design.get('caption_box'), 'caption_box'),
        'image_fit': image_fit, 'media_treatment': treatment, 'entry_motion': motion,
        'title_size': _number(design.get('title_size'), 28, 96, 'title_size'),
        'caption_size': _number(design.get('caption_size'), 22, 56, 'caption_size'),
        'title_weight': int(_number(design.get('title_weight'), 400, 900, 'title_weight')),
    }


def _entry(lines, selector, design, cursor, duration):
    entrance = min(.8, duration / 3)
    starts = {'fade': '{opacity:0}', 'rise': '{y:24,opacity:0}', 'push': '{x:30,opacity:0}', 'scale': '{scale:.96,opacity:0}'}
    lines.append(f"tl.fromTo('{selector} .media',{starts[design['entry_motion']]},{{x:0,y:0,scale:1,opacity:1,duration:{entrance},ease:'power2.out'}},{cursor});")
    lines.append(f"tl.fromTo('{selector} .title',{{opacity:0}},{{opacity:1,duration:{min(.45, entrance)},ease:'sine.out'}},{cursor+.08});")


def compile_project(scenes, project, settings, runtime):
    if not scenes:
        raise ValueError('No scenes')
    if (settings.width, settings.height) != (1920, 1080):
        raise ValueError('Director-authored scenes require 1920x1080')
    assets = project / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(runtime / 'node_modules/gsap/dist/gsap.min.js', assets / 'gsap.min.js')
    sections, records = [], []
    lines = ["window.__timelines={};const tl=gsap.timeline({paused:true});"]
    cursor, seen = 0.0, set()
    for index, scene in enumerate(scenes, 1):
        genre = scene.layout.get('genre_id')
        if genre not in GENRES:
            raise ValueError('Missing or unsupported genre')
        design = _design(scene.layout)
        if not re.fullmatch(r'[A-Za-z0-9_-]+', scene.id) or scene.id in seen:
            raise ValueError('Invalid scene ID')
        seen.add(scene.id)
        duration = float(scene.duration_seconds)
        if not math.isfinite(duration) or duration < .5:
            raise ValueError('Invalid duration')

        provenance = scene.layout.get('asset_provenance') or scene.layout.get('provenance', {})
        source = str(provenance.get('source_label', '')).strip()
        origin = provenance.get('origin') or scene.layout.get('asset_origin')
        if provenance.get('archive_verified') is True and source:
            credit = source
        elif origin in ('generated', 'mock'):
            credit = 'AI 생성 재현 삽화'
        elif provenance.get('kind') == 'illustration':
            credit = '재현 삽화' + (' · ' + source if source else '')
        else:
            credit = '자료 출처 확인 필요'
        credit_html = f'<div class="credit">{html.escape(credit)}</div>' if genre in ('history', 'documentary') else ''

        labels = scene.layout.get('visual_labels', [])
        if not isinstance(labels, list) or len(labels) > 8:
            raise ValueError('Invalid visual labels')
        labels_html = []
        for label in labels:
            if not isinstance(label, dict):
                raise ValueError('Invalid visual label')
            x, y, text = label.get('x'), label.get('y'), label.get('text')
            if any(type(n) not in (int, float) or not math.isfinite(n) for n in (x, y)) or not .15 <= x <= .85 or not .05 <= y <= .85:
                raise ValueError('Visual label outside safe media area')
            if not isinstance(text, str) or not 1 <= len(text) <= 60:
                raise ValueError('Invalid visual label text')
            labels_html.append(f'<div class="visual-label" style="left:{x*100}%;top:{y*100}%">{html.escape(text)}</div>')

        suffix = Path(scene.image_path).suffix.lower()
        if suffix not in ('.png', '.jpg', '.jpeg', '.webp', '.svg'):
            raise ValueError('Unsupported image type')
        filename = f'{scene.id}{suffix}'
        shutil.copy2(scene.image_path, assets / filename)
        variables = ';'.join([
            f"--background:{design['background']}", f"--foreground:{design['foreground']}", f"--accent:{design['accent']}",
            f"--caption-background:{design['caption_background']}", f"--caption-foreground:{design['caption_foreground']}",
            f"--image-fit:{design['image_fit']}", f"--title-size:{design['title_size']}px", f"--caption-size:{design['caption_size']}px",
            f"--title-weight:{design['title_weight']}", '--border-width:6px', '--matte:#FFFFFF', '--media-padding:18px',
        ])
        sections.append(
            f'<section class="scene" id="s{index}" style="{variables}"><div class="region media {design["media_treatment"]}" style="{_box_style(design["media_box"])}">'
            f'<img src="assets/{filename}" alt="">{"".join(labels_html)}</div><h2 class="region title" style="{_box_style(design["title_box"])}">'
            f'{html.escape(scene.viewer_takeaway)}</h2>{credit_html}<div class="region caption" style="{_box_style(design["caption_box"])}">{html.escape(scene.narration)}</div></section>'
        )
        selector = f'#s{index}'
        if index > 1:
            lines.append(f"tl.set('#s{index-1}',{{opacity:0}},{cursor});")
        lines.append(f"tl.set('{selector}',{{opacity:1}},{cursor});")
        _entry(lines, selector, design, cursor, duration)
        design_hash = hashlib.sha256(json.dumps(design, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        records.append({'scene_id': scene.id, 'genre_id': genre, 'design_contract_version': DESIGN_VERSION,
                        'design_contract_sha256': design_hash, 'design_rationale': design['rationale'],
                        'start': cursor, 'end': cursor + duration, 'narration': scene.narration,
                        'source_status': credit if credit_html else None})
        cursor += duration
    if cursor > 60.05:
        raise ValueError('Episode exceeds 60 seconds')
    payload = json.dumps({'version': 'genre-slide-0.4.0', 'records': records,
                          'resolution': [settings.width, settings.height], 'fps': settings.fps},
                         ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    composition_id = 'director-scene-' + hashlib.sha256(payload).hexdigest()[:16]
    lines.append(f"tl.set({{}},{{}}, {cursor});")
    meta = {'name': composition_id, 'duration': cursor, 'resolution': {'width': settings.width, 'height': settings.height}, 'fps': settings.fps}
    master = f'<div data-composition-id="{composition_id}" data-width="{settings.width}" data-height="{settings.height}" data-start="0" data-duration="{cursor}" data-fps="{settings.fps}">'
    fit_script = (Path(__file__).parent / 'text_fit.js').read_text(encoding='utf-8').replace('__COMPOSITION_ID__', composition_id)
    document = '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Director Scene</title><script src="assets/gsap.min.js"></script><style>' + CSS + '</style></head><body>' + master + ''.join(sections) + '</div><script>' + ''.join(lines) + fit_script + '</script></body></html>'
    (project / 'index.html').write_text(document, encoding='utf-8')
    (project / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')
    (project / 'genre-scenes.json').write_text(json.dumps({'composition_id': composition_id, 'compiler_version': '0.4.0', 'scenes': records}, ensure_ascii=False, indent=2), encoding='utf-8')
