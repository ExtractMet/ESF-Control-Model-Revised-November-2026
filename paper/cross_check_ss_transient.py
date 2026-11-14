#!/usr/bin/env python3
"""
Direct comparison of the steady-state and transient modules under identical
operating conditions.  Written for Reviewer 3 comment R3-1 and Reviewer 2
comment R2-4, both of which ask whether the two modules agree with each other
rather than only with the literature.

Procedure
---------
1. Solve the steady state at a fixed feed, metallisation and tapping
   temperature.  The steady state returns the carbon and flux demand.
2. Feed exactly those demands to the transient module and run it long enough
   for the bath to stop drifting.
3. Compare the stationary transient state against the steady-state solution.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from esf_dt.static_model import run_static
from esf_dt.dynamic_model import run_dynamic

DRI = "DRI-A (13.8 % gangue)"
MR = 94.0
TAP_C = 1500.0
B2 = 1.10
FEED_T_H = 160.0
C_IN_HM = 3.40


def main():
    # ---- 1. steady state -------------------------------------------------
    ss = run_static(dri_name=DRI, metallisation_pct=MR, tap_temperature_C=TAP_C,
                    target_basicity_B2=B2, target_C_in_HM_pct=C_IN_HM,
                    heat_loss_mode="fraction", heat_loss_fraction=0.10)
    k = ss["KPI"]

    # per tonne of DRI rather than per tonne of hot metal, which is what the
    # transient module is fed
    dri_kg = ss["inputs_kg"]["DRI"]
    hm_kg = ss["outputs_kg"]["Hot metal"]
    f = hm_kg / dri_kg                      # t HM per t DRI

    c_kg_t_dri = k["Carbon_charged_kg_tHM"] * f
    flux_kg_t_dri = k["Flux_rate_kg_tHM"] * f

    # the steady state reports a single flux demand; split it between the two
    # fluxes in the ratio the transient base case uses
    lime = flux_kg_t_dri * 73.0 / (73.0 + 36.0)
    dolo = flux_kg_t_dri * 36.0 / (73.0 + 36.0)

    print("=== steady state ===")
    print(f"  DRI {dri_kg:.1f} kg -> hot metal {hm_kg:.1f} kg  (f = {f:.4f})")
    print(f"  carbon charged   {c_kg_t_dri:8.2f} kg/t DRI")
    print(f"  flux demand      {flux_kg_t_dri:8.2f} kg/t DRI "
          f"(lime {lime:.2f}, dolo {dolo:.2f})")
    print(f"  SEC operating    {k['SEC_operating_kWh_tHM']:8.1f} kWh/tHM")
    print(f"  slag rate        {k['Slag_rate_kg_tHM']:8.1f} kg/tHM")
    for key in ("C", "Si", "Mn", "S", "P"):
        print(f"  HM {key:<3s}          {ss['hot_metal_wt_pct'][key]:8.4f} wt%")
    for key in ("FeO", "CaO", "SiO2", "MgO", "Al2O3", "MnO"):
        print(f"  slag {key:<5s}      {ss['slag_wt_pct'][key]:8.4f} wt%")
    print(f"  slag B2          {ss['slag_properties']['B2 (CaO/SiO2)']:8.4f}")

    # ---- 2. transient fed with the steady-state demands ------------------
    # long run so that the bath stops drifting; tap masses matched to feed
    dyn = run_dynamic(duration_min=1440.0, dt_s=10.0, log_every_s=300.0,
                      dri_name=DRI, metallisation_pct=MR,
                      dri_feed_t_h=FEED_T_H,
                      carbon_feed_kg_t_dri=c_kg_t_dri,
                      lime_feed_kg_t_dri=lime, dolo_feed_kg_t_dri=dolo,
                      target_metal_T_C=TAP_C, target_basicity_B2=B2,
                      power_MW=140.0,
                      metal_tap_interval_min=60.0,
                      metal_tap_mass_t=FEED_T_H * f,
                      slag_tap_interval_min=30.0,
                      slag_tap_mass_t=FEED_T_H * k["Slag_rate_kg_tHM"] / 1000.0 * f / 2.0)

    tr = dyn["trajectory"]
    last = {kk: vv[-1] for kk, vv in tr.items()} if isinstance(tr, dict) else None

    print("\n=== transient, stationary state after 24 h ===")
    print("  summary keys:", list(dyn["summary"].keys())[:40])
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "ss_transient_raw.json"), "w") as fh:
        json.dump({"steady": {"KPI": k,
                              "hot_metal_wt_pct": ss["hot_metal_wt_pct"],
                              "slag_wt_pct": ss["slag_wt_pct"],
                              "slag_properties": ss["slag_properties"]},
                   "dynamic_summary": dyn["summary"],
                   "feeds": {"carbon_kg_t_dri": c_kg_t_dri,
                             "lime_kg_t_dri": lime, "dolo_kg_t_dri": dolo,
                             "f_HM_per_DRI": f}},
                  fh, indent=1, default=str)
    for kk, vv in dyn["summary"].items():
        print(f"  {kk:44s} {vv}")


if __name__ == "__main__":
    main()
