# QR Label Generator

Generates printable sheets of inventory labels, each with a unique ID and a matching QR code. It outputs SVG for pre-cut label sheets (Avery, SheetLabels.com) and SVG + PNG for Cricut Print Then Cut on blank sticker paper.

The labels don't belong to any particular system. Print a batch of random IDs, stick one on something, then scan it into your inventory system to link it to that item. The system never has to issue codes, so any app that stores a scanned string works.

## Setup

Requires Python 3.8+.

    pip install -r requirements.txt

Cricut PNG export also needs the Cairo library: `brew install cairo` on macOS.

## Usage

    python app.py --list-templates
    python app.py -t SL855 --title "Waffle Track" --title-color "#1a2c6e" --subtitle "Inventory Tag"

Output is a timestamped SVG in the current directory, or wherever `-o` points (a file name or a directory). Print it at 100% / actual size.

Common options (see `python app.py --help` for all of them):

| Option | Purpose |
|---|---|
| `-t SL855` | Label sheet template |
| `--title`, `--subtitle`, `--title-color`, `--subtitle-color` | Label text and colors (`--subtitle ''` drops the line) |
| `--prefix WS-` | Text before every ID |
| `--sequential --start 1 --digits 8` | Numbered IDs instead of random: `ASN00000001`, ... (see below) |
| `--ids-file ids.txt` | Print specific IDs, one per line, e.g. to reprint a damaged label |
| `--qr-data 'https://example.com/{id}'` | Encode something other than the bare ID; the plain ID is still printed |
| `--count 100` / `--pages 2` | How many labels; extra pages are numbered `-p1`, `-p2`, ... |
| `--skip 12` | Leave the first 12 labels blank, to finish a partly used sheet |
| `--outlines` | Draw label edges; print on plain paper and hold it against a label sheet to check alignment |

### Examples

A sheet of workshop inventory labels:

    python app.py -t Avery6570 --title Workshop --subtitle "Inventory Tag"

Paperless-ngx archive serial numbers, which need to be numbered. Set `--start` to one past your last label so you don't print duplicates:

    python app.py -t SL588 --title Paperless-ngx --subtitle "Archive Serial Number" --sequential --prefix ASN --start 153

## About the IDs

Random IDs are 12 characters from shortuuid's alphabet: digits, upper and lower case, minus lookalikes such as 0/O and 1/l/I. That's the same format as the earlier scripts, so old and new labels mix freely. There are about 1.2 × 10²¹ possible IDs. Even after printing a million labels, the chance that any two match is under one in a billion, and IDs within a single run are guaranteed different.

The IDs are case-sensitive, so scan them instead of typing them in.

Sequential IDs restart at `--start` every run. Only use them when you need numbers, and keep track of where the last batch ended.

## Templates

| Name | Label | Per sheet | Notes |
|---|---|---|---|
| SL588 | 1.75" x 0.5" | 76 | SheetLabels.com |
| SL855 | 1.375" x 0.5625" | 80 | SheetLabels.com |
| Avery6570 | 1.75" x 1.25" | 32 | QR above text, turned sideways |
| MR183 | 1.46" x 1.02" | 30 | Cable labels on landscape paper, ID printed twice |

The measurements come from the earlier scripts, which were tuned on real prints, not from the manufacturers' spec sheets. Do an `--outlines` test print before using a new box of labels.

**One-off sizes:** override any part of a template from the command line. Lengths take `in`, `mm` or points (no unit):

    python app.py -t SL855 --label-size 2in 1in --grid 4 10 --origin 0.25in 0.5in --gap 0.125in 0

**Permanent templates:** add a `LabelTemplate` to `TEMPLATES` in `qrlabels/templates.py`. You need the label size, column and row count, the top-left corner of the first label (`origin`), and the gaps between labels. All values are in points (72 per inch). Avery and SheetLabels.com list these on each product's template page.

## Cricut Print Then Cut

`--cricut` takes the chosen template's label size, lays as many labels as fit into the Print Then Cut area (6.75" x 9.25" on Letter) with a gap between them, and writes a PNG with a transparent background. Design Space cuts around each opaque white label shape and adds its own registration marks when it prints.

    python app.py -t SL855 --title "Waffle Track" --cricut

The script prints the exact size to use. Then, in Design Space (menu names vary a little between versions):

1. **Upload** → **Upload Image** → choose the `.png`.
2. Pick **Complex** if asked, and click **Continue** on the background-removal step without erasing anything. The background is already transparent.
3. Choose **Print Then Cut image**, then upload and insert it.
4. With the image selected, set the **W** and **H** to the size the script printed. Design Space doesn't always size uploads correctly.
5. **Make It**, then send it to your printer. If you use the system print dialog, print at 100% with no scaling.
6. Load the printed sheet on the mat, top-left aligned, and cut.

`--cricut-gap` changes the spacing between labels (default 0.125"). Labels need some gap, or they merge into one shape and Design Space cuts only the outer edge. `--corner-radius` rounds the corners.

## Using it from other code

The `qrlabels` package doesn't depend on the CLI:

```python
from qrlabels import LabelStyle, get_template, print_then_cut, random_ids, render_pages, write_svg, write_png

template = get_template("SL855")
style = LabelStyle(title="Workshop", subtitle="Inventory Tag")
for n, page in enumerate(render_pages(template, random_ids(80), style), 1):
    write_svg(page, f"labels-{n}.svg")

cricut = print_then_cut(template)
for n, page in enumerate(render_pages(cricut, random_ids(52), style, background=True), 1):
    write_png(page, f"cricut-{n}.png")
```

`render_sheet` / `render_pages` return `xml.etree` elements, and `svg_bytes()` turns one into bytes, so you can serve labels from a web app without writing files.
