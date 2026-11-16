#!/usr/bin/env python3
"""Generate the model development and solution flowchart (Figure 2)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

INK, GREY, MOLT, COOL, EMB = "#141A22", "#5C6B7A", "#C25E10", "#2A7F72", "#B03030"
LIGHT, PAPER = "#EDF1F4", "#FFFFFF"

fig, ax = plt.subplots(figsize=(13.2, 15.0))
ax.set_xlim(0, 100); ax.set_ylim(0, 122); ax.axis("off")


def box(x, y, w, h, text, fc=LIGHT, ec=INK, fs=9.2, bold=False, tc=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                fc=fc, ec=ec, lw=1.1, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=tc, zorder=3, fontweight="bold" if bold else "normal",
            linespacing=1.45)


def diamond(x, y, w, h, text, fc="#FDF3E3", ec=MOLT, fs=8.8):
    ax.add_patch(Polygon([[x + w / 2, y], [x + w, y + h / 2],
                          [x + w / 2, y + h], [x, y + h / 2]],
                         closed=True, fc=fc, ec=ec, lw=1.2, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            color=INK, zorder=3, linespacing=1.4)


def arrow(x1, y1, x2, y2, c=INK, style="-|>", ls="-", lw=1.2, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=13, lw=lw, color=c,
                                 linestyle=ls, zorder=1,
                                 connectionstyle=f"arc3,rad={rad}"))


def label(x, y, t, c=GREY, fs=8.2, ha="center", style="italic"):
    ax.text(x, y, t, ha=ha, va="center", fontsize=fs, color=c, style=style)


def band(y, t, c):
    ax.add_patch(FancyBboxPatch((1.5, y), 97, 3.0,
                                boxstyle="round,pad=0.2,rounding_size=0.8",
                                fc=c, ec="none", zorder=0))
    ax.text(3.5, y + 1.5, t, ha="left", va="center", fontsize=10.2,
            color=PAPER, fontweight="bold")


# ---------------------------------------------------------------- stage A
band(113.5, "A.  SPECIFICATION AND PHYSICAL BASIS", INK)
box(3, 105.5, 28, 6.2, "Define scope and duty\n35 m x 11 m OSBF, 116 MW,\nsix electrodes")
box(36, 105.5, 28, 6.2, "Select physical sub-models\nthermochemistry, transport,\nkinetics, lining, electrical")
box(69, 105.5, 28, 6.2, "Assemble property and\nthermochemical libraries\n[15, 23-29]")
arrow(31, 108.6, 36, 108.6); arrow(64, 108.6, 69, 108.6)

# ---------------------------------------------------------------- stage B
band(100.5, "B.  STEADY-STATE SOLVER", MOLT)
box(3, 92.5, 30, 6.0, "Basis: 1000 kg contained Fe\nSpeciate DRI, scrap,\ncarburiser, flux")
box(3, 84.5, 30, 6.0, "Initialise slag composition,\nhot metal mass, carbon\ndemand, silicon")
arrow(18, 92.5, 18, 90.5)

box(37, 80.0, 30, 18.5,
    "ITERATION LOOP\n\n1  Gangue and ash to slag\n2  Flux demand: exact 2x2\n    system, Eqs. (24)-(26)\n"
    "3  Slag/metal equilibria\n    Si, Mn, P, S, Ti, Eqs. (6)-(10)\n"
    "4  Apply departure-from-\n    equilibrium limits, Eq. (11)\n"
    "5  Carbon demand and yield\n6  Update hot metal mass",
    fc="#FFF6EC", ec=MOLT, fs=8.6)
arrow(33, 87.5, 37, 87.5)

diamond(71, 84.8, 26, 13.4, "Residual of Eq. (30)\nbelow 1e-6 ?")
arrow(67, 91.5, 71, 91.5)
# "no" branch: down and back into the foot of the loop box
arrow(84, 84.8, 84, 77.5, c=MOLT, style="-")
arrow(84, 77.5, 52, 77.5, c=MOLT, style="-")
arrow(52, 77.5, 52, 80.0, c=MOLT)
label(68, 78.6, "no: damp and repeat", c=MOLT)

box(37, 68.0, 30, 6.5, "Heat balance, Eqs. (1)-(4)\nTwo SEC tiers, Eq. (28)\nClosure check, Eq. (27)")
# "yes" branch: out to the right margin, down, into the heat balance
arrow(97, 91.5, 99.0, 91.5, c=COOL, style="-")
arrow(99.0, 91.5, 99.0, 71.25, c=COOL, style="-")
arrow(99.0, 71.25, 67, 71.25, c=COOL)
label(93.5, 74.5, "yes", c=COOL)

box(3, 68.0, 30, 6.5, "Lining network, Eqs. (12)-(13)\nFreeze lining, Eqs. (14)-(16)")
box(3, 59.5, 30, 6.5, "Electrical operating point\nEqs. (17)-(21), power setpoint")
box(37, 59.5, 30, 6.5, "Slag valorisation index\nEq. (29)")
arrow(37, 71.25, 33, 71.25); arrow(18, 68.0, 18, 66.0); arrow(52, 68.0, 52, 66.0)

# ---------------------------------------------------------------- stage C
band(54.0, "C.  TRANSIENT SOLVER", COOL)
box(3, 44.0, 30, 6.5, "Initialise five control volumes\npile, slag, metal,\nfreeboard, lining")
box(37, 33.0, 30, 18.5,
    "TIME STEP, dt = 10 s\n\n1  Electrical operating point\n2  Charge feed to pile\n"
    "3  Lining network (periodic)\n4  Melt at pile interface, Eq. (5)\n"
    "5  Mass-transfer kinetics,\n    Table 8, Eqs. (22)-(23)\n"
    "6  Energy balances per zone\n7  Service tapping schedule\n8  Test alarms, write trajectory",
    fc="#EAF6F3", ec=COOL, fs=8.6)
arrow(33, 47.25, 37, 47.25)
diamond(71, 38.0, 26, 11.0, "t < t_end ?")
arrow(67, 43.5, 71, 43.5)
# "yes" branch: back along the top into the time-step box
arrow(97, 43.5, 99.2, 43.5, c=COOL, style="-")
arrow(99.2, 43.5, 99.2, 53.0, c=COOL, style="-")
arrow(99.2, 53.0, 52, 53.0, c=COOL, style="-")
arrow(52, 53.0, 52, 51.5, c=COOL)
label(80, 51.3, "yes: advance t", c=COOL)
box(3, 33.0, 30, 6.5, "Campaign summary,\nevent log, trajectories")
# "no" branch: down and back to the campaign summary
arrow(84, 38.0, 84, 30.0, c=INK, style="-")
arrow(84, 30.0, 18, 30.0, c=INK, style="-")
arrow(18, 30.0, 18, 33.0, c=INK)
label(52, 28.8, "no: close out campaign", c=INK)

# ---------------------------------------------------------------- stage D
band(25.0, "D.  TWO-TIER VERIFICATION", EMB)
box(3, 16.0, 44, 7.5,
    "TIER 1  Literature agreement\n48 benchmarks, 17 single-valued;\n"
    "fitted and consistency comparisons\nreported separately",
    fc="#FDECEC", ec=EMB, fs=8.8)
box(53, 16.0, 44, 7.5,
    "TIER 2  Physical admissibility\n178 configurations swept.\nClosure, bounds, convergence,\n"
    "no negative or NaN quantities",
    fc="#FDECEC", ec=EMB, fs=8.8)
arrow(25, 16.0, 25, 13.5, c=EMB, style="-")
arrow(75, 16.0, 75, 13.5, c=EMB, style="-")
arrow(25, 13.5, 50, 13.5, c=EMB, style="-")
arrow(75, 13.5, 50, 13.5, c=EMB, style="-")
diamond(35, 4.0, 30, 9.0, "Both tiers\npass ?", fc="#FDECEC", ec=EMB)
arrow(50, 13.5, 50, 13.0, c=EMB)
# "no" branch: back up the left edge to tier 1
arrow(35, 8.5, 1.0, 8.5, c=EMB, style="-", ls="--")
arrow(1.0, 8.5, 1.0, 19.75, c=EMB, style="-", ls="--")
arrow(1.0, 19.75, 3.0, 19.75, c=EMB, ls="--")
label(18, 7.0, "no: diagnose, correct, re-run both tiers", c=EMB)
arrow(50, 4.0, 50, 1.6, c=COOL)
label(50, 0.6, "yes: release", c=COOL)

ax.text(50, 120.0, "Model development and solution procedure",
        ha="center", va="center", fontsize=13.5, fontweight="bold", color=INK)

plt.tight_layout()
plt.savefig("figures/Fig2_solution_flowchart.png", dpi=150,
            bbox_inches="tight", facecolor="white")
print("wrote figures/Fig2_solution_flowchart.png")
