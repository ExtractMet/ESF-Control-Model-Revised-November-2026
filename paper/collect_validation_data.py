#!/usr/bin/env python3
"""Collect every dataset needed for the validation workbook into one JSON."""
import sys, os, json, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from esf_dt.static_model import (run_static, DRI_LIBRARY, CARBON_LIBRARY,
                                 FLUX_LIBRARY, SCRAP_DEFAULT, ESFInputs)
from esf_dt.dynamic_model import run_dynamic, DynamicInputs
from esf_dt.geometry import (FurnaceGeometry, default_lining, REFRACTORY_DB,
                             heat_loss_network)
from esf_dt.electrical import ElectricalConfig
import esf_dt.properties as pr

B = dict(heat_loss_mode="fraction", heat_loss_fraction=0.10)
EQ = dict(B, silicon_mode="equilibrium")
D = {}

# ---- 1. libraries ------------------------------------------------------
D["dri"] = DRI_LIBRARY
D["carbon"] = CARBON_LIBRARY
D["flux"] = FLUX_LIBRARY
D["scrap"] = SCRAP_DEFAULT

# ---- 2. geometry, electrical, defaults --------------------------------
g, el, si, di = FurnaceGeometry(), ElectricalConfig(), ESFInputs(), DynamicInputs()
D["geometry"] = {k: v for k, v in vars(g).items() if not k.startswith("_")}
D["electrical_cfg"] = {k: v for k, v in vars(el).items() if not k.startswith("_")}
D["static_defaults"] = {k: v for k, v in vars(si).items()
                        if not k.startswith("_") and isinstance(v, (int, float, str, bool))}
D["dynamic_defaults"] = {k: v for k, v in vars(di).items()
                         if not k.startswith("_") and isinstance(v, (int, float, str, bool))}

# ---- 3. refractory -----------------------------------------------------
lin = default_lining()
D["lining"] = {z: [{"material": L.material, "thickness_mm": L.thickness * 1000}
                   for L in layers] for z, layers in lin.items()}
D["refractory_db"] = REFRACTORY_DB
D["cooling"] = {"hearth": "forced air", "metal_wall": "forced air",
                "slag_wall": "water", "freeboard": "water", "roof": "water"}

# ---- 4. lining solution ------------------------------------------------
slag_ref = {"SiO2": 36.9, "CaO": 40.6, "MgO": 8.0, "Al2O3": 13.9,
            "MnO": 0.3, "TiO2": 0.13, "CaS": 0.1}
hl = heat_loss_network(g, 1823.15, 1773.15, 1780.0, slag_ref)
D["lining_solution"] = {z: {"area_m2": v["area_m2"],
                            "q_kW_m2": v["q_flux_W_m2"] / 1e3,
                            "Q_MW": v["Q_W"] / 1e6,
                            "T_hotface_C": v["T_hotface_K"] - 273.15,
                            "T_shell_C": v["T_shell_K"] - 273.15,
                            "freeze_mm": v["freeze_thickness_m"] * 1000}
                        for z, v in hl["zones"].items()}
D["lining_total"] = {"Q_MW": hl["Q_total_W"] / 1e6,
                     "water_fraction_pct": hl["water_fraction"] * 100}

# ---- 5. validation table ----------------------------------------------
vt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "figures", "validation_table.csv")
D["validation_rows"] = list(csv.DictReader(open(vt)))
D["validation_stats"] = json.load(open(vt.replace("_table.csv", "_stats.json")))

# ---- 6. stream balance -------------------------------------------------
# Kinetic basis. The source reports 0.40 wt% Si at 1600 degC, which cannot be
# an equilibrium value for an endothermic reduction, so its silicon is itself
# kinetically limited and the like-for-like comparison is on the kinetic basis.
sh = run_static(dri_name="DRI-Shahabuddin (16 % gangue)", metallisation_pct=100.0,
                tap_temperature_C=1600.0, target_basicity_B2=1.10,
                target_MgO_in_slag_pct=0.5, target_C_in_HM_pct=3.5, **B)
D["stream_model"] = {"inputs_kg": sh["inputs_kg"], "outputs_kg": sh["outputs_kg"],
                     "hot_metal_wt_pct": sh["hot_metal_wt_pct"],
                     "slag_wt_pct": sh["slag_wt_pct"],
                     "offgas_kg": sh["offgas_kg"],
                     "SEC": sh["KPI"]["SEC_thermodynamic_kWh_tHM"],
                     "heat": sh["heat_balance_MJ_per_tHM"],
                     "closure": sh["closure"]}
# published values, Sabah et al. 2026 Table 3 (after Shahabuddin et al. 2024)
D["stream_lit"] = {
    "in_DRI_kg": 1189.9, "in_C_kg": 41.49, "in_fluxCaO_kg": 118.16,
    "out_HM_kg": 1055.0, "out_slag_kg": 283.83, "out_gas_kg": 10.66,
    "HM": {"Fe": 94.75, "S": 0.04, "Si": 0.40, "P": 0.10, "C": 3.50, "Mn": 1.20},
    "slag": {"SiO2": 37.75, "Al2O3": 20.45, "CaO": 41.63, "FeO": 0.17},
    "gas": {"CO": 99.95, "CO2": 0.05},
    "energy_kWh": 631.13, "SEC": 598.2}

# ---- 7. silicon --------------------------------------------------------
D["silicon"] = [[T,
                 run_static(tap_temperature_C=T, **EQ)["hot_metal_wt_pct"]["Si"],
                 run_static(tap_temperature_C=T, **B)["hot_metal_wt_pct"]["Si"]]
                for T in (1400, 1425, 1450, 1475, 1500, 1525, 1550, 1575, 1600)]
D["silicon_lit"] = {1400: "0.03", 1450: "0.10", 1500: "0.30-0.36",
                    1525: "0.62", 1550: "<0.5", 1600: "0.40"}

# ---- 8. sensitivities --------------------------------------------------
def sec(**k):
    return run_static(**dict(EQ, **k))["KPI"]["SEC_thermodynamic_kWh_tHM"]
D["sens"] = {
    "dSEC/dT per 25 degC": [(sec(tap_temperature_C=1525) - sec(tap_temperature_C=1400)) / 5, 20.0],
    "dSEC/dMR per 1 wt%": [(sec(metallisation_pct=100) - sec(metallisation_pct=80)) / 20, -12.0],
    "dSEC/dC per 1 wt%": [(sec(target_C_in_HM_pct=3.5) - sec(target_C_in_HM_pct=1.0)) / 2.5, 10.0],
    "dSEC/dgangue per 1 wt%": [(sec(dri_name="DRI-B (15.5 % gangue)")
                                - sec(dri_name="DRI-A (13.8 % gangue)")) / 1.72, 16.5],
    "dSEC/dscrap per 1 wt%": [(sec(dri_name="DRI-B (15.5 % gangue)", metallisation_pct=90,
                                   scrap_fraction_pct=60)
                               - sec(dri_name="DRI-B (15.5 % gangue)", metallisation_pct=90,
                                     scrap_fraction_pct=0)) / 60, -2.5]}
D["mr_sweep"] = [[m, sec(metallisation_pct=m)] for m in (80, 85, 90, 95, 100)]
D["scrap_sweep"] = [[s, sec(dri_name="DRI-B (15.5 % gangue)", metallisation_pct=90,
                            scrap_fraction_pct=s)] for s in (0, 20, 40, 60)]
D["scrap_lit"] = [677.4, 623.8, 569.6, 515.2]
D["grade_sweep"] = {d: sec(dri_name=d) for d in
                    ("DRI-A (13.8 % gangue)", "DRI-B (15.5 % gangue)", "DRI-C (16.0 % gangue)")}
D["grade_lit"] = {"DRI-A (13.8 % gangue)": 553.9, "DRI-B (15.5 % gangue)": 575.8,
                  "DRI-C (16.0 % gangue)": 575.5}
D["T_sweep"] = [[T, sec(dri_name="DRI-Shahabuddin (16 % gangue)", metallisation_pct=90,
                        tap_temperature_C=T, target_MgO_in_slag_pct=0.5)]
                for T in (1300, 1400, 1500, 1600)]
D["T_lit"] = {1300: 706.0, 1600: 850.0}

# ---- 9. industrial OSBF ------------------------------------------------
o = run_static(dri_name="DRI-OSBF (industrial reference)", metallisation_pct=97.0,
               tap_temperature_C=1500.0, target_C_in_HM_pct=4.5,
               target_basicity_B2=1.10, target_MgO_in_slag_pct=7.25, **B)
D["osbf_model"] = {"HM": o["hot_metal_wt_pct"], "slag": o["slag_wt_pct"],
                   "slag_rate": o["KPI"]["Slag_rate_kg_tHM"],
                   "valor": o["slag_valorisation"]}
# Sabah et al. 2026 Table 1 (after Belford et al. 2022)
# Exactly as printed in Sabah et al. 2026 Table 1, after Belford et al. 2022.
# Ranges are reproduced verbatim and are NOT widened; entries the source gives
# as a single value are held separately and compared numerically.
D["osbf_lit"] = {
    "HM": {"Si": (0.0, 0.50), "S": (0.025, 0.030),
           "P": (0.020, 0.030), "Fe": (94.7, 94.8)},
    "HM_single": {"C": 4.5, "Mn": 0.14},
    "slag": {"CaO": (40.5, 41.5), "SiO2": (36.5, 37.5), "MgO": (7.0, 7.5),
             "Al2O3": (10.5, 11.0), "FeO": (0.6, 0.7), "MnO": (0.20, 0.25)},
    "BF_HM": {"C": "4.5", "Si": "0.75", "Mn": "0.13-0.15", "S": "0.02-0.025",
              "P": "0.10-0.12", "Fe": "94.6-94.8"},
    "BF_slag": {"CaO": "41-43", "SiO2": "37-38", "MgO": "7.3-7.5",
                "Al2O3": "10.5-11.0", "FeO": "0.3-0.5", "MnO": "0.15-0.20"}}

# ---- 10. laboratory ----------------------------------------------------
bp = run_static(dri_name="H2-DRI-BP88 (88 % MR, lab)", target_C_in_HM_pct=3.0,
                tap_temperature_C=1550.0, **B)
dbp = run_dynamic(duration_min=180, dri_name="H2-DRI-BP88 (88 % MR, lab)",
                  metallisation_pct=88.0, carbon_feed_kg_t_dri=88.0,
                  lime_feed_kg_t_dri=40.0, dolo_feed_kg_t_dri=20.0, log_every_s=60)
D["lab"] = {"C_req_model": bp["KPI"]["Carbon_consumed_kg_tHM"], "C_req_lit": 66.0,
            "FeO_model": dbp["summary"]["Final slag FeO (wt%)"], "FeO_lit": 3.0,
            "HMC_model": dbp["summary"]["Final C (wt%)"], "HMC_lit": 2.8}

# ---- 11. base case, energy, dynamic -----------------------------------
gg = run_static(heat_loss_mode="geometry", productivity_tHM_h=143.0)
D["base_static"] = {"KPI": gg["KPI"], "inputs_kg": gg["inputs_kg"],
                    "outputs_kg": gg["outputs_kg"],
                    "HM": gg["hot_metal_wt_pct"], "slag": gg["slag_wt_pct"],
                    "offgas": gg["offgas_kg"], "heat": gg["heat_balance_MJ_per_tHM"],
                    "slagprop": gg["slag_properties"], "metalprop": gg["metal_properties"],
                    "elec": gg["electrical"], "closure": gg["closure"],
                    "valor": gg["slag_valorisation"], "temps": gg["temperatures_C"]}
dy = run_dynamic(duration_min=420, dt_s=10, log_every_s=60)
D["dyn_summary"] = dy["summary"]
T = dy["trajectory"]
keys = ["t_min", "T_metal_C", "T_slag_C", "power_MW", "m_metal_t", "m_slag_t",
        "C_pct", "Si_pct", "Mn_pct", "FeO_pct", "B2", "SEC_cum_kWh_t",
        "freeze_mm", "T_shell_C", "Q_loss_MW"]
step = max(1, len(T["t_min"]) // 85)
D["dyn_traj"] = {k: [T[k][i] for i in range(0, len(T["t_min"]), step)]
                 for k in keys if k in T}
D["dyn_events"] = [{kk: e.get(kk) for kk in ("t_min", "type", "message")}
                   for e in dy["events"]]

# ---- 12. iBlue envelope ------------------------------------------------
D["iblue"] = {"SEC_model": gg["KPI"]["SEC_operating_kWh_tHM"], "SEC_lit": (500, 1200),
              "ratio_model": o["KPI"]["Slag_rate_kg_tHM"] / 1000.0, "ratio_lit": (0.07, 0.25)}

# ---- 13. slag property maps -------------------------------------------
sw = gg["slag_wt_pct"]
D["slag_props_vs_T"] = [[T_, pr.slag_viscosity(sw, T_ + 273.15),
                         pr.slag_conductivity_elec(sw, T_ + 273.15),
                         pr.slag_density(sw, T_ + 273.15), pr.slag_liquidus(sw) - 273.15]
                        for T_ in (1400, 1450, 1500, 1550, 1600)]

json.dump(D, open("/tmp/wb_data.json", "w"), indent=1, default=str)
print("collected. validation rows:", len(D["validation_rows"]),
      "| dyn points:", len(D["dyn_traj"]["t_min"]),
      "| events:", len(D["dyn_events"]))
