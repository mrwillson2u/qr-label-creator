"""Label sheet templates.

All measurements are PostScript points (1/72 inch), the same unit the SVG
output uses for its viewBox. Use parse_length() to convert from in/mm.
"""
import re
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple

PT_PER_INCH = 72.0
PT_PER_MM = PT_PER_INCH / 25.4
LETTER = (612.0, 792.0)
LETTER_LANDSCAPE = (792.0, 612.0)

# Largest Print Then Cut image Cricut Design Space allows on Letter paper.
PRINT_THEN_CUT_AREA = (6.75 * PT_PER_INCH, 9.25 * PT_PER_INCH)

_LENGTH = re.compile(r"^\s*(-?\d*\.?\d+)\s*(pt|in|mm|cm)?\s*$")
_UNITS = {None: 1.0, "pt": 1.0, "in": PT_PER_INCH, "mm": PT_PER_MM, "cm": PT_PER_MM * 10}


def parse_length(value: str) -> float:
    """Convert '0.5in', '13mm' or '36' (points) to points."""
    match = _LENGTH.match(str(value))
    if not match:
        raise ValueError(f"not a length: {value!r} (try 36, 36pt, 0.5in or 13mm)")
    return float(match.group(1)) * _UNITS[match.group(2)]


@dataclass(frozen=True)
class Slot:
    """Top-left corner of one label on the page. rotation is 0 or 180."""
    x: float
    y: float
    rotation: int = 0


@dataclass(frozen=True)
class LabelTemplate:
    name: str
    description: str
    label_size: Tuple[float, float]
    columns: int
    rows: int
    origin: Tuple[float, float] = (0.0, 0.0)  # top-left corner of the first label
    gap: Tuple[float, float] = (0.0, 0.0)  # space between columns, between rows
    page_size: Tuple[float, float] = LETTER
    corner_radius: float = 0.0
    layout: str = "side"  # "side": QR left of the text. "stacked": QR above the text.
    rotation: int = 0  # turn the label content within the label, in 90 degree steps
    copies: int = 1  # repeat the content stacked vertically, e.g. both ends of a cable flag
    fill_order: str = "columns"  # "columns": fill down each column first. "rows": across.
    url: Optional[str] = None
    fixed_slots: Optional[Tuple[Slot, ...]] = None  # for sheets that aren't a plain grid

    def slots(self) -> List[Slot]:
        if self.fixed_slots is not None:
            return list(self.fixed_slots)
        w, h = self.label_size
        (ox, oy), (gx, gy) = self.origin, self.gap
        if self.fill_order == "rows":
            cells = [(c, r) for r in range(self.rows) for c in range(self.columns)]
        else:
            cells = [(c, r) for c in range(self.columns) for r in range(self.rows)]
        return [Slot(ox + c * (w + gx), oy + r * (h + gy)) for c, r in cells]


def _mr183_slots() -> Tuple[Slot, ...]:
    # Staggered pairs of columns, alternate labels flipped. Positions carried
    # over from the original qr-generator-MR183.py.
    slots = []
    for i in range(30):
        x = 20.41 + (i % 2) * 133.23 + (i // 10) * 256.5351
        y = 22.5358 + (i % 10) / 2 * 113.3851 - (i % 2) * 17.0075
        slots.append(Slot(x, y, 180 if i % 2 == 0 else 0))
    return tuple(slots)


TEMPLATES: Dict[str, LabelTemplate] = {t.name: t for t in (
    LabelTemplate(
        name="SL588",
        description='SheetLabels.com SL588, 1.75" x 0.5"',
        label_size=(126, 36), columns=4, rows=19,
        origin=(21.6002, 31), gap=(24, 0.375),
        url="https://www.sheetlabels.com/labels/SL588",
    ),
    LabelTemplate(
        name="SL855",
        description='SheetLabels.com SL855, 1.375" x 0.5625"',
        label_size=(99, 40.5), columns=5, rows=16,
        origin=(22.9968, 72.438), gap=(18, 0),
        corner_radius=4.5,
        url="https://www.sheetlabels.com/labels/SL855",
    ),
    LabelTemplate(
        name="Avery6570",
        description='Avery 6570 permanent ID labels, 1.75" x 1.25"',
        label_size=(126, 90), columns=4, rows=8,
        origin=(33.6806, 36), gap=(13.5463, 0),
        layout="stacked", rotation=270,
        url="https://www.avery.com/templates/6570",
    ),
    LabelTemplate(
        name="MR183",
        description="MR183 cable labels, landscape, ID printed twice per label",
        label_size=(104.881, 73.7), columns=6, rows=5,
        page_size=LETTER_LANDSCAPE, copies=2,
        fixed_slots=_mr183_slots(),
    ),
)}


def get_template(name: str) -> LabelTemplate:
    """Look up a template by name, ignoring case."""
    for key, template in TEMPLATES.items():
        if key.lower() == name.lower():
            return template
    raise KeyError(f"unknown template {name!r}; choose from {', '.join(TEMPLATES)}")


def print_then_cut(base: LabelTemplate, gap: float = 9.0, margin: float = 4.5,
                   area: Tuple[float, float] = PRINT_THEN_CUT_AREA) -> LabelTemplate:
    """Lay base's label out on blank sticker paper for Cricut Print Then Cut.

    The page shrinks to just the labels so the exported image is the whole
    cut area. Labels need a gap between them or Design Space sees one shape.
    """
    w, h = base.label_size
    columns = int((area[0] - 2 * margin + gap) // (w + gap))
    rows = int((area[1] - 2 * margin + gap) // (h + gap))
    if columns < 1 or rows < 1:
        raise ValueError(f"a {w:g} x {h:g} pt label doesn't fit the Print Then Cut area")
    page = (2 * margin + columns * w + (columns - 1) * gap,
            2 * margin + rows * h + (rows - 1) * gap)
    return replace(
        base,
        name=f"{base.name}-cricut",
        description=f"{base.description}, Cricut Print Then Cut",
        columns=columns, rows=rows,
        origin=(margin, margin), gap=(gap, gap),
        page_size=page, fixed_slots=None,
    )
