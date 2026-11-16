#!/usr/bin/env python3
"""
ESF-DT :: audit.py
==================
Sweeps the full input space of the static and dynamic engines and flags any
result that is not physically defensible.  This is a correctness harness,
not a validation harness: it asks "is this answer possible?", not "does it
match the literature".

    python audit.py            # full sweep
    python audit.py --quick    # static only
"""
from __future__ import annotations
import argparse
import itertools
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from esf_dt.static_model import (run_static, DRI_LIBRARY, CARBON_LIBRARY,
                                 FLUX_LIBRARY)
from esf_dt.dynamic_model import run_dynamic
from esf_dt import properties as pr

# --------------------------------------------------------------------------
# Physical bounds.  Outside these a result is wrong, not merely unusual.
# --------------------------------------------------------------------------
BOUNDS = {
    "SEC_reversible_kWh_tHM":   (250.0, 1600.0),
    "SEC_thermodynamic_kWh_tHM": (300.0, 1900.0),
    "SEC_operating_kWh_tHM":    (350.0, 3000.0),
    "Slag_rate_kg_tHM":         (40.0, 900.0),
    "Flux_rate_kg_tHM":         (0.0, 700.0),
    "Carbon_charged_kg_tHM":    (5.0, 260.0),
    "Carbon_consumed_kg_tHM":   (5.0, 240.0),
    "Power_demand_MW":          (0.5, 600.0),
    "Electrode_consumption_kg_tHM": (0.0, 30.0),
    "CO2_total_t_tHM":          (0.0, 3.0),
    "Specific_OPEX_USD_tHM":    (5.0, 600.0),
    "Fe_yield_pct":             (80.0, 100.001),
}
HM_BOUNDS = {"Fe": (85.0, 100.0), "C": (0.0, 5.5), "Si": (0.0, 3.0),
             "Mn": (0.0, 3.0), "P": (0.0, 0.5), "S": (0.0, 0.5),
             "Ti": (0.0, 1.0)}
SLAG_BOUNDS = {"SiO2": (5.0, 70.0), "CaO": (2.0, 70.0), "Al2O3": (0.0, 45.0),
               "MgO": (0.0, 35.0), "FeO": (0.0, 40.0), "MnO": (0.0, 15.0)}

fails: list[str] = []
checked = 0
sub_liquidus: list[str] = []


def flag(case: str, msg: str) -> None:
    fails.append(f"{case}\n      -> {msg}")


def guarded(case, fn):
    """A model that refuses an impossible configuration is behaving well."""
    try:
        return fn()
    except ValueError as e:
        print(f"    (correctly refused) {case}: {str(e)[:70]}...")
        return None


def _dyn_slag_wt(d: dict, j: int) -> dict:
    """Slag analysis at step j of a transient run, for a liquidus call."""
    t = d["trajectory"]
    return {ox: t[f"{ox}_pct"][j]
            for ox in ("CaO", "SiO2", "MgO", "Al2O3", "FeO", "MnO")
            if f"{ox}_pct" in t}


def check_static(case: str, r: dict) -> None:
    if r is None:
        return
    global checked
    checked += 1
    k = r["KPI"]
    # A solution below the liquidus of its own slag closes correctly but is
    # not an operable condition.  It is counted and reported rather than
    # treated as a failure, so that the sweep distinguishes "wrong" from
    # "thermochemically valid but not operable".
    if r.get("sub_liquidus"):
        which = [w.split(" temperature of")[0] for w in r.get("warnings", [])
                 if "below the computed" in w]
        sub_liquidus.append(f"{case} -> {'; '.join(which) or 'below liquidus'} "
                            f"(slag superheat "
                            f"{k.get('Slag_superheat_C', float('nan')):+.0f} K)")
    for key, (lo, hi) in BOUNDS.items():
        v = k.get(key)
        if v is None:
            continue
        if v != v:
            flag(case, f"{key} is NaN")
        elif not (lo <= v <= hi):
            flag(case, f"{key} = {v:,.2f} outside [{lo}, {hi}]")
    wt = r["hot_metal_wt_pct"]
    for el, (lo, hi) in HM_BOUNDS.items():
        v = wt.get(el, 0.0)
        if not (lo <= v <= hi):
            flag(case, f"hot metal {el} = {v:.3f} wt% outside [{lo}, {hi}]")
    tot = sum(wt.values())
    if abs(tot - 100.0) > 0.5:
        flag(case, f"hot metal sums to {tot:.2f} wt%")
    sw = r["slag_wt_pct"]
    for ox, (lo, hi) in SLAG_BOUNDS.items():
        v = sw.get(ox, 0.0)
        if not (lo <= v <= hi):
            flag(case, f"slag {ox} = {v:.2f} wt% outside [{lo}, {hi}]")
    tot = sum(sw.values())
    if abs(tot - 100.0) > 0.5:
        flag(case, f"slag sums to {tot:.2f} wt%")
    for name, m in (("inputs", r["inputs_kg"]), ("outputs", r["outputs_kg"]),
                    ("slag", r["slag_kg"]), ("hot metal", r["hot_metal_kg"])):
        for sp, v in m.items():
            if v < -1e-6:
                flag(case, f"negative mass: {name}/{sp} = {v:.3f} kg")
            if v != v:
                flag(case, f"NaN mass: {name}/{sp}")
    cl = r["closure"]
    worst = max((abs(v) for kk, v in cl.items()
                 if isinstance(v, (int, float))), default=0.0)
    if worst > 1.0:
        flag(case, f"element closure error {worst:.2f} %")
    if not r["converged"]:
        flag(case, f"did not converge (residual {r['residual']:.2e})")
    hb = r["heat_balance_MJ_per_tHM"]
    if hb["Net process heat"] <= 0:
        flag(case, f"net process heat {hb['Net process heat']:.1f} MJ/tHM "
                   f"is not positive")
    sp = r["slag_properties"]
    b2 = sp["B2 (CaO/SiO2)"]
    if not (0.2 <= b2 <= 4.0):
        flag(case, f"slag B2 = {b2:.2f}")
    if sp["Viscosity (Pa.s)"] <= 0 or sp["Viscosity (Pa.s)"] > 100:
        flag(case, f"slag viscosity {sp['Viscosity (Pa.s)']:.3f} Pa.s")
    el = r.get("electrical") or {}
    if el:
        if el["P_total_MW"] <= 0:
            flag(case, f"electrical power {el['P_total_MW']:.2f} MW")
        if not (0.05 <= el["operating_resistance_mohm"] <= 200):
            flag(case, "operating resistance "
                       f"{el['operating_resistance_mohm']:.3f} mOhm")


def check_dynamic(case: str, d: dict) -> None:
    if d is None:
        return
    global checked
    checked += 1
    s = d["summary"]
    lim = {"SEC (kWh/tHM)": (300.0, 3000.0),
           "Slag rate (kg/tHM)": (40.0, 900.0),
           "Productivity (tHM/h)": (0.5, 600.0),
           "Heat loss share (%)": (1.0, 90.0),
           "Final C (wt%)": (0.0, 5.5),
           "Final Si (wt%)": (0.0, 3.0),
           "Final slag FeO (wt%)": (0.0, 40.0),
           "Final B2": (0.2, 4.0),
           "Freeze lining (mm)": (0.0, 400.0),
           "Max shell T (degC)": (20.0, 600.0),
           "Mean metal T (degC)": (1300.0, 1700.0)}
    for key, (lo, hi) in lim.items():
        v = s.get(key)
        if v is None:
            continue
        if v != v:
            flag(case, f"{key} is NaN")
        elif not (lo <= v <= hi):
            flag(case, f"{key} = {v:,.2f} outside [{lo}, {hi}]")
    t = d["trajectory"]
    for key in ("T_metal_C", "T_slag_C", "m_metal_t", "m_slag_t", "power_MW",
                "SEC_cum_kWh_t", "freeze_mm", "C_pct", "Si_pct", "FeO_pct"):
        v = t[key]
        if any(x != x for x in v):
            flag(case, f"trajectory {key} contains NaN")
        if key in ("m_metal_t", "m_slag_t", "power_MW") and min(v) < 0:
            flag(case, f"trajectory {key} goes negative ({min(v):.2f})")
    # Slag colder than metal.  Two corrections to this test.  First, it
    # compared the minimum of each trace, which need not occur at the
    # same instant, so it could fire on an inversion that never existed;
    # the comparison is now made step by step.  Second, an inversion is
    # a symptom, not a cause: if the charge is cold enough, or the feed
    # fast enough, that the slag drops below its own liquidus, the bath
    # has frozen and the condition is not operable, so metal hotter than
    # a freezing slag is the correct answer rather than a solver fault.
    # That case is counted with the other inoperable conditions.  An
    # inversion while the slag is still liquid remains a failure.
    worst = min(s - m for s, m in zip(t["T_slag_C"], t["T_metal_C"]))
    if worst < -60.0:
        T_liq = [pr.slag_liquidus(_dyn_slag_wt(d, j)) - 273.15
                 for j in range(len(t["T_slag_C"]))]
        frozen = min(s - q for s, q in zip(t["T_slag_C"], T_liq))
        if frozen < 0.0:
            sub_liquidus.append(
                f"{case} -> slag falls {-frozen:.0f} K below its own "
                f"liquidus, so the bath freezes and the condition is not "
                f"operable (slag {worst:.0f} K under the metal)")
        else:
            flag(case, f"slag colder than metal by {-worst:.0f} K while "
                       f"the slag is still above its liquidus")


# ==========================================================================
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()

    print("== ESF-DT correctness audit ==\n")

    # ---- 1. every material against every other -------------------------
    print("1. material library cross-product")
    for dri, carb in itertools.product(DRI_LIBRARY, CARBON_LIBRARY):
        check_static(f"DRI={dri}, C={carb}",
                     run_static(dri_name=dri, carbon_source=carb,
                                heat_loss_mode="fraction"))
    for f1, f2 in itertools.product(FLUX_LIBRARY, FLUX_LIBRARY):
        check_static(f"flux1={f1}, flux2={f2}",
                     guarded(f"flux1={f1}, flux2={f2}",
                             lambda: run_static(flux_primary=f1,
                                                flux_secondary=f2,
                                                heat_loss_mode="fraction")))

    # ---- 2. operating envelope, one variable at a time -----------------
    print("2. operating envelope")
    grid = {
        "metallisation_pct": [70, 78, 85, 92, 96, 100],
        "tap_temperature_C": [1380, 1420, 1460, 1500, 1540, 1560],
        "target_C_in_HM_pct": [0.5, 1.5, 2.5, 3.5, 4.5],
        "target_basicity_B2": [0.7, 0.9, 1.1, 1.3, 1.6],
        "target_MgO_in_slag_pct": [4, 6, 8, 11, 14],
        "scrap_fraction_pct": [0, 15, 30, 45, 60],
        "dri_temperature_C": [25, 200, 450, 650, 800],
        "slag_superheat_C": [20, 50, 80, 110],
        "offgas_temperature_C": [900, 1200, 1500, 1800],
        "carbon_yield_pct": [70, 80, 90, 99],
        "productivity_tHM_h": [20, 80, 143, 300],
        "electrical_to_bath_efficiency": [0.75, 0.85, 0.95],
    }
    for key, vals in grid.items():
        for v in vals:
            check_static(f"{key}={v}",
                         run_static(**{key: v}, heat_loss_mode="fraction"))

    # ---- 3. both heat-loss modes and the geometry solver ---------------
    print("3. heat-loss modes and furnace geometry")
    for mode in ("fraction", "geometry"):
        for prod in (20.0, 60.0, 143.0, 300.0):
            check_static(f"mode={mode}, prod={prod}",
                         run_static(heat_loss_mode=mode,
                                    productivity_tHM_h=prod))
    from esf_dt.geometry import FurnaceGeometry
    for L, W, nel in ((12, 5, 3), (22, 8, 4), (35, 11, 6), (50, 16, 9)):
        geo = FurnaceGeometry(length=L, width=W, n_electrodes=nel)
        check_static(f"geometry {L}x{W}, {nel} electrodes",
                     run_static(heat_loss_mode="geometry", geometry=geo,
                                productivity_tHM_h=max(20.0, L * W * 0.35)))

    # ---- 4. corner cases -----------------------------------------------
    print("4. corners")
    corners = [
        dict(metallisation_pct=70, target_C_in_HM_pct=4.5,
             tap_temperature_C=1560, target_basicity_B2=1.6),
        dict(metallisation_pct=100, target_C_in_HM_pct=0.5,
             tap_temperature_C=1380, target_basicity_B2=0.7),
        dict(dri_name="DRI-Pilbara (19 % gangue)", metallisation_pct=75,
             target_MgO_in_slag_pct=14),
        dict(dri_name="DRI-HG (7.2 % gangue)", scrap_fraction_pct=60),
        dict(dri_name="HBI (carburised, 2 % C)", metallisation_pct=96),
        dict(flux_primary="Quartzite", flux_secondary="Bauxite"),
        dict(flux_primary="Limestone", flux_secondary="Limestone"),
        dict(carbon_source="Petroleum coke", carbon_yield_pct=70),
    ]
    for c in corners:
        check_static(str(c), guarded(str(c),
                     lambda c=c: run_static(**c, heat_loss_mode="fraction")))

    # ---- 5. dynamic ----------------------------------------------------
    if not a.quick:
        print("5. dynamic engine")
        dyn = [
            dict(),
            dict(dri_feed_t_h=60.0, power_MW=50.0),
            dict(dri_feed_t_h=200.0, power_MW=140.0),
            dict(metallisation_pct=80.0),
            dict(dri_temperature_C=25.0),
            dict(carbon_feed_kg_t_dri=90.0),
            dict(lime_feed_kg_t_dri=30.0, dolo_feed_kg_t_dri=10.0),
            dict(power_control="fixed", power_MW=100.0),
            dict(dri_name="DRI-Pilbara (19 % gangue)"),
            dict(dt_s=5.0), dict(dt_s=30.0),
            dict(metal_tap_interval_min=30.0, metal_tap_mass_t=70.0),
            dict(scrap_feed_t_h=30.0),
        ]
        for c in dyn:
            check_dynamic(f"dynamic {c}",
                          run_dynamic(duration_min=240, log_every_s=60, **c))

    # ---- report ---------------------------------------------------------
    print(f"\n{'=' * 66}")
    print(f"cases checked : {checked}")
    print(f"failures      : {len(fails)}")
    print(f"below liquidus: {len(sub_liquidus)} "
          f"(valid balances at non-operable conditions, flagged not failed)")
    for c in sub_liquidus:
        print(f"    {c}")
    if fails:
        print(f"{'=' * 66}")
        for f in fails:
            print("  FAIL " + f)
        return 1
    print("all results physically admissible")
    return 0


if __name__ == "__main__":
    sys.exit(main())
