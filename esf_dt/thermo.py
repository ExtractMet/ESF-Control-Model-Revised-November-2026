"""
ESF-DT :: thermo.py
===================
Thermochemical foundation for the Electric Smelting Furnace (ESF / OSBF)
digital twin.

Contents
--------
1.  Molar masses and stoichiometric maps (oxide <-> element).
2.  Shomate-type heat-capacity polynomials and standard enthalpies of
    formation for every condensed and gaseous species carried by the model.
3.  Absolute enthalpy functions H(T) for solids, liquids and gases, with
    explicit latent heats of fusion.
4.  Reaction set (carbothermic reduction, carburisation, Boudouard,
    post-combustion, desulphurisation) with temperature-dependent
    Gibbs energies.
5.  Activity models
        - Metal phase : Wagner interaction formalism (Fe-C-Si-Mn-P-S-Ti).
        - Slag phase  : modified optical-basicity / regular-solution model
                        calibrated against the FactSage 7.0 results of
                        Owusu et al. (2026) for the CaO-SiO2-Al2O3-MgO-FeO-MnO
                        system relevant to DRI smelting.
6.  Distribution ratios (Si, Mn, P, S) and sulphide capacity.

Units
-----
    mass      kg
    amount    mol
    energy    J
    T         K unless the symbol carries `_C`
    pressure  atm

Author :  Extractmet Private Limited  (ESF-DT product line)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Tuple

R_GAS = 8.314462618          # J/mol/K
T_REF = 298.15               # K
KWH_PER_J = 1.0 / 3.6e6

# --------------------------------------------------------------------------
# 1. Molar masses  (kg/mol)
# --------------------------------------------------------------------------
MW: Dict[str, float] = {
    # elements / metal-phase species
    "Fe": 0.055845, "C": 0.012011, "Si": 0.028086, "Mn": 0.054938,
    "P": 0.030974, "S": 0.032065, "Ti": 0.047867, "Cr": 0.051996,
    "Ni": 0.058693, "V": 0.050942, "Cu": 0.063546, "Al": 0.026982,
    "Ca": 0.040078, "Mg": 0.024305, "O": 0.015999, "N": 0.014007,
    "H": 0.001008,
    # oxides / slag species
    "FeO": 0.071844, "Fe2O3": 0.159688, "Fe3O4": 0.231533,
    "SiO2": 0.060084, "CaO": 0.056077, "MgO": 0.040304,
    "Al2O3": 0.101961, "MnO": 0.070937, "TiO2": 0.079866,
    "Ti2O3": 0.143732, "P2O5": 0.141944, "V2O5": 0.181880,
    "Cr2O3": 0.151990, "Na2O": 0.061979, "K2O": 0.094196,
    "CaS": 0.072143, "CaCO3": 0.100087, "CaMg(CO3)2": 0.184401,
    # gases
    "CO": 0.028010, "CO2": 0.044009, "H2": 0.002016, "H2O": 0.018015,
    "N2": 0.028014, "O2": 0.031998, "CH4": 0.016043,
}

# oxide -> (element, moles element per mole oxide)
OXIDE_CATION: Dict[str, Tuple[str, float]] = {
    "FeO": ("Fe", 1.0), "Fe2O3": ("Fe", 2.0), "Fe3O4": ("Fe", 3.0),
    "SiO2": ("Si", 1.0), "MnO": ("Mn", 1.0), "TiO2": ("Ti", 1.0),
    "P2O5": ("P", 2.0), "V2O5": ("V", 2.0), "Cr2O3": ("Cr", 2.0),
    "CaO": ("Ca", 1.0), "MgO": ("Mg", 1.0), "Al2O3": ("Al", 2.0),
}

SLAG_SPECIES = ["FeO", "SiO2", "CaO", "MgO", "Al2O3", "MnO",
                "TiO2", "P2O5", "V2O5", "Cr2O3", "CaS", "Na2O", "K2O"]
METAL_SPECIES = ["Fe", "C", "Si", "Mn", "P", "S", "Ti", "Cr", "Ni", "V", "Cu"]
GAS_SPECIES = ["CO", "CO2", "H2", "H2O", "N2", "O2"]


def oxide_to_metal_mass(oxide: str, m_oxide: float) -> float:
    """Mass of contained cation element in `m_oxide` kg of oxide."""
    el, n = OXIDE_CATION[oxide]
    return m_oxide * (n * MW[el]) / MW[oxide]


def metal_to_oxide_mass(oxide: str, m_element: float) -> float:
    """Mass of oxide equivalent to `m_element` kg of the cation element."""
    el, n = OXIDE_CATION[oxide]
    return m_element * MW[oxide] / (n * MW[el])


# --------------------------------------------------------------------------
# 2. Thermodynamic data
#    Cp(T) = a + b*T + c*T^-2 + d*T^2      [J/mol/K]
#    valid over the phase window given; latent heat applied at Tm.
# --------------------------------------------------------------------------
@dataclass
class SpeciesThermo:
    name: str
    Hf298: float                 # J/mol, standard enthalpy of formation
    S298: float = 0.0            # J/mol/K
    cp_s: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    cp_l: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    Tm: float = 1.0e9            # melting point, K
    Hfus: float = 0.0            # J/mol
    Tb: float = 1.0e9
    Hvap: float = 0.0
    phase_at_298: str = "s"      # 's', 'l' or 'g'

    def cp(self, T: float) -> float:
        coeff = self.cp_l if (T >= self.Tm and self.cp_l[0] != 0.0) else self.cp_s
        a, b, c, d = coeff
        T = max(T, 200.0)
        return a + b * T + c / (T * T) + d * T * T

    def _integral(self, coeff, T1: float, T2: float) -> float:
        a, b, c, d = coeff
        f = lambda T: a * T + 0.5 * b * T * T - c / T + d * T ** 3 / 3.0
        return f(T2) - f(T1)

    def H(self, T: float, force_liquid: bool = False) -> float:
        """
        Absolute enthalpy referenced to elements at 298.15 K (J/mol).

        `force_liquid=True` returns the enthalpy of the *undercooled liquid*
        (solid path to Tm, latent heat, liquid Cp back down to T).  This is
        the correct reference for a solute that is liquid only because it is
        dissolved in an alloy or a slag whose liquidus lies below the pure
        substance melting point - e.g. Fe in 3.5 wt% C hot metal at 1500 degC.
        """
        if self.phase_at_298 == "g" or self.Tm >= 1.0e8:
            return self.Hf298 + self._integral(self.cp_s, T_REF, T)
        if T <= self.Tm and not force_liquid:
            return self.Hf298 + self._integral(self.cp_s, T_REF, T)
        h = self.Hf298 + self._integral(self.cp_s, T_REF, self.Tm) + self.Hfus
        coeff = self.cp_l if self.cp_l[0] != 0.0 else self.cp_s
        return h + self._integral(coeff, self.Tm, T)

    def h_mass(self, T: float, mw: float) -> float:
        """Specific enthalpy, J/kg."""
        return self.H(T) / mw


# Data assembled from Barin, JANAF, NIST-Shomate and FactSage FactPS.
# Where a liquid Cp is unknown the solid polynomial is retained.
DB: Dict[str, SpeciesThermo] = {
    "Fe": SpeciesThermo("Fe", 0.0, 27.3, (23.99, 8.36e-3, 0.0, 0.0),
                        (46.02, 0.0, 0.0, 0.0), 1811.0, 13807.0),
    "C": SpeciesThermo("C", 0.0, 5.74, (17.17, 4.27e-3, -8.79e5, 0.0),
                       (0, 0, 0, 0), 1.0e9, 0.0),
    "Si": SpeciesThermo("Si", 0.0, 18.8, (22.82, 3.86e-3, -3.54e5, 0.0),
                        (27.20, 0.0, 0.0, 0.0), 1687.0, 50210.0),
    "Mn": SpeciesThermo("Mn", 0.0, 32.0, (23.85, 14.14e-3, -1.57e5, 0.0),
                        (46.02, 0.0, 0.0, 0.0), 1519.0, 12058.0),
    "P": SpeciesThermo("P", 0.0, 41.1, (16.0, 22.6e-3, 0.0, 0.0),
                       (26.3, 0.0, 0.0, 0.0), 317.3, 659.0),
    "S": SpeciesThermo("S", 0.0, 32.1, (14.8, 24.0e-3, 0.0, 0.0),
                       (32.0, 0.0, 0.0, 0.0), 388.4, 1718.0),
    "Ti": SpeciesThermo("Ti", 0.0, 30.7, (22.09, 10.04e-3, -0.13e5, 0.0),
                        (47.24, 0.0, 0.0, 0.0), 1941.0, 14150.0),
    "Cr": SpeciesThermo("Cr", 0.0, 23.6, (21.6, 8.9e-3, -0.9e5, 0.0),
                        (39.3, 0.0, 0.0, 0.0), 2180.0, 21000.0),
    "Ni": SpeciesThermo("Ni", 0.0, 29.9, (25.1, 7.8e-3, 0.0, 0.0),
                        (43.1, 0.0, 0.0, 0.0), 1728.0, 17480.0),
    "V": SpeciesThermo("V", 0.0, 28.9, (20.5, 10.8e-3, 0.0, 0.0),
                       (46.4, 0.0, 0.0, 0.0), 2183.0, 21500.0),
    "Cu": SpeciesThermo("Cu", 0.0, 33.2, (22.6, 6.3e-3, 0.0, 0.0),
                        (32.8, 0.0, 0.0, 0.0), 1358.0, 13260.0),
    "Al": SpeciesThermo("Al", 0.0, 28.3, (20.7, 12.4e-3, 0.0, 0.0),
                        (31.8, 0.0, 0.0, 0.0), 933.5, 10700.0),

    # --- oxides -----------------------------------------------------------
    "FeO": SpeciesThermo("FeO", -272044.0, 60.8, (50.80, 8.61e-3, -3.31e5, 0.0),
                         (68.20, 0.0, 0.0, 0.0), 1650.0, 24058.0),
    "Fe2O3": SpeciesThermo("Fe2O3", -825503.0, 87.4, (98.28, 77.82e-3, -14.85e5, 0.0),
                           (142.0, 0.0, 0.0, 0.0), 1895.0, 138000.0),
    "Fe3O4": SpeciesThermo("Fe3O4", -1120894.0, 146.1, (91.55, 201.7e-3, 0.0, 0.0),
                           (200.0, 0.0, 0.0, 0.0), 1870.0, 138000.0),
    "SiO2": SpeciesThermo("SiO2", -910700.0, 41.5, (58.93, 10.04e-3, -14.42e5, 0.0),
                          (85.77, 0.0, 0.0, 0.0), 1996.0, 9585.0),
    "CaO": SpeciesThermo("CaO", -635090.0, 38.1, (50.42, 4.18e-3, -8.49e5, 0.0),
                         (62.76, 0.0, 0.0, 0.0), 3200.0, 79500.0),
    "MgO": SpeciesThermo("MgO", -601600.0, 26.9, (48.98, 3.14e-3, -11.34e5, 0.0),
                         (66.94, 0.0, 0.0, 0.0), 3098.0, 77000.0),
    "Al2O3": SpeciesThermo("Al2O3", -1675700.0, 50.9, (117.49, 10.38e-3, -37.11e5, 0.0),
                           (144.9, 0.0, 0.0, 0.0), 2327.0, 111100.0),
    "MnO": SpeciesThermo("MnO", -385221.0, 59.7, (46.48, 8.12e-3, -3.68e5, 0.0),
                         (60.67, 0.0, 0.0, 0.0), 2058.0, 54400.0),
    "TiO2": SpeciesThermo("TiO2", -944750.0, 50.6, (73.35, 3.05e-3, -17.03e5, 0.0),
                          (100.4, 0.0, 0.0, 0.0), 2130.0, 68000.0),
    "Ti2O3": SpeciesThermo("Ti2O3", -1520900.0, 78.8, (135.0, 12.0e-3, -25.0e5, 0.0),
                           (170.0, 0.0, 0.0, 0.0), 2115.0, 90000.0),
    "P2O5": SpeciesThermo("P2O5", -1492000.0, 114.4, (143.0, 40.0e-3, -22.0e5, 0.0),
                          (190.0, 0.0, 0.0, 0.0), 853.0, 30000.0),
    "V2O5": SpeciesThermo("V2O5", -1550600.0, 131.0, (122.0, 60.0e-3, -20.0e5, 0.0),
                          (190.0, 0.0, 0.0, 0.0), 943.0, 64500.0),
    "Cr2O3": SpeciesThermo("Cr2O3", -1139700.0, 81.2, (119.4, 9.2e-3, -15.7e5, 0.0),
                           (160.0, 0.0, 0.0, 0.0), 2603.0, 117000.0),
    "Na2O": SpeciesThermo("Na2O", -414200.0, 75.1, (66.2, 43.8e-3, 0.0, 0.0),
                          (104.6, 0.0, 0.0, 0.0), 1405.0, 47700.0),
    "K2O": SpeciesThermo("K2O", -363200.0, 94.1, (70.0, 40.0e-3, 0.0, 0.0),
                         (110.0, 0.0, 0.0, 0.0), 1013.0, 27900.0),
    "CaS": SpeciesThermo("CaS", -482400.0, 56.5, (45.5, 7.0e-3, -2.5e5, 0.0),
                         (67.0, 0.0, 0.0, 0.0), 2798.0, 60000.0),
    "CaCO3": SpeciesThermo("CaCO3", -1206900.0, 92.9, (104.5, 21.9e-3, -25.9e5, 0.0),
                           (0, 0, 0, 0), 1.0e9, 0.0),
    "CaMg(CO3)2": SpeciesThermo("CaMg(CO3)2", -2326300.0, 155.2,
                                (180.0, 40.0e-3, -45.0e5, 0.0),
                                (0, 0, 0, 0), 1.0e9, 0.0),

    # --- gases ------------------------------------------------------------
    "CO": SpeciesThermo("CO", -110530.0, 197.7, (28.41, 4.10e-3, -0.46e5, 0.0),
                        phase_at_298="g"),
    "CO2": SpeciesThermo("CO2", -393510.0, 213.8, (44.14, 9.04e-3, -8.54e5, 0.0),
                         phase_at_298="g"),
    "H2": SpeciesThermo("H2", 0.0, 130.7, (27.28, 3.26e-3, 0.50e5, 0.0),
                        phase_at_298="g"),
    "H2O": SpeciesThermo("H2O", -241830.0, 188.8, (30.00, 10.71e-3, 0.33e5, 0.0),
                         phase_at_298="g"),
    "N2": SpeciesThermo("N2", 0.0, 191.6, (27.87, 4.27e-3, 0.0, 0.0),
                        phase_at_298="g"),
    "O2": SpeciesThermo("O2", 0.0, 205.2, (29.96, 4.18e-3, -1.67e5, 0.0),
                        phase_at_298="g"),
}


def H_species(sp: str, T: float) -> float:
    """Absolute molar enthalpy J/mol at T (K), referenced to elements @298 K."""
    return DB[sp].H(T)


def h_specific(sp: str, T: float) -> float:
    """Specific enthalpy J/kg."""
    return DB[sp].H(T) / MW[sp]


def sensible_heat(sp: str, m_kg: float, T_from: float, T_to: float) -> float:
    """Heat (J) required to take m_kg of species from T_from to T_to."""
    n = m_kg / MW[sp]
    return n * (DB[sp].H(T_to) - DB[sp].H(T_from))


# --------------------------------------------------------------------------
# 3. Dissolution enthalpies in liquid iron (J/mol solute)
#    X(pure, 298 K) -> [X] (1 wt% std state in liquid Fe)
# --------------------------------------------------------------------------
H_DISSOLUTION = {
    "C":  22590.0,      # graphite -> [C],  endothermic
    "Si": -131500.0,    # Si(l)   -> [Si],  exothermic
    "Mn": 4080.0,
    "P":  -122200.0,
    "S":  -135100.0,
    "Ti": -69500.0,
    "Cr": 19250.0,
    "Ni": -20900.0,
    "V":  -20700.0,
    "Cu": 33500.0,
}


# --------------------------------------------------------------------------
# 4. Reaction Gibbs energies  dG0 = A + B*T  (J/mol), 1500-1900 K
#    Reference states: [X] = 1 wt% in Fe(l); (MO) = pure liquid oxide;
#    {CO} = 1 atm.
# --------------------------------------------------------------------------
REACTIONS = {
    # (FeO) + [C] = Fe(l) + {CO}
    "FeO_C":   dict(A=-118500.0, B=-102.5,
                    eq="(FeO) + [C] = Fe(l) + {CO}"),
    # (FeO) + {CO} = Fe(l) + {CO2}
    "FeO_CO":  dict(A=-22800.0, B=24.3,
                    eq="(FeO) + {CO} = Fe(l) + {CO2}"),
    # {C} + {CO2} = 2{CO}   (Boudouard)
    "boudouard": dict(A=170700.0, B=-174.5,
                      eq="C(s) + {CO2} = 2{CO}"),
    # (SiO2) + 2[C] = [Si] + 2{CO}
    # A refitted from 581 500 when the spurious square on the silica mole
    # fraction was removed from a_SiO2; see the note there.  Fitted to the
    # two printed silicon anchors of Owusu et al., 0.03 wt% at 1400 degC and
    # 0.62 wt% at 1525 degC.
    "SiO2_C":  dict(A=596200.0, B=-329.5,
                    eq="(SiO2) + 2[C] = [Si] + 2{CO}"),
    # (MnO) + [C] = [Mn] + {CO}
    "MnO_C":   dict(A=230600.0, B=-143.0,
                    eq="(MnO) + [C] = [Mn] + {CO}"),
    # (P2O5) + 5[C] = 2[P] + 5{CO}
    "P2O5_C":  dict(A=553500.0, B=-541.0,
                    eq="(P2O5) + 5[C] = 2[P] + 5{CO}"),
    # (TiO2) + 2[C] = [Ti] + 2{CO}
    "TiO2_C":  dict(A=723000.0, B=-337.0,
                    eq="(TiO2) + 2[C] = [Ti] + 2{CO}"),
    # (Cr2O3) + 3[C] = 2[Cr] + 3{CO}
    "Cr2O3_C": dict(A=782000.0, B=-534.0,
                    eq="(Cr2O3) + 3[C] = 2[Cr] + 3{CO}"),
    # [S] + (CaO) + [C] = (CaS) + {CO}
    "desulph": dict(A=105000.0, B=-72.0,
                    eq="[S] + (CaO) + [C] = (CaS) + {CO}"),
    # {CO} + 1/2{O2} = {CO2}   (post-combustion)
    "pcr":     dict(A=-282400.0, B=86.8,
                    eq="{CO} + 1/2{O2} = {CO2}"),
}


def dG0(reaction: str, T: float) -> float:
    r = REACTIONS[reaction]
    return r["A"] + r["B"] * T


def Keq(reaction: str, T: float) -> float:
    return math.exp(-dG0(reaction, T) / (R_GAS * T))


# --------------------------------------------------------------------------
# 5a. Metal-phase activity : Wagner first-order interaction parameters
#     e_i^j at 1873 K; scaled as e(T) = e(1873)*1873/T
# --------------------------------------------------------------------------
WAGNER_1873 = {
    "C":  {"C": 0.14, "Si": 0.08, "Mn": -0.012, "P": 0.051, "S": 0.046,
           "Ti": -0.165, "Cr": -0.024, "Ni": 0.012},
    "Si": {"C": 0.18, "Si": 0.11, "Mn": 0.002, "P": 0.11, "S": 0.056,
           "Ti": -0.03, "Cr": -0.0003, "Ni": 0.005},
    "Mn": {"C": -0.07, "Si": 0.0, "Mn": 0.0, "P": -0.0035, "S": -0.048},
    "P":  {"C": 0.13, "Si": 0.12, "Mn": 0.0, "P": 0.062, "S": 0.028},
    "S":  {"C": 0.11, "Si": 0.063, "Mn": -0.026, "P": 0.029, "S": -0.028,
           "Ti": -0.072, "Cr": -0.011},
    "Ti": {"C": -0.16, "Si": 0.05, "Ti": 0.013, "S": -0.11},
    "Cr": {"C": -0.12, "Si": -0.0043, "Cr": -0.0003, "S": -0.02},
}


def gamma_wagner(solute: str, wt: Dict[str, float], T: float) -> float:
    """1-wt% activity coefficient of `solute` in liquid Fe (Wagner, 1st order)."""
    if solute not in WAGNER_1873:
        return 1.0
    scale = 1873.0 / max(T, 1200.0)
    log_g = 0.0
    for j, e in WAGNER_1873[solute].items():
        log_g += e * scale * wt.get(j, 0.0)
    return 10.0 ** log_g


def a_metal(solute: str, wt: Dict[str, float], T: float) -> float:
    """Henrian 1-wt% activity."""
    return gamma_wagner(solute, wt, T) * wt.get(solute, 0.0)


def carbon_saturation(T_C: float, wt: Dict[str, float] | None = None) -> float:
    """
    Carbon solubility in liquid iron (wt%).
    Base : %C_sat = 1.30 + 2.57e-3 * T(degC)     (Neumann / Chipman)
    Corrected for Si, Mn, P, S, Ti and Cr.
    """
    cs = 1.30 + 2.57e-3 * T_C
    if wt:
        cs += (-0.31 * wt.get("Si", 0.0)
               + 0.027 * wt.get("Mn", 0.0)
               - 0.30 * wt.get("P", 0.0)
               - 0.04 * wt.get("S", 0.0)
               + 0.06 * wt.get("Cr", 0.0)
               - 0.10 * wt.get("Ti", 0.0))
    return max(0.5, cs)


# --------------------------------------------------------------------------
# 5b. Slag-phase model
# --------------------------------------------------------------------------
# Optical basicity of the pure oxides (Duffy & Ingram)
LAMBDA_OPT = {
    "CaO": 1.00, "MgO": 0.78, "SiO2": 0.48, "Al2O3": 0.60, "FeO": 1.00,
    "MnO": 0.95, "TiO2": 0.61, "P2O5": 0.40, "Cr2O3": 0.77, "V2O5": 0.45,
    "Na2O": 1.15, "K2O": 1.40, "CaS": 1.00,
}
N_OXYGEN = {
    "CaO": 1, "MgO": 1, "SiO2": 2, "Al2O3": 3, "FeO": 1, "MnO": 1,
    "TiO2": 2, "P2O5": 5, "Cr2O3": 3, "V2O5": 5, "Na2O": 1, "K2O": 1,
    "CaS": 0,
}


def mole_fractions(wt_pct: Dict[str, float]) -> Dict[str, float]:
    n = {k: (v / 100.0) / MW[k] for k, v in wt_pct.items() if v > 0 and k in MW}
    tot = sum(n.values())
    if tot <= 0:
        return {k: 0.0 for k in wt_pct}
    return {k: v / tot for k, v in n.items()}


def optical_basicity(slag_wt: Dict[str, float]) -> float:
    """Corrected optical basicity of the slag."""
    x = mole_fractions(slag_wt)
    num = den = 0.0
    for sp, xi in x.items():
        if sp in LAMBDA_OPT and N_OXYGEN.get(sp, 0) > 0:
            num += xi * N_OXYGEN[sp] * LAMBDA_OPT[sp]
            den += xi * N_OXYGEN[sp]
    return num / den if den > 0 else 0.6


def basicity_B2(slag_wt: Dict[str, float]) -> float:
    s = slag_wt.get("SiO2", 0.0)
    return slag_wt.get("CaO", 0.0) / s if s > 1e-9 else 0.0


def basicity_B3(slag_wt: Dict[str, float]) -> float:
    s = slag_wt.get("SiO2", 0.0)
    return (slag_wt.get("CaO", 0.0) + slag_wt.get("MgO", 0.0)) / s if s > 1e-9 else 0.0


def basicity_B4(slag_wt: Dict[str, float]) -> float:
    d = slag_wt.get("SiO2", 0.0) + slag_wt.get("Al2O3", 0.0)
    return (slag_wt.get("CaO", 0.0) + slag_wt.get("MgO", 0.0)) / d if d > 1e-9 else 0.0


def a_FeO(slag_wt: Dict[str, float], T: float) -> float:
    """
    Activity of FeO in the smelter slag.
    gamma_FeO is regressed on optical basicity; it rises steeply as the slag
    becomes more basic and more alumina-rich (Al2O3 forces FeO out of the
    silicate network).  Calibrated so that FeO activity coefficients fall in
    the 1.5-3.5 band typical of CaO-SiO2-Al2O3-MgO smelter slags at 1773 K.
    """
    x = mole_fractions(slag_wt)
    xFeO = x.get("FeO", 0.0)
    Lam = optical_basicity(slag_wt)
    g = 1.42 * math.exp(2.15 * (Lam - 0.58)) * (1.0 + 0.55 * x.get("Al2O3", 0.0))
    g *= math.exp(2400.0 * (1.0 / T - 1.0 / 1773.0))
    return max(1e-9, g * xFeO)


def a_SiO2(slag_wt: Dict[str, float], T: float) -> float:
    """
    Activity of SiO2 referenced to pure liquid silica, written in the ordinary
    way as an activity coefficient multiplying the mole fraction.

    Earlier versions squared the mole fraction, described in the code as a
    quasi-chemical exponent.  That was wrong and has been corrected.  There
    were three reasons to remove it.  It made this the only oxide in the model
    not written to the first power, while FeO, MnO and TiO2 all were, so no
    structural argument could justify it here and not there.  The silica mole
    fraction varies by only about 1 % across the four anchors the expression
    was fitted to, and by about 29 % across the whole operating range, so the
    exponent was absorbed almost entirely into the Gibbs energy of Eq. (8)
    rather than being determined by the data.  And refitting that Gibbs energy
    with the first power reproduces the published anchors more closely than
    the squared form did, to 1.2 % and 0.9 % against 3.3 % and 6.7 %.

    The coefficient below is an empirical correlation in basicity, alumina
    ratio and temperature, fitted as described in Section 5.3; it is not
    taken from a solution model.
    """
    x = mole_fractions(slag_wt)
    xSi = x.get("SiO2", 0.0)
    B = basicity_B3(slag_wt)
    Al = slag_wt.get("Al2O3", 0.0) / max(slag_wt.get("SiO2", 1e-9), 1e-9)
    log_g = -2.05 * (B - 1.0) - 0.42 * Al - 0.35
    g = 10.0 ** log_g
    g *= math.exp(-3100.0 * (1.0 / T - 1.0 / 1773.0))
    return max(1e-12, g * xSi)


def a_MnO(slag_wt: Dict[str, float], T: float) -> float:
    x = mole_fractions(slag_wt)
    Lam = optical_basicity(slag_wt)
    g = 1.15 * math.exp(1.30 * (Lam - 0.58))
    return max(1e-12, g * x.get("MnO", 0.0))


def a_TiO2(slag_wt: Dict[str, float], T: float) -> float:
    x = mole_fractions(slag_wt)
    return max(1e-12, 0.65 * x.get("TiO2", 0.0))


def sulphide_capacity(slag_wt: Dict[str, float], T: float) -> float:
    """
    Young / Sosinsky-Sommerville optical-basicity correlation for
    log10(Cs) valid for Lambda > 0.8; extended low-basicity branch below.
    """
    Lam = optical_basicity(slag_wt)
    if Lam >= 0.8:
        log_Cs = (-13.913 + 42.84 * Lam - 23.82 * Lam ** 2
                  - 11710.0 / T - 0.02223 * slag_wt.get("SiO2", 0.0)
                  - 0.02275 * slag_wt.get("Al2O3", 0.0))
    else:
        log_Cs = (-0.6261 + 0.4808 * Lam + 0.7917 * Lam ** 2
                  + (1697.0 - 2587.0 * Lam) * (1.0 / T) - 1.5)
    return 10.0 ** log_Cs


def L_S(slag_wt: Dict[str, float], T: float, wt_metal: Dict[str, float],
        aO: float = 1.0e-4) -> float:
    """
    Sulphur partition (S)/[S].  Under the strongly reducing conditions of the
    ESF the oxygen activity is fixed by C/CO equilibrium, giving high L_S.
    """
    Cs = sulphide_capacity(slag_wt, T)
    fS = gamma_wagner("S", wt_metal, T)
    log_Ls = math.log10(max(Cs, 1e-12)) + math.log10(max(fS, 1e-6)) \
        + 935.0 / T + 1.375 - math.log10(max(aO, 1e-9))
    return min(20.0, max(1.0, 10.0 ** log_Ls))


def L_P(slag_wt: Dict[str, float], T: float, aO: float = 1.0e-4) -> float:
    """
    Phosphate capacity route.  In an ESF the oxygen potential is far too low
    for dephosphorisation, so L_P collapses and essentially all P reports to
    the hot metal (consistent with 0.04-0.10 wt% P in ESF hot metal).
    """
    Lam = optical_basicity(slag_wt)
    log_Cp = 21.55 * Lam - 9.25 - 21000.0 / T
    log_Lp = log_Cp + 2.5 * math.log10(max(aO, 1e-12)) + 5.0
    return max(1e-4, min(50.0, 10.0 ** log_Lp))


def oxygen_activity_CO(T: float, aC: float, p_CO: float = 1.0) -> float:
    """[O] in equilibrium with [C] and CO(g) at p_CO (wt%)."""
    # [C] + [O] = {CO} ; log K = 1168/T + 2.07
    logK = 1168.0 / T + 2.07
    K = 10.0 ** logK
    return p_CO / (K * max(aC, 1e-6))


# --------------------------------------------------------------------------
# 6. Equilibrium silicon / manganese in hot metal
# --------------------------------------------------------------------------
def si_equilibrium(slag_wt: Dict[str, float], metal_wt: Dict[str, float],
                   T: float, p_CO: float = 1.0) -> float:
    """
    Equilibrium [Si] (wt%) from   (SiO2) + 2[C] = [Si] + 2{CO}
        K = (h_Si * p_CO^2) / (a_SiO2 * h_C^2)
    Solved for h_Si and converted to wt% through the Wagner coefficient.
    """
    K = Keq("SiO2_C", T)
    aSiO2 = a_SiO2(slag_wt, T)
    hC = a_metal("C", metal_wt, T)
    if hC <= 1e-6 or aSiO2 <= 1e-12:
        return 0.0
    hSi = K * aSiO2 * hC ** 2 / max(p_CO, 1e-6) ** 2
    fSi = gamma_wagner("Si", metal_wt, T)
    return max(0.0, min(6.0, hSi / max(fSi, 1e-6)))


def mn_equilibrium(slag_wt: Dict[str, float], metal_wt: Dict[str, float],
                   T: float, p_CO: float = 1.0) -> float:
    K = Keq("MnO_C", T)
    aMnO = a_MnO(slag_wt, T)
    hC = a_metal("C", metal_wt, T)
    if hC <= 1e-6 or aMnO <= 1e-12:
        return 0.0
    hMn = K * aMnO * hC / max(p_CO, 1e-6)
    fMn = gamma_wagner("Mn", metal_wt, T)
    return max(0.0, min(20.0, hMn / max(fMn, 1e-6)))


def feo_equilibrium(metal_wt: Dict[str, float], T: float,
                    p_CO: float = 1.0) -> float:
    """Equilibrium a_FeO in contact with carbon-saturated metal."""
    K = Keq("FeO_C", T)
    hC = a_metal("C", metal_wt, T)
    return max(1e-6, p_CO / (K * max(hC, 1e-6)))


# --------------------------------------------------------------------------
# 7. Enthalpy of a multi-species stream
# --------------------------------------------------------------------------
# Effective latent heat of the oxide when it melts *as part of a slag
# solution* (J/kg).  These are markedly lower than the pure-oxide heats of
# fusion because the silicate network forms exothermically; the pair
# (L_eff, OMEGA) reproduces molten-slag heat contents of 1.80-1.95 MJ/kg at
# 1550 degC, in line with published blast-furnace and smelter slag data.
L_SLAG_EFF = {
    "SiO2": 135.0e3, "CaO": 445.0e3, "MgO": 515.0e3, "Al2O3": 365.0e3,
    "FeO": 335.0e3, "MnO": 325.0e3, "TiO2": 340.0e3, "Ti2O3": 340.0e3,
    "P2O5": 270.0e3, "V2O5": 270.0e3, "Cr2O3": 405.0e3, "CaS": 540.0e3,
    "Na2O": 405.0e3, "K2O": 405.0e3,
}
CP_SLAG_LIQ = 1200.0        # J/kg/K above the liquidus


def slag_enthalpy(mass_kg: Dict[str, float], T: float, T_liquidus: float,
                  T_ref: float = T_REF) -> Dict[str, float]:
    """
    Enthalpy of a slag stream (J), split into sensible-solid, latent and
    superheat contributions, plus the chemical (formation) enthalpy.

        H = SUM n_i Hf_i(298)                          chemical
          + SUM n_i [H_i(T_liq) - H_i(298)]            sensible (solid path)
          + m * L_eff                                  latent (solution)
          + m * Cp_liq * (T - T_liq)                   superheat
    """
    m_tot = sum(v for v in mass_kg.values() if v > 0)
    if m_tot <= 0:
        return {"H": 0.0, "chemical": 0.0, "sensible": 0.0,
                "latent": 0.0, "superheat": 0.0}
    chem = sens = latent = 0.0
    for sp, m in mass_kg.items():
        if m <= 0 or sp not in DB:
            continue
        n = m / MW[sp]
        chem += n * DB[sp].Hf298
        sens += n * (DB[sp].H(min(T_liquidus, T)) - DB[sp].H(T_REF))
        latent += m * L_SLAG_EFF.get(sp, 250.0e3)
    superheat = m_tot * CP_SLAG_LIQ * max(0.0, T - T_liquidus)
    return {"H": chem + sens + latent + superheat, "chemical": chem,
            "sensible": sens, "latent": latent, "superheat": superheat}


def hot_metal_enthalpy(mass_kg: Dict[str, float], T: float
                       ) -> Dict[str, float]:
    """
    Enthalpy of the liquid hot metal (J).  Fe and the alloying metals are
    evaluated on the *liquid* branch (undercooled liquid below their own
    melting points) and every solute carries its enthalpy of dissolution in
    liquid iron.
    """
    chem = sens = diss = 0.0
    for sp, m in mass_kg.items():
        if m <= 0 or sp not in DB:
            continue
        n = m / MW[sp]
        chem += n * DB[sp].Hf298
        if sp == "C":
            sens += n * (DB[sp].H(T) - DB[sp].H(T_REF))
        else:
            sens += n * (DB[sp].H(T, force_liquid=True) - DB[sp].H(T_REF))
        if sp in H_DISSOLUTION:
            diss += n * H_DISSOLUTION[sp]
    return {"H": chem + sens + diss, "chemical": chem,
            "sensible": sens, "dissolution": diss}


def stream_enthalpy(mass_kg: Dict[str, float], T: float,
                    dissolved: bool = False) -> float:
    """
    Total enthalpy (J) of a stream given as {species: kg}.
    If `dissolved` the metal solutes carry their dissolution enthalpy.
    """
    H = 0.0
    for sp, m in mass_kg.items():
        if m <= 0.0 or sp not in DB:
            continue
        n = m / MW[sp]
        H += n * DB[sp].H(T)
        if dissolved and sp in H_DISSOLUTION:
            H += n * H_DISSOLUTION[sp]
    return H


def normalise(d: Dict[str, float], total: float = 100.0) -> Dict[str, float]:
    s = sum(v for v in d.values() if v > 0)
    if s <= 0:
        return {k: 0.0 for k in d}
    return {k: max(0.0, v) * total / s for k, v in d.items()}


__all__ = [n for n in dir() if not n.startswith("_")]
