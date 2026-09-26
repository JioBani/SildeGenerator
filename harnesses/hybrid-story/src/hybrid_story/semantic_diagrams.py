"""Versioned editable diagrams with distinct quantitative and procedural geometry."""
import html

from .graphic_type import format_measure, svg_text, validate_semantic_labels


def markup(diagram, index, duration, cursor, design=None):
    nodes = diagram.nodes
    validate_semantic_labels(diagram)
    if design is not None and diagram.grammar == "cumulative_change":
        # The .35s bar tween and .25s value reveal must finish before the next
        # increment. A percentage of a long narration is not a time budget.
        if any(duration*(b.change_at-a.change_at) < .6 for a,b in zip(nodes,nodes[1:])):
            raise ValueError("accumulation_voice_events_too_close_for_render")
    final_hold = duration * (1 - max(n.change_at for n in nodes)) - .35
    if final_hold < max(1.2, max(len(n.after) for n in nodes) / 8):
        raise ValueError("semantic_diagram_insufficient_reading_hold")
    parts, actions = [], []
    line = design.palette.line if design else "#c5cfce"
    surface = design.palette.surface if design else "#dce4e2"
    edge_ink = design.palette.line if design else "#536e69"
    stroke_width = design.line_width if design else 5

    def text(value, x, y, role="label", anchor="start", wrap=None):
        return svg_text(value, x, y, role=role, anchor=anchor, width=wrap, design=design)

    def reveal(identifier, at):
        actions.append(f"tl.to('#{identifier}',{{opacity:1,duration:.25}},{cursor+duration*at});")

    if diagram.grammar == "quantitative_comparison":
        maximum = diagram.comparison_scale_max
        layout = getattr(design, "comparison_layout", "rows")
        if layout == "columns":
            for tick in range(5):
                y = 410 - tick * 65
                parts.append(f'<path d="M155 {y} H865" stroke="{line}"/>')
                parts.append(text(f'{maximum*tick/4:g}', 135, y+7, "axis", "end"))
            parts.append(text(nodes[0].unit, 870, 140, "axis"))
            for j, node in enumerate(nodes):
                x = 240 + j * (520 / max(1, len(nodes)-1))
                identifier = f"measure-{index}-{j}"
                height = 260 * node.quantity / maximum
                parts.append(text(node.label, x, 452, anchor="middle", wrap=8))
                parts.append(f'<rect id="{identifier}" x="{x-29}" y="410" width="58" height="0" fill="{node.color}"/>')
                parts.append(f'<g id="value-{identifier}" opacity="0">{text(format_measure(node.quantity,node.unit),x,397-height,"value","middle")}</g>')
                actions.append(f"tl.to('#{identifier}',{{attr:{{y:{410-height},height:{height}}},duration:.35,ease:'power2.out'}},{cursor+duration*node.change_at});")
                reveal(f"value-{identifier}", node.change_at+.35/duration)
        else:
            for tick in range(5):
                x = 245 + tick * 135
                parts.append(f'<path d="M{x} 145 V415" stroke="{line}"/>')
                parts.append(text(f'{maximum*tick/4:g}', x, 445, "axis", "middle"))
            parts.append(text(nodes[0].unit, 830, 445, "axis"))
            for j, node in enumerate(nodes):
                y = 165 + j * (210 / max(1, len(nodes)-1))
                identifier = f"measure-{index}-{j}"
                width = 540 * node.quantity / maximum
                parts.append(text(node.label, 220, y+15, anchor="end",wrap=8))
                if layout == "dot_tracks":
                    value_anchor, value_x, value_y = "middle", 245+width, y-27
                else:
                    value_anchor = "end" if width > 405 else "start"
                    value_x = 235+width if width > 405 else 255+width
                    value_y = y-9 if width > 405 else y+25
                parts.append(f'<g id="value-{identifier}" opacity="0">{text(format_measure(node.quantity,node.unit),value_x,value_y,"value",value_anchor)}</g>')
                if layout == "dot_tracks":
                    parts.append(f'<path d="M245 {y+18} H785" stroke="{line}" stroke-width="4"/>')
                    parts.append(f'<circle id="{identifier}" cx="245" cy="{y+18}" r="12" fill="{node.color}" opacity="0"/>')
                    actions.append(f"tl.to('#{identifier}',{{attr:{{cx:{245+width}}},opacity:1,duration:.35,ease:'power2.out'}},{cursor+duration*node.change_at});")
                else:
                    parts.append(f'<rect id="{identifier}" x="245" y="{y}" width="0" height="36" fill="{node.color}"/>')
                    actions.append(f"tl.to('#{identifier}',{{attr:{{width:{width}}},duration:.35,ease:'power2.out'}},{cursor+duration*node.change_at});")
                reveal(f"value-{identifier}", node.change_at+.35/duration)
    elif diagram.grammar == "cumulative_change":
        total = 0
        parts.append(f'<rect x="100" y="200" width="800" height="92" fill="{surface}"/>')
        parts.append(text('0', 100, 315, "axis"))
        parts.append(text(format_measure(diagram.comparison_scale_max,nodes[0].unit), 900, 315, "axis", "end"))
        for j, node in enumerate(nodes):
            x = 100 + 800*total/diagram.comparison_scale_max
            width = 800*node.quantity/diagram.comparison_scale_max
            total += node.quantity
            identifier = f"increment-{index}-{j}"
            parts.append(f'<rect id="{identifier}" x="{x}" y="200" width="0" height="92" fill="{node.color}"/>')
            lx = 100 + j * 800 / len(nodes)
            parts.append(f'<g id="value-{identifier}" opacity="0">{text(node.label,lx,365,wrap=8)}{text("+"+format_measure(node.quantity,node.unit),lx,410,"value")}{text("누적 "+format_measure(total,node.unit),lx,445,"annotation")}</g>')
            actions.append(f"tl.to('#{identifier}',{{attr:{{width:{width}}},duration:.35,ease:'power2.out'}},{cursor+duration*node.change_at});")
            reveal(f"value-{identifier}", node.change_at+.35/duration)
    else:
        for j, node in enumerate(nodes):
            x = 140 + j * 720 / (len(nodes)-1)
            identifier = f"step-{index}-{j}"
            if j:
                previous = 140 + (j-1) * 720 / (len(nodes)-1)
                edge = diagram.edges[j-1]
                edge_id = f"sequence-{index}-{j}"
                parts.append(f'<path id="{edge_id}" d="M{previous+38} 245 H{x-38}" stroke="{edge_ink}" stroke-width="{stroke_width}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>')
                actions.append(f"tl.to('#{edge_id}',{{strokeDashoffset:0,duration:{duration*(edge.end_at-edge.start_at)},ease:'none'}},{cursor+duration*edge.start_at});")
            parts.append(f'<circle cx="{x}" cy="245" r="34" fill="{surface}"/>{text(str(j+1),x,255,"step","middle")}')
            parts.append(text(node.label,x,310,"label","middle",8))
            parts.append(f'<g id="{identifier}" opacity="0"><circle cx="{x}" cy="245" r="40" stroke="{node.color}" stroke-width="6" fill="none"/>{text(node.after,x,385,"annotation","middle",9)}</g>')
            reveal(identifier,node.change_at)
    title = html.escape(diagram.title)
    return f'<h2>{title}</h2><svg viewBox="0 0 1000 600" aria-label="{title}">{"".join(parts)}</svg>', actions
