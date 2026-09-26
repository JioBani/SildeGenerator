"""Compare two snapshots without implying a cause or inventing intermediate data."""
import html
from .graphic_type import format_measure


def markup(diagram,index,duration,cursor,design):
    pair=diagram.snapshot_pair
    if pair is None or design is None:
        raise ValueError('snapshot_pair_and_design_required')
    before,after=pair.before,pair.after
    if duration*(after.show_at-before.show_at)<1.5 or duration*(1-after.show_at)-.25<max(1.5,len(after.time_label)/8):
        raise ValueError('snapshot_pair_insufficient_reading_hold')
    p=design.palette
    def text(value,x,y,size=24,anchor='middle'):
        return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{p.text}" font-size="{size}">{html.escape(value)}</text>'
    # Reserve the bottom region for up to two caption lines. Entity, metric and
    # measured value have separate fixed tracks even at maximum label lengths.
    parts=[text(pair.entity,500,110,26),text(f'{pair.metric} ({pair.unit})',500,150,22)]
    layout=getattr(design,'snapshot_layout','columns')
    # Equal axes and retained before state make a decrease as visible as an increase.
    for j,state in enumerate((before,after)):
        identifier=f'snapshot-{index}-{j}'
        if layout in {'rows','dot_tracks'}:
            y=250+j*140
            start,end=220,780
            position=start+(end-start)*state.value/pair.scale_max
            parts.append(f'<path d="M{start} {y} H{end} M{start} {y-9} V{y+9} M{end} {y-9} V{y+9}" stroke="{p.line}" stroke-width="{design.line_width}"/>')
            parts.append(text('0',start,y+40,18))
            parts.append(text(f'{pair.scale_max:g}',end,y+40,18))
            parts.append(text(state.time_label,start,y-48,24,'start'))
            if layout=='rows':
                mark=f'<rect x="{start}" y="{y-14}" width="{position-start}" height="28" fill="{pair.color}"/>'
            else:
                mark=f'<circle cx="{position}" cy="{y}" r="12" fill="{pair.color}"/>'
            parts.append(f'<g id="{identifier}" opacity="0">{mark}{text(format_measure(state.value,pair.unit),end,y-48,28,"end")}</g>')
            continue
        x=270+j*380
        parts.append(f'<path d="M{x-100} 420 H{x+100} M{x-100} 220 H{x+100}" stroke="{p.line}" stroke-width="{design.line_width}"/>')
        parts.append(text('0',x-115,405,18,'end'))
        parts.append(text(f'{pair.scale_max:g}',x-115,225,14,'end'))
        parts.append(text(state.time_label,x,450,24))
        height=200*state.value/pair.scale_max
        parts.append(f'<g id="{identifier}" opacity="0"><rect x="{x-65}" y="{420-height}" width="130" height="{height}" fill="{pair.color}"/>{text(format_measure(state.value,pair.unit),x,195,28)}</g>')
    actions=[f"tl.to('#snapshot-{index}-{j}',{{opacity:1,duration:.25,ease:'power2.out'}},{cursor+duration*s.show_at});" for j,s in enumerate((before,after))]
    title=html.escape(diagram.title)
    return f'<h2>{title}</h2><svg viewBox="0 0 1000 600" aria-label="{title}">{"".join(parts)}</svg>',actions
