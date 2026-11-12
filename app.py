#!/usr/bin/env python3
"""Command-line front end for the qrlabels package. Run with --help for options."""
import argparse
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from qrlabels import (
    PT_PER_INCH, TEMPLATES, LabelStyle, get_template, parse_length, print_then_cut,
    random_ids, read_ids, render_pages, sequential_ids, write_png, write_svg,
)


def _length(value):
    try:
        return parse_length(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="qr-labels",
        description="Create printable sheets of QR code labels. "
                    "Lengths accept units: 36 (points), 0.5in, 13mm.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-t", "--template", default="SL588", help="label sheet template")
    parser.add_argument("--list-templates", action="store_true", help="show templates and exit")
    parser.add_argument("-o", "--output", help="output file or directory (default: timestamped name here)")

    text = parser.add_argument_group("label text")
    text.add_argument("--title", default=LabelStyle.title)
    text.add_argument("--subtitle", default=LabelStyle.subtitle, help="pass '' to leave out")
    text.add_argument("--title-color", default=LabelStyle.title_color)
    text.add_argument("--subtitle-color", default=LabelStyle.subtitle_color)
    text.add_argument("--id-color", default=LabelStyle.id_color)
    text.add_argument("--font", default=LabelStyle.font_family)

    ids = parser.add_argument_group("label IDs (random unless --sequential or --ids-file)")
    ids.add_argument("--random-length", type=int, default=12, help="characters in each random ID")
    ids.add_argument("--prefix", default="", help="text before each ID, e.g. ASN for Paperless-ngx")
    ids.add_argument("--sequential", action="store_true",
                     help="numbered IDs instead; numbering restarts each run, so set --start")
    ids.add_argument("--start", type=int, default=1, help="first number with --sequential")
    ids.add_argument("--digits", type=int, default=8, help="zero-padded width with --sequential")
    ids.add_argument("--ids-file", help="print these IDs, one per line, e.g. to reprint a damaged label")
    ids.add_argument("--count", type=int, help="number of labels (default: fill --pages sheets)")

    qr = parser.add_argument_group("QR code")
    qr.add_argument("--qr-data", default=LabelStyle.qr_data,
                    help="what the code encodes, e.g. 'https://inventory.local/item/{id}'")
    qr.add_argument("--error", choices="lmqh", default=LabelStyle.error_correction,
                    help="error correction; lower makes larger, easier-to-scan modules")

    sheet = parser.add_argument_group("sheet")
    sheet.add_argument("--pages", type=int, default=1)
    sheet.add_argument("--skip", type=int, default=0, help="leave this many labels empty on a used sheet")
    sheet.add_argument("--outlines", action="store_true", help="draw label edges, for test prints")

    geometry = parser.add_argument_group("custom geometry (overrides the template)")
    geometry.add_argument("--label-size", nargs=2, type=_length, metavar=("W", "H"))
    geometry.add_argument("--grid", nargs=2, type=int, metavar=("COLUMNS", "ROWS"))
    geometry.add_argument("--origin", nargs=2, type=_length, metavar=("X", "Y"),
                          help="top-left corner of the first label")
    geometry.add_argument("--gap", nargs=2, type=_length, metavar=("COLUMN", "ROW"))
    geometry.add_argument("--page-size", nargs=2, type=_length, metavar=("W", "H"))
    geometry.add_argument("--corner-radius", type=_length)
    geometry.add_argument("--layout", choices=("side", "stacked"))
    geometry.add_argument("--rotate", type=int, choices=(0, 90, 180, 270), help="turn content in the label")

    cricut = parser.add_argument_group("Cricut Print Then Cut")
    cricut.add_argument("--cricut", action="store_true",
                        help="lay the template's label out for Print Then Cut and also export a PNG")
    cricut.add_argument("--cricut-gap", type=_length, default="0.125in", help="space between labels")
    cricut.add_argument("--dpi", type=int, default=300, help="PNG resolution")
    return parser


def _apply_overrides(template, args):
    changes = {}
    if args.label_size:
        changes["label_size"] = tuple(args.label_size)
    if args.grid:
        changes["columns"], changes["rows"] = args.grid
    if args.origin:
        changes["origin"] = tuple(args.origin)
    if args.gap:
        changes["gap"] = tuple(args.gap)
    if args.page_size:
        changes["page_size"] = tuple(args.page_size)
    if args.corner_radius is not None:
        changes["corner_radius"] = args.corner_radius
    if args.layout:
        changes["layout"] = args.layout
    if args.rotate is not None:
        changes["rotation"] = args.rotate
    if changes.keys() & {"columns", "origin", "gap"}:
        changes["fixed_slots"] = None
    return replace(template, **changes) if changes else template


def _off_page(template):
    w, h = template.label_size
    page_w, page_h = template.page_size
    return any(s.x < 0 or s.y < 0 or s.x + w > page_w + 0.01 or s.y + h > page_h + 0.01
               for s in template.slots())


def _output_base(output, template_name):
    name = f"labels-{template_name}-{datetime.now():%Y-%m-%d_%H-%M-%S}"
    if not output:
        return Path(name)
    path = Path(output)
    if path.is_dir():
        return path / name
    return path.with_suffix("") if path.suffix.lower() in (".svg", ".png") else path


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_templates:
        for t in TEMPLATES.values():
            w, h = (v / PT_PER_INCH for v in t.label_size)
            print(f"{t.name:<10} {len(t.slots()):>3} per sheet  {w:.3g} x {h:.3g} in  {t.description}")
        return 0

    try:
        template = _apply_overrides(get_template(args.template), args)
        if args.cricut:
            template = print_then_cut(template, gap=args.cricut_gap)
    except (KeyError, ValueError) as error:
        parser.error(str(error).strip("'\""))
    if _off_page(template):
        print("warning: some labels run past the page edge; check the geometry", file=sys.stderr)

    per_page = len(template.slots())
    if args.ids_file:
        label_ids = read_ids(args.ids_file)
    else:
        count = args.count if args.count is not None else per_page * args.pages - args.skip
        if args.sequential:
            label_ids = sequential_ids(count, args.start, args.prefix, args.digits)
        else:
            label_ids = random_ids(count, args.prefix, args.random_length)

    style = LabelStyle(
        title=args.title, subtitle=args.subtitle,
        title_color=args.title_color, subtitle_color=args.subtitle_color, id_color=args.id_color,
        font_family=args.font, qr_data=args.qr_data, error_correction=args.error,
    )
    try:
        pages = render_pages(template, label_ids, style, skip=args.skip,
                             background=args.cricut, outlines=args.outlines)
    except ValueError as error:
        parser.error(str(error))

    base = _output_base(args.output, template.name)
    for number, page in enumerate(pages, 1):
        stem = base if len(pages) == 1 else base.with_name(f"{base.name}-p{number}")
        svg_path = stem.with_name(stem.name + ".svg")
        write_svg(page, svg_path)
        print(svg_path)
        if args.cricut:
            png_path = stem.with_name(stem.name + ".png")
            try:
                write_png(page, png_path, args.dpi)
            except RuntimeError as error:
                print(f"error: {error}", file=sys.stderr)
                return 1
            print(png_path)

    print(f"{len(label_ids)} labels on {len(pages)} page(s), {template.name}, {per_page} per page",
          file=sys.stderr)
    if args.cricut:
        w, h = (v / PT_PER_INCH for v in template.page_size)
        print(f"In Design Space, upload the PNG as a Print Then Cut image and size it to "
              f"{w:.3f} in x {h:.3f} in (W x H) before Make It.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
