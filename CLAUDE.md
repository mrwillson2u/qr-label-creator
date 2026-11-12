# CLAUDE.md

Context for working on this repo. Usage is in README.md.

## Purpose

Prints sheets of QR labels for a workshop inventory system. The codes don't belong to any system: print a batch of random IDs, stick one on an item, then scan it into the inventory system to link it. The inventory system deliberately never issues codes, and it warns when a scanned code is already in use. All that matters is that IDs never repeat.

- Random IDs are the default: 12 characters from shortuuid's alphabet, the same format as older printed labels (the old code used `shortuuid.uuid()[:12]`). Don't make sequential the default. Sequential numbering restarts every run and could repeat across runs or machines.
- `--sequential` exists for Paperless-ngx ASN labels, which need numbers. The last ASN sheet printed was around ASN00000153 (March 2025).

## Layout

- `qrlabels/templates.py`: `LabelTemplate` definitions in points (1/72 in), `print_then_cut()` re-grids a label for the Cricut area.
- `qrlabels/render.py`: SVG rendering (QR via segno as a single path), text auto-shrinks with a Helvetica width estimate, PNG via cairosvg.
- `qrlabels/ids.py`: random / sequential / file IDs.
- `app.py`: argparse CLI only; the package is meant to be importable into the inventory system.

## Status / unverified

- Template measurements (SL588, SL855, Avery6570, MR183) were carried over from the original scripts, which were tuned on real prints. They don't come from the manufacturers' spec sheets.
- All templates render, and every QR code decodes correctly (checked with OpenCV).
- Cricut Print Then Cut (`--cricut`) has NOT been tested in Design Space or on the Maker 3 yet. It relies on Design Space cutting around each opaque label in a transparent PNG. The 6.75" x 9.25" area limit came from a third-party source.
- The original dev environment was pyenv `qr-generator-env` on Python 3.8. The code stays compatible with 3.8 (no 3.9+ syntax).
