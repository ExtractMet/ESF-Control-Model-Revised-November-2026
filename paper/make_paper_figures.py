#!/usr/bin/env python3
"""
Regenerate the two manuscript figures that are drawn from a model state
rather than from the validation sweep.

Figure 1  the furnace schematic, rendered from the transient state at the
          end of the base-case campaign, so the bath levels, freeze
          lining, temperatures and compositions on it are the ones the
          model actually computes.
Figure 8  the transient campaign dashboard, which run_validation.py
          writes as figures/F15_dynamic_dashboard.png; it is copied here
          under its manuscript name so that the two cannot drift apart.

The remaining six figures come from run_validation.py directly.

    python paper/make_paper_figures.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

OUT = os.path.join(HERE, "figures")
FIG1 = os.path.join(OUT, "Fig1_furnace_schematic.png")
FIG8 = os.path.join(OUT, "Fig8_dynamic_campaign.png")
DASH = os.path.join(ROOT, "figures", "F15_dynamic_dashboard.png")

FIG1_WIDTH = 1600          # matches the submitted figure


def _svg_to_png(svg: str, path: str, width: int) -> None:
    """Rasterise with cairosvg if present, otherwise with Inkscape."""
    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode("utf-8"),
                         write_to=path, output_width=width)
        return
    except ImportError:
        pass
    tmp = path.replace(".png", ".svg")
    with open(tmp, "w") as f:
        f.write(svg)
    for cmd in (["inkscape", tmp, f"--export-filename={path}",
                 f"--export-width={width}"],
                ["rsvg-convert", "-w", str(width), "-o", path, tmp]):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            os.unlink(tmp)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("no SVG rasteriser found (cairosvg, inkscape "
                       "or rsvg-convert)")


def main() -> int:
    from esf_dt.dynamic_model import run_dynamic
    from esf_dt.schematic import furnace_svg, state_from_dynamic

    os.makedirs(OUT, exist_ok=True)

    # ---- Figure 1 --------------------------------------------------
    # Drawn from the transient state, not the steady-state result: the
    # steady-state solver works per 1000 kg of contained iron, so its
    # masses are per-tonne figures and not furnace inventories.
    d = run_dynamic(duration_min=420.0)
    state = state_from_dynamic(d["trajectory"], idx=-1)
    _svg_to_png(furnace_svg(state), FIG1, FIG1_WIDTH)
    print(f"  wrote {os.path.relpath(FIG1, ROOT)}")
    print(f"     freeboard gas on the figure: "
          f"{d['trajectory']['T_gas_C'][-1]:.0f} degC")

    # ---- Figure 8 --------------------------------------------------
    if not os.path.exists(DASH):
        print(f"  {os.path.relpath(DASH, ROOT)} is missing; "
              f"run run_validation.py first", file=sys.stderr)
        return 1
    shutil.copyfile(DASH, FIG8)
    print(f"  wrote {os.path.relpath(FIG8, ROOT)} "
          f"(copied from the validation dashboard)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
