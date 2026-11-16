"""
ESF-DT :: dynamic_model.py
==========================
Transient, multi-zone model of the Electric Smelting Furnace.

Zones (well-mixed control volumes)
----------------------------------
    PILE      unmelted DRI + flux + carbon sitting on the slag surface
    SLAG      molten oxide bath, electrically heated, open to the freeboard
    METAL     hot-metal hearth layer under the slag
    FREEBOARD CO / CO2 / N2 gas space above the bath
    LINING    quasi-steady multilayer refractory (recomputed periodically)

Physics resolved at every time step
-----------------------------------
*  Electrical  : slag Joule heating + brush-arc power, both dependent on the
                 instantaneous slag conductivity, electrode immersion and
                 arc length.
*  Heat        : pile heating and melting, slag/metal interfacial transfer,
                 wall and roof losses by coupled conduction/convection/
                 radiation, off-gas sensible heat, post-combustion return.
*  Mass        : elemental balances on Fe, C, Si, Mn, P, S, Ti, Ca, Mg, Al, O
                 across pile, slag, metal and gas.
*  Kinetics    : FeO reduction by dissolved C and by char, SiO2 and MnO
                 reduction (mixed control), carburiser dissolution, lime
                 dissolution (shrinking core with a C2S product layer),
                 Boudouard and freeboard post-combustion.
*  Operations  : feed schedules, power programme, electrode regulation,
                 metal and slag tapping, with a full time-stamped event log.

Every quantity written to the trajectory is a physical state, so the same
object drives the plots, the KPI panels and the schematic animation in the
GUIs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple

from . import thermo as th
from . import properties as pr
from .thermo import MW, normalise, oxide_to_metal_mass, metal_to_oxide_mass
from .geometry import FurnaceGeometry, heat_loss_network, lining_life_index
from .electrical import ElectricalConfig, solve_electrical
from .static_model import (DRI_LIBRARY, FLUX_LIBRARY, CARBON_LIBRARY,
                           SCRAP_DEFAULT, _split_flux,
                           _flux_calcination_heat)

R = 8.314462618
KWH = 1.0 / 3.6e6


# ==========================================================================
@dataclass
class Schedule:
    """Piecewise-constant time schedule; times in minutes."""
    points: List[Tuple[float, float]] = field(default_factory=list)
    default: float = 0.0

    def value(self, t_min: float) -> float:
        v = self.default
        for t0, val in self.points:
            if t_min >= t0:
                v = val
            else:
                break
        return v


@dataclass
class DynamicInputs:
    # --- run control -------------------------------------------------
    duration_min: float = 240.0
    dt_s: float = 10.0
    log_every_s: float = 60.0

    # --- feed ---------------------------------------------------------
    dri_name: str = "DRI-A (13.8 % gangue)"
    dri_composition: Dict[str, float] = field(default_factory=dict)
    metallisation_pct: float = 94.0
    dri_feed_t_h: float = 160.0
    dri_temperature_C: float = 600.0        # HDRI by default
    dri_particle_mm: float = 12.0
    scrap_feed_t_h: float = 0.0
    scrap_temperature_C: float = 25.0

    carbon_source: str = "Metallurgical coke"
    carbon_feed_kg_t_dri: float = 62.0
    carbon_particle_mm: float = 20.0
    flux_primary: str = "Burnt lime"
    flux_secondary: str = "Dolomitic lime"
    lime_feed_kg_t_dri: float = 73.0
    dolo_feed_kg_t_dri: float = 36.0
    flux_particle_mm: float = 25.0

    # --- power --------------------------------------------------------
    # Rated power of the transient base case.  This was 112 MW while the
    # freeboard gas temperature was computed from the old mixing rule,
    # which put the roof hot face above the bath and so suppressed the
    # open-bath radiation debit, at times to zero.  With that debit
    # restored, 112 MW saturates the temperature controller at 160 t/h
    # and the hot metal settles about 24 K below setpoint; 116 MW leaves
    # the loop with authority to spare at the same feed rate.
    power_MW: float = 116.0                 # rated / maximum active power
    power_control: str = "temperature"      # temperature | fixed | schedule
    power_min_fraction: float = 0.35
    # The integral is clamped below at +/-2.0e4 K.s, which with Ki caps
    # the integral's authority at 4.0 MW.  A steady bias larger than that
    # cannot be removed, so a residual offset of order 10 K between hot
    # metal and setpoint is a property of this tuning, not of the solver.
    Kp_power_MW_per_K: float = 1.10
    Ki_power_MW_per_Ks: float = 2.0e-4
    charge_enthalpy_MJ_kg: float = 1.15     # feed-forward melting demand
    power_schedule: Optional[Schedule] = None
    electrode_control: str = "resistance"   # resistance | fixed
    target_resistance_mohm: float = 1.6

    # --- initial bath -------------------------------------------------
    initial_metal_t: float = 420.0
    initial_slag_t: float = 260.0
    initial_metal_T_C: float = 1480.0
    initial_slag_T_C: float = 1545.0
    initial_slag_comp: Dict[str, float] = field(default_factory=lambda: {
        "SiO2": 34.0, "CaO": 37.5, "Al2O3": 13.5, "MgO": 8.0,
        "FeO": 3.5, "MnO": 1.0, "TiO2": 0.4, "CaS": 0.6})
    initial_metal_comp: Dict[str, float] = field(default_factory=lambda: {
        "Fe": 95.4, "C": 3.6, "Si": 0.35, "Mn": 0.55, "P": 0.06,
        "S": 0.025, "Ti": 0.015})

    # --- tapping ------------------------------------------------------
    metal_tap_interval_min: float = 60.0
    metal_tap_mass_t: float = 150.0
    metal_tap_duration_min: float = 12.0
    slag_tap_interval_min: float = 30.0
    slag_tap_mass_t: float = 24.0
    slag_tap_duration_min: float = 8.0
    first_metal_tap_min: float = 55.0
    first_slag_tap_min: float = 25.0

    # --- freeboard ----------------------------------------------------
    post_combustion_ratio: float = 0.15
    air_ingress_Nm3_t: float = 45.0
    offgas_extraction_efficiency: float = 0.95

    # --- efficiencies / control targets -------------------------------
    electrical_to_bath_efficiency: float = 0.92
    target_metal_T_C: float = 1500.0
    target_basicity_B2: float = 1.10
    lining_update_every_min: float = 5.0

    # --- kinetic parameters (tunable, plant-calibratable) -------------
    # mass-transfer / reaction pre-exponentials, k = k0 exp(-Ea/RT)  [m/s]
    k0_FeO_C: float = 3.0           # slag/metal FeO reduction by [C]
    Ea_FeO_C: float = 1.55e5        # J/mol
    k0_FeO_char: float = 0.90       # FeO reduction on floating char
    Ea_FeO_char: float = 1.60e5
    k0_SiO2: float = 20.0           # SiO2 reduction, slag-side control
    Ea_SiO2: float = 1.90e5
    k0_MnO: float = 5.5
    Ea_MnO: float = 1.80e5
    k0_C_diss: float = 2.0e-2       # carburiser dissolution into metal
    Ea_C_diss: float = 1.10e5
    tau_lime_s: float = 480.0       # lime dissolution time constant

    # --- solid-carbon behaviour, after Bae and Park (2025) -------------
    # Solid carbon is less dense than the slag and floats on it, forming a
    # physical barrier that keeps it away from the metal.  Only part of the
    # charged char is therefore in useful contact.
    carbon_contact_efficiency: float = 0.55
    # Reduction of FeO by solid carbon alone shows a measured incubation
    # period of about five minutes while CO/CO2 nucleates and a stable gas
    # film forms around the particles.  Dissolved carbon in the hot heel
    # removes that delay entirely.
    tau_incubation_s: float = 300.0
    hot_heel_C_ref_wt_pct: float = 1.0
    melt_htc_pile: float = 2000.0  # W/m2/K slag -> feed pile
    charge_softening_C: float = 1450.0   # pile temperature ceiling
    latent_charge_J_kg: float = 3.20e5   # latent heat of the charge
    slag_metal_htc_scale: float = 1.0
    # Averaging window for every mean reported in the summary, expressed as a
    # fraction of the campaign measured back from the end.  A single window is
    # used for all averaged quantities so that the reported means refer to a
    # stated period rather than to several different ones.
    summary_window_frac: float = 0.5


# ==========================================================================
class ESFDynamicModel:
    """Time-marching solver."""

    def __init__(self, inp: DynamicInputs,
                 geo: Optional[FurnaceGeometry] = None,
                 elec: Optional[ElectricalConfig] = None):
        self.inp = inp
        self.geo = geo or FurnaceGeometry()
        self.elec = elec or ElectricalConfig(
            n_electrodes=(geo or FurnaceGeometry()).n_electrodes)
        self.events: List[Dict] = []
        self.traj: Dict[str, List[float]] = {}
        self._hl_cache = None
        self._hl_last_t = -1e9
        # seed freeboard composition; replaced each step by the
        # composition computed from the actual gas streams
        self._gas_y = {"CO": 0.30, "CO2": 0.08, "N2": 0.62}

    # ------------------------------------------------------------------
    def log_event(self, t_min: float, kind: str, message: str,
                  **kw) -> None:
        e = {"t_min": round(t_min, 3),
             "clock": f"{int(t_min // 60):02d}:{int(t_min % 60):02d}:"
                      f"{int((t_min * 60) % 60):02d}",
             "type": kind, "message": message}
        e.update({k: (round(v, 4) if isinstance(v, float) else v)
                  for k, v in kw.items()})
        self.events.append(e)

    # ------------------------------------------------------------------
    def run(self, progress: Optional[Callable[[float], None]] = None
            ) -> Dict[str, object]:
        i = self.inp
        geo = self.geo
        dt = i.dt_s
        n_steps = int(i.duration_min * 60.0 / dt)
        log_every = max(1, int(i.log_every_s / dt))

        dri = normalise(dict(i.dri_composition) if i.dri_composition
                        else dict(DRI_LIBRARY[i.dri_name]))
        cs = CARBON_LIBRARY[i.carbon_source]
        MRfrac = min(1.0, max(0.5, i.metallisation_pct / 100.0))
        FeO_assay_frac = (dri.get("FeO", 0.0) / 100.0
                          + dri.get("Fe2O3", 0.0) / 100.0)

        # ---------- initial state ------------------------------------
        m_metal0 = i.initial_metal_t * 1000.0
        m_slag0 = i.initial_slag_t * 1000.0
        metal = {k: v / 100.0 * m_metal0
                 for k, v in normalise(dict(i.initial_metal_comp)).items()}
        slag = {k: v / 100.0 * m_slag0
                for k, v in normalise(dict(i.initial_slag_comp)).items()}
        pile: Dict[str, float] = {}
        char_kg = 0.0          # unreacted carbon particles floating in slag
        lime_undissolved = 0.0
        T_m = i.initial_metal_T_C + 273.15
        T_s = i.initial_slag_T_C + 273.15
        T_g = 1500.0 + 273.15
        T_pile = i.dri_temperature_C + 273.15

        cum = dict(energy_J=0.0, metal_tapped_t=0.0, slag_tapped_t=0.0,
                   metal_produced_t=0.0, slag_produced_t=0.0,
                   dri_charged_t=0.0, C_charged_t=0.0, flux_charged_t=0.0,
                   CO_Nm3=0.0, CO2_kg=0.0, electrode_kg=0.0)

        next_metal_tap = i.first_metal_tap_min
        next_slag_tap = i.first_slag_tap_min
        metal_tapping_until = -1.0
        slag_tapping_until = -1.0
        metal_tap_rate = 0.0
        slag_tap_rate = 0.0

        keys = ["t_min", "T_metal_C", "T_slag_C", "T_gas_C", "T_pile_C",
                "m_metal_t", "m_slag_t", "m_pile_t", "char_t",
                "power_MW", "P_slag_MW", "P_arc_MW", "P_to_bath_MW",
                "heat_loss_MW", "Q_pile_MW", "Q_slag_metal_MW",
                "melt_rate_t_h", "current_kA", "voltage_V",
                "resistance_mohm", "sigma_slag_S_m", "immersion_m",
                "C_pct", "Si_pct", "Mn_pct", "P_pct", "S_pct", "Ti_pct",
                "Fe_pct", "FeO_pct", "SiO2_pct", "CaO_pct", "MgO_pct",
                "Al2O3_pct", "MnO_pct", "TiO2_pct", "CaS_pct",
                "B2", "B3", "B4", "optical_basicity",
                "slag_visc_Pa_s", "slag_dens", "slag_liquidus_C",
                "slag_superheat_C", "metal_liquidus_C", "metal_superheat_C",
                "foaming_index_s", "C_sat_pct", "C_over_Csat",
                "r_FeO_kg_s", "r_Si_kg_s", "r_Mn_kg_s", "r_Cdiss_kg_s",
                "hot_heel_index", "char_incubation",
                "CO_Nm3_h", "CO2_kg_h", "offgas_T_C", "pcr",
                "freeze_mm", "shell_T_C", "hotface_slagwall_C",
                "SEC_cum_kWh_t", "energy_cum_MWh", "metal_tapped_t",
                "slag_tapped_t", "slag_rate_kg_t", "Fe_yield_pct",
                "dri_feed_t_h", "flux_feed_t_h", "carbon_feed_t_h",
                "wall_loss_MW", "roof_loss_MW", "hearth_loss_MW",
                "offgas_enthalpy_MW", "arc_rad_MW", "electrode_kg_cum",
                "CO2_intensity_t_t", "power_density_MW_m2"]
        traj = {k: [] for k in keys}

        self.log_event(0.0, "START",
                       f"Simulation started - {i.dri_name}, "
                       f"MR {i.metallisation_pct:.1f} %, "
                       f"power {i.power_MW:.1f} MW",
                       power_MW=i.power_MW, dri_feed_t_h=i.dri_feed_t_h)

        # ---------- march --------------------------------------------
        for step in range(n_steps + 1):
            t = step * dt
            t_min = t / 60.0
            m_slag = max(1.0, sum(slag.values()))
            m_metal = max(1.0, sum(metal.values()))
            m_pile = sum(pile.values())
            slag_wt = normalise(slag)
            metal_wt = normalise(metal)

            # ---- 1. electrical ------------------------------------
            if i.power_control == "schedule" and i.power_schedule:
                P_set = i.power_schedule.value(t_min)
            elif i.power_control == "temperature":
                # feed-forward: melting demand + measured lining losses
                charge_kg_s = (i.dri_feed_t_h * (1.0 + (i.carbon_feed_kg_t_dri
                                                        + i.lime_feed_kg_t_dri
                                                        + i.dolo_feed_kg_t_dri) / 1000.0)
                               + i.scrap_feed_t_h) * 1000.0 / 3600.0
                Q_loss_ff = (self._hl_cache["Q_total_W"] / 1e6
                             if self._hl_cache else 28.0)
                P_ff = (charge_kg_s * i.charge_enthalpy_MJ_kg + Q_loss_ff) \
                    / max(i.electrical_to_bath_efficiency, 0.5)
                err_T = (i.target_metal_T_C + 273.15) - T_m
                self._I_T = getattr(self, "_I_T", 0.0) + err_T * dt
                self._I_T = max(-2.0e4, min(2.0e4, self._I_T))
                P_set = (P_ff + i.Kp_power_MW_per_K * err_T
                         + i.Ki_power_MW_per_Ks * self._I_T)
                P_set = max(i.power_min_fraction * i.power_MW,
                            min(i.power_MW, P_set))
            else:
                P_set = i.power_MW
            slag_depth = m_slag / max(pr.slag_density(slag_wt, T_s)
                                      * geo.bath_area, 1e-6)
            metal_depth = m_metal / max(pr.metal_density(metal_wt, T_m)
                                        * geo.bath_area, 1e-6)
            immersion = max(0.10, min(0.75 * slag_depth,
                                      geo.electrode_immersion))
            self.elec.n_electrodes = geo.n_electrodes
            self.elec.electrode_diameter_m = geo.electrode_diameter
            el = solve_electrical(self.elec, slag_wt, T_s, immersion,
                                  geo.arc_length, geo.electrode_pitch,
                                  max(slag_depth, 0.3),
                                  power_setpoint_MW=P_set)
            P_bath = el["P_to_slag_MW"] * 1e6 * i.electrical_to_bath_efficiency
            P_fb = el["P_to_freeboard_MW"] * 1e6
            P_total = el["P_total_MW"] * 1e6
            cum["energy_J"] += P_total * dt
            cum["electrode_kg"] += (el["electrode_consumption_kg_MWh"]
                                    * P_total / 1e6 * dt / 3600.0)

            # ---- 2. feed ------------------------------------------
            dri_rate = i.dri_feed_t_h * 1000.0 / 3600.0
            scrap_rate = i.scrap_feed_t_h * 1000.0 / 3600.0
            c_rate = dri_rate * i.carbon_feed_kg_t_dri / 1000.0
            lime_rate = dri_rate * i.lime_feed_kg_t_dri / 1000.0
            dolo_rate = dri_rate * i.dolo_feed_kg_t_dri / 1000.0

            m_dri_in = dri_rate * dt
            # Same two reporting conventions as the static model: an
            # analysis that states an explicit iron-oxide assay has already
            # fixed its own metallisation, and applying the ratio again
            # would charge the oxidised iron twice.
            for sp, pct in dri.items():
                m = m_dri_in * pct / 100.0
                if sp == "Fe":
                    if FeO_assay_frac > 1e-9:
                        pile["Fe_met"] = pile.get("Fe_met", 0.0) + m
                    else:
                        pile["Fe_met"] = pile.get("Fe_met", 0.0) + m * MRfrac
                        pile["FeO"] = pile.get("FeO", 0.0) + \
                            metal_to_oxide_mass("FeO", m * (1.0 - MRfrac))
                elif sp == "Fe2O3":
                    pile["FeO"] = pile.get("FeO", 0.0) + metal_to_oxide_mass(
                        "FeO", oxide_to_metal_mass("Fe2O3", m))
                elif sp in ("Mn", "Si", "P"):
                    # metallic solutes arrive already reduced
                    pile[sp + "_met"] = pile.get(sp + "_met", 0.0) + m
                else:
                    pile[sp] = pile.get(sp, 0.0) + m
            if scrap_rate > 0:
                sc = normalise(dict(SCRAP_DEFAULT))
                for sp, pct in sc.items():
                    m = scrap_rate * dt * pct / 100.0
                    key = "Fe_met" if sp == "Fe" else sp
                    pile[key] = pile.get(key, 0.0) + m
            m_c_in = c_rate * dt
            pile["C_solid"] = pile.get("C_solid", 0.0) + m_c_in * cs["C"] / 100.0
            pile["SiO2"] = pile.get("SiO2", 0.0) + m_c_in * cs.get("ash_SiO2", 0) / 100.0
            pile["Al2O3"] = pile.get("Al2O3", 0.0) + m_c_in * cs.get("ash_Al2O3", 0) / 100.0
            pile["S"] = pile.get("S", 0.0) + m_c_in * cs.get("S", 0) / 100.0
            fl = _split_flux(i.flux_primary, lime_rate * dt)
            for k, v in _split_flux(i.flux_secondary, dolo_rate * dt).items():
                fl[k] = fl.get(k, 0.0) + v
            CO2_calc = fl.pop("CO2", 0.0)
            # A raw carbonate flux must be calcined in the furnace, and that
            # endotherm is paid by the bath.  Without it, charging limestone
            # instead of burnt lime would look free.
            Q_calcine = (
                _flux_calcination_heat(i.flux_primary, lime_rate * dt, T_g)
                + _flux_calcination_heat(i.flux_secondary, dolo_rate * dt,
                                         T_g)) / dt
            H2O_flux = fl.pop("H2O", 0.0)
            for k, v in fl.items():
                pile[k] = pile.get(k, 0.0) + v
            lime_undissolved += fl.get("CaO", 0.0) + fl.get("MgO", 0.0)

            cum["dri_charged_t"] += m_dri_in / 1000.0
            cum["C_charged_t"] += m_c_in / 1000.0
            cum["flux_charged_t"] += (lime_rate + dolo_rate) * dt / 1000.0

            # ---- 3. lining heat losses (quasi-steady) --------------
            # Freeboard composition on a mole basis, carried from the
            # previous step.  It is used for the grey-gas emissivity, so
            # it has to be the composition the gas actually has: the
            # reaction CO, the CO2 of calcination and post-combustion,
            # and the ingress air, which on this furnace is the larger
            # part of the freeboard mass flow and dilutes the radiating
            # species considerably.
            gas_y = self._gas_y
            if t_min - self._hl_last_t >= i.lining_update_every_min or self._hl_cache is None:
                self._hl_cache = heat_loss_network(
                    geo, T_s, T_m, T_g, slag_wt, gas_y,
                    arc_power_W=el["P_arc_MW"] * 1e6,
                    f_arc_radiation=el["f_arc_radiative"])
                self._hl_last_t = t_min
            hl = self._hl_cache
            Q_wall = hl["zones"]["slag_wall"]["Q_W"]
            Q_metal_wall = hl["zones"]["metal_wall"]["Q_W"]
            Q_hearth = hl["zones"]["hearth"]["Q_W"]
            Q_roof = hl["zones"]["roof"]["Q_W"]
            Q_fbwall = hl["zones"]["freeboard"]["Q_W"]
            T_hf_roof = hl["zones"]["roof"]["T_hotface_K"]
            # radiation leaving the open slag bath towards the roof and the
            # upper sidewall; this is a slag-side energy debit and it is what
            # the water-cooled panels above the bath ultimately remove.
            eps_bath = pr.slag_emissivity(slag_wt)
            Q_open_rad_gb = max(0.0, eps_bath * pr.SIGMA_SB
                                * geo.bath_area_free
                                * (T_s ** 4 - T_hf_roof ** 4) / 1.30)
            # Energy conservation bounds this debit: whatever the panels
            # above the bath remove has to have arrived either from the
            # bath or from the brush arcs, so the slag-side debit cannot
            # exceed the roof and upper-sidewall duty less the arc's own
            # radiation into the freeboard.  The grey-body figure is kept
            # as the upper bound.  Without this cap the grey-body estimate
            # over-debits the slag by one to two megawatts, which is the
            # bound the browser engine has always applied.
            Q_open_rad = max(0.0, min(
                Q_open_rad_gb,
                hl["zones"]["roof"]["Q_W"]
                + hl["zones"]["freeboard"]["Q_W"] - P_fb))

            # ---- 4. pile heating and melting ----------------------
            m_pile = sum(pile.values())
            A_pile = min(0.60 * geo.bath_area,
                         max(5.0, m_pile / 500.0))          # spread area
            h_pile = i.melt_htc_pile
            Q_pile_conv = h_pile * A_pile * max(0.0, T_s - T_pile)
            eps = 0.85
            Q_pile_rad = (eps * pr.SIGMA_SB * A_pile
                          * (max(T_g, T_pile) ** 4 - T_pile ** 4)) \
                + P_fb * min(0.6, A_pile / max(geo.bath_area, 1.0))
            Q_pile_total = Q_pile_conv + Q_pile_rad

            # Feed-pile enthalpy balance.  Melting happens at the pile/slag
            # interface, so the heat arriving is used to raise the material
            # that actually melts from the bulk pile temperature to the
            # softening temperature and then to supply its latent heat:
            #
            #     dh = cp (T_soft - T_pile) + L      [J/kg]
            #     melt = Q_avail / dh
            #
            # The bulk pile temperature follows from an enthalpy balance on
            # the pile, so a cold, fast feed depresses T_pile and slows
            # melting exactly as it does in the plant.
            cp_pile = 900.0
            T_soft = i.charge_softening_C + 273.15
            m_new = m_dri_in + scrap_rate * dt + m_c_in \
                + (lime_rate + dolo_rate) * dt
            T_feed = ((m_dri_in * (i.dri_temperature_C + 273.15)
                       + (m_new - m_dri_in) * 298.15) / m_new) \
                if m_new > 1e-9 else T_pile
            if m_pile > 1e-6:
                T_pile = ((m_pile - m_new) * T_pile + m_new * T_feed) / m_pile
            else:
                T_pile = T_feed
            T_pile = max(298.15, min(T_soft, T_pile))

            Q_avail = Q_pile_total * dt
            dh_spec = max(i.latent_charge_J_kg,
                          cp_pile * (T_soft - T_pile) + i.latent_charge_J_kg)
            melt_kg = min(m_pile, Q_avail / dh_spec)
            E_pile = m_pile * cp_pile * (T_pile - 298.15) + Q_avail \
                - melt_kg * (cp_pile * (T_soft - 298.15) + i.latent_charge_J_kg)
            m_pile_after = max(1e-6, m_pile - melt_kg)
            T_pile = 298.15 + E_pile / (m_pile_after * cp_pile)
            T_pile = max(298.15, min(T_soft, T_pile))
            f_melt = melt_kg / max(m_pile, 1e-9)
            melted = {k: v * f_melt for k, v in pile.items()}
            for k in list(pile):
                pile[k] -= melted[k]
                if pile[k] < 1e-9:
                    pile[k] = 0.0

            # route melted material
            for _m, _e in (("Mn_met", "Mn"), ("Si_met", "Si"),
                           ("P_met", "P")):
                _v = melted.pop(_m, 0.0)
                if _v > 0:
                    metal[_e] = metal.get(_e, 0.0) + _v
            fe_melted = melted.pop("Fe_met", 0.0)
            metal["Fe"] = metal.get("Fe", 0.0) + fe_melted
            cum["metal_produced_t"] += fe_melted / 0.955 / 1000.0
            char_kg += melted.pop("C_solid", 0.0)
            S_melt = melted.pop("S", 0.0)
            for k, v in melted.items():
                if v > 0:
                    slag[k] = slag.get(k, 0.0) + v
                    cum["slag_produced_t"] += v / 1000.0
            if S_melt > 0:
                slag["CaS"] = slag.get("CaS", 0.0) + S_melt * MW["CaS"] / MW["S"]

            m_slag = max(1.0, sum(slag.values()))
            m_metal = max(1.0, sum(metal.values()))
            slag_wt = normalise(slag)
            metal_wt = normalise(metal)

            # ---- 5. transport properties & interfacial areas ------
            eta_s = pr.slag_viscosity(slag_wt, T_s)
            rho_s = pr.slag_density(slag_wt, T_s)
            cp_s = pr.slag_cp(slag_wt)
            k_s = pr.slag_thermal_conductivity(slag_wt, T_s)
            rho_m = pr.metal_density(metal_wt, T_m)
            cp_m = pr.metal_cp(metal_wt)
            A_sm = geo.bath_area                     # slag/metal interface
            A_char = 6.0 * char_kg / (2000.0 * max(i.carbon_particle_mm, 1.0)
                                      / 1000.0)

            # ---- 6. reaction kinetics -----------------------------
            aFeO = th.a_FeO(slag_wt, T_s)
            aFeO_eq = th.feo_equilibrium(metal_wt, T_m, 1.0)
            C_FeO = slag_wt.get("FeO", 0.0) / 100.0 * rho_s / MW["FeO"]   # mol/m3
            drive = max(0.0, 1.0 - aFeO_eq / max(aFeO, 1e-9))
            k_FeO = i.k0_FeO_C * math.exp(-i.Ea_FeO_C / (R * T_s))
            n_FeO_C = k_FeO * A_sm * C_FeO * drive                        # mol/s
            k_ch = i.k0_FeO_char * math.exp(-i.Ea_FeO_char / (R * T_s))
            # Only the char actually wetted by slag and metal reacts; the
            # rest floats. And on solid carbon alone the reaction has to
            # nucleate a gas film first, which is the incubation period Bae
            # and Park measured. A hot heel carrying dissolved carbon
            # short-circuits that delay, so the incubation is scaled out as
            # the bath carbon rises.
            heel = min(1.0, (metal_wt.get("C", 0.0)
                             / max(i.hot_heel_C_ref_wt_pct, 1e-6)))
            f_incub = heel + (1.0 - heel) * (
                1.0 - math.exp(-t / max(i.tau_incubation_s, 1.0)))
            n_FeO_char = (k_ch * A_char * i.carbon_contact_efficiency
                          * f_incub * C_FeO * drive)
            n_FeO = n_FeO_C + n_FeO_char
            C_available = char_kg + 0.30 * metal.get("C", 0.0)
            m_FeO_red = min(slag.get("FeO", 0.0) * 0.5,
                            n_FeO * MW["FeO"] * dt,
                            C_available * MW["FeO"] / MW["C"])
            m_FeO_red = max(0.0, m_FeO_red)

            Si_eq = th.si_equilibrium(slag_wt, metal_wt, T_m, 1.0)
            k_Si = i.k0_SiO2 * math.exp(-i.Ea_SiO2 / (R * T_s))
            dSi = (Si_eq - metal_wt.get("Si", 0.0)) / 100.0
            m_Si = k_Si * A_sm * rho_m * dSi * dt
            m_Si = max(-0.25 * metal.get("Si", 0.0),
                       min(m_Si, slag.get("SiO2", 0.0) * MW["Si"]
                           / MW["SiO2"] * 0.05))

            Mn_eq = th.mn_equilibrium(slag_wt, metal_wt, T_m, 1.0)
            k_Mn = i.k0_MnO * math.exp(-i.Ea_MnO / (R * T_s))
            dMn = (Mn_eq - metal_wt.get("Mn", 0.0)) / 100.0
            m_Mn = k_Mn * A_sm * rho_m * dMn * dt
            m_Mn = max(-0.25 * metal.get("Mn", 0.0),
                       min(m_Mn, slag.get("MnO", 0.0) * MW["Mn"]
                           / MW["MnO"] * 0.20))

            # carburiser dissolution (particle-surface controlled)
            C_sat = th.carbon_saturation(T_m - 273.15, metal_wt)
            k_Cd = i.k0_C_diss * math.exp(-i.Ea_C_diss / (R * T_m))
            m_Cdiss = k_Cd * A_char * i.carbon_contact_efficiency * rho_m \
                * max(0.0, (C_sat - metal_wt.get("C", 0.0)) / 100.0) * dt
            m_Cdiss = min(m_Cdiss, max(0.0, char_kg - m_FeO_red
                                       * MW["C"] / MW["FeO"]) * 0.6)

            # lime dissolution (first-order relaxation, product-layer control)
            m_lime_diss = lime_undissolved * (1.0 - math.exp(-dt / i.tau_lime_s))
            lime_undissolved -= m_lime_diss

            # apply reactions
            if m_FeO_red > 0:
                slag["FeO"] = slag.get("FeO", 0.0) - m_FeO_red
                Fe_new = oxide_to_metal_mass("FeO", m_FeO_red)
                metal["Fe"] = metal.get("Fe", 0.0) + Fe_new
                cum["metal_produced_t"] += Fe_new / 0.955 / 1000.0
                # the FeO that is reduced never leaves as slag, so it must
                # not be counted in the slag production figure
                cum["slag_produced_t"] -= m_FeO_red / 1000.0
                C_used = m_FeO_red / MW["FeO"] * MW["C"]
                from_char = min(char_kg, C_used)
                char_kg -= from_char
                metal["C"] = max(0.0, metal.get("C", 0.0) - (C_used - from_char))
            if abs(m_Si) > 0:
                slag["SiO2"] = max(0.0, slag.get("SiO2", 0.0)
                                   - metal_to_oxide_mass("SiO2", m_Si))
                metal["Si"] = max(0.0, metal.get("Si", 0.0) + m_Si)
                metal["C"] = max(0.0, metal.get("C", 0.0)
                                 - 2.0 * m_Si / MW["Si"] * MW["C"])
            if abs(m_Mn) > 0:
                slag["MnO"] = max(0.0, slag.get("MnO", 0.0)
                                  - metal_to_oxide_mass("MnO", m_Mn))
                metal["Mn"] = max(0.0, metal.get("Mn", 0.0) + m_Mn)
                metal["C"] = max(0.0, metal.get("C", 0.0)
                                 - m_Mn / MW["Mn"] * MW["C"])
            if m_Cdiss > 0:
                char_kg -= m_Cdiss
                metal["C"] = metal.get("C", 0.0) + m_Cdiss

            # sulphur redistribution towards equilibrium partition
            LS = th.L_S(slag_wt, T_s, metal_wt,
                        th.oxygen_activity_CO(T_m,
                                              th.a_metal("C", metal_wt, T_m)))
            S_metal = metal.get("S", 0.0)
            S_slag = slag.get("CaS", 0.0) * MW["S"] / MW["CaS"]
            S_tot = S_metal + S_slag
            S_metal_eq = S_tot / (1.0 + LS * m_slag / max(m_metal, 1.0))
            relax_S = min(1.0, dt / 300.0)
            S_metal_new = S_metal + relax_S * (S_metal_eq - S_metal)
            metal["S"] = max(0.0, S_metal_new)
            slag["CaS"] = max(0.0, (S_tot - S_metal_new) * MW["CaS"] / MW["S"])

            # phosphorus: fully reduced under ESF conditions
            if slag.get("P2O5", 0.0) > 0:
                dP = slag["P2O5"] * min(1.0, dt / 600.0)
                slag["P2O5"] -= dP
                metal["P"] = metal.get("P", 0.0) + oxide_to_metal_mass("P2O5", dP)
            if slag.get("TiO2", 0.0) > 0:
                fTi = 0.70 + 0.30 * (T_m - 1773.15) / 60.0
                fTi = max(0.0, min(0.9, fTi))
                dTi = slag["TiO2"] * fTi * min(1.0, dt / 3000.0)
                slag["TiO2"] -= dTi
                metal["Ti"] = metal.get("Ti", 0.0) + oxide_to_metal_mass("TiO2", dTi)
                metal["C"] = max(0.0, metal.get("C", 0.0)
                                 - 2.0 * oxide_to_metal_mass("TiO2", dTi)
                                 / MW["Ti"] * MW["C"])

            # ---- 7. gas generation --------------------------------
            n_CO = (m_FeO_red / MW["FeO"]
                    + max(0.0, m_Si) / MW["Si"] * 2.0
                    + max(0.0, m_Mn) / MW["Mn"])
            Q_CO_Nm3_h = n_CO / dt * 22.414e-3 * 3600.0
            cum["CO_Nm3"] += n_CO * 22.414e-3
            pcr = i.post_combustion_ratio
            n_CO_burn = n_CO * pcr
            Q_pc = n_CO_burn * 282400.0 / dt          # W released in freeboard
            CO2_kg = (n_CO_burn * MW["CO2"] + CO2_calc)
            cum["CO2_kg"] += CO2_kg

            # ---- 8. energy balances --------------------------------
            dT_sm = T_s - T_m
            h_sm = pr.h_slag_metal(eta_s, k_s, abs(dT_sm), 1.0, rho_s, cp_s,
                                   stir=min(2.0, Q_CO_Nm3_h / 4000.0)) \
                * i.slag_metal_htc_scale
            Q_sm = h_sm * A_sm * dT_sm

            # reaction enthalpies (endothermic positive = heat sink)
            dH_rxn = 0.0
            dH_rxn += m_FeO_red / MW["FeO"] * (-th.dG0("FeO_C", T_s) * 0.0
                                               + 118500.0 * 0.0 + 152000.0)
            dH_rxn += max(0.0, m_Si) / MW["Si"] * 689000.0
            dH_rxn += max(0.0, m_Mn) / MW["Mn"] * 275000.0
            dH_rxn += m_Cdiss / MW["C"] * 22590.0
            dH_rxn /= dt                                        # W
            dH_rxn += Q_calcine                                 # W

            # Enthalpy the off-gas carries past the uptake, on a 298.15 K
            # datum.  This is a plant-level loss, not a bath-side one, and
            # it is deliberately absent from the slag and metal balances
            # below: the CO is generated in situ at bath temperature, and
            # the heat needed to bring it there is already carried by the
            # reaction enthalpies in dH_rxn, so debiting it a second time
            # here would count it twice.  The steady-state model works on
            # absolute enthalpies from the same datum for every stream, so
            # it does debit the gas at the uptake temperature; the two
            # conventions differ in bookkeeping, not in physics.  Reported
            # as an enthalpy flow rather than a loss for that reason.
            Q_offgas = n_CO / dt * MW["CO"] * 1150.0 * (T_g - 298.15) \
                + CO2_calc / dt * 1240.0 * (T_g - 298.15)
            Q_feed_sensible = 0.0

            # slag energy
            dEs = (P_bath - Q_sm - Q_wall - Q_open_rad
                   - Q_pile_total - dH_rxn) * dt
            T_s += dEs / max(m_slag * cp_s, 1e3)
            # metal energy
            dEm = (Q_sm - Q_metal_wall - Q_hearth) * dt
            T_m += dEm / max(m_metal * cp_m, 1e3)
            T_s = max(1300.0, min(2200.0, T_s))
            T_m = max(1300.0, min(2100.0, T_m))

            # ---- freeboard gas temperature ------------------------
            # The freeboard gas holds a negligible amount of heat
            # compared with the baths, so its temperature is obtained
            # from a steady balance rather than from an accumulation
            # term.  The gas is a participating medium: it absorbs from
            # the slag surface below and radiates to the roof and the
            # upper sidewall above, both of which are water cooled, and
            # it is carried through the freeboard at the rate the
            # reactions and the ingress air supply it.  Post-combustion
            # of CO releases Q_pc inside the gas itself.
            #
            #   m cp (Tg - Tin) = Q_pc
            #                   + eps_g sigma A_bath (Ts^4 - Tg^4)
            #                   - eps_g sigma A_roof (Tg^4 - Troof^4)
            #                   - eps_g sigma A_fb   (Tg^4 - Twall^4)
            #                   + h A_bath (Ts - Tg)
            #                   - h A_roof (Tg - Troof)
            #                   - h A_fb   (Tg - Twall)
            #
            # The left side is monotone increasing in Tg and every term
            # on the right is monotone decreasing, so the balance has a
            # single root, found below by bisection.
            #
            # This replaces an earlier mixing rule, Tg = 0.5 Ts +
            # 0.5 Troof + dT_pc, which entered the water-cooled roof as
            # a heat source carrying the same weight as the bath.  The
            # roof hot face is itself a response to the gas temperature
            # through heat_loss_network, so the two drove each other
            # upwards with a loop gain of one half, and the gas settled
            # roughly 200 K above the bath that is its only heat source,
            # with the roof hot face above the bath as well.  In the
            # balance below the cooled surfaces appear only in loss
            # terms, so the gas is bounded below by the coldest surface
            # it sees and above by the slag temperature plus the
            # adiabatic post-combustion rise.
            m_CO_s = n_CO / dt * MW["CO"]
            m_CO2_s = CO2_calc / dt
            m_air_s = (i.air_ingress_Nm3_t * 1.29 / 3600.0
                       * i.dri_feed_t_h)
            m_gas_s = max(0.05, m_CO_s + m_CO2_s + m_air_s)
            cp_g = 1200.0
            # CO and calcination CO2 leave the charge at bath
            # temperature; ingress air enters cold
            T_g_in = ((m_CO_s + m_CO2_s) * T_s
                      + m_air_s * 298.15) / m_gas_s
            T_hf_wall = hl["zones"]["freeboard"]["T_hotface_K"]
            A_bath_fb = geo.bath_area_free
            A_roof_fb = geo.area_roof
            A_wall_fb = geo.area_freeboard
            h_cv_fb = 22.0
            eps_g_fb = pr.gas_emissivity(gas_y, geo.mean_beam_length, T_g)
            C_rad = eps_g_fb * pr.SIGMA_SB

            def _freeboard_residual(Tg: float) -> float:
                return (Q_pc
                        - m_gas_s * cp_g * (Tg - T_g_in)
                        + C_rad * A_bath_fb * (T_s ** 4 - Tg ** 4)
                        - C_rad * A_roof_fb * (Tg ** 4 - T_hf_roof ** 4)
                        - C_rad * A_wall_fb * (Tg ** 4 - T_hf_wall ** 4)
                        + h_cv_fb * A_bath_fb * (T_s - Tg)
                        - h_cv_fb * A_roof_fb * (Tg - T_hf_roof)
                        - h_cv_fb * A_wall_fb * (Tg - T_hf_wall))

            lo, hi = 500.0, 2600.0
            if _freeboard_residual(lo) < 0.0:
                T_g_qs = lo
            elif _freeboard_residual(hi) > 0.0:
                T_g_qs = hi
            else:
                for _ in range(48):
                    mid = 0.5 * (lo + hi)
                    if _freeboard_residual(mid) > 0.0:
                        lo = mid
                    else:
                        hi = mid
                T_g_qs = 0.5 * (lo + hi)
            # the hot faces are taken from the previous network solve, so
            # the gas temperature is relaxed rather than set outright;
            # the relaxation changes the path, not the balance it settles on
            T_g += 0.50 * (T_g_qs - T_g)
            dT_pc = Q_pc / max(m_gas_s * cp_g, 1e3)
            T_g = max(600.0, min(2400.0, T_g))

            # Freeboard composition for the next step's emissivity.
            # n_CO and n_CO_burn are already molar amounts over the step
            # and MW is in kg/mol, so the air stream is the only one that
            # has to be converted from a mass rate.
            n_CO_out = max(0.0, n_CO - n_CO_burn) / dt
            n_CO2_out = n_CO_burn / dt + m_CO2_s / MW["CO2"]
            n_air_out = m_air_s / 0.028850
            n_tot_out = max(1e-9, n_CO_out + n_CO2_out + n_air_out)
            self._gas_y = {"CO": n_CO_out / n_tot_out,
                           "CO2": n_CO2_out / n_tot_out,
                           "N2": n_air_out / n_tot_out}

            # ---- 9. tapping ---------------------------------------
            if t_min >= next_metal_tap and metal_tapping_until < t_min:
                metal_tapping_until = t_min + i.metal_tap_duration_min
                metal_tap_rate = (i.metal_tap_mass_t * 1000.0
                                  / (i.metal_tap_duration_min * 60.0))
                next_metal_tap += i.metal_tap_interval_min
                self.log_event(t_min, "TAP-METAL",
                               f"Metal tap opened - target {i.metal_tap_mass_t:.0f} t "
                               f"over {i.metal_tap_duration_min:.0f} min",
                               T_metal_C=T_m - 273.15,
                               C_pct=normalise(metal).get("C", 0.0),
                               Si_pct=normalise(metal).get("Si", 0.0),
                               bath_t=m_metal / 1000.0)
            if t_min >= next_slag_tap and slag_tapping_until < t_min:
                slag_tapping_until = t_min + i.slag_tap_duration_min
                slag_tap_rate = (i.slag_tap_mass_t * 1000.0
                                 / (i.slag_tap_duration_min * 60.0))
                next_slag_tap += i.slag_tap_interval_min
                self.log_event(t_min, "TAP-SLAG",
                               f"Slag tap opened - target {i.slag_tap_mass_t:.0f} t "
                               f"over {i.slag_tap_duration_min:.0f} min",
                               T_slag_C=T_s - 273.15,
                               B2=th.basicity_B2(normalise(slag)),
                               FeO_pct=normalise(slag).get("FeO", 0.0))

            if t_min < metal_tapping_until and m_metal > 60.0e3:
                take = min(metal_tap_rate * dt, m_metal - 60.0e3)
                f = take / m_metal
                for k in metal:
                    metal[k] *= (1.0 - f)
                cum["metal_tapped_t"] += take / 1000.0
            elif metal_tapping_until > 0 and t_min >= metal_tapping_until:
                self.log_event(metal_tapping_until, "TAP-METAL-CLOSE",
                               "Metal tap-hole closed",
                               cum_metal_t=cum["metal_tapped_t"])
                metal_tapping_until = -1.0

            if t_min < slag_tapping_until and m_slag > 80.0e3:
                take = min(slag_tap_rate * dt, m_slag - 80.0e3)
                f = take / m_slag
                for k in slag:
                    slag[k] *= (1.0 - f)
                cum["slag_tapped_t"] += take / 1000.0
            elif slag_tapping_until > 0 and t_min >= slag_tapping_until:
                self.log_event(slag_tapping_until, "TAP-SLAG-CLOSE",
                               "Slag tap-hole closed",
                               cum_slag_t=cum["slag_tapped_t"])
                slag_tapping_until = -1.0

            # ---- 10. alarms & advisories --------------------------
            self._alarms(t_min, T_m, T_s, T_g, slag_wt, metal_wt, hl,
                         m_pile, el, eta_s)

            # ---- 11. logging --------------------------------------
            if step % log_every == 0:
                slag_wt = normalise(slag)
                metal_wt = normalise(metal)
                T_liq_s = pr.slag_liquidus(slag_wt)
                T_liq_m = pr.metal_liquidus(metal_wt)
                prod = max(cum["metal_produced_t"], 1e-3)
                sec = cum["energy_J"] * KWH / prod
                row = {
                    "t_min": t_min, "T_metal_C": T_m - 273.15,
                    "T_slag_C": T_s - 273.15, "T_gas_C": T_g - 273.15,
                    "T_pile_C": T_pile - 273.15,
                    "m_metal_t": m_metal / 1000.0, "m_slag_t": m_slag / 1000.0,
                    "m_pile_t": m_pile / 1000.0, "char_t": char_kg / 1000.0,
                    "power_MW": el["P_total_MW"],
                    "P_slag_MW": el["P_slag_joule_MW"],
                    "P_arc_MW": el["P_arc_MW"],
                    "P_to_bath_MW": P_bath / 1e6,
                    "heat_loss_MW": hl["Q_total_W"] / 1e6,
                    "Q_pile_MW": Q_pile_total / 1e6,
                    "Q_slag_metal_MW": Q_sm / 1e6,
                    "melt_rate_t_h": melt_kg / dt * 3.6,
                    "current_kA": el["current_A"] / 1000.0,
                    "voltage_V": el["tap_voltage_V"],
                    "resistance_mohm": el["operating_resistance_mohm"],
                    "sigma_slag_S_m": el["sigma_slag_S_m"],
                    "immersion_m": immersion,
                    "C_pct": metal_wt.get("C", 0.0),
                    "Si_pct": metal_wt.get("Si", 0.0),
                    "Mn_pct": metal_wt.get("Mn", 0.0),
                    "P_pct": metal_wt.get("P", 0.0),
                    "S_pct": metal_wt.get("S", 0.0),
                    "Ti_pct": metal_wt.get("Ti", 0.0),
                    "Fe_pct": metal_wt.get("Fe", 0.0),
                    "FeO_pct": slag_wt.get("FeO", 0.0),
                    "SiO2_pct": slag_wt.get("SiO2", 0.0),
                    "CaO_pct": slag_wt.get("CaO", 0.0),
                    "MgO_pct": slag_wt.get("MgO", 0.0),
                    "Al2O3_pct": slag_wt.get("Al2O3", 0.0),
                    "MnO_pct": slag_wt.get("MnO", 0.0),
                    "TiO2_pct": slag_wt.get("TiO2", 0.0),
                    "CaS_pct": slag_wt.get("CaS", 0.0),
                    "B2": th.basicity_B2(slag_wt),
                    "B3": th.basicity_B3(slag_wt),
                    "B4": th.basicity_B4(slag_wt),
                    "optical_basicity": th.optical_basicity(slag_wt),
                    "slag_visc_Pa_s": eta_s, "slag_dens": rho_s,
                    "slag_liquidus_C": T_liq_s - 273.15,
                    "slag_superheat_C": T_s - T_liq_s,
                    "metal_liquidus_C": T_liq_m - 273.15,
                    "metal_superheat_C": T_m - T_liq_m,
                    "foaming_index_s": pr.slag_foaming_index(slag_wt, T_s),
                    "C_sat_pct": C_sat,
                    "C_over_Csat": metal_wt.get("C", 0.0) / max(C_sat, 1e-6),
                    "r_FeO_kg_s": m_FeO_red / dt,
                    "r_Si_kg_s": m_Si / dt, "r_Mn_kg_s": m_Mn / dt,
                    "r_Cdiss_kg_s": m_Cdiss / dt,
                    "hot_heel_index": heel,
                    "char_incubation": f_incub,
                    "CO_Nm3_h": Q_CO_Nm3_h, "CO2_kg_h": CO2_kg / dt * 3600.0,
                    "offgas_T_C": T_g - 273.15, "pcr": pcr,
                    "freeze_mm": hl["freeze_thickness_m"] * 1000.0,
                    "shell_T_C": hl["T_shell_max_K"] - 273.15,
                    "hotface_slagwall_C": hl["zones"]["slag_wall"]["T_hotface_K"] - 273.15,
                    "SEC_cum_kWh_t": sec,
                    "energy_cum_MWh": cum["energy_J"] * KWH / 1000.0,
                    "metal_tapped_t": cum["metal_tapped_t"],
                    "slag_tapped_t": cum["slag_tapped_t"],
                    "slag_rate_kg_t": (cum["slag_produced_t"] * 1000.0
                                       / max(cum["metal_produced_t"], 1e-3)),
                    "Fe_yield_pct": min(100.0, 100.0 * (
                        1.0 - slag_wt.get("FeO", 0.0) * m_slag
                        * 0.7773 / max(m_metal, 1.0) / 100.0)),
                    "dri_feed_t_h": dri_rate * 3.6,
                    "flux_feed_t_h": (lime_rate + dolo_rate) * 3.6,
                    "carbon_feed_t_h": c_rate * 3.6,
                    "wall_loss_MW": (Q_wall + Q_metal_wall + Q_fbwall) / 1e6,
                    "roof_loss_MW": Q_roof / 1e6,
                    "hearth_loss_MW": Q_hearth / 1e6,
                    "offgas_enthalpy_MW": Q_offgas / 1e6,
                    "arc_rad_MW": P_fb / 1e6,
                    "electrode_kg_cum": cum["electrode_kg"],
                    "CO2_intensity_t_t": cum["CO2_kg"] / 1000.0
                    / max(cum["metal_produced_t"], 1e-3),
                    "power_density_MW_m2": el["P_total_MW"] / geo.bath_area,
                }
                for k in keys:
                    traj[k].append(row.get(k, 0.0))
            if progress and step % max(1, n_steps // 50) == 0:
                progress(step / max(n_steps, 1))

        self.log_event(i.duration_min, "END",
                       f"Simulation finished - {cum['metal_tapped_t']:.1f} t HM, "
                       f"{cum['slag_tapped_t']:.1f} t slag, "
                       f"{cum['energy_J'] * KWH / 1000.0:.1f} MWh",
                       SEC_kWh_t=cum["energy_J"] * KWH
                       / max(cum["metal_produced_t"], 1e-3))

        self.traj = traj
        life = lining_life_index(self._hl_cache, normalise(slag), T_s)
        return {
            "trajectory": traj,
            "events": self.events,
            "final_metal_kg": metal,
            "final_slag_kg": slag,
            "final_pile_kg": pile,
            "final_metal_wt_pct": normalise(metal),
            "final_slag_wt_pct": normalise(slag),
            "cumulative": cum,
            "lining_life": life,
            "heat_loss": self._hl_cache,
            "summary": self._summary(traj, cum, self.inp.summary_window_frac),
        }

    # ------------------------------------------------------------------
    def _alarms(self, t_min, T_m, T_s, T_g, slag_wt, metal_wt, hl,
                m_pile, el, eta_s) -> None:
        """Raise operating advisories once per condition transition."""
        if not hasattr(self, "_alarm_state"):
            self._alarm_state = {}
        st = self._alarm_state

        def fire(key, cond, kind, msg, **kw):
            was = st.get(key, False)
            if cond and not was:
                self.log_event(t_min, kind, msg, **kw)
            st[key] = cond

        T_liq = pr.slag_liquidus(slag_wt)
        fire("slag_cold", T_s - T_liq < 40.0, "ALARM",
             "Slag superheat below 40 K - freeze-up and tap-hole risk",
             slag_superheat_C=T_s - T_liq)
        fire("metal_cold", T_m - 273.15 < 1440.0, "ALARM",
             "Hot-metal temperature below 1440 degC - raise power",
             T_metal_C=T_m - 273.15)
        fire("metal_hot", T_m - 273.15 > 1545.0, "WARNING",
             "Hot-metal temperature above 1545 degC - refractory wear and "
             "excess Si pickup", T_metal_C=T_m - 273.15)
        fire("feo_high", slag_wt.get("FeO", 0.0) > 8.0, "ALARM",
             "Slag FeO above 8 wt% - iron loss and aggressive refractory attack",
             FeO_pct=slag_wt.get("FeO", 0.0))
        fire("si_high", metal_wt.get("Si", 0.0) > 1.0, "WARNING",
             "Silicon above 1.0 wt% in hot metal - BOF lime and oxygen demand "
             "will rise", Si_pct=metal_wt.get("Si", 0.0))
        fire("b2_low", th.basicity_B2(slag_wt) < 0.90, "WARNING",
             "Slag basicity B2 below 0.90 - increase lime addition",
             B2=th.basicity_B2(slag_wt))
        fire("b2_high", th.basicity_B2(slag_wt) > 1.35, "WARNING",
             "Slag basicity B2 above 1.35 - slag becomes short and viscous",
             B2=th.basicity_B2(slag_wt))
        fire("visc", eta_s > 1.2, "WARNING",
             "Slag viscosity above 1.2 Pa.s - poor stirring and slow melting",
             viscosity=eta_s)
        fire("pile", m_pile > 260.0e3, "WARNING",
             "Feed pile exceeding 260 t - melting rate limited, reduce feed "
             "or raise power", pile_t=m_pile / 1000.0)
        fire("freeze_thin", hl["freeze_thickness_m"] < 0.012, "ALARM",
             "Freeze lining thinner than 12 mm - increase slag-zone cooling",
             freeze_mm=hl["freeze_thickness_m"] * 1000.0)
        fire("shell", hl["T_shell_max_K"] - 273.15 > 220.0, "ALARM",
             "Shell temperature above 220 degC - inspect lining",
             shell_T_C=hl["T_shell_max_K"] - 273.15)
        fire("csat", metal_wt.get("C", 0.0)
             / max(th.carbon_saturation(T_m - 273.15, metal_wt), 1e-6) > 0.98,
             "WARNING", "Hot metal at carbon saturation - kish graphite risk")

    # ------------------------------------------------------------------
    @staticmethod
    def _summary(traj, cum, window_frac: float = 0.5) -> Dict[str, float]:
        def last(k):
            return traj[k][-1] if traj[k] else 0.0

        # Every mean below is taken over the same window: the final
        # `window_frac` of the campaign, measured back from the end.  The
        # window excludes the initial heating transient, during which the
        # bath is still approaching its operating temperature, so that the
        # reported means describe the operating period rather than the
        # start-up.  Quantities that are cumulative by nature (energy,
        # tapped mass, specific energy consumption) are reported over the
        # whole campaign and are labelled as such.
        def mean(k, frac=None):
            v = traj[k]
            if not v:
                return 0.0
            n = max(1, int(len(v) * (window_frac if frac is None else frac)))
            return sum(v[-n:]) / n

        t_end = last("t_min")
        return {
            "Averaging window (fraction of campaign)": window_frac,
            "Averaging window (min, from start of campaign)":
                round(t_end * (1.0 - window_frac), 1),
            "Campaign duration (min)": round(t_end, 1),
            "Hot metal tapped (t)": cum["metal_tapped_t"],
            "Slag tapped (t)": cum["slag_tapped_t"],
            "Slag rate (kg/tHM)": last("slag_rate_kg_t"),
            "Energy (MWh)": cum["energy_J"] * KWH / 1000.0,
            "Hot metal produced (t)": cum["metal_produced_t"],
            "SEC (kWh/tHM)": last("SEC_cum_kWh_t"),
            "Mean power (MW)": mean("power_MW"),
            "Mean heat loss (MW)": mean("heat_loss_MW"),
            "Heat loss share (%)": 100.0 * mean("heat_loss_MW")
            / max(mean("power_MW"), 1e-6),
            "Final C (wt%)": last("C_pct"),
            "Final Si (wt%)": last("Si_pct"),
            "Final Mn (wt%)": last("Mn_pct"),
            "Final S (wt%)": last("S_pct"),
            "Final P (wt%)": last("P_pct"),
            "Final slag FeO (wt%)": last("FeO_pct"),
            "Final B2": last("B2"),
            "Mean metal T (degC)": mean("T_metal_C"),
            "Mean slag T (degC)": mean("T_slag_C"),
            "Freeze lining (mm)": last("freeze_mm"),
            "Max shell T (degC)": max(traj["shell_T_C"]) if traj["shell_T_C"] else 0.0,
            "Electrode consumed (kg)": cum["electrode_kg"],
            "CO2 intensity (t/tHM)": last("CO2_intensity_t_t"),
            "Productivity (tHM/h)": cum["metal_produced_t"]
            / max(last("t_min") / 60.0, 1e-6),
            # Basis of the cumulative quantities, stated so that the means
            # above and the totals here cannot be confused.
            "Cumulative quantities basis": "whole campaign, including start-up",
            "Mean quantities basis":
                f"final {window_frac:.0%} of campaign",
        }


def run_dynamic(**kwargs) -> Dict[str, object]:
    geo = kwargs.pop("geometry", None)
    elec = kwargs.pop("electrical", None)
    inp = DynamicInputs(**kwargs)
    return ESFDynamicModel(inp, geo, elec).run()


__all__ = ["DynamicInputs", "ESFDynamicModel", "run_dynamic", "Schedule"]
