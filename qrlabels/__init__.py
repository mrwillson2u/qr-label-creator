"""Printable sheets of QR code labels, for sticker sheets or Cricut Print Then Cut."""
from .ids import random_ids, read_ids, sequential_ids
from .render import LabelStyle, render_pages, render_sheet, svg_bytes, write_png, write_svg
from .templates import (
    PRINT_THEN_CUT_AREA, PT_PER_INCH, TEMPLATES, LabelTemplate, Slot,
    get_template, parse_length, print_then_cut,
)
