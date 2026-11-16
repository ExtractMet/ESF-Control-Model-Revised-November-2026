#!/usr/bin/env python3
"""
ESF-DT :: esf_streamlit.py
==========================
Full web workbench for the Electric Smelting Furnace digital twin.

    streamlit run gui/esf_streamlit.py

Thirteen work areas: schematic, static mass/energy balances, slag and metal
properties, refractory and heat loss, electrical, parametric studies,
dynamic setup and trajectories, event log, validation, economics and help.

(c) Extractmet Private Limited.  Reference plant anonymised as Industry-X.
"""

from __future__ import annotations

import io
import os
import sys
import time

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from esf_dt import __version__, PRODUCT, VENDOR
from esf_dt import thermo as th
from esf_dt import properties as pr
from esf_dt.static_model import (run_static, DRI_LIBRARY, FLUX_LIBRARY,
                                 CARBON_LIBRARY, SCRAP_DEFAULT)
from esf_dt.dynamic_model import run_dynamic, Schedule
from esf_dt.geometry import FurnaceGeometry, heat_loss_network, default_lining
from esf_dt.electrical import ElectricalConfig, solve_electrical
from esf_dt.schematic import furnace_svg, state_from_static, state_from_dynamic

PAL = ["#1f4e79", "#c1121f", "#2a9d8f", "#e07a5f", "#6a4c93",
       "#f4a261", "#264653", "#8ab17d", "#b5179e", "#457b9d"]
plt.rcParams.update({"figure.dpi": 110, "font.size": 9, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linestyle": ":",
                     "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "figure.autolayout": True})

st.set_page_config(page_title=f"{PRODUCT} - Electric Smelting Furnace "
                              f"digital twin", layout="wide",
                   initial_sidebar_state="expanded")


# ==========================================================================
# helpers
# ==========================================================================
def fig(w=6.2, h=3.6):
    return plt.subplots(figsize=(w, h))


def show(f):
    st.pyplot(f, clear_figure=True)
    plt.close(f)


def df_from(d, name="value", idx="quantity"):
    return pd.DataFrame({idx: list(d.keys()), name: list(d.values())})


def dl(df, label, fname):
    st.download_button(label, df.to_csv(index=False).encode(),
                       file_name=fname, mime="text/csv")


def _package_root() -> str:
    """
    Locate the ESF-DT package root.

    Depending on how Streamlit was launched - from the package root, from
    inside gui/, or from a copy of the script placed somewhere else - the
    script directory is not a reliable anchor. Try the sensible candidates
    and pick the first that actually looks like the package.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.path.dirname(here), here, os.getcwd(),
                  os.path.dirname(os.getcwd()),
                  os.path.dirname(os.path.dirname(here))]
    for c in candidates:
        if os.path.isdir(os.path.join(c, "esf_dt")) or \
                os.path.isfile(os.path.join(c, "run_validation.py")):
            return c
    for c in candidates:
        if os.path.isdir(os.path.join(c, "figures")):
            return c
    return os.path.dirname(here)


PKG_ROOT = _package_root()


def figures_dir() -> str:
    """The figures directory, preferring one that already has results."""
    for c in (os.path.join(PKG_ROOT, "figures"),
              os.path.join(os.getcwd(), "figures")):
        if os.path.isfile(os.path.join(c, "validation_table.csv")):
            return c
    return os.path.join(PKG_ROOT, "figures")


def svg_block(svg, height=800):
    st.components.v1.html(
        f'<div style="background:#f7f8fa;overflow:auto">{svg}</div>',
        height=height, scrolling=True)


# ==========================================================================
# sidebar - inputs
# ==========================================================================
st.sidebar.title(f"{PRODUCT}  v{__version__}")
st.sidebar.caption(f"{VENDOR} - Electric Smelting Furnace digital twin")

with st.sidebar.expander("1. Feed materials", expanded=True):
    dri_name = st.selectbox("DRI grade", list(DRI_LIBRARY),
                            help="Reference DRI grades from published "
                                 "hydrogen-DRI smelting studies.")
    custom_dri = st.checkbox("Edit DRI composition")
    dri_comp = dict(DRI_LIBRARY[dri_name])
    if custom_dri:
        edit = st.data_editor(
            pd.DataFrame({"species": list(dri_comp),
                          "wt%": list(dri_comp.values())}),
            hide_index=True, width="stretch", key="dri_edit")
        dri_comp = {r["species"]: float(r["wt%"]) for _, r in edit.iterrows()}
    MR = st.slider("Metallisation ratio (%)", 70.0, 100.0, 94.0, 0.5)
    T_dri = st.slider("DRI charging temperature (degC)", 25.0, 800.0, 600.0,
                      25.0)
    scrap_pct = st.slider("Scrap in metallic charge (wt%)", 0.0, 60.0, 0.0,
                          5.0)
    carbon_source = st.selectbox("Carburiser", list(CARBON_LIBRARY))
    flux1 = st.selectbox("Primary flux", list(FLUX_LIBRARY), index=0)
    flux2 = st.selectbox("Secondary flux", list(FLUX_LIBRARY), index=1)

with st.sidebar.expander("2. Product targets", expanded=True):
    T_tap = st.slider("Hot-metal tapping temperature (degC)", 1380.0, 1560.0,
                      1500.0, 5.0)
    C_target = st.slider("Target [C] in hot metal (wt%)", 0.5, 4.5, 3.5, 0.1)
    B2_target = st.slider("Target slag basicity B2", 0.7, 1.6, 1.10, 0.02)
    MgO_target = st.slider("Target slag MgO (wt%)", 4.0, 14.0, 8.0, 0.5)
    dT_slag = st.slider("Slag superheat above metal (K)", 20.0, 120.0, 60.0,
                        5.0)
    T_gas = st.slider("Off-gas temperature (degC)", 900.0, 1800.0, 1450.0,
                      25.0)

with st.sidebar.expander("3. Furnace geometry"):
    L = st.number_input("Hearth length (m)", 8.0, 60.0, 35.0, 0.5)
    Wd = st.number_input("Hearth width (m)", 4.0, 20.0, 11.0, 0.5)
    n_el = st.number_input("Number of electrodes", 3, 9, 6, 1)
    d_el = st.number_input("Electrode diameter (m)", 0.6, 2.2, 1.70, 0.05)
    pitch = st.number_input("Electrode pitch (m)", 1.5, 8.0, 4.60, 0.1)
    imm = st.number_input("Electrode immersion (m)", 0.05, 1.20, 0.45, 0.01)
    arc_len = st.number_input("Brush-arc length (m)", 0.0, 0.30, 0.09, 0.01)
    d_slag = st.number_input("Slag depth (m)", 0.4, 2.5, 1.35, 0.05)
    d_metal = st.number_input("Metal depth (m)", 0.3, 2.0, 0.90, 0.05)
    fb_h = st.number_input("Freeboard height (m)", 1.0, 6.0, 3.2, 0.1)

with st.sidebar.expander("4. Electrical system"):
    V_sec = st.number_input("Secondary (tap) voltage, nominal (V)",
                            150.0, 900.0, 420.0, 10.0)
    pf = st.number_input("Power factor", 0.60, 0.98, 0.86, 0.01)
    eta_el = st.number_input("Electrical-to-bath efficiency", 0.70, 0.99,
                             0.90, 0.01)
    si_mode = st.radio("Silicon basis", ["kinetic", "equilibrium"], index=0,
                       help="Equilibrium silicon rises steeply with "
                            "temperature and, above about 1525 degC, far "
                            "exceeds what an ESF actually taps. 'kinetic' "
                            "applies the limitation measured under ESF "
                            "conditions; 'equilibrium' reproduces what an "
                            "equilibrium code reports.")
    si_ceiling = st.slider("Silicon kinetic ceiling (wt%)", 0.20, 1.20, 0.45,
                           0.05)
    feo_floor = st.slider("Residual slag FeO (wt%)", 0.0, 3.0, 0.65, 0.05,
                          help="Equilibrium FeO is essentially nil at ESF "
                               "carbon levels; industrial open-bath slag is "
                               "reported at 0.6-0.7 wt%.")
    eta_th = st.number_input("Thermal utilisation (reporting basis)",
                             0.60, 1.00, 1.00, 0.01,
                             help="Only used to express SEC on the same "
                                  "basis as published equilibrium-code "
                                  "figures; see VALIDATION.md.")

with st.sidebar.expander("5. Heat-loss model"):
    hl_mode = st.radio("Mode", ["geometry", "fraction"], index=0,
                       help="'geometry' solves the coupled conduction / "
                            "convection / radiation lining network; "
                            "'fraction' applies a fixed loss share.")
    hl_frac = st.slider("Loss fraction (fraction mode)", 0.02, 0.40, 0.10,
                        0.01)
    prod = st.number_input("Design productivity (tHM/h)", 5.0, 400.0, 143.0,
                           1.0)

with st.sidebar.expander("6. Economics"):
    p_power = st.number_input("Power price (USD/MWh)", 5.0, 250.0, 55.0, 1.0)
    p_carbon = st.number_input("Carburiser price (USD/t)", 50.0, 900.0, 320.0,
                               5.0)
    p_lime = st.number_input("Flux price (USD/t)", 20.0, 400.0, 95.0, 5.0)
    p_electrode = st.number_input("Electrode paste price (USD/t)", 200.0,
                                  4000.0, 1150.0, 50.0)
    grid_ef = st.number_input("Grid emission factor (kgCO2/MWh)", 0.0, 1200.0,
                              120.0, 10.0)

geo = FurnaceGeometry(length=L, width=Wd, n_electrodes=int(n_el),
                      electrode_diameter=d_el, electrode_pitch=pitch,
                      electrode_immersion=imm, arc_length=arc_len,
                      slag_depth=d_slag, metal_depth=d_metal,
                      freeboard_height=fb_h)
elec = ElectricalConfig(n_electrodes=int(n_el), electrode_diameter_m=d_el,
                        secondary_voltage_V=V_sec, power_factor=pf)

STATIC_KW = dict(
    dri_name=dri_name, dri_composition=(dri_comp if custom_dri else {}),
    metallisation_pct=MR, dri_temperature_C=T_dri,
    scrap_fraction_pct=scrap_pct, carbon_source=carbon_source,
    flux_primary=flux1, flux_secondary=flux2,
    tap_temperature_C=T_tap, target_C_in_HM_pct=C_target,
    target_basicity_B2=B2_target, target_MgO_in_slag_pct=MgO_target,
    slag_superheat_C=dT_slag, offgas_temperature_C=T_gas,
    heat_loss_mode=hl_mode, heat_loss_fraction=hl_frac,
    productivity_tHM_h=prod, electrical_to_bath_efficiency=eta_el,
    thermal_utilisation_efficiency=eta_th,
    silicon_mode=si_mode, silicon_ceiling_wt_pct=si_ceiling,
    residual_FeO_floor_wt_pct=feo_floor,
    power_price_USD_MWh=p_power, carbon_price_USD_t=p_carbon,
    lime_price_USD_t=p_lime, electrode_price_USD_t=p_electrode,
    grid_emission_factor_kgCO2_MWh=grid_ef,
    geometry=geo, electrical=elec,
)


@st.cache_data(show_spinner=False)
def _static(kw_key, **kw):
    return run_static(**kw)


with st.spinner("Solving the static heat and mass balance..."):
    try:
        R = run_static(**STATIC_KW)
    except ValueError as exc:
        # An impossible configuration must stop here rather than render a
        # furnace nobody could operate.
        st.error(f"**Configuration rejected.**  {exc}")
        st.stop()

K = R["KPI"]
for _w in R.get("warnings", []):
    st.warning(_w)

# ==========================================================================
TABS = st.tabs([
    "Overview & schematic", "Mass balance", "Energy balance",
    "Slag & metal", "Refractory & heat loss", "Electrical",
    "Parametric studies", "Dynamic setup", "Dynamic trajectories",
    "Event log", "Validation", "Economics & CO2", "Help",
])

# --------------------------------------------------------------------------
with TABS[0]:
    st.subheader("Live process schematic")
    c = st.columns(6)
    c[0].metric("SEC (operating)", f"{K['SEC_operating_kWh_tHM']:.0f} kWh/tHM")
    c[1].metric("Power demand", f"{K['Power_demand_MW']:.1f} MW")
    c[2].metric("Slag rate", f"{K['Slag_rate_kg_tHM']:.0f} kg/tHM")
    c[3].metric("Carbon", f"{K['Carbon_consumed_kg_tHM']:.1f} kg/tHM")
    c[4].metric("Fe yield", f"{K['Fe_yield_pct']:.2f} %")
    c[5].metric("Closure error", f"{R['closure']['max_abs_error_pct']:.2f} %")
    st_state = state_from_static(R, geo)
    st_state["electrode_dia_m"] = d_el
    svg = furnace_svg(st_state)
    svg_block(svg, 820)
    st.download_button("Download schematic (SVG)", svg.encode(),
                       file_name="esf_schematic.svg", mime="image/svg+xml")
    st.caption("Every dimension, colour and number in the drawing is taken "
               "from the current solution: bath depths, electrode immersion, "
               "brush-arc length, freeze-lining thickness, temperatures, "
               "compositions and the power split.")

    st.markdown("#### Furnace envelope")
    st.dataframe(df_from(R["geometry"]), hide_index=True,
                 width="stretch")

# --------------------------------------------------------------------------
with TABS[1]:
    st.subheader("Charge, products and elemental closure")
    a, b = st.columns(2)
    with a:
        st.markdown("**Inputs (kg per 1000 kg Fe basis)**")
        din = df_from(R["inputs_kg"], "kg", "stream")
        st.dataframe(din, hide_index=True, width="stretch")
        dl(din, "Download inputs", "esf_inputs.csv")
    with b:
        st.markdown("**Outputs (kg)**")
        dout = df_from(R["outputs_kg"], "kg", "stream")
        st.dataframe(dout, hide_index=True, width="stretch")
        dl(dout, "Download outputs", "esf_outputs.csv")

    a, b, c = st.columns(3)
    with a:
        st.markdown("**Hot metal**")
        hm = pd.DataFrame({"element": list(R["hot_metal_wt_pct"]),
                           "wt%": list(R["hot_metal_wt_pct"].values()),
                           "kg": [R["hot_metal_kg"].get(k, 0.0)
                                  for k in R["hot_metal_wt_pct"]]})
        st.dataframe(hm, hide_index=True, width="stretch")
    with b:
        st.markdown("**Tapped slag**")
        sl = pd.DataFrame({"oxide": list(R["slag_wt_pct"]),
                           "wt%": list(R["slag_wt_pct"].values()),
                           "kg": [R["slag_kg"].get(k, 0.0)
                                  for k in R["slag_wt_pct"]]})
        st.dataframe(sl, hide_index=True, width="stretch")
    with c:
        st.markdown("**Off-gas**")
        og = pd.DataFrame({"species": list(R["offgas_kg"]),
                           "kg": list(R["offgas_kg"].values()),
                           "vol%": [R["offgas_vol_pct"].get(k, 0.0)
                                    for k in R["offgas_kg"]]})
        st.dataframe(og, hide_index=True, width="stretch")
        st.markdown("**Dust / unreacted carbon**")
        st.dataframe(df_from(R["dust_kg"], "kg", "species"), hide_index=True,
                     width="stretch")

    st.markdown("**Element-by-element closure (%)**")
    clo = pd.DataFrame({"element": list(R["closure"]),
                        "error %": [float(v) for v in R["closure"].values()]})
    st.dataframe(clo, hide_index=True, width="stretch")

    f, ax = fig(11, 3.6)
    ins = {k: v for k, v in R["inputs_kg"].items() if k != "Total charge"}
    ax.bar(list(ins), list(ins.values()), color=PAL[0], label="in")
    ax.bar([k + " " for k in R["outputs_kg"]], list(R["outputs_kg"].values()),
           color=PAL[1], label="out")
    ax.set_ylabel("kg")
    ax.tick_params(axis="x", rotation=20)
    ax.legend()
    ax.set_title("Charge and product masses")
    show(f)

# --------------------------------------------------------------------------
with TABS[2]:
    st.subheader("Heat balance")
    hb = R["heat_balance_MJ_per_tHM"]
    a, b = st.columns([1, 1])
    with a:
        d = df_from(hb, "MJ/tHM", "term")
        st.dataframe(d, hide_index=True, width="stretch",
                     height=430)
        dl(d, "Download heat balance", "esf_heat_balance.csv")
    with b:
        items = ["  Hot metal sensible+fusion", "  Hot metal dissolution",
                 "  Slag sensible (to liquidus)", "  Slag latent (solution)",
                 "  Slag superheat", "Refractory + shell loss"]
        vals = [abs(hb.get(k, 0.0)) for k in items]
        f, ax = fig(6.4, 4.2)
        bars = ax.barh([k.strip() for k in items], vals, color=PAL[:len(items)])
        for bb, v in zip(bars, vals):
            ax.text(v + max(vals) * 0.01, bb.get_y() + bb.get_height() / 2,
                    f"{v:.0f}", va="center", fontsize=8)
        ax.set_xlabel("MJ per tonne of hot metal")
        ax.set_title("Where the energy goes")
        show(f)

    c = st.columns(4)
    c[0].metric("SEC reversible", f"{K['SEC_reversible_kWh_tHM']:.0f}")
    c[1].metric("SEC equilibrium basis",
                f"{K['SEC_thermodynamic_kWh_tHM']:.0f}")
    c[2].metric("SEC operating", f"{K['SEC_operating_kWh_tHM']:.0f}")
    c[3].metric("Lining loss", f"{K['Heat_loss_kWh_tHM']:.0f} kWh/tHM")
    st.info("**SEC reversible** is the pure thermodynamic requirement. "
            "**SEC equilibrium basis** divides it by the thermal-utilisation "
            "factor so it can be compared like-for-like with published "
            "FactSage and HSC figures. **SEC operating** adds the lining "
            "losses and the electrical-to-bath efficiency and is what the "
            "transformer must deliver.")

    st.markdown("**Temperatures assumed (degC)**")
    st.dataframe(df_from(R["temperatures_C"], "degC", "stream"),
                 hide_index=True, width="stretch")

# --------------------------------------------------------------------------
with TABS[3]:
    st.subheader("Slag and hot-metal physical chemistry")
    a, b = st.columns(2)
    with a:
        st.markdown("**Slag**")
        st.dataframe(df_from(R["slag_properties"], "value", "property"),
                     hide_index=True, width="stretch", height=430)
    with b:
        st.markdown("**Hot metal**")
        st.dataframe(df_from(R["metal_properties"], "value", "property"),
                     hide_index=True, width="stretch", height=430)

    st.markdown("#### Slag valorisation - reuse as a cementitious material")
    v = R["slag_valorisation"]
    cv = st.columns(4)
    cv[0].metric("Suitability score",
                 f"{v['Cement suitability score (0-100)']:.0f}", v["Verdict"])
    cv[1].metric("Basicity B2", f"{v['B2 (CaO/SiO2)']:.2f}", "target 0.85-1.30")
    cv[2].metric("Slag FeO", f"{v['FeO (wt%)']:.2f} wt%", "target < 2")
    cv[3].metric("Free MgO risk", v["Free MgO risk"],
                 f"MgO {v['MgO (wt%)']:.1f} vs sat "
                 f"{v['Estimated MgO saturation (wt%)']:.1f} wt%")
    for _n in v["Notes"]:
        st.warning(_n)
    st.caption("The commercial case for the ESF route rests partly on its "
               "slag being usable in cement, which blast-furnace slag "
               "already is and a high-basicity foaming EAF slag is not.")

    st.markdown("#### Property maps at the current slag composition")
    Ts_ = np.linspace(1350, 1650, 60)
    sw = R["slag_wt_pct"]
    f, axs = plt.subplots(1, 4, figsize=(14, 3.3))
    axs[0].plot(Ts_, [pr.slag_viscosity(sw, t + 273.15) for t in Ts_],
                color=PAL[0])
    axs[0].set(xlabel="T (degC)", ylabel="Pa.s", title="Viscosity")
    axs[1].plot(Ts_, [pr.slag_conductivity_elec(sw, t + 273.15) for t in Ts_],
                color=PAL[1])
    axs[1].set(xlabel="T (degC)", ylabel="S/m", title="Electrical conductivity")
    axs[2].plot(Ts_, [pr.slag_density(sw, t + 273.15) for t in Ts_],
                color=PAL[2])
    axs[2].set(xlabel="T (degC)", ylabel="kg/m3", title="Density")
    axs[3].plot(Ts_, [pr.slag_thermal_conductivity(sw, t + 273.15)
                      for t in Ts_], color=PAL[3])
    axs[3].set(xlabel="T (degC)", ylabel="W/m/K", title="Thermal conductivity")
    for ax in axs:
        ax.axvline(R["temperatures_C"]["Slag"], color="grey", ls="--", lw=0.8)
    show(f)

    st.markdown("#### Equilibrium partition at the current state")
    Ts2 = np.linspace(1400, 1560, 40)
    mw = R["hot_metal_wt_pct"]
    f, axs = plt.subplots(1, 3, figsize=(12, 3.3))
    axs[0].plot(Ts2, [th.si_equilibrium(sw, mw, t + 273.15, 1.0) for t in Ts2],
                color=PAL[0])
    axs[0].axhline(mw.get("Si", 0), color=PAL[1], ls="--", label="current")
    axs[0].set(xlabel="T (degC)", ylabel="wt%", title="[Si] equilibrium")
    axs[0].legend(fontsize=8)
    axs[1].plot(Ts2, [th.mn_equilibrium(sw, mw, t + 273.15, 1.0) for t in Ts2],
                color=PAL[2])
    axs[1].axhline(mw.get("Mn", 0), color=PAL[1], ls="--")
    axs[1].set(xlabel="T (degC)", ylabel="wt%", title="[Mn] equilibrium")
    axs[2].plot(Ts2, [th.carbon_saturation(t, mw) for t in Ts2], color=PAL[4])
    axs[2].axhline(mw.get("C", 0), color=PAL[1], ls="--")
    axs[2].set(xlabel="T (degC)", ylabel="wt%", title="Carbon saturation")
    show(f)

# --------------------------------------------------------------------------
with TABS[4]:
    st.subheader("Refractory design and heat loss")
    hl = R["heat_loss"]
    if hl is None:
        st.warning("Switch the heat-loss model to **geometry** in the sidebar "
                   "to solve the lining network.")
    else:
        c = st.columns(4)
        c[0].metric("Total lining loss", f"{hl['Q_total_W']/1e6:.1f} MW")
        c[1].metric("To cooling water",
                    f"{100*hl['water_fraction']:.0f} %")
        c[2].metric("Freeze lining",
                    f"{hl['freeze_thickness_m']*1000:.0f} mm")
        c[3].metric("Max shell T", f"{hl['T_shell_max_K']-273.15:.0f} degC")

        rows = []
        for z, v in hl["zones"].items():
            rows.append({"zone": z, "area (m2)": v["area_m2"],
                         "q (kW/m2)": v["q_flux_W_m2"] / 1e3,
                         "Q (MW)": v["Q_W"] / 1e6,
                         "hot face (degC)": v["T_hotface_K"] - 273.15,
                         "shell (degC)": v["T_shell_K"] - 273.15,
                         "freeze (mm)": v["freeze_thickness_m"] * 1000.0})
        dz = pd.DataFrame(rows)
        st.dataframe(dz, hide_index=True, width="stretch")
        dl(dz, "Download zone losses", "esf_heat_loss_zones.csv")

        f, axs = plt.subplots(1, 2, figsize=(12, 4))
        for j, (z, v) in enumerate(hl["zones"].items()):
            xs, x = [0.0], 0.0
            for _, t_ in v["layers"]:
                x += t_
                xs.append(x)
            axs[0].plot(np.array(xs) * 1000,
                        np.array(v["T_nodes_K"]) - 273.15, "-o", ms=3,
                        color=PAL[j], label=z)
        axs[0].set(xlabel="distance from hot face (mm)",
                   ylabel="temperature (degC)",
                   title="Through-lining temperature profiles")
        axs[0].legend(fontsize=8)
        axs[1].bar(list(hl["zones"]),
                   [v["Q_W"] / 1e6 for v in hl["zones"].values()],
                   color=PAL[:len(hl["zones"])])
        axs[1].set(ylabel="MW", title="Zone heat losses")
        axs[1].tick_params(axis="x", rotation=20)
        show(f)

        st.markdown("#### Freeze-lining sensitivity")
        Tsl = np.linspace(R["temperatures_C"]["Slag"] - 70,
                          R["temperatures_C"]["Slag"] + 70, 30)
        fz = [heat_loss_network(geo, t + 273.15, t + 253.15, t + 273.15,
                                R["slag_wt_pct"])["freeze_thickness_m"] * 1e3
              for t in Tsl]
        f, ax = fig(6.4, 3.4)
        ax.plot(Tsl, fz, color=PAL[0], lw=2)
        ax.axvline(R["temperatures_C"]["Slag"], color="grey", ls="--")
        ax.set(xlabel="slag temperature (degC)",
               ylabel="freeze-lining thickness (mm)",
               title="Protective skull vs bath temperature")
        show(f)

        st.markdown("#### Lining stack")
        lay = []
        for z, layers in default_lining().items():
            for l_ in layers:
                lay.append({"zone": z, "material": l_.material,
                            "thickness (mm)": l_.thickness * 1000})
        st.dataframe(pd.DataFrame(lay), hide_index=True,
                     width="stretch", height=320)
        if R.get("lining_life"):
            st.markdown("#### Lining life index")
            st.dataframe(df_from(R["lining_life"], "value", "indicator"),
                         hide_index=True, width="stretch")

# --------------------------------------------------------------------------
with TABS[5]:
    st.subheader("Electrical operating point")
    el = R["electrical"]
    c = st.columns(5)
    c[0].metric("Active power", f"{el['P_total_MW']:.1f} MW")
    c[1].metric("Current", f"{el['current_A']/1000:.1f} kA")
    c[2].metric("Tap voltage", f"{el['tap_voltage_V']:.0f} V")
    c[3].metric("Resistance", f"{el['operating_resistance_mohm']:.2f} mOhm")
    c[4].metric("Slag conductivity", f"{el['sigma_slag_S_m']:.1f} S/m")
    st.dataframe(df_from(el, "value", "quantity"), hide_index=True,
                 width="stretch", height=430)

    st.markdown("#### Operating characteristics")
    immv = np.linspace(0.10, min(0.9, 0.75 * d_slag), 40)
    f, axs = plt.subplots(1, 3, figsize=(13, 3.4))
    for j, dT in enumerate((-60.0, 0.0, 60.0)):
        Tsl = R["temperatures_C"]["Slag"] + 273.15 + dT
        P, Rr, I = [], [], []
        for m in immv:
            e = solve_electrical(elec, R["slag_wt_pct"], Tsl, float(m),
                                 arc_len, pitch, d_slag,
                                 tap_voltage_V=el["tap_voltage_V"])
            P.append(e["P_total_MW"])
            Rr.append(e["operating_resistance_mohm"])
            I.append(e["current_A"] / 1000)
        lab = f"T_slag {Tsl-273.15:.0f} degC"
        axs[0].plot(immv, P, color=PAL[j], label=lab)
        axs[1].plot(immv, Rr, color=PAL[j], label=lab)
        axs[2].plot(immv, I, color=PAL[j], label=lab)
    axs[0].set(xlabel="immersion (m)", ylabel="MW", title="Power")
    axs[1].set(xlabel="immersion (m)", ylabel="mOhm", title="Resistance")
    axs[2].set(xlabel="immersion (m)", ylabel="kA", title="Current")
    for ax in axs:
        ax.axvline(imm, color="grey", ls="--", lw=0.8)
        ax.legend(fontsize=7.5)
    show(f)

# --------------------------------------------------------------------------
with TABS[6]:
    st.subheader("Parametric studies")
    var = st.selectbox("Sweep variable", [
        "Metallisation ratio (%)", "Tapping temperature (degC)",
        "Target [C] in hot metal (wt%)", "Target basicity B2",
        "Scrap fraction (wt%)", "DRI charging temperature (degC)",
        "Target slag MgO (wt%)"])
    lo, hi, n = st.columns(3)
    defaults = {"Metallisation ratio (%)": (80.0, 100.0),
                "Tapping temperature (degC)": (1420.0, 1540.0),
                "Target [C] in hot metal (wt%)": (1.0, 4.2),
                "Target basicity B2": (0.8, 1.5),
                "Scrap fraction (wt%)": (0.0, 60.0),
                "DRI charging temperature (degC)": (25.0, 750.0),
                "Target slag MgO (wt%)": (4.0, 13.0)}
    v0 = lo.number_input("from", value=defaults[var][0])
    v1 = hi.number_input("to", value=defaults[var][1])
    npt = int(n.number_input("points", 5, 40, 15, 1))

    key = {"Metallisation ratio (%)": "metallisation_pct",
           "Tapping temperature (degC)": "tap_temperature_C",
           "Target [C] in hot metal (wt%)": "target_C_in_HM_pct",
           "Target basicity B2": "target_basicity_B2",
           "Scrap fraction (wt%)": "scrap_fraction_pct",
           "DRI charging temperature (degC)": "dri_temperature_C",
           "Target slag MgO (wt%)": "target_MgO_in_slag_pct"}[var]

    if st.button("Run sweep", type="primary"):
        xs = np.linspace(v0, v1, npt)
        rows = []
        bar = st.progress(0.0)
        for i2, x in enumerate(xs):
            kw = dict(STATIC_KW)
            kw[key] = float(x)
            rr = run_static(**kw)
            rows.append({
                var: x,
                "SEC reversible (kWh/tHM)": rr["KPI"]["SEC_reversible_kWh_tHM"],
                "SEC equilibrium (kWh/tHM)": rr["KPI"]["SEC_thermodynamic_kWh_tHM"],
                "SEC operating (kWh/tHM)": rr["KPI"]["SEC_operating_kWh_tHM"],
                "Slag rate (kg/tHM)": rr["KPI"]["Slag_rate_kg_tHM"],
                "Carbon (kg/tHM)": rr["KPI"]["Carbon_consumed_kg_tHM"],
                "Flux (kg/tHM)": rr["KPI"]["Flux_rate_kg_tHM"],
                "[Si] (wt%)": rr["hot_metal_wt_pct"].get("Si", 0),
                "[Mn] (wt%)": rr["hot_metal_wt_pct"].get("Mn", 0),
                "[S] (wt%)": rr["hot_metal_wt_pct"].get("S", 0),
                "(FeO) (wt%)": rr["slag_wt_pct"].get("FeO", 0),
                "Slag viscosity (Pa.s)": rr["slag_properties"]["Viscosity (Pa.s)"],
                "Slag liquidus (degC)": rr["slag_properties"]["Liquidus (degC)"],
                "Power (MW)": rr["KPI"]["Power_demand_MW"],
                "OPEX (USD/tHM)": rr["KPI"]["Specific_OPEX_USD_tHM"],
                "CO2 total (t/tHM)": rr["KPI"]["CO2_total_t_tHM"],
            })
            bar.progress((i2 + 1) / len(xs))
        d = pd.DataFrame(rows)
        st.session_state["sweep"] = d
    if "sweep" in st.session_state:
        d = st.session_state["sweep"]
        st.dataframe(d, hide_index=True, width="stretch", height=300)
        dl(d, "Download sweep", "esf_sweep.csv")
        cols = [c for c in d.columns[1:]]
        sel = st.multiselect("Plot", cols, default=cols[:4])
        if sel:
            f, axs = plt.subplots(1, len(sel), figsize=(3.4 * len(sel), 3.2))
            axs = np.atleast_1d(axs)
            for j, cname in enumerate(sel):
                axs[j].plot(d[d.columns[0]], d[cname], "-o", ms=3,
                            color=PAL[j % len(PAL)])
                axs[j].set(xlabel=d.columns[0], title=cname)
            show(f)

# --------------------------------------------------------------------------
with TABS[7]:
    st.subheader("Dynamic simulation setup")
    a, b, c = st.columns(3)
    with a:
        dur = st.number_input("Duration (min)", 30, 1440, 420, 30)
        dt = st.number_input("Time step (s)", 2.0, 60.0, 10.0, 1.0)
        logs = st.number_input("Log interval (s)", 10.0, 600.0, 60.0, 10.0)
        pwr_ctrl = st.selectbox("Power control",
                                ["temperature", "fixed", "schedule"])
        P_rated = st.number_input("Rated active power (MW)", 5.0, 300.0,
                                  116.0, 1.0)
        T_set = st.number_input("Hot-metal setpoint (degC)", 1400.0, 1560.0,
                                1500.0, 5.0)
    with b:
        dri_rate = st.number_input("DRI feed (t/h)", 5.0, 500.0, 160.0, 5.0)
        scrap_rate = st.number_input("Scrap feed (t/h)", 0.0, 200.0, 0.0, 5.0)
        c_rate = st.number_input("Carburiser (kg/t DRI)", 10.0, 150.0, 55.0,
                                 1.0)
        lime_rate = st.number_input("Primary flux (kg/t DRI)", 0.0, 200.0,
                                    73.0, 1.0)
        dolo_rate = st.number_input("Secondary flux (kg/t DRI)", 0.0, 150.0,
                                    36.0, 1.0)
        pcr = st.slider("Post-combustion ratio", 0.0, 0.6, 0.15, 0.01)
    with c:
        m_int = st.number_input("Metal tap interval (min)", 10.0, 240.0, 60.0,
                                5.0)
        m_mass = st.number_input("Metal tap mass (t)", 5.0, 400.0, 150.0, 5.0)
        m_dur = st.number_input("Metal tap duration (min)", 2.0, 60.0, 12.0,
                                1.0)
        s_int = st.number_input("Slag tap interval (min)", 5.0, 180.0, 30.0,
                                5.0)
        s_mass = st.number_input("Slag tap mass (t)", 2.0, 120.0, 24.0, 1.0)
        s_dur = st.number_input("Slag tap duration (min)", 2.0, 40.0, 8.0, 1.0)

    with st.expander("Initial bath state"):
        a, b = st.columns(2)
        m0 = a.number_input("Initial metal (t)", 50.0, 1200.0, 420.0, 10.0)
        s0 = a.number_input("Initial slag (t)", 20.0, 800.0, 260.0, 10.0)
        Tm0 = b.number_input("Initial metal T (degC)", 1350.0, 1600.0, 1480.0,
                             5.0)
        Ts0 = b.number_input("Initial slag T (degC)", 1350.0, 1650.0, 1545.0,
                             5.0)

    with st.expander("Kinetic constants (plant-calibratable)"):
        a, b, c = st.columns(3)
        k_feo = a.number_input("k0 FeO by [C]", 0.1, 30.0, 3.0, 0.1)
        k_char = a.number_input("k0 FeO on char", 0.05, 10.0, 0.90, 0.05)
        k_si = b.number_input("k0 SiO2", 0.5, 80.0, 20.0, 0.5)
        k_mn = b.number_input("k0 MnO", 0.5, 40.0, 5.5, 0.5)
        k_c = c.number_input("k0 C dissolution", 0.001, 0.2, 0.02, 0.001,
                             format="%.3f")
        h_pile = c.number_input("Pile heat-transfer coeff (W/m2/K)", 300.0,
                                6000.0, 2000.0, 100.0)

    if st.button("Run dynamic simulation", type="primary"):
        prog = st.progress(0.0)
        t0 = time.time()
        D = run_dynamic(
            duration_min=dur, dt_s=dt, log_every_s=logs,
            dri_name=dri_name, dri_composition=(dri_comp if custom_dri else {}),
            metallisation_pct=MR, dri_feed_t_h=dri_rate,
            dri_temperature_C=T_dri, scrap_feed_t_h=scrap_rate,
            carbon_source=carbon_source, carbon_feed_kg_t_dri=c_rate,
            flux_primary=flux1, flux_secondary=flux2,
            lime_feed_kg_t_dri=lime_rate, dolo_feed_kg_t_dri=dolo_rate,
            power_MW=P_rated, power_control=pwr_ctrl,
            target_metal_T_C=T_set, target_basicity_B2=B2_target,
            initial_metal_t=m0, initial_slag_t=s0,
            initial_metal_T_C=Tm0, initial_slag_T_C=Ts0,
            metal_tap_interval_min=m_int, metal_tap_mass_t=m_mass,
            metal_tap_duration_min=m_dur, slag_tap_interval_min=s_int,
            slag_tap_mass_t=s_mass, slag_tap_duration_min=s_dur,
            post_combustion_ratio=pcr,
            k0_FeO_C=k_feo, k0_FeO_char=k_char, k0_SiO2=k_si, k0_MnO=k_mn,
            k0_C_diss=k_c, melt_htc_pile=h_pile,
            geometry=geo, electrical=elec)
        st.session_state["dyn"] = D
        prog.progress(1.0)
        st.success(f"Solved {dur:.0f} min of furnace operation in "
                   f"{time.time()-t0:.1f} s.")

    if "dyn" in st.session_state:
        D = st.session_state["dyn"]
        st.markdown("#### Campaign summary")
        s = D["summary"]
        cs = st.columns(5)
        for j, k in enumerate(["SEC (kWh/tHM)", "Slag rate (kg/tHM)",
                               "Productivity (tHM/h)", "Heat loss share (%)",
                               "Freeze lining (mm)"]):
            cs[j].metric(k, f"{s[k]:.1f}")
        st.dataframe(df_from(s, "value", "KPI"), hide_index=True,
                     width="stretch", height=400)
        st.markdown("#### Final tapped compositions")
        a, b = st.columns(2)
        a.dataframe(df_from(D["final_metal_wt_pct"], "wt%", "element"),
                    hide_index=True, width="stretch")
        b.dataframe(df_from(D["final_slag_wt_pct"], "wt%", "oxide"),
                    hide_index=True, width="stretch")

# --------------------------------------------------------------------------
with TABS[8]:
    st.subheader("Process trajectories")
    if "dyn" not in st.session_state:
        st.info("Run a dynamic simulation on the **Dynamic setup** tab first.")
    else:
        D = st.session_state["dyn"]
        T = D["trajectory"]
        dfT = pd.DataFrame(T)
        idx = st.slider("Replay the schematic at time (min)", 0.0,
                        float(T["t_min"][-1]),
                        float(T["t_min"][-1]), float(max(1.0, T["t_min"][1])))
        i2 = int(np.argmin(np.abs(np.array(T["t_min"]) - idx)))
        recent = [e for e in D["events"]
                  if e["type"] in ("ALARM", "WARNING")
                  and e["t_min"] <= T["t_min"][i2]]
        stt = state_from_dynamic(T, i2, geo,
                                 alarm=recent[-1]["message"] if recent else "")
        stt["electrode_dia_m"] = d_el
        svg_block(furnace_svg(stt), 820)

        groups = {
            "Temperatures": ["T_metal_C", "T_slag_C", "T_gas_C", "T_pile_C"],
            "Power and losses": ["power_MW", "P_slag_MW", "P_arc_MW",
                                 "heat_loss_MW", "P_to_bath_MW"],
            "Bath inventory": ["m_metal_t", "m_slag_t", "m_pile_t", "char_t"],
            "Hot-metal chemistry": ["C_pct", "Si_pct", "Mn_pct", "Ti_pct",
                                    "P_pct", "S_pct"],
            "Slag chemistry": ["SiO2_pct", "CaO_pct", "Al2O3_pct", "MgO_pct",
                               "FeO_pct", "MnO_pct", "CaS_pct"],
            "Basicity": ["B2", "B3", "B4", "optical_basicity"],
            "Reaction rates": ["r_FeO_kg_s", "r_Si_kg_s", "r_Mn_kg_s",
                               "r_Cdiss_kg_s"],
            "Electrical": ["current_kA", "voltage_V", "resistance_mohm",
                           "sigma_slag_S_m", "immersion_m"],
            "Slag physics": ["slag_visc_Pa_s", "slag_liquidus_C",
                             "slag_superheat_C", "foaming_index_s"],
            "Metal physics": ["metal_liquidus_C", "metal_superheat_C",
                              "C_sat_pct", "C_over_Csat"],
            "Lining": ["freeze_mm", "shell_T_C", "hotface_slagwall_C"],
            "Production": ["metal_tapped_t", "slag_tapped_t",
                           "slag_rate_kg_t", "melt_rate_t_h",
                           "SEC_cum_kWh_t", "Fe_yield_pct"],
            "Gas and emissions": ["CO_Nm3_h", "CO2_kg_h", "offgas_T_C",
                                  "CO2_intensity_t_t"],
            "Loss breakdown": ["wall_loss_MW", "roof_loss_MW",
                               "hearth_loss_MW", "offgas_enthalpy_MW",
                               "arc_rad_MW"],
        }
        pick = st.multiselect("Panels to display", list(groups),
                              default=list(groups)[:6])
        for gname in pick:
            keys = groups[gname]
            f, ax = fig(11, 3.0)
            for j, k in enumerate(keys):
                ax.plot(T["t_min"], T[k], color=PAL[j % len(PAL)], lw=1.3,
                        label=k)
            ax.axvline(T["t_min"][i2], color="grey", ls="--", lw=0.8)
            ax.set(xlabel="time (min)", title=gname)
            ax.legend(fontsize=7.5, ncol=4)
            show(f)

        st.markdown("#### Custom cross-plot")
        a, b = st.columns(2)
        xk = a.selectbox("x", list(T), index=list(T).index("t_min"))
        yk = b.selectbox("y", list(T), index=list(T).index("SEC_cum_kWh_t"))
        f, ax = fig(7, 3.2)
        ax.plot(T[xk], T[yk], color=PAL[0])
        ax.set(xlabel=xk, ylabel=yk)
        show(f)

        st.markdown("#### Full trajectory table")
        st.dataframe(dfT, hide_index=True, width="stretch",
                     height=320)
        dl(dfT, "Download trajectory", "esf_trajectory.csv")

# --------------------------------------------------------------------------
with TABS[9]:
    st.subheader("Event log")
    if "dyn" not in st.session_state:
        st.info("Run a dynamic simulation to populate the event log.")
    else:
        D = st.session_state["dyn"]
        ev = pd.DataFrame(D["events"])
        kinds = st.multiselect("Filter by type", sorted(ev["type"].unique()),
                               default=sorted(ev["type"].unique()))
        view = ev[ev["type"].isin(kinds)]
        st.dataframe(view, hide_index=True, width="stretch",
                     height=520)
        dl(view, "Download event log", "esf_event_log.csv")
        st.caption("Every charge addition schedule, tap-hole opening and "
                   "closing, alarm and advisory is time-stamped against the "
                   "furnace clock, with the process state at the moment it "
                   "was raised.")

        st.markdown("#### Additions and rates in force")
        add = pd.DataFrame({
            "stream": ["DRI", "Scrap", "Carburiser", "Primary flux",
                       "Secondary flux"],
            "rate": [D["trajectory"]["dri_feed_t_h"][-1],
                     0.0,
                     D["trajectory"]["carbon_feed_t_h"][-1],
                     D["trajectory"]["flux_feed_t_h"][-1] * 0.67,
                     D["trajectory"]["flux_feed_t_h"][-1] * 0.33],
            "unit": ["t/h"] * 5,
            "cumulative (t)": [D["cumulative"]["dri_charged_t"], 0.0,
                               D["cumulative"]["C_charged_t"],
                               D["cumulative"]["flux_charged_t"] * 0.67,
                               D["cumulative"]["flux_charged_t"] * 0.33]})
        st.dataframe(add, hide_index=True, width="stretch")

# --------------------------------------------------------------------------
with TABS[10]:
    st.subheader("Validation against published data")
    base = figures_dir()
    vt = os.path.join(base, "validation_table.csv")

    if not os.path.exists(vt):
        st.info("No validation results found yet. They are generated from "
                "the engine, not shipped as fixed numbers, so they can be "
                "produced right here.")
        st.caption(f"Looked in: `{base}`")
        c1, c2 = st.columns(2)
        if c1.button("Generate the validation table",
                     help="Runs the full literature comparison. Takes about "
                          "half a minute."):
            try:
                sys.path.insert(0, PKG_ROOT)
                from run_validation import validation_tables
                os.makedirs(base, exist_ok=True)
                with st.spinner("Reproducing the published benchmarks..."):
                    validation_tables(base)
                st.success("Validation table generated.")
                st.rerun()
            except Exception as exc:              # noqa: BLE001
                st.error(f"Could not generate the table: {exc}")
        if c2.button("Generate the table and all figures",
                     help="Adds the nineteen figure sets. Takes a couple of "
                          "minutes."):
            try:
                sys.path.insert(0, PKG_ROOT)
                from run_validation import (validation_tables, figures_static,
                                            figures_dynamic)
                os.makedirs(base, exist_ok=True)
                with st.spinner("Reproducing benchmarks and figures..."):
                    _, _, _, _dyn = validation_tables(base)
                    figures_static(base)
                    figures_dynamic(base, _dyn)
                st.success("Validation table and figures generated.")
                st.rerun()
            except Exception as exc:              # noqa: BLE001
                st.error(f"Could not generate the figures: {exc}")

    if os.path.exists(vt):
        d = pd.read_csv(vt)
        stats_path = os.path.join(base, "validation_stats.json")
        if os.path.exists(stats_path):
            import json as _json
            stt = _json.load(open(stats_path))
            cs = st.columns(5)
            cs[0].metric("Comparisons", stt["n_comparisons"])
            cs[1].metric("Mean deviation",
                         f"{stt['mean_abs_RPD_pct']:.1f} %")
            cs[2].metric("Median", f"{stt['median_abs_RPD_pct']:.1f} %")
            cs[3].metric("Within 10 %",
                         f"{stt['within_10_pct']}/{stt['n_comparisons']}")
            nwin = int((d["rpd_pct"] == "in window").sum())
            nout = int((d["rpd_pct"] == "outside").sum())
            cs[4].metric("Windows met", f"{nwin}/{nwin + nout}")
        only_out = st.checkbox("Show only the comparisons that miss")
        view = d
        if only_out:
            def _miss(v):
                try:
                    return abs(float(v)) > 10.0
                except (TypeError, ValueError):
                    return str(v) == "outside"
            view = d[d["rpd_pct"].map(_miss)]
        st.dataframe(view, hide_index=True, width="stretch", height=520)
        dl(d, "Download validation table", "esf_validation.csv")
        st.caption("Every number here is regenerated from the engine by "
                   "`run_validation.py`; nothing is cached or hand-entered.")

    figs = sorted([f for f in os.listdir(base) if f.endswith(".png")]) \
        if os.path.isdir(base) else []
    if figs:
        pick = st.selectbox("Figure", figs)
        st.image(os.path.join(base, pick), width="stretch")

# --------------------------------------------------------------------------
with TABS[11]:
    st.subheader("Economics and carbon intensity")
    c = st.columns(5)
    c[0].metric("Specific OPEX", f"{K['Specific_OPEX_USD_tHM']:.1f} USD/tHM")
    c[1].metric("Power", f"{K['SEC_operating_kWh_tHM']:.0f} kWh/tHM")
    c[2].metric("Electrode", f"{K['Electrode_consumption_kg_tHM']:.2f} kg/tHM")
    c[3].metric("CO2 direct", f"{K['CO2_direct_t_tHM']:.3f} t/tHM")
    c[4].metric("CO2 total", f"{K['CO2_total_t_tHM']:.3f} t/tHM")

    cost = {
        "Electric power": K["SEC_operating_kWh_tHM"] / 1000.0 * p_power,
        "Carburiser": K["Carbon_charged_kg_tHM"] / 1000.0 * p_carbon,
        "Fluxes": K["Flux_rate_kg_tHM"] / 1000.0 * p_lime,
        "Electrode paste": K["Electrode_consumption_kg_tHM"] / 1000.0
        * p_electrode,
    }
    cost = {k: max(0.0, v) for k, v in cost.items()}
    a, b = st.columns([1, 1])
    with a:
        d = df_from(cost, "USD/tHM", "item")
        d.loc[len(d)] = ["TOTAL", sum(cost.values())]
        st.dataframe(d, hide_index=True, width="stretch")
    with b:
        if sum(cost.values()) > 0:
            f, ax = fig(5.6, 3.4)
            ax.pie(list(cost.values()), labels=list(cost),
                   colors=PAL[:len(cost)], autopct="%1.0f%%",
                   textprops={"fontsize": 8})
            ax.set_title("Conversion-cost split")
            show(f)

    st.markdown("#### Sensitivity of conversion cost")
    pw = np.linspace(max(5.0, p_power * 0.4), p_power * 1.8, 30)
    f, ax = fig(6.4, 3.2)
    for j, sec in enumerate([K["SEC_operating_kWh_tHM"] * f_
                             for f_ in (0.9, 1.0, 1.1)]):
        ax.plot(pw, sec / 1000.0 * pw + sum(cost.values())
                - cost["Electric power"], color=PAL[j],
                label=f"SEC {sec:.0f} kWh/tHM")
    ax.axvline(p_power, color="grey", ls="--")
    ax.set(xlabel="power price (USD/MWh)", ylabel="conversion cost (USD/tHM)")
    ax.legend(fontsize=8)
    show(f)

    st.markdown("#### Annualised view")
    hrs = st.number_input("Operating hours per year", 4000, 8600, 8000, 100)
    ann = {
        "Hot metal (Mt/a)": prod * hrs / 1e6,
        "Energy (GWh/a)": K["SEC_operating_kWh_tHM"] * prod * hrs / 1e6,
        "Slag (Mt/a)": K["Slag_rate_kg_tHM"] * prod * hrs / 1e9,
        "Carburiser (kt/a)": K["Carbon_charged_kg_tHM"] * prod * hrs / 1e6,
        "Flux (kt/a)": K["Flux_rate_kg_tHM"] * prod * hrs / 1e6,
        "CO2 (Mt/a)": K["CO2_total_t_tHM"] * prod * hrs / 1e6,
        "Conversion cost (MUSD/a)": sum(cost.values()) * prod * hrs / 1e6,
    }
    st.dataframe(df_from(ann, "value", "quantity"), hide_index=True,
                 width="stretch")

# --------------------------------------------------------------------------
with TABS[12]:
    doc = os.path.join(PKG_ROOT, "docs", "HELP.md")
    if os.path.exists(doc):
        st.markdown(open(doc).read())
    else:
        st.markdown(f"""
### {PRODUCT} - quick help

**Workflow.** Set the feed, product targets, geometry and electrical system
in the sidebar. The static solver runs on every change and feeds every tab.
For transient behaviour, open **Dynamic setup**, set the feed and tapping
schedule and press *Run dynamic simulation*.

**Static vs dynamic.** The static model answers *what does a tonne of hot
metal cost in energy and materials?*; the dynamic model answers *what does
the furnace actually do over a shift?* - bath temperatures, tapping cycles,
kinetically limited chemistry, freeze-lining response and alarms.

**Anonymisation.** All plant references in this package use the label
**Industry-X**.

(c) {VENDOR}.
""")
