"""
ESF-DT :: electrical.py
=======================
Electrical and arc submodel for the Electric Smelting Furnace.

The open-slag-bath furnace (OSBF) runs with a short "brush" arc between the
electrode tip and the slag surface plus resistive (Joule) heating in the
conductive slag.  The submodel therefore couples:

*  an equivalent circuit  (transformer -> secondary -> electrode ->
   contact/arc -> slag path -> bath / adjacent electrode),
*  a channel-arc model (CAM) for the brush arc, giving arc voltage,
   radius and radiative fraction,
*  a slag-path resistance from the slag electrical conductivity and the
   electrode immersion geometry,
*  the power split between arc column, slag Joule volume, electrode
   ohmic loss and secondary circuit loss,
*  Soderberg / graphite electrode consumption.

Reference behaviour reproduced
------------------------------
*  Electrode-interface voltage drop of the order of 100-120 V for an
   applied 180-230 V (measured in industrial furnaces).
*  Joule heat increasing with both electrode immersion depth and slag
   electrical conductivity.
*  Arc length / radius growing with arc voltage and current.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict

from .properties import slag_conductivity_elec

MU0 = 4.0e-7 * math.pi


@dataclass
class ElectricalConfig:
    n_electrodes: int = 6
    n_phases: int = 3
    transformer_MVA: float = 135.0
    # Nominal voltage between one electrode and the bath on the reference
    # transformer tap.  It is a phase quantity, not a line-to-line one: the
    # circuit below applies it directly across the electrode-to-bath path.
    # An earlier comment described it as line-to-line, which did not match
    # how it is used and made the reported operating voltage look wrong.
    secondary_voltage_V: float = 420.0
    # Highest tap, as a multiple of the nominal.  The solver selects the tap
    # needed to meet the power setpoint, so the reported operating voltage
    # may exceed the nominal: that is a higher tap, not an inconsistency.
    tap_range_factor: float = 3.0
    power_factor: float = 0.86
    electrode_type: str = "Soderberg"       # Soderberg | Graphite
    electrode_diameter_m: float = 1.70
    electrode_resistivity: float = 55e-6    # ohm.m (Soderberg paste ~50-70)
    electrode_stickout_m: float = 2.4       # current-carrying length
    secondary_R_ohm: float = 0.22e-3
    secondary_X_ohm: float = 0.55e-3
    arc_mode: str = "brush"                 # brush | submerged | open
    control_mode: str = "power"             # power | current | resistance


def slag_path_resistance(sigma: float, d_el: float, immersion: float,
                         pitch: float, bath_depth: float,
                         n_el: int = 6) -> float:
    """
    Resistance of the slag current path for one electrode, ohm.

    Treats the immersed electrode as a cylinder plus hemispherical tip
    injecting current into a semi-infinite conducting medium bounded by the
    metal bath.  The classic spreading resistance of a cylindrical electrode
    of radius r, immersion h, into a medium of conductivity sigma is

        R = (1 / (2 pi sigma h)) * ln( L_eff / r )

    with L_eff set by the electrode pitch (electrode-to-electrode conduction)
    or by the distance to the metal bath, whichever is shorter.
    """
    r = 0.5 * d_el
    h = max(0.05, immersion)
    L_eff = max(1.2 * r, min(0.5 * pitch, bath_depth - immersion + r))
    R_cyl = math.log(max(L_eff / r, 1.05)) / (2.0 * math.pi * sigma * h)
    R_tip = 1.0 / (4.0 * sigma * r)          # hemispherical tip spreading
    R = 1.0 / (1.0 / R_cyl + 1.0 / R_tip)
    return max(1e-5, R)


def electrode_resistance(cfg: ElectricalConfig) -> float:
    A = math.pi * cfg.electrode_diameter_m ** 2 / 4.0
    return cfg.electrode_resistivity * cfg.electrode_stickout_m / A


def brush_arc(voltage_V: float, current_A: float, arc_len_m: float
              ) -> Dict[str, float]:
    """
    Channel-arc model of the short brush arc.

    Bowman / Jordan style relations:
        U_arc  = U_cathode+anode + E_col * L_arc
        E_col  ~ 1000-1400 V/m in a CO-rich atmosphere at 1 atm
        r_arc  = sqrt(I / (pi * j))   with j ~ 3.5e7 A/m2
    Radiative fraction of the arc power rises with arc length because a
    longer column radiates more of its enthalpy to the freeboard.
    """
    U_electrode_fall = 40.0                       # cathode + anode fall
    E_column = 1250.0                             # V/m
    U_arc = U_electrode_fall + E_column * max(arc_len_m, 0.0)
    j = 3.5e7
    r_arc = math.sqrt(max(current_A, 1.0) / (math.pi * j))
    P_arc = U_arc * current_A
    f_rad = min(0.75, 0.18 + 1.9 * arc_len_m)     # 0.18 submerged -> ~0.5 brush
    T_arc = 6500.0 + 1.2e-3 * current_A
    # magnetic pinch / arc jet velocity (Maecker)
    v_jet = math.sqrt(max(1.0, MU0 * current_A ** 2
                          / (4.0 * math.pi ** 2 * r_arc ** 2 * 0.25)))
    return {
        "U_arc_V": U_arc,
        "r_arc_m": r_arc,
        "P_arc_W": P_arc,
        "f_radiative": f_rad,
        "T_arc_K": T_arc,
        "v_jet_m_s": min(600.0, v_jet),
        "E_column_V_m": E_column,
    }


def solve_electrical(cfg: ElectricalConfig, slag_wt: Dict[str, float],
                     T_slag: float, immersion_m: float, arc_len_m: float,
                     pitch_m: float, slag_depth_m: float,
                     power_setpoint_MW: float | None = None,
                     tap_voltage_V: float | None = None) -> Dict[str, float]:
    """
    Solve the furnace electrical circuit.

    If `power_setpoint_MW` is given the tap voltage is adjusted (within the
    transformer envelope) to deliver that power; otherwise the supplied tap
    voltage is used directly.
    """
    sigma = slag_conductivity_elec(slag_wt, T_slag)
    R_slag = slag_path_resistance(sigma, cfg.electrode_diameter_m,
                                  immersion_m, pitch_m, slag_depth_m,
                                  cfg.n_electrodes)
    R_el = electrode_resistance(cfg)
    V = tap_voltage_V if tap_voltage_V else cfg.secondary_voltage_V

    def circuit(V_ph: float) -> Dict[str, float]:
        arc0 = brush_arc(V_ph, 1.0, arc_len_m)
        U_arc = arc0["U_arc_V"] if cfg.arc_mode != "submerged" else 0.0
        # solve I from V_ph = I*(R_slag + R_el + R_sec) + U_arc  (arc ~ const V)
        R_tot = R_slag + R_el + cfg.secondary_R_ohm
        Z = math.hypot(R_tot, cfg.secondary_X_ohm)
        I = max(0.0, (V_ph - U_arc)) / max(Z, 1e-6)
        arc = brush_arc(V_ph, I, arc_len_m)
        P_arc = arc["P_arc_W"] if cfg.arc_mode != "submerged" else 0.0
        P_slag = I * I * R_slag
        P_el = I * I * R_el
        P_sec = I * I * cfg.secondary_R_ohm
        P_ph = P_arc + P_slag + P_el + P_sec
        return dict(I=I, P_arc=P_arc, P_slag=P_slag, P_el=P_el,
                    P_sec=P_sec, P_ph=P_ph, arc=arc, U_arc=arc["U_arc_V"],
                    R_tot=R_tot)

    n_ph = cfg.n_electrodes / 2.0 if cfg.n_electrodes % 2 == 0 else cfg.n_electrodes
    if power_setpoint_MW is not None and power_setpoint_MW > 0:
        target = power_setpoint_MW * 1e6 / max(n_ph, 1.0)
        lo, hi = 20.0, cfg.tap_range_factor * max(cfg.secondary_voltage_V,
                                                  200.0)
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if circuit(mid)["P_ph"] < target:
                lo = mid
            else:
                hi = mid
        V = 0.5 * (lo + hi)

    c = circuit(V)
    P_total = c["P_ph"] * n_ph
    P_bath = (c["P_slag"]) * n_ph
    P_arc_tot = c["P_arc"] * n_ph
    P_losses = (c["P_el"] + c["P_sec"]) * n_ph
    arc = c["arc"]

    # power delivered to the process = slag Joule + non-radiated arc
    P_to_slag = P_bath + P_arc_tot * (1.0 - arc["f_radiative"])
    P_to_freeboard = P_arc_tot * arc["f_radiative"]

    # electrode consumption: Soderberg 4-6 kg/MWh, graphite 1.5-2.5 kg/MWh
    cons_rate = 5.0 if cfg.electrode_type.lower().startswith("sod") else 2.0
    return {
        "sigma_slag_S_m": sigma,
        "R_slag_ohm": R_slag,
        "R_electrode_ohm": R_el,
        "tap_voltage_V": V,
        # Reported alongside so that the relation between the nominal tap and
        # the selected operating tap is visible wherever the voltage is shown.
        "secondary_voltage_nominal_V": cfg.secondary_voltage_V,
        "tap_ratio_to_nominal": V / max(cfg.secondary_voltage_V, 1e-6),
        "current_A": c["I"],
        "current_density_A_cm2": c["I"] / (math.pi
                                           * (cfg.electrode_diameter_m * 100) ** 2 / 4.0),
        "U_arc_V": c["U_arc"],
        "arc_radius_m": arc["r_arc_m"],
        "arc_T_K": arc["T_arc_K"],
        "arc_jet_m_s": arc["v_jet_m_s"],
        "f_arc_radiative": arc["f_radiative"],
        "P_total_MW": P_total / 1e6,
        "P_slag_joule_MW": P_bath / 1e6,
        "P_arc_MW": P_arc_tot / 1e6,
        "P_electrode_loss_MW": P_losses / 1e6,
        "P_to_slag_MW": P_to_slag / 1e6,
        "P_to_freeboard_MW": P_to_freeboard / 1e6,
        "electrical_efficiency": P_to_slag / max(P_total, 1.0),
        "power_factor": cfg.power_factor,
        "apparent_MVA": P_total / 1e6 / max(cfg.power_factor, 0.5),
        "electrode_consumption_kg_MWh": cons_rate,
        "operating_resistance_mohm": c["R_tot"] * 1e3,
    }


__all__ = [n for n in dir() if not n.startswith("_")]
