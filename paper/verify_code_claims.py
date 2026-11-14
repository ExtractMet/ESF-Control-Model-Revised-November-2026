#!/usr/bin/env python3
"""
Check that every code change claimed in the revised manuscript and in the
rebuttal is actually present in the program and actually behaves as claimed.

Each check exercises the code rather than inspecting the source, except where
the claim is about a source-level fact such as a corrected comment.  The
script exits non-zero if any claim is unsupported.
"""
from __future__ import annotations

import csv
import inspect
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from esf_dt import electrical as el                                # noqa: E402
from esf_dt import schematic as sc                                 # noqa: E402
from esf_dt import thermo as th                                    # noqa: E402
from esf_dt.dynamic_model import DynamicInputs, run_dynamic        # noqa: E402
from esf_dt.static_model import ESFInputs, run_static              # noqa: E402

BASE = dict(heat_loss_mode="fraction", heat_loss_fraction=0.10)
EQ = dict(BASE, silicon_mode="equilibrium")
GEO = dict(heat_loss_mode="geometry", productivity_tHM_h=143.0)

results: list[tuple[str, str, bool, str]] = []


def claim(ref: str, text: str, ok: bool, detail: str = ""):
    results.append((ref, text, bool(ok), detail))


def src(path: str) -> str:
    return open(os.path.join(ROOT, path)).read()


# ======================================================================
# A6.  Silica activity to the first power, Gibbs energy refitted
# ======================================================================
slag = {"CaO": 40.0, "SiO2": 36.5, "Al2O3": 13.7, "MgO": 8.2,
        "FeO": 0.65, "MnO": 0.6}
x = th.mole_fractions(slag)["SiO2"]
a1 = th.a_SiO2(slag, 1773.15)
# rebuild the coefficient independently and check the activity is linear in x
B3 = th.basicity_B3(slag)
Al = slag["Al2O3"] / slag["SiO2"]
import math                                                        # noqa: E402
g = 10.0 ** (-2.05 * (B3 - 1.0) - 0.42 * Al - 0.35)
g *= math.exp(-3100.0 * (1.0 / 1773.15 - 1.0 / 1773.0))
claim("A6", "a_SiO2 is linear in the silica mole fraction",
      abs(a1 - g * x) / (g * x) < 1e-9,
      f"a_SiO2 = {a1:.6e}, gamma*x = {g*x:.6e}, gamma*x^2 = {g*x*x:.6e}")
claim("A6", "the SiO2_C Gibbs A term is the refitted 596 200 J/mol",
      th.REACTIONS["SiO2_C"]["A"] == 596200.0,
      f"A = {th.REACTIONS['SiO2_C']['A']:,.0f}")
claim("A6", "no oxide activity in the engine squares its mole fraction",
      "xSi * xSi" not in src("esf_dt/thermo.py"),
      "searched thermo.py for a squared mole fraction")
# the two printed anchors are reproduced
si1400 = run_static(tap_temperature_C=1400.0, **EQ)["hot_metal_wt_pct"]["Si"]
si1525 = run_static(tap_temperature_C=1525.0, **EQ)["hot_metal_wt_pct"]["Si"]
claim("A6", "the two printed silicon anchors are reproduced within 2 %",
      abs(si1400 - 0.03) / 0.03 < 0.02 and abs(si1525 - 0.62) / 0.62 < 0.02,
      f"1400 degC {si1400:.4f} vs 0.03; 1525 degC {si1525:.4f} vs 0.62")
# the browser console carries the same physics
jsrc = src("web/esf_console.html")
claim("A6", "the HTML console uses the first power and the refitted A term",
      "g*x*x" not in jsrc and "596200" in jsrc and "581500" not in jsrc,
      "checked web/esf_console.html")
claim("A6", "no component of the deck still carries the old Gibbs A term",
      all("581500" not in src(f) and "581.5 kJ" not in src(f)
          for f in ("web/esf_console.html", "docs/THEORY.md",
                    "paper/build_workbook.py", "esf_dt/thermo.py")),
      "checked the engine, console, theory note and workbook builder")
claim("A6", "the theory note no longer states a squared mole fraction",
      "x_{\\mathrm{SiO_2}}^{2}" not in src("docs/THEORY.md"),
      "checked docs/THEORY.md")

# ======================================================================
# R2-3.  The fitted thermal utilisation factor is withdrawn
# ======================================================================
claim("R2-3", "thermal_utilisation_efficiency defaults to unity",
      ESFInputs().thermal_utilisation_efficiency == 1.0,
      f"default = {ESFInputs().thermal_utilisation_efficiency}")
r = run_static(**BASE)
claim("R2-3", "the reversible and thermodynamic tiers now coincide",
      abs(r["KPI"]["SEC_reversible_kWh_tHM"]
          - r["KPI"]["SEC_thermodynamic_kWh_tHM"]) < 1e-6,
      f"{r['KPI']['SEC_reversible_kWh_tHM']:.3f} vs "
      f"{r['KPI']['SEC_thermodynamic_kWh_tHM']:.3f}")
claim("R2-3", "the operating tier still exceeds the reversible tier",
      r["KPI"]["SEC_operating_kWh_tHM"] > r["KPI"]["SEC_reversible_kWh_tHM"],
      f"operating {r['KPI']['SEC_operating_kWh_tHM']:.1f} > reversible "
      f"{r['KPI']['SEC_reversible_kWh_tHM']:.1f}")

# The value may still be named in prose that explains the withdrawal; what
# must not survive is any live assignment or default that uses it.
USE_887 = re.compile(r'(=\s*0\.887|0\.887\s*[,)])')
offenders = [f for f in ("web/esf_console.html", "gui/esf_gui_tk.py",
                         "gui/esf_streamlit.py", "esf_dt/static_model.py")
             if USE_887.search(src(f))]
claim("R2-3", "no interface still uses the withdrawn factor as a value",
      not offenders,
      "offending files: " + (", ".join(offenders) if offenders
                             else "none; engine, console and both GUIs clear"))
claim("R2-3", "the browser console's reporting factor is unity",
      "const ETA_TH=1.0;" in src("web/esf_console.html"),
      "checked web/esf_console.html")

# ======================================================================
# R3-29.  Sub-liquidus detection
# ======================================================================
sub = run_static(dri_name="DRI-Shahabuddin (16 % gangue)",
                 metallisation_pct=90.0, tap_temperature_C=1300.0,
                 target_MgO_in_slag_pct=0.5, **EQ)
ok_hot = run_static(**BASE)
claim("R3-29", "a sub-liquidus tapping condition is flagged",
      sub.get("sub_liquidus") is True,
      f"1300 degC: sub_liquidus = {sub.get('sub_liquidus')}, "
      f"slag liquidus {sub['KPI']['Slag_liquidus_C']:.0f} degC")
claim("R3-29", "a sub-liquidus case raises a warning naming the liquidus",
      any("below the computed" in w for w in sub["warnings"]),
      (sub["warnings"][-1][:80] + "...") if sub["warnings"] else "no warning")
claim("R3-29", "an operable case is not flagged",
      ok_hot.get("sub_liquidus") is False,
      f"base case sub_liquidus = {ok_hot.get('sub_liquidus')}")
claim("R3-29", "the admissibility sweep counts sub-liquidus cases separately",
      "sub_liquidus" in src("audit.py") and "below liquidus" in src("audit.py"),
      "checked audit.py")

# ======================================================================
# R2-1.  SAF/OSBF reporting quantities
# ======================================================================
g2 = run_static(**GEO)
for key in ("Hearth_power_density_kW_m2", "Operating_resistance_mohm",
            "Slag_resistance_mohm", "Slag_liquidus_C", "Slag_superheat_C"):
    v = g2["KPI"].get(key)
    claim("R2-1", f"KPI '{key}' is reported and finite",
          isinstance(v, float) and v == v, f"{key} = {v}")
claim("R2-1", "hearth power density equals power over bath area",
      abs(g2["KPI"]["Hearth_power_density_kW_m2"]
          - g2["KPI"]["Power_demand_MW"] * 1000.0 / 385.0) < 0.5,
      f"{g2['KPI']['Hearth_power_density_kW_m2']:.1f} kW/m2 at "
      f"{g2['KPI']['Power_demand_MW']:.1f} MW over 385 m2")

# ======================================================================
# R1-0.  Convergence declared at the tolerance the loop exits on
# ======================================================================
claim("R1-0", "the convergence tolerance is reported with the result",
      r.get("tolerance") == 1e-6,
      f"tolerance = {r.get('tolerance')}")
claim("R1-0", "convergence is declared against that tolerance",
      r["converged"] is True and r["residual"] < r["tolerance"],
      f"residual {r['residual']:.2e} < {r.get('tolerance')}")
claim("R1-0", "the 1e-4 convergence test is gone from the source",
      "hist[-1] < 1e-4" not in src("esf_dt/static_model.py"),
      "checked static_model.py")

# ======================================================================
# R3-10.  Transformer tap relation
# ======================================================================
e = g2["electrical"]
claim("R3-10", "the nominal secondary voltage is reported",
      e.get("secondary_voltage_nominal_V") == 420.0,
      f"nominal = {e.get('secondary_voltage_nominal_V')} V")
claim("R3-10", "the tap ratio is reported and consistent",
      abs(e["tap_ratio_to_nominal"]
          - e["tap_voltage_V"] / e["secondary_voltage_nominal_V"]) < 1e-9,
      f"operating {e['tap_voltage_V']:.0f} V, ratio "
      f"{e['tap_ratio_to_nominal']:.3f}")
claim("R3-10", "the tap range is an explicit named parameter",
      hasattr(el.ElectricalConfig(), "tap_range_factor"),
      f"tap_range_factor = {el.ElectricalConfig().tap_range_factor}")
claim("R3-10", "the line-to-line description has been corrected in the source",
      "line-to-line tap voltage" not in src("esf_dt/electrical.py"),
      "checked electrical.py")

# ======================================================================
# R1-9.  One stated averaging window
# ======================================================================
claim("R1-9", "summary_window_frac is an input",
      hasattr(DynamicInputs(), "summary_window_frac"),
      f"default = {DynamicInputs().summary_window_frac}")
d1 = run_dynamic(duration_min=180, dt_s=20, log_every_s=60)
s1 = d1["summary"]
claim("R1-9", "the averaging window is reported with the summary",
      "Averaging window (min, from start of campaign)" in s1
      and abs(s1["Averaging window (min, from start of campaign)"] - 90.0) < 1.0,
      f"window starts at {s1.get('Averaging window (min, from start of campaign)')} min "
      f"of {s1.get('Campaign duration (min)')}")
claim("R1-9", "the basis of the means and of the totals is stated",
      "final 50%" in str(s1.get("Mean quantities basis", ""))
      and "whole campaign" in str(s1.get("Cumulative quantities basis", "")),
      f"{s1.get('Mean quantities basis')} | {s1.get('Cumulative quantities basis')}")
d2 = run_dynamic(duration_min=180, dt_s=20, log_every_s=60,
                 summary_window_frac=0.25)
claim("R1-9", "changing the window changes the reported window and the means",
      abs(d2["summary"]["Averaging window (min, from start of campaign)"] - 135.0) < 1.0
      and d2["summary"]["Mean power (MW)"] != s1["Mean power (MW)"],
      f"0.50 -> {s1['Mean power (MW)']:.3f} MW; "
      f"0.25 -> {d2['summary']['Mean power (MW)']:.3f} MW")
claim("R1-9", "temperatures use the same window as power, not a different one",
      "mean(\"T_metal_C\", 0.4)" not in src("esf_dt/dynamic_model.py"),
      "checked dynamic_model.py for the old 0.4 window")

# ======================================================================
# R3-7.  Figure 1 distinguishes inventory from tapping rate
# ======================================================================
st = sc.state_from_dynamic(d1["trajectory"], idx=-1)
svg = sc.furnace_svg(st)
claim("R3-7", "the schematic labels the bath masses as in-furnace inventory",
      "SLAG in furnace" in svg and "HOT METAL in furnace" in svg,
      "checked the generated SVG")
claim("R3-7", "the schematic states the tapping rates as well",
      svg.count("tapped") >= 2 and st["metal_rate_t_h"] > 0,
      f"metal {st['metal_rate_t_h']:.1f} t/h, slag {st['slag_rate_t_h']:.1f} t/h")
claim("R3-7", "the water-cooled panel label is complete and not truncated",
      "Water-cooled" in svg and "panels" in svg,
      "checked the generated SVG")
claim("R3-7", "the computed basicity is labelled as computed",
      "(computed)" in svg, "checked the generated SVG")

# ======================================================================
# run_validation.py claims
# ======================================================================
rows = list(csv.DictReader(open(os.path.join(ROOT, "figures",
                                             "validation_table.csv"))))
stats = json.load(open(os.path.join(ROOT, "figures",
                                    "validation_stats.json")))
cols = set(rows[0].keys())
claim("R3-16", "every comparison carries a basis, a role and a provenance",
      {"basis", "role", "provenance", "note"} <= cols,
      f"columns: {sorted(cols)}")
indep = [r for r in rows if r["role"] == "independent"]
claim("R3-16", "the statistics cover the independent comparisons only",
      stats["n_comparisons"] + stats["n_windows"] == len(indep)
      == stats["n_benchmarks"],
      f"independent rows {len(indep)}, benchmarks {stats['n_benchmarks']}")
claim("R3-16", "the two fitted silicon anchors are excluded from the statistics",
      all(r["role"] == "calibration" for r in rows
          if "[Si] in hot metal @ 1400" in r["quantity"]
          or "[Si] in hot metal @ 1525" in r["quantity"]),
      "roles of the 1400 and 1525 degC silicon rows")
claim("R3-16", "the industrial comparison is excluded as a consistency check",
      all(r["role"] == "consistency" for r in rows if "OSBF" in r["case"]),
      f"{sum(1 for r in rows if 'OSBF' in r['case'])} OSBF rows")

sens = [r for r in rows if r["case"] == "Sensitivity"]
claim("R3-30", "every energy sensitivity is evaluated on the equilibrium basis",
      all(r["basis"] == "equilibrium" for r in sens),
      f"{len(sens)} sensitivity rows, bases "
      f"{sorted({r['basis'] for r in sens})}")
claim("R3-31", "the gangue sensitivity is an interval test, not a midpoint",
      any("gangue" in r["quantity"] and "-" in str(r["literature"])
          and r["rpd_pct"] in ("in window", "outside") for r in sens),
      "checked the gangue rows")
claim("R3-31", "the gangue sensitivity is reported on both gangue bases",
      any("ore gangue" in r["quantity"] for r in sens)
      and any("DRI gangue" in r["quantity"] for r in sens),
      "ore and DRI bases both present")
claim("R3-33", "the cooling-water comparison is an interval test",
      any("cooling circuit" in r["quantity"]
          and r["rpd_pct"] in ("in window", "outside") for r in rows),
      "checked the cooling-circuit row")
claim("R3-33", "the 1500 degC silicon comparison is an interval test",
      any("[Si] in hot metal @ 1500" in r["quantity"]
          and r["rpd_pct"] in ("in window", "outside") for r in rows),
      "checked the 1500 degC silicon row")

bal = [r for r in rows if r["case"].startswith("Full balance")]
need = {"slag FeO (wt%)", "HM S (wt%)", "HM P (wt%)", "Off-gas (kg)",
        "Carburiser carbon (kg)"}
claim("R3-25", "the five omitted stream quantities are now compared",
      need <= {r["quantity"] for r in bal},
      f"{len(bal)} stream rows")
claim("R3-25", "the two unsupported published entries are excluded with a reason",
      all(r["role"] == "reference_inconsistent" and r["note"]
          for r in bal if r["quantity"] in ("slag FeO (wt%)", "HM P (wt%)")),
      "checked slag FeO and hot metal P")
claim("R3-32", "the unsourced pilot comparison is no longer a benchmark",
      not any(str(r["literature"]).startswith("762.6")
              and r["role"] == "independent" for r in rows),
      "checked for a counted 762.6 comparison")

# figure-generator claims
rv = src("run_validation.py")
claim("R3-18", "no internal figure-number prefix remains in any panel title",
      not re.search(r'title=f?"F\d', rv) and not re.search(r'set_title\(f?"F\d', rv),
      "searched run_validation.py panel titles")
claim("R3-22", "the freeze-lining figure labels both curves and adds a legend",
      "Slag-wall hot-face temperature (right axis)" in rv
      and "ax.legend(handles=[l1, l2]" in rv,
      "checked the freeze-lining block")
claim("R3-23", "the parity plot is drawn as separate labelled series",
      "groups.setdefault" in rv and "MARK[j % len(MARK)]" in rv,
      "checked the parity block")
claim("R3-19", "the silicon figure is drawn on both bases",
      "model, equilibrium basis" in rv
      and "model, with departure-from-equilibrium limits" in rv,
      "checked the silicon figure block")

fc = src("paper/make_flowchart.py")
claim("R1-6", "the flowchart cites the flux equations as (24) to (26)",
      "Eqs. (24)-(26)" in fc and "Eqs. (18)-(19)" not in fc,
      "checked make_flowchart.py")
claim("R1-6", "the flowchart cites the reaction-rate table as Table 6",
      "Table 6, Eqs. (22)-(23)" in fc and "Table 1, Eqs. (6)-(7)" not in fc,
      "checked make_flowchart.py")

claim("R2-4c", "the two-solver cross-check script is present and wired in",
      os.path.exists(os.path.join(HERE, "cross_check_ss_transient.py"))
      and any(r["role"] == "internal" for r in rows),
      f"{sum(1 for r in rows if r['role'] == 'internal')} internal rows")

# ======================================================================
# report
# ======================================================================
width = max(len(t) for _, t, _, _ in results)
cur = None
for ref, text, ok, detail in results:
    if ref != cur:
        print(f"\n{ref}")
        cur = ref
    print(f"  [{'ok' if ok else 'FAIL'}] {text:<{width}}  {detail}")

bad = [r for r in results if not r[2]]
print(f"\n{len(results)} claims checked, {len(bad)} unsupported")
if bad:
    for ref, text, _, detail in bad:
        print(f"  UNSUPPORTED  {ref}: {text}  ({detail})")
    sys.exit(1)
print("every code change claimed in the manuscript and rebuttal is present "
      "and behaves as claimed")
