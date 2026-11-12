"""Render QR label sheets to SVG, and to PNG for Cricut Print Then Cut."""
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import segno

from .templates import PT_PER_INCH, LabelTemplate, Slot

# Approximate Helvetica/Arial glyph widths as a fraction of font size, slightly
# generous. Only used to shrink lines that would run off the label.
_CHAR_WIDTH = {
    "normal": {"wide": 0.89, "narrow": 0.30, "upper": 0.70, "lower": 0.54,
               "digit": 0.56, "space": 0.28, "other": 0.58},
    "bold": {"wide": 0.92, "narrow": 0.34, "upper": 0.74, "lower": 0.60,
             "digit": 0.56, "space": 0.28, "other": 0.62},
}
_WIDE = set("mwMW@")
_NARROW = set("fijlrtI.,:;!|'")
_LEADING = 1.25


def _char_kind(c: str) -> str:
    if c in _WIDE:
        return "wide"
    if c in _NARROW:
        return "narrow"
    if c.isupper():
        return "upper"
    if c.islower():
        return "lower"
    if c.isdigit():
        return "digit"
    return "space" if c == " " else "other"


def _text_width(text: str, weight: str) -> float:
    """Estimated width of text at font size 1, with 6% to spare."""
    return 1.06 * sum(_CHAR_WIDTH[weight][_char_kind(c)] for c in text)


@dataclass(frozen=True)
class LabelStyle:
    """Text, colors and QR settings shared by every label on a sheet."""
    title: str = "Inventory"
    subtitle: str = "Asset Tag"
    title_color: str = "#336699"
    subtitle_color: str = "#000000"
    id_color: str = "#000000"
    font_family: str = "Helvetica"
    qr_data: str = "{id}"  # what the QR code encodes; {id} becomes the label ID
    error_correction: str = "m"  # l, m, q or h
    quiet_zone: int = 2  # blank modules around the code
    padding: float = 2.0  # points between the label edge and its content


def _num(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _rotation(degrees: int, w: float, h: float) -> Tuple[str, float, float]:
    """Transform that turns content drawn in the returned box to fill a w x h box."""
    turn = degrees % 360
    if turn == 0:
        return "", w, h
    if turn == 90:
        return f"translate({_num(w)} 0) rotate(90)", h, w
    if turn == 180:
        return f"translate({_num(w)} {_num(h)}) rotate(180)", w, h
    if turn == 270:
        return f"translate(0 {_num(h)}) rotate(270)", h, w
    raise ValueError(f"rotation must be a multiple of 90, got {degrees}")


def _qr(parent: ET.Element, data: str, x: float, y: float, size: float, style: LabelStyle):
    code = segno.make_qr(data, error=style.error_correction, boost_error=False)
    scale = size / (len(code.matrix) + 2 * style.quiet_zone)
    offset = style.quiet_zone * scale
    # One path of horizontal runs, drawn in module units and scaled into place.
    runs = []
    for row_index, row in enumerate(code.matrix):
        col = 0
        while col < len(row):
            if not row[col]:
                col += 1
                continue
            start = col
            while col < len(row) and row[col]:
                col += 1
            runs.append(f"M{start} {row_index}h{col - start}v1h-{col - start}z")
    ET.SubElement(parent, "path", {
        "d": "".join(runs),
        "fill": "#000000",
        "transform": f"translate({_num(x + offset)} {_num(y + offset)}) scale({scale:.6f})",
    })


def _text(parent: ET.Element, lines, box, anchor: str, font_family: str):
    """Stack lines vertically centered in box, shrinking any that would overflow it."""
    x, y, w, h = box
    lines = [line for line in lines if line[0]]
    if not lines or w <= 0 or h <= 0:
        return
    base = h / (_LEADING * len(lines))
    sizes = [min(base, w / _text_width(text, weight)) for text, weight, _ in lines]
    line_bottom = y + (h - _LEADING * sum(sizes)) / 2
    text_x = x + w / 2 if anchor == "middle" else x
    for (text, weight, color), size in zip(lines, sizes):
        line_bottom += _LEADING * size
        attrs = {
            "x": _num(text_x),
            "y": _num(line_bottom - 0.27 * size),  # baseline that centers caps in the line
            "font-family": font_family,
            "font-size": _num(size),
            "fill": color,
        }
        if weight == "bold":
            attrs["font-weight"] = "bold"
        if anchor == "middle":
            attrs["text-anchor"] = "middle"
        ET.SubElement(parent, "text", attrs).text = text


def _content(parent: ET.Element, w: float, h: float, label_id: str, style: LabelStyle, layout: str):
    p = style.padding
    data = style.qr_data.format(id=label_id)
    lines = [
        (style.title, "bold", style.title_color),
        (style.subtitle, "normal", style.subtitle_color),
        (label_id, "normal", style.id_color),
    ]
    if layout == "stacked":
        size = min(w - 2 * p, (h - 2 * p) * 0.68)
        _qr(parent, data, (w - size) / 2, p, size, style)
        _text(parent, lines, (p, p + size, w - 2 * p, h - 2 * p - size), "middle", style.font_family)
    elif layout == "side":
        size = min(h - 2 * p, (w - 2 * p) * 0.6)
        _qr(parent, data, p, (h - size) / 2, size, style)
        _text(parent, lines, (p + size, p, w - 2 * p - size, h - 2 * p), "start", style.font_family)
    else:
        raise ValueError(f"layout must be 'side' or 'stacked', got {layout!r}")


def _label(parent: ET.Element, template: LabelTemplate, slot: Slot, label_id: str,
           style: LabelStyle, background: bool, outline: bool):
    w, h = template.label_size
    group = ET.SubElement(parent, "g", {"transform": f"translate({_num(slot.x)} {_num(slot.y)})"})
    turn, _, _ = _rotation(slot.rotation, w, h)
    if turn:
        group = ET.SubElement(group, "g", {"transform": turn})
    if background or outline:
        rect = {"width": _num(w), "height": _num(h), "fill": "#ffffff" if background else "none"}
        if template.corner_radius:
            rect["rx"] = rect["ry"] = _num(template.corner_radius)
        if outline:
            rect.update({"stroke": "#999999", "stroke-width": "0.25"})
        ET.SubElement(group, "rect", rect)
    strip = h / template.copies
    for copy in range(template.copies):
        turn, content_w, content_h = _rotation(template.rotation, w, strip)
        transform = f"translate(0 {_num(copy * strip)}) {turn}".strip()
        content = ET.SubElement(group, "g", {"transform": transform})
        _content(content, content_w, content_h, label_id, style, template.layout)


def render_sheet(template: LabelTemplate, label_ids: Sequence[str], style: LabelStyle = LabelStyle(),
                 *, skip: int = 0, background: bool = False, outlines: bool = False) -> ET.Element:
    """Draw one page as an <svg> element.

    skip leaves the first slots empty, for reusing a partly used sheet.
    background fills each label white, which is what Cricut cuts around.
    outlines draws label edges, handy for test prints on plain paper.
    """
    slots = template.slots()[skip:]
    if len(label_ids) > len(slots):
        raise ValueError(f"{len(label_ids)} labels won't fit in {len(slots)} free slots on {template.name}")
    page_w, page_h = template.page_size
    svg = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "version": "1.1",
        "width": f"{_num(page_w / PT_PER_INCH)}in",
        "height": f"{_num(page_h / PT_PER_INCH)}in",
        "viewBox": f"0 0 {_num(page_w)} {_num(page_h)}",
    })
    for slot, label_id in zip(slots, label_ids):
        _label(svg, template, slot, label_id, style, background, outlines)
    return svg


def render_pages(template: LabelTemplate, label_ids: Sequence[str], style: LabelStyle = LabelStyle(),
                 *, skip: int = 0, **options) -> List[ET.Element]:
    """Spread label_ids over as many pages as needed. skip applies to the first page only."""
    per_page = len(template.slots())
    if not 0 <= skip < per_page:
        raise ValueError(f"skip must be between 0 and {per_page - 1}")
    pages = []
    remaining = list(label_ids)
    while remaining or not pages:
        offset = 0 if pages else skip
        take = per_page - offset
        pages.append(render_sheet(template, remaining[:take], style, skip=offset, **options))
        remaining = remaining[take:]
    return pages


def svg_bytes(svg: ET.Element) -> bytes:
    return ET.tostring(svg, encoding="utf-8", xml_declaration=True)


def write_svg(svg: ET.Element, path) -> None:
    with open(path, "wb") as f:
        f.write(svg_bytes(svg))


def write_png(svg: ET.Element, path, dpi: int = 300) -> None:
    """Rasterize with a transparent background, as Print Then Cut expects."""
    try:
        import cairosvg
    except (ImportError, OSError) as error:
        raise RuntimeError("PNG export needs cairosvg (pip install cairosvg) "
                           "and the Cairo library (brew install cairo)") from error
    cairosvg.svg2png(bytestring=svg_bytes(svg), write_to=str(path), dpi=dpi)
