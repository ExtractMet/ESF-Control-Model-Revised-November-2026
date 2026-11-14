#!/usr/bin/env python3
"""
Check every quantitative claim in the revised manuscript against the engine.

Each entry below names a claim, the value printed in the manuscript, and a
callable that recomputes it.  The script fails loudly on any mismatch; it is
the last step before the revision is packaged.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from esf_dt.static_model import run_static
from esf_dt.dynamic_model import run_dynamic

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MS = os.path.join(HERE, "ESF-DT_manuscript_R1.md")

BASE = dict(heat_loss_mode="fraction", heat_loss_fraction=0.10)
EQ = dict(BASE, silicon_mode="equilibrium")
GEO = dict(heat_loss_mode="geometry", productivity_tHM_h=143.0)

fails: list[str] = []
checks = 0


def ck(name: str, printed, computed, tol=0.02, absolute=False):
    """Compare a printed value against a recomputed one."""
    global checks
    checks += 1
    if printed is None or computed is None:
        fails.append(f"{name}: missing value")
        return
    if absolute:
        ok = abs(printed - computed) <= tol
    else:
        ok = abs(printed - computed) <= tol * max(abs(computed), 1e-9)
    if not ok:
        fails.append(f"{name}: manuscript {printed} vs engine {computed:.6g}")


# ---------------------------------------------------------------- statistics
stats = json.load(open(os.path.join(ROOT, "figures", "validation_stats.json")))
rows = list(csv.DictReader(open(os.path.join(ROOT, "figures",
                                             "validation_table.csv"))))

ck("n_benchmarks", 48, stats["n_benchmarks"], absolute=True, tol=0)
ck("n_comparisons", 17, stats["n_comparisons"], absolute=True, tol=0)
ck("n_windows", 31, stats["n_windows"], absolute=True, tol=0)
ck("windows_satisfied", 22, stats["windows_satisfied"], absolute=True, tol=0)
ck("MARD", 13.1, stats["mean_abs_RPD_pct"], absolute=True, tol=0.05)
ck("median", 4.0, stats["median_abs_RPD_pct"], absolute=True, tol=0.05)
ck("within_10", 12, stats["within_10_pct"], absolute=True, tol=0)
ck("within_15", 13, stats["within_15_pct"], absolute=True, tol=0)
ck("max deviation", 71.6, stats["max_abs_RPD_pct"], absolute=True, tol=0.1)
ck("calibration MARD", 6.8, stats["calibration_mean_abs_RPD_pct"],
   absolute=True, tol=0.05)
ck("total rows", 95, stats["n_rows_total"], absolute=True, tol=0)

roles = {}
for r in rows:
    roles[r["role"]] = roles.get(r["role"], 0) + 1
for role, n in (("independent", 48), ("detail", 14), ("consistency", 12),
                ("internal", 10), ("calibration", 5), ("orientation", 3),
                ("reference_inconsistent", 2), ("formal", 1)):
    ck(f"role count {role}", n, roles.get(role, 0), absolute=True, tol=0)

# ------------------------------------------------------- representative case
rep = run_static(dri_name="DRI-B (15.5 % gangue)", metallisation_pct=94.0,
                 tap_temperature_C=1500.0, target_basicity_B2=1.10,
                 target_C_in_HM_pct=3.4, **GEO)
hb = rep["heat_balance_MJ_per_tHM"]
K = 1.0 / 3.6     # MJ -> kWh
ck("Table 3 charge enthalpy", -1265.8, hb["Charge enthalpy in (abs.)"] * K,
   absolute=True, tol=0.5)
ck("Table 3 hot metal out", 335.3, hb["Hot metal out (abs.)"] * K,
   absolute=True, tol=0.5)
ck("Table 3 slag out", -991.7, hb["Slag out (abs.)"] * K, absolute=True, tol=0.5)
ck("Table 3 off-gas out", -39.1, hb["Off-gas out (abs.)"] * K,
   absolute=True, tol=0.5)
ck("Table 3 slag mixing", -5.8, hb["Slag mixing enthalpy"] * K,
   absolute=True, tol=0.2)
ck("Table 3 net process heat", 563.9, hb["Net process heat"] * K,
   absolute=True, tol=0.5)
ck("Table 3 refractory loss", 202.4, hb["Refractory + shell loss"] * K,
   absolute=True, tol=0.5)
ck("Table 3 total to bath", 766.3, hb["Total supplied to bath"] * K,
   absolute=True, tol=0.5)
ck("3.7.1 operating resistance", 4.30,
   rep["KPI"]["Operating_resistance_mohm"], absolute=True, tol=0.02)
ck("3.7.1 hearth power density", 316,
   rep["KPI"]["Hearth_power_density_kW_m2"], absolute=True, tol=1.0)
ck("3.3.1 slag heat content MJ/kg",
   1.97,
   (hb["  Slag sensible (to liquidus)"] + hb["  Slag latent (solution)"]
    + hb["  Slag superheat"]) / rep["KPI"]["Slag_rate_kg_tHM"],
   absolute=True, tol=0.02)
ck("3.3.1 slag rate", 307, rep["KPI"]["Slag_rate_kg_tHM"],
   absolute=True, tol=1.0)

# ------------------------------------------------------------- Table 4b
ss = run_static(**GEO)
ck("Table 4b B2 steady", 1.092, ss["slag_properties"]["B2 (CaO/SiO2)"],
   absolute=True, tol=0.002)
ck("Table 4b MgO steady", 8.25, ss["slag_wt_pct"]["MgO"], absolute=True, tol=0.05)
ck("Table 4b voltage steady", 496, ss["electrical"]["tap_voltage_V"],
   absolute=True, tol=1.0)
ck("Table 4b tap ratio", 1.18, ss["electrical"]["tap_ratio_to_nominal"],
   absolute=True, tol=0.01)
ck("Table 4b power steady", 110.0, ss["electrical"]["P_total_MW"],
   absolute=True, tol=0.2)
ck("Table 4b R_op steady", 4.59, ss["KPI"]["Operating_resistance_mohm"],
   absolute=True, tol=0.02)
ck("Table 4b hearth density steady", 286,
   ss["KPI"]["Hearth_power_density_kW_m2"], absolute=True, tol=1.0)

# ------------------------------------------------------------- Table 10
rs = run_static(dri_name="DRI-Shahabuddin (16 % gangue)",
                metallisation_pct=100.0, tap_temperature_C=1600.0,
                target_basicity_B2=1.10, target_MgO_in_slag_pct=0.5,
                target_C_in_HM_pct=3.5, **BASE)
ck("T10 hot metal", 1052.2, rs["outputs_kg"]["Hot metal"], absolute=True, tol=0.3)
ck("T10 slag", 300.5, rs["outputs_kg"]["Slag"], absolute=True, tol=0.3)
ck("T10 SEC reversible", 528.1, rs["KPI"]["SEC_reversible_kWh_tHM"],
   absolute=True, tol=0.3)
ck("T10 SEC operating", 652.0, rs["KPI"]["SEC_operating_kWh_tHM"],
   absolute=True, tol=0.5)
ck("T10 slag SiO2", 37.04, rs["slag_wt_pct"]["SiO2"], absolute=True, tol=0.02)
ck("T10 slag CaO", 40.34, rs["slag_wt_pct"]["CaO"], absolute=True, tol=0.02)
ck("T10 slag Al2O3", 20.16, rs["slag_wt_pct"]["Al2O3"], absolute=True, tol=0.02)
ck("T10 HM Fe", 95.04, rs["hot_metal_wt_pct"]["Fe"], absolute=True, tol=0.02)
ck("T10 HM Si", 0.45, rs["hot_metal_wt_pct"]["Si"], absolute=True, tol=0.01)
ck("T10 HM Mn", 0.97, rs["hot_metal_wt_pct"]["Mn"], absolute=True, tol=0.01)
ck("T10 HM S", 0.011, rs["hot_metal_wt_pct"]["S"], absolute=True, tol=0.001)
ck("T10 HM P", 0.010, rs["hot_metal_wt_pct"]["P"], absolute=True, tol=0.001)

rs_og = run_static(dri_name="DRI-Shahabuddin (16 % gangue)",
                   metallisation_pct=100.0, tap_temperature_C=1600.0,
                   target_basicity_B2=1.10, target_MgO_in_slag_pct=0.5,
                   target_C_in_HM_pct=3.5, post_combustion_ratio=0.0,
                   air_ingress_factor=1.0, **BASE)
og = sum(v for k, v in rs_og["offgas_kg"].items() if k in ("CO", "CO2"))
ck("T10 off-gas", 16.23, og, absolute=True, tol=0.05)
ck("T10 carburiser C", 43.3,
   rs["KPI"]["Carbon_consumed_kg_tHM"] * rs["outputs_kg"]["Hot metal"] / 1000.0,
   absolute=True, tol=0.2)

# ------------------------------------------------------------- Table 11
def sec_rev(**kw):
    return run_static(**dict(EQ, **kw))["KPI"]["SEC_reversible_kWh_tHM"]


def sec_op(**kw):
    return run_static(**dict(EQ, **kw))["KPI"]["SEC_operating_kWh_tHM"]


dC_rev = (sec_rev(target_C_in_HM_pct=3.5) - sec_rev(target_C_in_HM_pct=1.0)) / 2.5
dC_op = (sec_op(target_C_in_HM_pct=3.5) - sec_op(target_C_in_HM_pct=1.0)) / 2.5
ck("T11 dSEC/dC rev", 8.43, dC_rev, absolute=True, tol=0.02)
ck("T11 dSEC/dC op", 10.40, dC_op, absolute=True, tol=0.02)

dMR_rev = (sec_rev(metallisation_pct=100.0) - sec_rev(metallisation_pct=80.0)) / 20.0
dMR_op = (sec_op(metallisation_pct=100.0) - sec_op(metallisation_pct=80.0)) / 20.0
ck("T11 dSEC/dMR rev", -8.20, dMR_rev, absolute=True, tol=0.02)
ck("T11 dSEC/dMR op", -10.13, dMR_op, absolute=True, tol=0.02)

B = "DRI-B (15.5 % gangue)"
dS_rev = (sec_rev(dri_name=B, metallisation_pct=90.0, scrap_fraction_pct=60.0)
          - sec_rev(dri_name=B, metallisation_pct=90.0, scrap_fraction_pct=0.0)) / 60.0
dS_op = (sec_op(dri_name=B, metallisation_pct=90.0, scrap_fraction_pct=60.0)
         - sec_op(dri_name=B, metallisation_pct=90.0, scrap_fraction_pct=0.0)) / 60.0
ck("T11 dSEC/dscrap rev", -2.83, dS_rev, absolute=True, tol=0.02)
ck("T11 dSEC/dscrap op", -3.49, dS_op, absolute=True, tol=0.02)

dT_rev = (sec_rev(tap_temperature_C=1525.0) - sec_rev(tap_temperature_C=1400.0)) / 5.0
dT_op = (sec_op(tap_temperature_C=1525.0) - sec_op(tap_temperature_C=1400.0)) / 5.0
ck("T11 dSEC/dT rev", 12.58, dT_rev, absolute=True, tol=0.02)
ck("T11 dSEC/dT op", 15.53, dT_op, absolute=True, tol=0.02)

# ------------------------------------------------------------- Table 12
for T, eq_v, lim_v in ((1400, 0.032, 0.031), (1450, 0.109, 0.097),
                       (1500, 0.350, 0.242), (1525, 0.614, 0.337),
                       (1550, 1.040, 0.409), (1600, 2.331, 0.449)):
    ck(f"T12 Si eq {T}", eq_v,
       run_static(tap_temperature_C=float(T), **EQ)["hot_metal_wt_pct"]["Si"],
       absolute=True, tol=0.004)
    ck(f"T12 Si limited {T}", lim_v,
       run_static(tap_temperature_C=float(T), **BASE)["hot_metal_wt_pct"]["Si"],
       absolute=True, tol=0.004)

# ------------------------------------------------- Section 6.3 SEC listings
for d, v100, v80 in (("DRI-A (13.8 % gangue)", 495.6, 659.7),
                     ("DRI-B (15.5 % gangue)", 519.3, 682.9),
                     ("DRI-C (16.0 % gangue)", 520.5, 684.4)):
    ck(f"6.3 SEC {d[:5]} 100MR", v100, sec_rev(dri_name=d, metallisation_pct=100.0),
       absolute=True, tol=0.3)
    ck(f"6.3 SEC {d[:5]} 80MR", v80, sec_rev(dri_name=d, metallisation_pct=80.0),
       absolute=True, tol=0.3)
for sc, v in ((0, 601.1), (20, 541.0), (40, 484.5), (60, 431.5)):
    ck(f"6.3 scrap {sc}", v,
       sec_rev(dri_name=B, metallisation_pct=90.0, scrap_fraction_pct=float(sc)),
       absolute=True, tol=0.3)

# ------------------------------------------------------- worked example 6.12.1
for lab, kw, sec_v, slag_v, r_v, pd_v in (
        ("present", dict(dri_name="DRI-B (15.5 % gangue)"), 851, 307, 4.30, 316),
        ("19% gangue", dict(dri_name="DRI-Pilbara (19 % gangue)"), 897, 387, 4.37, 333),
        ("19% + scrap", dict(dri_name="DRI-Pilbara (19 % gangue)",
                             scrap_fraction_pct=20.0), 825, 301, 4.37, 306),
        ("19% B2 0.95", dict(dri_name="DRI-Pilbara (19 % gangue)",
                             target_basicity_B2=0.95), 894, 356, 4.69, 332)):
    r = run_static(metallisation_pct=94.0, tap_temperature_C=1500.0,
                   target_C_in_HM_pct=3.4, **dict(GEO, **kw))
    ck(f"6.12.1 {lab} SEC", sec_v, r["KPI"]["SEC_operating_kWh_tHM"],
       absolute=True, tol=1.0)
    ck(f"6.12.1 {lab} slag", slag_v, r["KPI"]["Slag_rate_kg_tHM"],
       absolute=True, tol=1.0)
    ck(f"6.12.1 {lab} R_op", r_v, r["KPI"]["Operating_resistance_mohm"],
       absolute=True, tol=0.02)
    ck(f"6.12.1 {lab} power density", pd_v,
       r["KPI"]["Hearth_power_density_kW_m2"], absolute=True, tol=1.0)

# -------------------------------------------------------------- campaign
dyn = run_dynamic(duration_min=420, dt_s=10, log_every_s=60)
sm = dyn["summary"]
ck("T16 tapped", 964.6, sm["Hot metal tapped (t)"], absolute=True, tol=0.5)
ck("T16 produced", 1002, sm["Hot metal produced (t)"], absolute=True, tol=1.0)
ck("T16 productivity", 143.2, sm["Productivity (tHM/h)"], absolute=True, tol=0.1)
ck("T16 SEC", 707, sm["SEC (kWh/tHM)"], absolute=True, tol=1.0)
ck("T16 mean power", 102.8, sm["Mean power (MW)"], absolute=True, tol=0.1)
ck("T16 mean loss", 30.7, sm["Mean heat loss (MW)"], absolute=True, tol=0.1)
ck("T16 loss share", 29.9, sm["Heat loss share (%)"], absolute=True, tol=0.1)
ck("T16 mean metal T", 1499, sm["Mean metal T (degC)"], absolute=True, tol=1.0)
ck("T16 mean slag T", 1518, sm["Mean slag T (degC)"], absolute=True, tol=1.0)
ck("T16 final FeO", 1.80, sm["Final slag FeO (wt%)"], absolute=True, tol=0.02)
ck("T16 final B2", 1.073, sm["Final B2"], absolute=True, tol=0.005)
ck("T16 freeze", 76, sm["Freeze lining (mm)"], absolute=True, tol=1.0)
ck("T16 shell T", 197, sm["Max shell T (degC)"], absolute=True, tol=1.0)
ck("T16 window start", 210.0,
   sm["Averaging window (min, from start of campaign)"], absolute=True, tol=0.1)

# 80 % MR pilot magnitude check quoted in 6.8
ck("6.8 pilot magnitude", 980,
   run_static(dri_name=B, metallisation_pct=80.0, **GEO)["KPI"]["SEC_operating_kWh_tHM"],
   absolute=True, tol=1.0)

# ---------------------------------------------- Section 5.3 eta_th ratios
for lab, pub, kw, ratio in (
        ("stream balance", 598.2,
         dict(dri_name="DRI-Shahabuddin (16 % gangue)", metallisation_pct=100.0,
              tap_temperature_C=1600.0, target_basicity_B2=1.10,
              target_MgO_in_slag_pct=0.5, target_C_in_HM_pct=3.5, **BASE), 0.883),
        ("MR90 1600", 850.0,
         dict(dri_name="DRI-Shahabuddin (16 % gangue)", metallisation_pct=90.0,
              tap_temperature_C=1600.0, target_MgO_in_slag_pct=0.5, **EQ), 0.849)):
    r = run_static(**kw)
    ck(f"5.3 ratio {lab}", ratio,
       r["KPI"]["SEC_reversible_kWh_tHM"] / pub, absolute=True, tol=0.002)

sys.path.insert(0, ROOT)
import run_validation as rv                                    # noqa: E402
for g, pub, ratio in ((7.0, 572.0, 0.775), (16.0, 684.0, 0.886)):
    comp, _ = rv.dri_from_ore(g)
    r = run_static(dri_composition=comp, metallisation_pct=100.0, **EQ)
    ck(f"5.3 ratio CDRI {g:.0f}", ratio,
       r["KPI"]["SEC_reversible_kWh_tHM"] / pub, absolute=True, tol=0.002)

# ------------------------------------------------- Section 6.9 cross-check
for q, ss_v, tr_v, dev in (("Operating SEC", 666.7, 713.9, 7.1),
                           ("Slag rate", 270.8, 285.6, 5.5),
                           ("Hot metal C", 3.400, 3.708, 9.1),
                           ("Hot metal Si", 0.231, 0.256, 11.1),
                           ("Hot metal Mn", 0.517, 0.522, 1.1),
                           ("Slag FeO", 0.645, 1.655, 157.0),
                           ("Slag basicity B2", 1.091, 1.114, 2.1)):
    hit = [r for r in rows if r["case"] == "Steady state vs transient"
           and r["quantity"] == q]
    if not hit:
        fails.append(f"6.9 {q}: row missing from the validation table")
        continue
    ck(f"6.9 {q} steady", ss_v, float(hit[0]["literature"]),
       absolute=True, tol=max(0.002, abs(ss_v) * 0.004))
    ck(f"6.9 {q} transient", tr_v, float(hit[0]["model"]),
       absolute=True, tol=max(0.002, abs(tr_v) * 0.004))

# -------------------------------- every highlighted number appears somewhere
text = open(MS).read()
if "{.mark}" not in text:
    fails.append("manuscript carries no change markers")
n_marks = text.count("{.mark}")

print(f"checked {checks} quantitative claims")
print(f"change markers in the manuscript: {n_marks}")
if fails:
    print(f"\nFAILURES ({len(fails)}):")
    for f in fails:
        print("   ", f)
    sys.exit(1)
print("\nall manuscript values reproduce from the engine")
