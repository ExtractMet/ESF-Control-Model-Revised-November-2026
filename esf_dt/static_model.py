"""
ESF-DT :: static_model.py
=========================
Steady-state (per-tonne) model of the Electric Smelting Furnace.

The static model answers the design and planning questions:

    "For this DRI, this metallisation, this target hot-metal chemistry and
     this tapping temperature - how much flux and carbon do I need, what
     hot metal and slag do I get, how much slag per tonne, what is the
     specific energy consumption, and where does the energy go?"

Structure
---------
1.  Charge speciation           : DRI + scrap + fluxes + carbon + electrode C
2.  Flux demand                 : CaO/MgO to hit target basicity and MgO
3.  Slag / metal equilibrium    : FeO, Si, Mn, Ti, P, S distribution solved
                                  iteratively with the activity models
4.  Elemental mass balance      : Fe, C, Si, Mn, P, S, Ti, O closed to <0.01 %
5.  Heat balance                : absolute enthalpies of all streams,
                                  reaction heats implicit, slag mixing
                                  enthalpy, heat losses from the refractory
                                  network, off-gas sensible heat and
                                  post-combustion credit
6.  KPIs                        : SEC, Fe yield, slag rate, C consumption,
                                  CO2 intensity, productivity, power demand

Convention on SEC
-----------------
`SEC_thermodynamic` is the net process heat requirement divided by the hot
metal mass - the same convention used by the FactSage / HSC equilibrium
studies published for this process, so that the model can be validated
directly against them.  `SEC_operating` adds refractory and off-gas losses
and divides by the electrical-to-bath efficiency; that is the number an
operator sees on the meter.
"""

from __future__ import annotations

import math

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

from . import thermo as th
from .thermo import (MW, normalise, oxide_to_metal_mass, metal_to_oxide_mass,
                     stream_enthalpy, carbon_saturation, basicity_B2,
                     basicity_B3, basicity_B4, optical_basicity)
from . import properties as pr
from .geometry import FurnaceGeometry, heat_loss_network, lining_life_index
from .electrical import ElectricalConfig, solve_electrical

KWH = 1.0 / 3.6e6

# --------------------------------------------------------------------------
# Feedstock library (H2-DRI from low-grade / medium-grade ores, wt%)
# Compositions are consistent with the gangue contents, SiO2/gangue ratios
# and hot-metal outcomes reported in the open ESF literature.
# --------------------------------------------------------------------------
DRI_LIBRARY: Dict[str, Dict[str, float]] = {
    "DRI-A (13.8 % gangue)": {
        "Fe": 86.22, "SiO2": 8.82, "Al2O3": 3.10, "CaO": 0.55, "MgO": 0.35,
        "MnO": 0.75, "TiO2": 0.10, "P2O5": 0.09, "S": 0.02, "C": 0.00,
    },
    "DRI-B (15.5 % gangue)": {
        "Fe": 84.50, "SiO2": 9.77, "Al2O3": 3.42, "CaO": 0.55, "MgO": 0.40,
        "MnO": 1.05, "TiO2": 0.20, "P2O5": 0.09, "S": 0.02, "C": 0.00,
    },
    "DRI-C (16.0 % gangue)": {
        "Fe": 84.05, "SiO2": 9.73, "Al2O3": 4.20, "CaO": 0.55, "MgO": 0.40,
        "MnO": 0.90, "TiO2": 0.06, "P2O5": 0.09, "S": 0.02, "C": 0.00,
    },
    "DRI-HG (7.2 % gangue)": {
        "Fe": 92.85, "SiO2": 4.35, "Al2O3": 1.60, "CaO": 0.40, "MgO": 0.25,
        "MnO": 0.45, "TiO2": 0.05, "P2O5": 0.03, "S": 0.02, "C": 0.00,
    },
    "DRI-Pilbara (19 % gangue)": {
        "Fe": 81.00, "SiO2": 11.20, "Al2O3": 5.30, "CaO": 0.60, "MgO": 0.45,
        "MnO": 1.10, "TiO2": 0.20, "P2O5": 0.13, "S": 0.02, "C": 0.00,
    },
    # Stream-by-stream reference case of Shahabuddin et al., as reproduced
    # in the ESF modelling review (Sabah et al., J. Sustain. Metall. 2026,
    # Table 3).  Used as a full mass-and-energy-balance benchmark.
    "DRI-Shahabuddin (16 % gangue)": {
        "Fe": 84.05, "SiO2": 9.76, "Al2O3": 4.88, "Mn": 1.07, "S": 0.04,
        "CaO": 0.10, "MgO": 0.05, "TiO2": 0.03, "P2O5": 0.02},
    # Low-grade H2-DRI actually smelted under ESF conditions by Bae and Park
    # (J. Cleaner Prod. 524, 2025, 146490).  Deliberately poor metallisation
    # to represent the hardest case a smelter is asked to take.
    "H2-DRI-BP85 (85 % MR, lab)": {
        "Fe": 76.8, "FeO": 17.4, "SiO2": 3.5, "Al2O3": 2.1, "CaO": 0.14,
        "MgO": 0.1},
    "H2-DRI-BP88 (88 % MR, lab)": {
        "Fe": 78.5, "FeO": 14.0, "SiO2": 3.9, "Al2O3": 1.4, "CaO": 1.60,
        "MgO": 0.5, "P2O5": 0.18, "S": 0.02},
    # Feed back-calculated from the industrial open-bath-furnace slag and
    # hot metal reported by Sabah et al. (2026, Table 1), so the model can
    # be asked the fair question: given this furnace's ore, does it make
    # this furnace's product?
    "DRI-OSBF (industrial reference)": {
        "Fe": 87.85, "SiO2": 8.72, "Al2O3": 2.19, "CaO": 0.40, "MgO": 0.30,
        "MnO": 0.21, "TiO2": 0.05, "P2O5": 0.05, "S": 0.08},
    "HBI (carburised, 2 % C)": {
        "Fe": 87.30, "SiO2": 5.60, "Al2O3": 2.10, "CaO": 1.20, "MgO": 0.45,
        "MnO": 0.55, "TiO2": 0.08, "P2O5": 0.06, "S": 0.02, "C": 2.00,
    },
}

SCRAP_DEFAULT = {"Fe": 98.00, "C": 0.20, "Si": 0.25, "Mn": 0.45,
                 "P": 0.03, "S": 0.03, "Cr": 0.15, "Ni": 0.10,
                 "Cu": 0.20, "SiO2": 0.35, "Al2O3": 0.14}

FLUX_LIBRARY: Dict[str, Dict[str, float]] = {
    "Burnt lime":       {"CaO": 93.0, "MgO": 1.5, "SiO2": 1.8, "Al2O3": 0.7,
                         "CaCO3": 2.0, "H2O": 1.0},
    "Limestone":        {"CaCO3": 95.0, "MgO": 1.0, "SiO2": 2.0, "Al2O3": 1.0,
                         "H2O": 1.0},
    "Dolomitic lime":   {"CaO": 57.0, "MgO": 38.0, "SiO2": 1.5, "Al2O3": 0.6,
                         "CaCO3": 2.0, "H2O": 0.9},
    "Raw dolomite":     {"CaMg(CO3)2": 96.0, "SiO2": 2.0, "Al2O3": 1.0,
                         "H2O": 1.0},
    "Calcined magnesia": {"MgO": 94.0, "CaO": 2.0, "SiO2": 2.5, "Al2O3": 1.0,
                          "H2O": 0.5},
    "Quartzite":        {"SiO2": 97.0, "Al2O3": 1.5, "CaO": 0.5, "H2O": 1.0},
    "Bauxite":          {"Al2O3": 85.0, "SiO2": 8.0, "TiO2": 3.0, "CaO": 0.5,
                         "H2O": 3.5},
}

CARBON_LIBRARY: Dict[str, Dict[str, float]] = {
    "Metallurgical coke":  {"C": 87.0, "ash_SiO2": 5.5, "ash_Al2O3": 3.0,
                            "H2O": 2.0, "S": 0.6, "VM": 1.9},
    "Anthracite":          {"C": 84.0, "ash_SiO2": 5.0, "ash_Al2O3": 2.5,
                            "H2O": 3.0, "S": 0.5, "VM": 5.0},
    "Char (biomass)":      {"C": 88.0, "ash_SiO2": 2.0, "ash_Al2O3": 0.8,
                            "H2O": 4.0, "S": 0.05, "VM": 5.15},
    "Graphite":            {"C": 99.0, "ash_SiO2": 0.5, "ash_Al2O3": 0.3,
                            "H2O": 0.1, "S": 0.02, "VM": 0.08},
    "Petroleum coke":      {"C": 89.0, "ash_SiO2": 0.4, "ash_Al2O3": 0.2,
                            "H2O": 1.0, "S": 4.5, "VM": 4.9},
}


# --------------------------------------------------------------------------
@dataclass
class ESFInputs:
    """Every operator-settable quantity of the static model."""
    # --- feed ---------------------------------------------------------
    dri_name: str = "DRI-A (13.8 % gangue)"
    dri_composition: Dict[str, float] = field(default_factory=dict)
    basis_kg_Fe: float = 1000.0          # calculation basis
    metallisation_pct: float = 100.0     # % of Fe present as metallic Fe
    dri_temperature_C: float = 25.0      # 25 = CDRI, 600-700 = HDRI
    scrap_fraction_pct: float = 0.0      # of the metallic charge, mass %
    scrap_composition: Dict[str, float] = field(
        default_factory=lambda: dict(SCRAP_DEFAULT))
    scrap_temperature_C: float = 25.0

    # --- carbon and fluxes --------------------------------------------
    carbon_source: str = "Metallurgical coke"
    target_C_in_HM_pct: float = 3.5
    carbon_yield_pct: float = 92.0       # fraction of charged C that reacts
    flux_primary: str = "Burnt lime"
    flux_secondary: str = "Dolomitic lime"
    target_basicity_B2: float = 1.10     # CaO/SiO2 in slag
    target_MgO_in_slag_pct: float = 8.0
    flux_temperature_C: float = 25.0

    # --- operating point ----------------------------------------------
    tap_temperature_C: float = 1500.0
    slag_superheat_C: float = 60.0       # slag above metal
    offgas_temperature_C: float = 1450.0
    pressure_atm: float = 1.0
    post_combustion_ratio: float = 0.12  # CO -> CO2 in the freeboard
    air_ingress_factor: float = 1.05
    electrical_to_bath_efficiency: float = 0.90
    # Optional reporting factor only.  Earlier versions set this to 0.887 and
    # described it as a bath thermal utilisation calibrated against published
    # equilibrium-code specific energies.  That justification does not hold:
    # across the published cases that can be verified, the ratio of the
    # reversible heat to the published figure varies from 0.775 to 0.886, so
    # it is not a stable constant and cannot be read as a physical efficiency.
    # The default is therefore unity, which makes the reported thermodynamic
    # specific energy identical to the reversible one and leaves the model
    # with no fitted energy parameter.  A user who wants to reproduce a
    # particular code's convention may still set it.
    thermal_utilisation_efficiency: float = 1.0
    # Silicon reporting. Equilibrium silicon rises steeply with temperature
    # and, above about 1525 degC, far exceeds anything an ESF actually
    # tapsc. Bae and Park (J. Cleaner Prod. 2025) measured the cause
    # directly: SiO2 reduction is sluggish and does not reach equilibrium
    # (their slag reached C/S 0.5 against 1.2 predicted). "kinetic" applies
    # that limitation and is the default; "equilibrium" reproduces the pure
    # thermodynamic result and is what equilibrium codes report.
    silicon_mode: str = "kinetic"          # kinetic | equilibrium
    silicon_ceiling_wt_pct: float = 0.45
    # At the carbon levels an ESF runs, equilibrium FeO in the slag is
    # essentially nil, yet industrial open-bath-furnace slag is reported at
    # 0.6-0.7 wt% FeO.  The difference is kinetic, in the same way as the
    # silicon, so a practical floor is applied.  Setting it to zero recovers
    # the pure equilibrium result.
    residual_FeO_floor_wt_pct: float = 0.65
    heat_loss_mode: str = "geometry"     # geometry | fraction
    heat_loss_fraction: float = 0.10     # used when mode == 'fraction'
    productivity_tHM_h: float = 150.0    # for absolute power demand

    # --- economics / emissions ----------------------------------------
    power_price_USD_MWh: float = 60.0
    grid_emission_factor_kgCO2_MWh: float = 120.0
    carbon_price_USD_t: float = 45.0
    lime_price_USD_t: float = 110.0
    electrode_price_USD_t: float = 1600.0

    def resolved_dri(self) -> Dict[str, float]:
        if self.dri_composition:
            return normalise(dict(self.dri_composition))
        return normalise(dict(DRI_LIBRARY[self.dri_name]))


# --------------------------------------------------------------------------
def _split_flux_yield(name: str) -> Dict[str, float]:
    """
    Oxide actually delivered to the slag per kilogram of flux charged,
    with carbonates calcined.  `total` is the sum over all slag-forming
    oxides and is what makes a flux dilute the slag it is modifying.
    """
    y = _split_flux(name, 1.0)
    out = {k: y.get(k, 0.0) for k in
           ("CaO", "MgO", "SiO2", "Al2O3", "TiO2")}
    out["total"] = sum(out.values())
    return out


def _split_flux(name: str, mass: float) -> Dict[str, float]:
    """Return {species: kg} of a flux charge, decomposing carbonates."""
    comp = FLUX_LIBRARY[name]
    out: Dict[str, float] = {}
    for sp, pct in comp.items():
        m = mass * pct / 100.0
        if sp == "CaCO3":
            out["CaO"] = out.get("CaO", 0.0) + m * MW["CaO"] / MW["CaCO3"]
            out["CO2"] = out.get("CO2", 0.0) + m * MW["CO2"] / MW["CaCO3"]
        elif sp == "CaMg(CO3)2":
            f = m / MW["CaMg(CO3)2"]
            out["CaO"] = out.get("CaO", 0.0) + f * MW["CaO"]
            out["MgO"] = out.get("MgO", 0.0) + f * MW["MgO"]
            out["CO2"] = out.get("CO2", 0.0) + 2.0 * f * MW["CO2"]
        elif sp == "H2O":
            out["H2O"] = out.get("H2O", 0.0) + m
        else:
            out[sp] = out.get(sp, 0.0) + m
    return out


def _flux_calcination_heat(name: str, mass: float, T_out: float,
                           carbonate_only: bool = False) -> float:
    """
    Heat (J) absorbed by calcination + moisture evaporation of the flux.
    `carbonate_only` returns just the carbonate decomposition term, which is
    what the input-side enthalpy correction needs.
    """
    comp = FLUX_LIBRARY[name]
    Q = 0.0
    m_cc = mass * comp.get("CaCO3", 0.0) / 100.0
    if m_cc > 0:
        Q += m_cc / MW["CaCO3"] * 178300.0
    m_dol = mass * comp.get("CaMg(CO3)2", 0.0) / 100.0
    if m_dol > 0:
        Q += m_dol / MW["CaMg(CO3)2"] * 302000.0
    if carbonate_only:
        return Q
    m_w = mass * comp.get("H2O", 0.0) / 100.0
    if m_w > 0:
        Q += m_w * (2.45e6 + 2.0e3 * (T_out - 373.0))
    return Q


# regular-solution interaction energies for the slag mixing enthalpy, J/mol
OMEGA = {
    ("CaO", "SiO2"): -142.0e3, ("MgO", "SiO2"): -68.0e3,
    ("CaO", "Al2O3"): -46.0e3, ("MgO", "Al2O3"): -30.0e3,
    ("Al2O3", "SiO2"): -12.0e3, ("FeO", "SiO2"): -20.0e3,
    ("MnO", "SiO2"): -38.0e3, ("CaO", "FeO"): -12.0e3,
    ("CaO", "TiO2"): -60.0e3, ("CaO", "P2O5"): -220.0e3,
}
SLAG_MIX_SCALE = 0.15   # calibration factor (see VALIDATION.md, Table V-1)


def slag_cement_suitability(slag_wt: Dict[str, float]) -> Dict[str, object]:
    """
    Score the tapped slag for reuse as a supplementary cementitious
    material (SCM).

    Both the ESF literature and the EAF literature make the same point: the
    commercial case for the ESF route rests partly on its slag being usable
    in cement, which is what a blast furnace slag already is and what a
    high-basicity EAF slag is not.  Three things decide it:

      * basicity near 1, as in blast-furnace slag, rather than the B2 near 2
        that a foaming EAF practice needs;
      * low FeO, both for iron yield and because iron-rich slag is not
        hydraulic;
      * free MgO below saturation, because free MgO hydrates to Mg(OH)2 with
        a volume expansion that cracks the product.
    """
    B2 = th.basicity_B2(slag_wt)
    feo = slag_wt.get("FeO", 0.0)
    mgo = slag_wt.get("MgO", 0.0)
    al = slag_wt.get("Al2O3", 0.0)
    # MgO saturation in a CaO-SiO2-Al2O3 slag rises as basicity falls
    mgo_sat = 4.0 + 7.5 / max(B2, 0.4) + 0.08 * al
    notes = []
    score = 100.0
    if not (0.85 <= B2 <= 1.30):
        score -= 45.0
        notes.append(f"basicity B2 = {B2:.2f} is outside the 0.85-1.30 band "
                     "that makes ESF slag behave like blast-furnace slag")
    if feo > 2.0:
        score -= min(35.0, (feo - 2.0) * 9.0)
        notes.append(f"FeO = {feo:.1f} wt% costs iron yield and reduces "
                     "hydraulic activity (target below 2 wt%)")
    if mgo > mgo_sat:
        score -= min(35.0, (mgo - mgo_sat) * 12.0)
        notes.append(f"MgO = {mgo:.1f} wt% exceeds the estimated saturation "
                     f"of {mgo_sat:.1f} wt%: free MgO hydrates to Mg(OH)2 "
                     "with a volume expansion that cracks cement products")
    score = max(0.0, min(100.0, score))
    return {"B2 (CaO/SiO2)": B2, "FeO (wt%)": feo, "MgO (wt%)": mgo,
            "Estimated MgO saturation (wt%)": mgo_sat,
            "Free MgO risk": "yes" if mgo > mgo_sat else "no",
            "Cement suitability score (0-100)": score,
            "Verdict": ("suitable as an SCM" if score >= 75 else
                        "marginal, needs adjustment" if score >= 50 else
                        "not suitable without treatment"),
            "Notes": notes}


def slag_mixing_enthalpy(slag_wt: Dict[str, float], mass_kg: float) -> float:
    """Integral enthalpy of mixing of the molten slag (J, negative)."""
    x = th.mole_fractions(slag_wt)
    Mbar = sum(x.get(k, 0.0) * MW[k] for k in x if k in MW)
    if Mbar <= 0 or mass_kg <= 0:
        return 0.0
    dh_mol = 0.0
    for (a, b), om in OMEGA.items():
        dh_mol += om * x.get(a, 0.0) * x.get(b, 0.0)
    n_tot = mass_kg / Mbar
    return SLAG_MIX_SCALE * dh_mol * n_tot


# --------------------------------------------------------------------------
class ESFStaticModel:
    """Steady-state mass and heat balance for the electric smelting furnace."""

    def _warn(self, msg: str) -> None:
        if not hasattr(self, "_warnings"):
            self._warnings = []
        if msg not in self._warnings:
            self._warnings.append(msg)

    """Steady-state ESF solver."""

    def __init__(self, inp: ESFInputs,
                 geo: Optional[FurnaceGeometry] = None,
                 elec: Optional[ElectricalConfig] = None):
        self.inp = inp
        self.geo = geo or FurnaceGeometry()
        self.elec = elec or ElectricalConfig()
        self.result: Dict[str, object] = {}

    # ------------------------------------------------------------------
    def solve(self, max_iter: int = 400, tol: float = 1e-6
              ) -> Dict[str, object]:
        i = self.inp
        T = i.tap_temperature_C + 273.15
        T_slag = T + i.slag_superheat_C
        T_gas = i.offgas_temperature_C + 273.15
        p_CO = max(0.05, i.pressure_atm * (1.0 - i.post_combustion_ratio * 0.5))

        dri = i.resolved_dri()
        MRfrac = min(1.0, max(0.5, i.metallisation_pct / 100.0))

        # ---------- 1. charge speciation -----------------------------
        Fe_basis = i.basis_kg_Fe
        m_dri = Fe_basis / (dri["Fe"] / 100.0)

        # scrap replaces part of the metallic charge
        f_scrap = min(0.9, max(0.0, i.scrap_fraction_pct / 100.0))
        if f_scrap > 0:
            m_metallic_total = m_dri / (1.0 - f_scrap)
            m_scrap = m_metallic_total * f_scrap
            m_dri = m_metallic_total * (1.0 - f_scrap)
        else:
            m_scrap = 0.0
        scrap = normalise(dict(i.scrap_composition))

        # ---- DRI speciation (kg) -------------------------------------
        # A DRI analysis may be reported in either of two conventions:
        #   (a) total Fe, with the split between metallic and oxidised iron
        #       given separately as the metallisation ratio, or
        #   (b) metallic Fe plus an explicit FeO (or Fe2O3) assay.
        # Convention (b) already fixes the metallisation, so applying the
        # ratio again would count the oxidised iron twice.  Detect which
        # convention the analysis uses and honour it.
        charge: Dict[str, float] = {}
        FeO_assay = m_dri * dri.get("FeO", 0.0) / 100.0
        Fe2O3_assay = m_dri * dri.get("Fe2O3", 0.0) / 100.0
        Fe_assayed_oxide = (oxide_to_metal_mass("FeO", FeO_assay)
                            + oxide_to_metal_mass("Fe2O3", Fe2O3_assay))

        if Fe_assayed_oxide > 1e-9:
            # convention (b): "Fe" is metallic iron
            Fe_met = m_dri * dri["Fe"] / 100.0
            Fe_tot_dri = Fe_met + Fe_assayed_oxide
            m_FeO_in = FeO_assay + metal_to_oxide_mass(
                "FeO", oxide_to_metal_mass("Fe2O3", Fe2O3_assay))
            MR_implied = 100.0 * Fe_met / max(Fe_tot_dri, 1e-9)
            if abs(MR_implied - i.metallisation_pct) > 1.0:
                self._warn(
                    f"The analysis of '{i.dri_name}' states metallic Fe and "
                    f"an iron-oxide assay, which fixes the metallisation at "
                    f"{MR_implied:.1f} %. The metallisation ratio input "
                    f"({i.metallisation_pct:.1f} %) has been ignored so the "
                    "iron is not counted twice.")
        else:
            # convention (a): "Fe" is total iron, split by the input ratio
            Fe_tot_dri = m_dri * dri["Fe"] / 100.0
            Fe_met = Fe_tot_dri * MRfrac
            m_FeO_in = metal_to_oxide_mass("FeO", Fe_tot_dri * (1.0 - MRfrac))

        # Metallic solutes reported in the DRI analysis (Mn, Si, P as
        # elements rather than oxides) arrive already reduced.
        Mn_from_dri = m_dri * dri.get("Mn", 0.0) / 100.0
        Si_from_dri = m_dri * dri.get("Si", 0.0) / 100.0
        P_from_dri = m_dri * dri.get("P", 0.0) / 100.0

        for sp, pct in dri.items():
            if sp in ("Fe", "FeO", "Fe2O3", "Mn", "Si", "P"):
                continue
            charge[sp] = charge.get(sp, 0.0) + m_dri * pct / 100.0
        charge["FeO"] = charge.get("FeO", 0.0) + m_FeO_in
        charge["Mn_met"] = Mn_from_dri
        charge["Si_met"] = Si_from_dri
        charge["P_met"] = P_from_dri
        charge["Fe_met"] = Fe_met

        # scrap species
        Fe_scrap = m_scrap * scrap.get("Fe", 0.0) / 100.0
        charge["Fe_met"] += Fe_scrap
        for sp, pct in scrap.items():
            if sp == "Fe":
                continue
            charge[sp] = charge.get(sp, 0.0) + m_scrap * pct / 100.0

        # Solutes the scrap brings in already dissolved.  These are held
        # once, outside the iteration, because every balance below has to
        # net them off: they arrive as metal and must not be counted again
        # as something reduced out of the slag.
        # Metallic solutes arriving already reduced, from either source.
        Si_from_scrap = (m_scrap * scrap.get("Si", 0.0) / 100.0
                         + Si_from_dri)
        Mn_from_scrap = (m_scrap * scrap.get("Mn", 0.0) / 100.0
                         + Mn_from_dri)
        P_from_scrap = (m_scrap * scrap.get("P", 0.0) / 100.0
                        + P_from_dri)
        C_from_scrap = m_scrap * scrap.get("C", 0.0) / 100.0

        # gangue oxides entering the slag from DRI + scrap
        gangue = {k: charge.get(k, 0.0) for k in
                  ("SiO2", "Al2O3", "CaO", "MgO", "MnO", "TiO2",
                   "P2O5", "V2O5", "Cr2O3", "Na2O", "K2O")}
        S_charge = charge.get("S", 0.0)
        # carbon already dissolved in the charge (DRI + scrap):
        # charge["C"] carries both, so it is netted off once only
        C_charge_metallic = charge.get("C", 0.0)

        # ---------- 2. iterate the coupled equilibrium ----------------
        self._warnings = []

        # initial guesses
        slag_wt = {"SiO2": 32.0, "CaO": 36.0, "Al2O3": 14.0, "MgO": 8.0,
                   "FeO": 2.0, "MnO": 0.8, "TiO2": 0.4, "P2O5": 0.02,
                   "CaS": 0.3}
        metal_wt = {"Fe": 95.0, "C": i.target_C_in_HM_pct, "Si": 0.35,
                    "Mn": 0.7, "P": 0.06, "S": 0.02, "Ti": 0.0}
        m_lime = m_dolo = 0.0
        m_HM = Fe_basis * 1.05
        C_needed = 40.0
        prev_Si_act = 0.35
        prev_m_slag = 300.0
        relax = 0.45
        hist: List[float] = []

        for it in range(max_iter):
            # -- 2a. flux demand ------------------------------------
            SiO2_slag = gangue["SiO2"] + 0.02 * C_needed * 0.05
            # carbon-source ash contributes SiO2/Al2O3
            cs = CARBON_LIBRARY[i.carbon_source]
            m_C_charged = C_needed / max(cs["C"] / 100.0, 0.3) \
                / max(i.carbon_yield_pct / 100.0, 0.5)
            ash_SiO2 = m_C_charged * cs.get("ash_SiO2", 0.0) / 100.0
            ash_Al2O3 = m_C_charged * cs.get("ash_Al2O3", 0.0) / 100.0
            S_from_C = m_C_charged * cs.get("S", 0.0) / 100.0
            SiO2_slag = gangue["SiO2"] + ash_SiO2
            Al2O3_slag = gangue["Al2O3"] + ash_Al2O3

            # residual FeO reporting to the slag (small at high MR)
            FeO_slag_est = max(0.0, gangue.get("FeO", 0.0) * 0.005)

            # SiO2 removed by reduction to [Si]
            Si_in_HM = metal_wt.get("Si", 0.0) / 100.0 * m_HM
            # only the silicon actually reduced out of the slag removes
            # SiO2 from it; scrap silicon arrives already metallic
            SiO2_reduced = metal_to_oxide_mass(
                "SiO2", max(0.0, Si_in_HM - Si_from_scrap))
            SiO2_slag_net = max(1e-6, SiO2_slag - SiO2_reduced)

            # ---- flux demand, solved exactly ----------------------
            # Both targets are written as linear constraints in the two
            # flux masses, including the fact that every kilogram of flux
            # also enlarges the slag it is trying to modify:
            #
            #   CaO :  CaO_g + m1 c1 + m2 c2 = B2 (SiO2_g + m1 s1 + m2 s2)
            #   MgO :  MgO_g + m1 g1 + m2 g2 = x  (S_base + m1 b1 + m2 b2)
            #
            # Solving these simultaneously removes the lagged slag-mass
            # estimate that used to make the iteration diverge whenever the
            # chosen flux could not actually deliver the MgO target.
            B2t = i.target_basicity_B2
            xMgO = min(0.60, max(0.0, i.target_MgO_in_slag_pct / 100.0))

            def yields(f):
                """Oxide delivered to the slag per kg of flux charged."""
                y = _split_flux_yield(f)
                return y

            y1, y2 = yields(i.flux_primary), yields(i.flux_secondary)

            # slag that exists before any flux is added
            S_base = (SiO2_slag_net + Al2O3_slag + gangue["CaO"]
                      + gangue["MgO"] + gangue.get("MnO", 0.0)
                      + gangue.get("TiO2", 0.0) + gangue.get("P2O5", 0.0)
                      + FeO_slag_est)

            a11 = y1["CaO"] - B2t * y1["SiO2"]
            a12 = y2["CaO"] - B2t * y2["SiO2"]
            b1 = B2t * SiO2_slag_net - gangue["CaO"]
            a21 = y1["MgO"] - xMgO * y1["total"]
            a22 = y2["MgO"] - xMgO * y2["total"]
            b2 = xMgO * S_base - gangue["MgO"]

            det = a11 * a22 - a12 * a21
            m_lime = m_dolo = 0.0
            mgo_ok = True
            if abs(det) > 1e-9:
                m_lime = (b1 * a22 - a12 * b2) / det
                m_dolo = (a11 * b2 - b1 * a21) / det
            # A flux charge above ~1.2 t per tonne of contained iron is not
            # an operating point, it is the algebra running away because the
            # chosen flux cannot reach the target.
            FLUX_MAX = 1.2 * i.basis_kg_Fe
            if not (m_lime >= 0.0 and m_dolo >= 0.0
                    and abs(det) > 1e-9
                    and m_lime + m_dolo < FLUX_MAX):
                # No non-negative solution: the flux pair cannot reach both
                # targets at once.  Basicity is the control that matters, so
                # it is honoured with whichever flux can raise it, and the
                # MgO target is reported as unreachable rather than chased.
                mgo_ok = False
                m_lime = m_dolo = 0.0
                best = None
                for tag, y in (("1", y1), ("2", y2)):
                    den = y["CaO"] - B2t * y["SiO2"]
                    if den > 1e-6:
                        m = max(0.0, b1 / den)
                        if m < FLUX_MAX and (best is None or m < best[1]):
                            best = (tag, m)
                if best is not None:
                    if best[0] == "1":
                        m_lime = best[1]
                    else:
                        m_dolo = best[1]
                else:
                    # Not a numerical difficulty: an electric smelting
                    # furnace cannot be operated with no basic flux at all.
                    # Refusing here is safer than returning a slag that no
                    # furnace could tap.
                    raise ValueError(
                        f"Neither '{i.flux_primary}' nor '{i.flux_secondary}' "
                        f"can raise the slag basicity to B2 = {B2t:.2f}: both "
                        "are acid (silica- or alumina-bearing). Choose a lime, "
                        "limestone, dolomitic or magnesian flux for at least "
                        "one of the two flux slots.")
            if not mgo_ok:
                self._warn(
                    f"Target slag MgO of {i.target_MgO_in_slag_pct:.1f} wt% "
                    f"is unreachable with {i.flux_primary} and "
                    f"{i.flux_secondary}: their MgO content is too low to "
                    "raise the slag above the target faster than they "
                    "dilute it. Basicity has been honoured and the MgO "
                    "target dropped. Use a dolomitic or magnesian flux.")

            flux_sp = _split_flux(i.flux_primary, m_lime)
            for k, v in _split_flux(i.flux_secondary, m_dolo).items():
                flux_sp[k] = flux_sp.get(k, 0.0) + v

            # -- 2b. slag composition -------------------------------
            slag_mass_sp: Dict[str, float] = {
                "SiO2": SiO2_slag_net,
                "Al2O3": Al2O3_slag + flux_sp.get("Al2O3", 0.0),
                "CaO": gangue["CaO"] + flux_sp.get("CaO", 0.0),
                "MgO": gangue["MgO"] + flux_sp.get("MgO", 0.0),
                "TiO2": 0.0, "MnO": 0.0, "FeO": 0.0, "P2O5": 0.0,
                "CaS": 0.0, "V2O5": gangue.get("V2O5", 0.0),
                "Cr2O3": gangue.get("Cr2O3", 0.0),
                "Na2O": gangue.get("Na2O", 0.0),
                "K2O": gangue.get("K2O", 0.0),
            }
            slag_mass_sp["SiO2"] += flux_sp.get("SiO2", 0.0)

            # residual FeO from carbothermic equilibrium
            aFeO_eq = th.feo_equilibrium(metal_wt, T, p_CO)
            x = th.mole_fractions(slag_wt)
            Lam = optical_basicity(slag_wt)
            gFeO = 1.42 * math.exp(2.15 * (Lam - 0.58)) \
                * (1.0 + 0.55 * x.get("Al2O3", 0.0)) \
                * math.exp(2400.0 * (1.0 / T - 1.0 / 1773.0))
            x_FeO_eq = min(0.25, aFeO_eq / max(gFeO, 1e-6))
            # convert mole fraction to a mass in the slag
            Mbar = sum(x.get(k, 0.0) * MW[k] for k in x if k in MW) or 0.058
            m_slag_wo_FeO = sum(slag_mass_sp.values())
            n_slag = m_slag_wo_FeO / Mbar
            m_FeO_slag = max(0.0, x_FeO_eq * n_slag / max(1.0 - x_FeO_eq, 1e-3)
                             * MW["FeO"])
            # kinetic floor: practice does not reach equilibrium
            if i.silicon_mode == "kinetic" and i.residual_FeO_floor_wt_pct > 0:
                floor = (i.residual_FeO_floor_wt_pct / 100.0
                         * m_slag_wo_FeO
                         / max(1.0 - i.residual_FeO_floor_wt_pct / 100.0, 0.5))
                m_FeO_slag = max(m_FeO_slag, floor)
            m_FeO_slag = min(m_FeO_slag, m_FeO_in + 1e-9)
            slag_mass_sp["FeO"] = m_FeO_slag

            # Mn distribution
            Mn_in = oxide_to_metal_mass("MnO", gangue["MnO"]) + Mn_from_scrap
            Mn_eq = th.mn_equilibrium(slag_wt, metal_wt, T, p_CO)
            Mn_metal = min(Mn_in, Mn_eq / 100.0 * m_HM)
            # Manganese is bounded on both sides: equilibrium alone would
            # strip essentially all of it into the metal, but industrial
            # open-bath slag is reported at 0.15-0.30 wt% MnO, so a fraction
            # always stays behind.  Equilibrium mode keeps the old bound.
            if i.silicon_mode == "kinetic":
                Mn_metal = min(0.80 * Mn_in, max(Mn_metal, 0.55 * Mn_in))
            else:
                Mn_metal = min(Mn_in, max(Mn_metal, 0.90 * Mn_in))
            slag_mass_sp["MnO"] = metal_to_oxide_mass("MnO", Mn_in - Mn_metal)

            # Ti distribution (mostly stays in slag as TiO2/Ti2O3)
            # titania can arrive with the gangue *and* with a flux
            # (bauxite carries ~3 wt% TiO2); both must report to the slag
            Ti_in = oxide_to_metal_mass(
                "TiO2", gangue["TiO2"] + flux_sp.get("TiO2", 0.0))
            f_Ti = min(0.92, max(0.02, 0.70 + 0.30 * (T - 1773.15) / 60.0))
            Ti_metal = f_Ti * Ti_in
            slag_mass_sp["TiO2"] = metal_to_oxide_mass("TiO2", Ti_in - Ti_metal)

            # P: essentially fully reduced under ESF conditions
            P_in = oxide_to_metal_mass("P2O5", gangue["P2O5"]) + P_from_scrap
            LP = th.L_P(slag_wt, T, th.oxygen_activity_CO(
                T, th.a_metal("C", metal_wt, T), p_CO))
            f_P_slag = min(0.15, LP / (LP + 1000.0))
            P_metal = P_in * (1.0 - f_P_slag)
            slag_mass_sp["P2O5"] = metal_to_oxide_mass("P2O5", P_in - P_metal)

            # S: partitioned by sulphide capacity
            # S_charge already includes the scrap sulphur (it was added to
            # the charge above), so it must not be added a second time
            S_in = S_charge + S_from_C
            LS = th.L_S(slag_wt, T, metal_wt,
                        th.oxygen_activity_CO(T, th.a_metal("C", metal_wt, T),
                                              p_CO))
            m_slag_now = sum(slag_mass_sp.values())
            # (S)/[S] = LS ;  S_in = S_metal + S_slag
            S_metal = S_in / (1.0 + LS * m_slag_now / max(m_HM, 1.0))
            S_slag = S_in - S_metal
            slag_mass_sp["CaS"] = S_slag * MW["CaS"] / MW["S"]
            slag_mass_sp["CaO"] = max(0.0, slag_mass_sp["CaO"]
                                      - S_slag * MW["CaO"] / MW["S"])

            m_slag = sum(slag_mass_sp.values())
            slag_wt_new = normalise(slag_mass_sp)

            # -- 2c. metal composition ------------------------------
            Fe_reduced = oxide_to_metal_mass("FeO", m_FeO_in - m_FeO_slag)
            Fe_metal = Fe_met + Fe_scrap + Fe_reduced
            Si_eq = th.si_equilibrium(slag_wt_new, metal_wt, T, p_CO)
            # kinetic ceiling on silicon pickup (see ESFInputs.silicon_mode)
            if i.silicon_mode == "kinetic":
                cap = max(0.02, i.silicon_ceiling_wt_pct)
                Si_metal_pct = cap * (1.0 - math.exp(-Si_eq / cap))
            else:
                Si_metal_pct = Si_eq
            Cr_metal = m_scrap * scrap.get("Cr", 0.0) / 100.0
            Ni_metal = m_scrap * scrap.get("Ni", 0.0) / 100.0
            Cu_metal = m_scrap * scrap.get("Cu", 0.0) / 100.0

            # hot-metal mass closes on Fe + solutes
            Cpct = i.target_C_in_HM_pct
            solute_kg_fixed = Mn_metal + P_metal + S_metal + Ti_metal \
                + Cr_metal + Ni_metal + Cu_metal
            # m_HM * (1 - C% - Si%) = Fe + fixed solutes
            denom = 1.0 - (Cpct + Si_metal_pct) / 100.0
            m_HM_new = (Fe_metal + solute_kg_fixed) / max(denom, 0.5)
            # Silicon cannot exceed what the silica in the slag can supply.
            # Without this the solver would happily reduce more silicon than
            # there is SiO2 present and quietly clamp the slag at zero,
            # breaking the silicon balance.
            Si_available = oxide_to_metal_mass("SiO2", SiO2_slag) * 0.98
            Si_kg = max(Si_from_scrap,
                        min(Si_metal_pct / 100.0 * m_HM_new,
                            Si_from_scrap + Si_available))
            C_kg = Cpct / 100.0 * m_HM_new

            metal_mass_sp = {
                "Fe": Fe_metal, "C": C_kg, "Si": Si_kg, "Mn": Mn_metal,
                "P": P_metal, "S": S_metal, "Ti": Ti_metal,
                "Cr": Cr_metal, "Ni": Ni_metal, "Cu": Cu_metal,
            }
            m_HM_new = sum(metal_mass_sp.values())
            metal_wt_new = normalise(metal_mass_sp)

            # -- 2d. carbon demand ----------------------------------
            C_carburise = C_kg - C_charge_metallic
            C_FeO = (m_FeO_in - m_FeO_slag) / MW["FeO"] * MW["C"]
            C_SiO2 = max(0.0, Si_kg - Si_from_scrap) / MW["Si"] * 2.0 * MW["C"]
            C_MnO = max(0.0, Mn_metal - m_scrap * scrap.get("Mn", 0.0) / 100.0) \
                / MW["Mn"] * MW["C"]
            C_TiO2 = Ti_metal / MW["Ti"] * 2.0 * MW["C"]
            # only the phosphorus reduced out of the slag consumes carbon;
            # scrap phosphorus arrives already metallic
            C_P2O5 = max(0.0, (P_in - P_from_scrap) * (1.0 - f_P_slag)) \
                / MW["P"] * 2.5 * MW["C"]
            C_needed_new = (C_carburise + C_FeO + C_SiO2 + C_MnO
                            + C_TiO2 + C_P2O5)
            C_needed_new = max(0.0, C_needed_new)

            # -- convergence ----------------------------------------
            # Measured on successive iterates of the *actual* state, never
            # against the equilibrium target: when scrap pins the silicon
            # above its equilibrium value the two never meet, and testing
            # against the target left the solver permanently unconverged.
            Si_act = Si_kg / max(m_HM_new, 1e-9) * 100.0
            m_slag_new_tot = sum(slag_mass_sp.values())
            err = (abs(C_needed_new - C_needed) / max(C_needed, 1.0)
                   + abs(m_HM_new - m_HM) / max(m_HM, 1.0)
                   + abs(Si_act - prev_Si_act) / max(Si_act, 0.05)
                   + abs(m_slag_new_tot - prev_m_slag) / max(m_slag_new_tot, 1.0))
            prev_Si_act = Si_act
            prev_m_slag = m_slag_new_tot
            C_needed = (1 - relax) * C_needed + relax * C_needed_new
            m_HM = (1 - relax) * m_HM + relax * m_HM_new
            slag_wt = {k: (1 - relax) * slag_wt.get(k, 0.0)
                       + relax * slag_wt_new.get(k, 0.0)
                       for k in set(slag_wt) | set(slag_wt_new)}
            metal_wt = {k: (1 - relax) * metal_wt.get(k, 0.0)
                        + relax * metal_wt_new.get(k, 0.0)
                        for k in set(metal_wt) | set(metal_wt_new)}
            hist.append(err)
            if err < tol:
                break
            # damp harder if the iteration starts to limit-cycle rather
            # than descend: a stalled residual means the fixed point is
            # being overshot, not that it does not exist
            if len(hist) > 10 and hist[-1] > 0.70 * hist[-5]:
                relax = max(0.02, relax * 0.55)

        # final consistent state
        slag_wt = normalise(slag_mass_sp)
        metal_wt = normalise(metal_mass_sp)
        m_slag = sum(slag_mass_sp.values())
        m_HM = sum(metal_mass_sp.values())
        m_C_charged = C_needed / max(CARBON_LIBRARY[i.carbon_source]["C"] / 100.0,
                                     0.3) / max(i.carbon_yield_pct / 100.0, 0.5)

        # ---------- 3. gas phase --------------------------------------
        n_CO = (C_FeO + C_SiO2 + C_MnO + C_TiO2 + C_P2O5) / MW["C"]
        m_CO = n_CO * MW["CO"]
        m_CO2_flux = flux_sp.get("CO2", 0.0)
        m_H2O = flux_sp.get("H2O", 0.0) \
            + m_C_charged * CARBON_LIBRARY[i.carbon_source].get("H2O", 0.0) / 100.0
        # post combustion of CO in the freeboard
        pcr = min(0.9, max(0.0, i.post_combustion_ratio))
        n_CO_burnt = n_CO * pcr
        m_CO_out = (n_CO - n_CO_burnt) * MW["CO"]
        m_CO2_out = m_CO2_flux + n_CO_burnt * MW["CO2"]
        m_O2 = n_CO_burnt * 0.5 * MW["O2"]
        m_N2 = m_O2 * (0.79 / 0.21) * (MW["N2"] / MW["O2"]) * i.air_ingress_factor
        # carbon charged but not consumed by reduction/carburisation is
        # burnt in the freeboard or lost with the off-gas dust
        C_unreacted = max(0.0, m_C_charged
                          * CARBON_LIBRARY[i.carbon_source]["C"] / 100.0
                          - C_needed)
        gas_sp = {"CO": m_CO_out, "CO2": m_CO2_out, "H2O": m_H2O, "N2": m_N2}
        dust_sp = {"C": C_unreacted}
        m_gas = sum(gas_sp.values())

        # ---------- 4. heat balance -----------------------------------
        T_dri = i.dri_temperature_C + 273.15
        T_scrap = i.scrap_temperature_C + 273.15
        T_flux = i.flux_temperature_C + 273.15

        # inputs
        H_in = 0.0
        in_dri = {k: v for k, v in charge.items()
                  if k not in ("Fe_met", "C", "S")}
        in_dri["Fe"] = Fe_met - Fe_scrap
        H_in += stream_enthalpy(in_dri, T_dri)
        H_in += stream_enthalpy({"Fe": Fe_scrap}, T_scrap)
        H_in += stream_enthalpy({"C": m_C_charged
                                 * CARBON_LIBRARY[i.carbon_source]["C"] / 100.0},
                                298.15)
        H_in += stream_enthalpy({"CaO": flux_sp.get("CaO", 0.0),
                                 "MgO": flux_sp.get("MgO", 0.0),
                                 "SiO2": flux_sp.get("SiO2", 0.0),
                                 "Al2O3": flux_sp.get("Al2O3", 0.0),
                                 "TiO2": flux_sp.get("TiO2", 0.0)}, T_flux)

        # A carbonate flux is charged as the carbonate, not as the calcined
        # oxide.  `_split_flux` calcines it on the way in, so its CO2 would
        # otherwise appear in the off-gas carrying a formation enthalpy that
        # was never charged - a large spurious energy credit for limestone
        # and raw dolomite.  Charging the CO2 (and the free moisture as
        # liquid water) restores the balance, and the calcination endotherm
        # then falls out of the arithmetic on its own.
        H_calc_carb = (
            _flux_calcination_heat(i.flux_primary, m_lime, T_gas, True)
            + _flux_calcination_heat(i.flux_secondary, m_dolo, T_gas, True))
        m_CO2_flux = flux_sp.get("CO2", 0.0)
        m_H2O_flux = flux_sp.get("H2O", 0.0)
        H_in += stream_enthalpy({"CO2": m_CO2_flux}, T_flux) - H_calc_carb
        H_in += stream_enthalpy({"H2O": m_H2O_flux}, T_flux) \
            - m_H2O_flux * 2.45e6

        # outputs
        hm_H = th.hot_metal_enthalpy(metal_mass_sp, T)
        H_metal = hm_H["H"]
        T_liq_slag = pr.slag_liquidus(slag_wt)
        sl_H = th.slag_enthalpy(
            {k: v for k, v in slag_mass_sp.items() if v > 0}, T_slag, T_liq_slag)
        H_mix = slag_mixing_enthalpy(slag_wt, m_slag)
        H_slag = sl_H["H"] + H_mix
        H_slag_pure = sl_H["H"]
        H_gas = stream_enthalpy(gas_sp, T_gas) + stream_enthalpy(dust_sp, T_gas)
        H_calc = _flux_calcination_heat(i.flux_primary, m_lime, T_gas) \
            + _flux_calcination_heat(i.flux_secondary, m_dolo, T_gas)

        Q_process = (H_metal + H_slag + H_gas) - H_in
        # (calcination and moisture already carried by the formation
        #  enthalpies of the decomposition products; H_calc is reported
        #  separately for the Sankey breakdown only)

        # ---------- 5. heat losses ------------------------------------
        gas_y = {k: v for k, v in gas_sp.items() if v > 0}
        if i.heat_loss_mode == "geometry":
            hl = heat_loss_network(self.geo, T_slag, T, T_gas, slag_wt,
                                   gas_y, arc_power_W=0.0)
            Q_loss_W = hl["Q_total_W"]
            prod_kg_s = i.productivity_tHM_h * 1000.0 / 3600.0
            Q_loss_per_tHM = Q_loss_W / max(prod_kg_s, 1e-6) * 1000.0
            life = lining_life_index(hl, slag_wt, T_slag)
        else:
            hl = None
            life = None
            Q_loss_per_tHM = (Q_process / max(m_HM, 1.0) * 1000.0) \
                * i.heat_loss_fraction / max(1.0 - i.heat_loss_fraction, 0.1)
            Q_loss_W = Q_loss_per_tHM * i.productivity_tHM_h / 3.6e3 * 1e3 / 1e3

        eta_th = max(0.4, min(1.0, i.thermal_utilisation_efficiency))
        SEC_reversible = Q_process * KWH / (m_HM / 1000.0)
        # With the default eta_th of unity this is identical to the
        # reversible specific energy.  The tier is retained so that a user
        # may reproduce a particular equilibrium code's reporting convention,
        # but the model no longer carries a fitted energy parameter.
        SEC_thermo = SEC_reversible / eta_th
        Q_total_per_tHM = Q_process / max(m_HM, 1.0) * 1000.0 + Q_loss_per_tHM
        # Operating SEC is the *electrical* energy the transformer must
        # deliver: process heat + lining losses, divided by the electrical
        # -to-bath efficiency.  eta_th is a reporting basis for comparison
        # with equilibrium codes and is deliberately NOT applied here.
        SEC_operating = (Q_total_per_tHM * KWH
                         / max(i.electrical_to_bath_efficiency, 0.3))

        # ---------- 6. electrical -------------------------------------
        P_MW = SEC_operating * i.productivity_tHM_h / 1000.0
        ecfg = self.elec
        ecfg.n_electrodes = self.geo.n_electrodes
        ecfg.electrode_diameter_m = self.geo.electrode_diameter
        el = solve_electrical(ecfg, slag_wt, T_slag,
                              self.geo.electrode_immersion, self.geo.arc_length,
                              self.geo.electrode_pitch, self.geo.slag_depth,
                              power_setpoint_MW=P_MW)

        # ---------- 7. KPIs -------------------------------------------
        Fe_in_total = Fe_tot_dri + Fe_scrap
        Fe_yield = metal_mass_sp["Fe"] / max(Fe_in_total, 1e-9) * 100.0
        slag_rate = m_slag / (m_HM / 1000.0)
        C_cons = C_needed / (m_HM / 1000.0)
        C_charged_rate = m_C_charged / (m_HM / 1000.0)
        el_cons = el["electrode_consumption_kg_MWh"] * SEC_operating / 1000.0

        co2_direct = (m_CO_out * MW["CO2"] / MW["CO"] + m_CO2_out) \
            / (m_HM / 1000.0) / 1000.0
        co2_power = SEC_operating * i.grid_emission_factor_kgCO2_MWh / 1e6 * 1000.0
        co2_total = co2_direct + co2_power / 1000.0

        opex = (SEC_operating / 1000.0 * i.power_price_USD_MWh
                + C_charged_rate / 1000.0 * i.carbon_price_USD_t * 1000.0 / 1000.0
                + (m_lime + m_dolo) / (m_HM / 1000.0) / 1000.0 * i.lime_price_USD_t
                + el_cons / 1000.0 * i.electrode_price_USD_t)

        # elemental closure check
        closure = self._closure_check(charge, flux_sp, m_C_charged,
                                      metal_mass_sp, slag_mass_sp, gas_sp,
                                      i, scrap, m_scrap, dust_sp)

        # -- tapping temperature against the computed liquidus -----------
        # A solution obtained below the liquidus of its own slag is a formal
        # thermochemical result, not an operating point: the slag would be
        # partly solid and could not be tapped.  The balance still closes, so
        # the solution is returned, but it is flagged so that such a case is
        # not mistaken for an attainable condition or used as a benchmark.
        T_liq_slag = pr.slag_liquidus(slag_wt)
        if T_slag < T_liq_slag:
            self._warn(
                f"Slag temperature of {T_slag - 273.15:.0f} degC is below the "
                f"computed slag liquidus of {T_liq_slag - 273.15:.0f} degC, so "
                f"the slag would be partly solid and could not be tapped. The "
                f"balance is returned as a formal thermochemical result and "
                f"must not be read as an attainable operating point. Raise the "
                f"tapping temperature above the liquidus, or lower the liquidus "
                f"by adjusting basicity, alumina or MgO.")
        T_liq_metal = pr.metal_liquidus(metal_wt)
        if T < T_liq_metal:
            self._warn(
                f"Hot metal temperature of {T - 273.15:.0f} degC is below the "
                f"computed metal liquidus of {T_liq_metal - 273.15:.0f} degC. "
                f"The balance is a formal result only.")

        self.result = {
            # Convergence is declared against the same tolerance the
            # iteration uses to exit.  The submitted version exited the loop
            # at 1e-6 but reported convergence at 1e-4, so a run that stalled
            # between the two was reported as converged.
            "converged": hist[-1] < tol if hist else False,
            "tolerance": tol,
            "max_iterations": max_iter,
            "iterations": len(hist),
            "residual": hist[-1] if hist else None,
            "residual_history": list(hist),
            "sub_liquidus": bool(T_slag < T_liq_slag or T < T_liq_metal),

            "inputs_kg": {
                "DRI": m_dri, "Scrap": m_scrap,
                "Carbon source": m_C_charged,
                i.flux_primary: m_lime, i.flux_secondary: m_dolo,
                "Total charge": m_dri + m_scrap + m_C_charged + m_lime + m_dolo,
            },
            "outputs_kg": {
                "Hot metal": m_HM, "Slag": m_slag, "Off-gas": m_gas,
            },
            "hot_metal_wt_pct": metal_wt,
            "hot_metal_kg": metal_mass_sp,
            "slag_wt_pct": slag_wt,
            "slag_kg": slag_mass_sp,
            "offgas_kg": gas_sp,
            "dust_kg": dust_sp,
            "offgas_vol_pct": self._gas_vol_pct(gas_sp),

            "slag_properties": {
                "B2 (CaO/SiO2)": basicity_B2(slag_wt),
                "B3 ((CaO+MgO)/SiO2)": basicity_B3(slag_wt),
                "B4 ((CaO+MgO)/(SiO2+Al2O3))": basicity_B4(slag_wt),
                "Optical basicity": optical_basicity(slag_wt),
                "Al2O3/SiO2": slag_wt.get("Al2O3", 0.0)
                / max(slag_wt.get("SiO2", 1e-9), 1e-9),
                "Viscosity (Pa.s)": pr.slag_viscosity(slag_wt, T_slag),
                "Density (kg/m3)": pr.slag_density(slag_wt, T_slag),
                "Elec. conductivity (S/m)": pr.slag_conductivity_elec(slag_wt, T_slag),
                "Thermal cond. (W/m/K)": pr.slag_thermal_conductivity(slag_wt, T_slag),
                "Surface tension (N/m)": pr.slag_surface_tension(slag_wt, T_slag),
                "Liquidus (degC)": pr.slag_liquidus(slag_wt) - 273.15,
                "Superheat (degC)": T_slag - pr.slag_liquidus(slag_wt),
                "Foaming index (s)": pr.slag_foaming_index(slag_wt, T_slag),
                "Sulphide capacity": th.sulphide_capacity(slag_wt, T_slag),
            },
            "metal_properties": {
                "Density (kg/m3)": pr.metal_density(metal_wt, T),
                "Viscosity (mPa.s)": pr.metal_viscosity(metal_wt, T) * 1e3,
                "Liquidus (degC)": pr.metal_liquidus(metal_wt) - 273.15,
                "Superheat (degC)": T - pr.metal_liquidus(metal_wt),
                "C saturation (wt%)": carbon_saturation(i.tap_temperature_C, metal_wt),
                "C / C_sat": metal_wt.get("C", 0.0)
                / max(carbon_saturation(i.tap_temperature_C, metal_wt), 1e-6),
                "Surface tension (N/m)": pr.metal_surface_tension(metal_wt, T),
            },

            "warnings": list(getattr(self, "_warnings", [])),
            "slag_valorisation": slag_cement_suitability(slag_wt),
            "heat_balance_MJ_per_tHM": self._heat_terms(
                H_in, H_metal, H_slag_pure, H_mix, H_gas, H_calc,
                Q_loss_per_tHM, m_HM, hm_H, sl_H),

            "KPI": {
                "Si_equilibrium_wt_pct": Si_eq,
                "SEC_reversible_kWh_tHM": SEC_reversible,
                "SEC_thermodynamic_kWh_tHM": SEC_thermo,
                "SEC_operating_kWh_tHM": SEC_operating,
                "Heat_loss_kWh_tHM": Q_loss_per_tHM * KWH,
                "Slag_rate_kg_tHM": slag_rate,
                "Carbon_consumed_kg_tHM": C_cons,
                "Carbon_charged_kg_tHM": C_charged_rate,
                "Flux_rate_kg_tHM": (m_lime + m_dolo) / (m_HM / 1000.0),
                "Fe_yield_pct": Fe_yield,
                "Metal_yield_pct": m_HM / max(m_dri + m_scrap, 1e-9) * 100.0,
                "Electrode_consumption_kg_tHM": el_cons,
                "Offgas_rate_kg_tHM": m_gas / (m_HM / 1000.0),
                "CO2_direct_t_tHM": co2_direct,
                "CO2_indirect_t_tHM": co2_power / 1000.0,
                "CO2_total_t_tHM": co2_total,
                "Power_demand_MW": P_MW,
                "Productivity_tHM_h": i.productivity_tHM_h,
                "Specific_OPEX_USD_tHM": opex,
                "Power_intensity_MW_m2": P_MW / max(self.geo.bath_area, 1.0),
                # Quantities in the form used by the submerged-arc and open
                # slag bath furnace community, so that an operating point can
                # be read off directly in the units that community uses.
                "Hearth_power_density_kW_m2":
                    P_MW * 1.0e3 / max(self.geo.bath_area, 1.0),
                "Operating_resistance_mohm": el.get("operating_resistance_mohm",
                                                    float("nan")),
                "Slag_resistance_mohm": el.get("R_slag_ohm", 0.0) * 1.0e3,
                "Slag_liquidus_C": pr.slag_liquidus(slag_wt) - 273.15,
                "Slag_superheat_C": T_slag - pr.slag_liquidus(slag_wt),
            },
            "electrical": el,
            "heat_loss": hl,
            "lining_life": life,
            "closure": closure,
            "geometry": self.geo.summary(),
            "temperatures_C": {
                "Hot metal tap": i.tap_temperature_C,
                "Slag": T_slag - 273.15,
                "Off-gas": i.offgas_temperature_C,
                "DRI feed": i.dri_temperature_C,
            },
        }
        return self.result

    # ------------------------------------------------------------------
    @staticmethod
    def _estimate_slag_mass(SiO2, Al2O3, CaO, gangue, slag_wt) -> float:
        base = SiO2 + Al2O3 + CaO + gangue.get("MgO", 0.0) \
            + gangue.get("MnO", 0.0) + gangue.get("TiO2", 0.0)
        mgo_frac = max(0.02, slag_wt.get("MgO", 8.0) / 100.0)
        return base / max(1.0 - mgo_frac, 0.5)

    @staticmethod
    def _gas_vol_pct(gas_sp: Dict[str, float]) -> Dict[str, float]:
        n = {k: v / MW[k] for k, v in gas_sp.items() if v > 0 and k in MW}
        tot = sum(n.values())
        if tot <= 0:
            return {}
        return {k: v / tot * 100.0 for k, v in n.items()}

    @staticmethod
    def _heat_terms(H_in, H_metal, H_slag_pure, H_mix, H_gas, H_calc,
                    Q_loss_per_tHM, m_HM, hm_H=None, sl_H=None
                    ) -> Dict[str, float]:
        """Energy terms expressed as MJ per tonne of hot metal."""
        f = 1.0 / (m_HM / 1000.0) / 1e6         # J -> MJ/tHM
        d = {
            "Charge enthalpy in (abs.)": H_in * f,
            "Hot metal out (abs.)": H_metal * f,
            "Slag out (abs.)": H_slag_pure * f,
            "Slag mixing enthalpy": H_mix * f,
            "Off-gas out (abs.)": H_gas * f,
            "Calcination + moisture": H_calc * f,
            "Net process heat": (H_metal + H_slag_pure + H_mix + H_gas - H_in) * f,
            "Refractory + shell loss": Q_loss_per_tHM / 1e6,
        }
        if hm_H:
            d["  Hot metal sensible+fusion"] = hm_H["sensible"] * f
            d["  Hot metal dissolution"] = hm_H["dissolution"] * f
        if sl_H:
            d["  Slag sensible (to liquidus)"] = sl_H["sensible"] * f
            d["  Slag latent (solution)"] = sl_H["latent"] * f
            d["  Slag superheat"] = sl_H["superheat"] * f
        d["Total supplied to bath"] = d["Net process heat"] + d["Refractory + shell loss"]
        return d

    @staticmethod
    def _closure_check(charge, flux_sp, m_C_charged, metal_sp, slag_sp,
                       gas_sp, inp, scrap, m_scrap,
                       dust_sp=None) -> Dict[str, float]:
        """Element-by-element input/output closure, %."""
        dust_sp = dust_sp or {}
        def el_in_stream(stream: Dict[str, float], element: str) -> float:
            tot = 0.0
            for sp, m in stream.items():
                if m <= 0:
                    continue
                if sp == element:
                    tot += m
                elif sp in th.OXIDE_CATION and th.OXIDE_CATION[sp][0] == element:
                    tot += oxide_to_metal_mass(sp, m)
                elif sp == "CaS" and element == "S":
                    tot += m * MW["S"] / MW["CaS"]
                elif sp == "CaS" and element == "Ca":
                    tot += m * MW["Ca"] / MW["CaS"]
                elif sp in ("CO", "CO2") and element == "C":
                    tot += m * MW["C"] / MW[sp]
            return tot

        cs = CARBON_LIBRARY[inp.carbon_source]
        inflow = dict(charge)
        inflow["Fe"] = charge.get("Fe_met", 0.0)
        inflow.pop("Fe_met", None)
        for met, el in (("Mn_met", "Mn"), ("Si_met", "Si"), ("P_met", "P")):
            if met in inflow:
                inflow[el] = inflow.get(el, 0.0) + inflow.pop(met)
        for k, v in flux_sp.items():
            if k == "H2O":
                continue
            if k == "CO2":
                # carbonate carbon enters with the flux and leaves in the
                # off-gas, so it belongs on both sides of the balance
                inflow["C"] = inflow.get("C", 0.0) + v * MW["C"] / MW["CO2"]
                continue
            inflow[k] = inflow.get(k, 0.0) + v
        inflow["C"] = inflow.get("C", 0.0) + m_C_charged * cs["C"] / 100.0
        inflow["SiO2"] = inflow.get("SiO2", 0.0) \
            + m_C_charged * cs.get("ash_SiO2", 0.0) / 100.0
        inflow["Al2O3"] = inflow.get("Al2O3", 0.0) \
            + m_C_charged * cs.get("ash_Al2O3", 0.0) / 100.0
        inflow["S"] = inflow.get("S", 0.0) + m_C_charged * cs.get("S", 0.0) / 100.0

        out = {}
        for stream in (metal_sp, slag_sp, gas_sp, dust_sp):
            for k, v in stream.items():
                out[k] = out.get(k, 0.0) + v

        report = {}
        for el in ("Fe", "Si", "Ca", "Mg", "Al", "Mn", "Ti", "P", "S", "C"):
            a = el_in_stream(inflow, el)
            b = el_in_stream(out, el)
            if a > 1e-6:
                report[el] = (b - a) / a * 100.0
        report["max_abs_error_pct"] = max((abs(v) for v in report.values()),
                                          default=0.0)
        return report


# --------------------------------------------------------------------------
def run_static(**kwargs) -> Dict[str, object]:
    """Convenience wrapper: run_static(dri_name=..., tap_temperature_C=...)."""
    geo = kwargs.pop("geometry", None)
    elec = kwargs.pop("electrical", None)
    inp = ESFInputs(**kwargs)
    return ESFStaticModel(inp, geo, elec).solve()


def sweep(param: str, values, base: Optional[ESFInputs] = None,
          kpi: str = "SEC_thermodynamic_kWh_tHM",
          geo: Optional[FurnaceGeometry] = None) -> Tuple[list, list]:
    """One-dimensional parametric sweep returning (values, kpi_values)."""
    base = base or ESFInputs()
    xs, ys = [], []
    for v in values:
        inp = ESFInputs(**{**asdict(base), param: v})
        r = ESFStaticModel(inp, geo).solve()
        xs.append(v)
        ys.append(_dig(r, kpi))
    return xs, ys


def _dig(res: Dict, key: str):
    for section in ("KPI", "slag_properties", "metal_properties",
                    "hot_metal_wt_pct", "slag_wt_pct", "electrical"):
        if section in res and isinstance(res[section], dict) and key in res[section]:
            return res[section][key]
    return res.get(key)


__all__ = ["ESFInputs", "ESFStaticModel", "run_static", "sweep",
           "DRI_LIBRARY", "FLUX_LIBRARY", "CARBON_LIBRARY", "SCRAP_DEFAULT"]
