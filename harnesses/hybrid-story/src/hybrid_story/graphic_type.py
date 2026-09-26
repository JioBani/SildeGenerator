"""Bounded type roles for editable 1000x600 diagrams."""
import html
import textwrap
import unicodedata


TYPE_ROLES = {
    "axis": (19, 500),
    "label": (23, 700),
    "value": (28, 800),
    "annotation": (21, 500),
    "step": (26, 700),
}


def format_measure(value, unit):
    """Keep a numeric value and Korean/counting unit in one visual token."""
    number = f"{value:g}"
    if not unit:
        return number
    separator = " " if all(unicodedata.category(char).startswith("L") and ord(char) < 128 for char in unit) else ""
    return f"{number}{separator}{unit}"


def lines_for(value, *, width=None, max_lines=2):
    if not value or not value.strip():
        raise ValueError("graphic_text_empty")
    if width is None:
        return [value]
    lines = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)
    if len(lines) > max_lines or any(len(line) > width for line in lines):
        raise ValueError("graphic_text_exceeds_role_bounds")
    return lines


def svg_text(value, x, y, *, role, anchor="start", width=None, max_lines=2, design=None):
    if role not in TYPE_ROLES:
        raise ValueError("unknown_graphic_type_role")
    size, weight = TYPE_ROLES[role]
    if design is not None:
        size = round(size * design.typography.title_px / 34)
        treatment = getattr(design, "type_treatment", None)
        if treatment == "documentary":
            weight = 600 if role in {"label", "value", "step"} else 400
        elif treatment == "editorial" and role == "value":
            size = round(size * 1.13)
            weight = 900
        elif treatment == "explainer" and role == "annotation":
            size = round(size * 1.08)
            weight = 600
    color = (design.palette.secondary_text if role in {"axis", "annotation"}
             else design.palette.text) if design else "#172923"
    lines = lines_for(value, width=width, max_lines=max_lines)
    spans = "".join(f'<tspan x="{x}" dy="{0 if index == 0 else size + 5}">{html.escape(line)}</tspan>'
                    for index, line in enumerate(lines))
    font = "Noto Serif CJK KR" if getattr(design, "type_treatment", None) == "documentary" and role == "value" else "Noto Sans CJK KR"
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" font-family="{font}" '
            f'font-size="{size}" font-weight="{weight}" letter-spacing="0" '
            f'data-type-role="{role}">{spans}</text>')


def validate_semantic_labels(diagram):
    """Reject unreadable labels before expensive image and voice work."""
    if diagram.grammar == "quantitative_comparison":
        for node in diagram.nodes:
            lines_for(node.label, width=8, max_lines=2)
            lines_for(format_measure(node.quantity, node.unit), width=12, max_lines=1)
    elif diagram.grammar == "cumulative_change":
        total = 0
        for node in diagram.nodes:
            lines_for(node.label, width=8, max_lines=2)
            total += node.quantity
            lines_for(f"+{format_measure(node.quantity, node.unit)}", width=12, max_lines=1)
            lines_for(f"누적 {format_measure(total, node.unit)}", width=14, max_lines=1)
    elif diagram.grammar == "step_sequence":
        for node in diagram.nodes:
            lines_for(node.label, width=8, max_lines=2)
            lines_for(node.after, width=9, max_lines=2)
