"""
ESF-DT :: properties.py
=======================
Physical-property closures for the Electric Smelting Furnace digital twin.

Covers
------
*  Slag  : density, viscosity (Urbain / Riboud / NPL), electrical
           conductivity, thermal conductivity, surface tension, liquidus
           temperature, emissivity.
*  Metal : density, viscosity, thermal conductivity, surface tension.
*  Gas   : density, Cp, viscosity, thermal conductivity of the freeboard
           CO/CO2/N2/H2O mixture.
*  Refractory / freeze-lining : temperature-dependent conductivity of the
           usual ESF lining materials, plus solidified-slag (freeze layer)
           properties.
*  Dimensionless-group correlations for natural and forced convection.

All property routines take slag / metal composition dictionaries in wt%.
"""

from __future__ import annotations

import math
from typing import Dict

from .thermo import (MW, mole_fractions, optical_basicity, basicity_B3,
                     basicity_B2)

SIGMA_SB = 5.670374419e-8      # Stefan-Boltzmann, W/m^2/K^4
G_ACC = 9.80665


# ==========================================================================
# SLAG
# ==========================================================================
# partial molar volumes (m3/mol) at 1773 K for density (Mills & Keene)
V_PARTIAL = {
    "CaO": 20.7e-6, "MgO": 16.1e-6, "SiO2": 27.5e-6, "Al2O3": 28.3e-6,
    "FeO": 15.8e-6, "MnO": 15.6e-6, "TiO2": 24.0e-6, "P2O5": 65.7e-6,
    "Cr2O3": 30.0e-6, "V2O5": 60.0e-6, "Na2O": 33.0e-6, "K2O": 51.0e-6,
    "CaS": 26.0e-6,
}


def slag_density(slag_wt: Dict[str, float], T: float) -> float:
    """kg/m3.  Molar-volume additivity with a linear thermal expansion term."""
    x = mole_fractions(slag_wt)
    Mbar = sum(x.get(k, 0.0) * MW[k] for k in x if k in MW)
    Vbar = sum(x.get(k, 0.0) * V_PARTIAL.get(k, 25.0e-6) for k in x)
    if Vbar <= 0:
        return 2900.0
    rho = Mbar / Vbar
    rho *= (1.0 - 1.0e-4 * (T - 1773.0))
    return max(2200.0, min(4200.0, rho))


def slag_viscosity(slag_wt: Dict[str, float], T: float) -> float:
    """
    Slag viscosity, Pa.s, Urbain-type Weymann-Frenkel form
        eta = A * T * exp(B*1000/T)
    with the B parameter regressed on the network-former / modifier balance.
    Valid for the CaO-SiO2-Al2O3-MgO-FeO-MnO system of DRI smelter slags.
    """
    x = mole_fractions(slag_wt)
    xSi = x.get("SiO2", 0.0)
    xAl = x.get("Al2O3", 0.0)
    xCa = x.get("CaO", 0.0)
    xMg = x.get("MgO", 0.0)
    xFe = x.get("FeO", 0.0)
    xMn = x.get("MnO", 0.0)
    xTi = x.get("TiO2", 0.0)

    former = xSi + xAl
    modifier = xCa + xMg + xFe + xMn + xTi
    alpha = modifier / max(modifier + xAl, 1e-9)

    B0 = 13.20 + 15.90 * alpha - 30.00 * alpha ** 2 + 14.10 * alpha ** 3
    B1 = 30.48 - 128.00 * alpha + 190.00 * alpha ** 2 - 89.70 * alpha ** 3
    B2_ = -40.90 + 275.00 * alpha - 395.00 * alpha ** 2 + 180.00 * alpha ** 3
    B3 = 60.70 - 232.00 * alpha + 321.00 * alpha ** 2 - 144.00 * alpha ** 3
    B = B0 + B1 * former + B2_ * former ** 2 + B3 * former ** 3
    B = max(8.0, min(60.0, B))

    lnA = -(0.2693 * B + 11.6725)
    A = math.exp(lnA)
    eta = A * T * math.exp(1000.0 * B / T)
    return max(1e-3, min(50.0, eta))


def slag_conductivity_elec(slag_wt: Dict[str, float], T: float) -> float:
    """
    Electrical conductivity of the molten slag, S/m.
        sigma = sigma0 * exp(-Ea / (R T))
    with sigma0 and Ea functions of optical basicity and of the FeO + MnO
    content (electronic conduction).  Returns values in the 5-80 S/m band
    reported for smelter slags (Karalis et al. used 10-60 S/m).
    """
    Lam = optical_basicity(slag_wt)
    feo = slag_wt.get("FeO", 0.0) + slag_wt.get("MnO", 0.0)
    Ea = (110.0 - 55.0 * (Lam - 0.55) - 0.9 * feo) * 1e3      # J/mol
    Ea = max(60.0e3, min(150.0e3, Ea))
    ln_s0 = 9.95 + 2.0 * (Lam - 0.55) + 0.020 * feo
    sigma = math.exp(ln_s0) * math.exp(-Ea / (8.3145 * T))
    return max(0.5, min(150.0, sigma))


def slag_resistivity(slag_wt: Dict[str, float], T: float) -> float:
    return 1.0 / slag_conductivity_elec(slag_wt, T)


def slag_thermal_conductivity(slag_wt: Dict[str, float], T: float) -> float:
    """Effective (phonon + radiative) thermal conductivity, W/m/K."""
    k_ph = 0.9 + 1.1e-4 * (T - 1573.0)
    k_rad = 0.9 * (T / 1773.0) ** 3
    return max(0.5, k_ph + k_rad)


def slag_cp(slag_wt: Dict[str, float]) -> float:
    """Mean specific heat of molten slag, J/kg/K (1.15-1.35 kJ/kg/K band)."""
    base = 1.20e3
    base += 2.0 * (slag_wt.get("CaO", 0.0) - 35.0) * 1.0
    base -= 1.5 * (slag_wt.get("FeO", 0.0) - 3.0)
    return max(1.05e3, min(1.45e3, base))


def slag_surface_tension(slag_wt: Dict[str, float], T: float) -> float:
    """N/m, additive partial surface tensions (Mills)."""
    coeff = {"CaO": 625e-3, "SiO2": 260e-3, "Al2O3": 655e-3, "MgO": 635e-3,
             "FeO": 645e-3, "MnO": 645e-3, "TiO2": 360e-3, "P2O5": 100e-3}
    x = mole_fractions(slag_wt)
    s = sum(x.get(k, 0.0) * v for k, v in coeff.items())
    s += -0.15e-3 * (T - 1773.0)
    return max(0.20, min(0.75, s))


def slag_liquidus(slag_wt: Dict[str, float]) -> float:
    """
    Liquidus temperature (K) of the CaO-SiO2-Al2O3-MgO-FeO slag.
    Regression across the smelter operating window (B2 0.8-1.6,
    Al2O3 5-25 wt%, MgO 4-14 wt%, FeO 0.5-10 wt%) giving 1550-1750 K.
    """
    B2 = basicity_B2(slag_wt)
    Al = slag_wt.get("Al2O3", 12.0)
    Mg = slag_wt.get("MgO", 8.0)
    Fe = slag_wt.get("FeO", 3.0)
    Ti = slag_wt.get("TiO2", 0.0)
    T_liq = (1673.0
             + 175.0 * (B2 - 1.10)
             - 40.0 * (B2 - 1.10) ** 2
             + 3.6 * (Al - 12.0)
             + 6.8 * max(0.0, Mg - 9.0)
             - 3.0 * max(0.0, 9.0 - Mg)
             - 9.5 * (Fe - 3.0)
             + 2.0 * Ti)
    return max(1450.0, min(1850.0, T_liq))


def slag_emissivity(slag_wt: Dict[str, float]) -> float:
    """Total hemispherical emissivity of the open slag bath surface."""
    feo = slag_wt.get("FeO", 3.0)
    return min(0.95, 0.78 + 0.012 * feo)


def slag_foaming_index(slag_wt: Dict[str, float], T: float) -> float:
    """
    Ito-Fruehan foaming index, s :  Sigma = 115 * eta / sqrt(rho * sigma)
    Long residence of CO bubbles raises the effective bath height.
    """
    eta = slag_viscosity(slag_wt, T)
    rho = slag_density(slag_wt, T)
    st = slag_surface_tension(slag_wt, T)
    return 115.0 * eta / math.sqrt(rho * st)


# ==========================================================================
# HOT METAL
# ==========================================================================
def metal_density(metal_wt: Dict[str, float], T: float) -> float:
    """kg/m3 for Fe-C-Si melt."""
    rho = 7030.0 - 0.88 * (T - 1823.0)
    rho -= 90.0 * metal_wt.get("C", 4.0)
    rho -= 60.0 * metal_wt.get("Si", 0.4)
    return max(6200.0, rho)


def metal_viscosity(metal_wt: Dict[str, float], T: float) -> float:
    """Pa.s (about 5-7 mPa.s for carbon-saturated iron)."""
    eta = 0.3699e-3 * math.exp(41400.0 / (8.3145 * T))
    eta *= (1.0 + 0.04 * metal_wt.get("C", 4.0))
    return max(2e-3, min(2e-2, eta))


def metal_cp(metal_wt: Dict[str, float]) -> float:
    """J/kg/K for liquid hot metal."""
    return 820.0 + 12.0 * metal_wt.get("C", 4.0)


def metal_thermal_conductivity(T: float) -> float:
    return 30.0 + 0.008 * (T - 1800.0)


def metal_surface_tension(metal_wt: Dict[str, float], T: float) -> float:
    """N/m; S is strongly surface active."""
    s = 1.91 - 0.0004 * (T - 1823.0)
    S = metal_wt.get("S", 0.02)
    s -= 0.30 * math.log10(1.0 + 220.0 * S)
    return max(0.7, s)


def metal_liquidus(metal_wt: Dict[str, float]) -> float:
    """K.  Fe-C-Si-Mn-P-S liquidus depression from pure iron (1811 K)."""
    T = 1811.0
    T -= 73.1 * metal_wt.get("C", 4.0)
    T -= 12.0 * metal_wt.get("Si", 0.4)
    T -= 4.9 * metal_wt.get("Mn", 0.7)
    T -= 34.4 * metal_wt.get("P", 0.06)
    T -= 38.0 * metal_wt.get("S", 0.02)
    T -= 3.0 * metal_wt.get("Ti", 0.0)
    return max(1350.0, T)


# ==========================================================================
# FREEBOARD GAS
# ==========================================================================
GAS_CP = {"CO": 1150.0, "CO2": 1240.0, "N2": 1180.0,
          "H2O": 2280.0, "H2": 15000.0, "O2": 1090.0}


def gas_mixture_cp(y: Dict[str, float]) -> float:
    """Mass-fraction weighted mean Cp, J/kg/K, at ~1500 K."""
    tot = sum(y.values())
    if tot <= 0:
        return 1180.0
    return sum(GAS_CP.get(k, 1150.0) * v for k, v in y.items()) / tot


def gas_density(y: Dict[str, float], T: float, P: float = 101325.0) -> float:
    tot = sum(y.values())
    if tot <= 0:
        return 0.2
    Mbar = sum(v * MW.get(k, 0.028) for k, v in y.items()) / tot
    return P * Mbar / (8.3145 * T)


def gas_emissivity(y: Dict[str, float], L_m: float, T: float,
                   P_atm: float = 1.0) -> float:
    """
    Grey-gas emissivity of a CO/CO2/H2O freeboard atmosphere,
    Hottel-type correlation, mean beam length L_m.
    """
    tot = sum(y.values()) or 1.0
    pC = (y.get("CO2", 0.0) + 0.35 * y.get("CO", 0.0)) / tot * P_atm
    pW = y.get("H2O", 0.0) / tot * P_atm
    pL = (pC + pW) * L_m
    eps = 0.55 * (1.0 - math.exp(-1.35 * pL)) * (1600.0 / max(T, 800.0)) ** 0.45
    return max(0.05, min(0.6, eps))


# ==========================================================================
# REFRACTORY AND FREEZE LINING
# ==========================================================================
REFRACTORY_DB: Dict[str, Dict[str, float]] = {
    # k(T) = k0 + k1*(T-298) ; rho kg/m3 ; cp J/kg/K ; Tmax K
    "MgO-C (20 %C)":        dict(k0=14.0, k1=-0.0055, rho=2950.0, cp=1050.0,
                                 Tmax=2073.0, cost=1.00),
    "Magnesia-chrome":      dict(k0=4.2, k1=-0.0009, rho=3050.0, cp=1000.0,
                                 Tmax=2000.0, cost=1.15),
    "Alumina-spinel":       dict(k0=3.1, k1=-0.0006, rho=3050.0, cp=1050.0,
                                 Tmax=1973.0, cost=0.95),
    "Fused-cast AZS":       dict(k0=5.0, k1=-0.0010, rho=3800.0, cp=950.0,
                                 Tmax=1973.0, cost=1.60),
    "Carbon block":         dict(k0=22.0, k1=-0.0040, rho=1650.0, cp=1150.0,
                                 Tmax=2273.0, cost=1.20),
    "Fireclay (safety)":    dict(k0=1.30, k1=0.00035, rho=2200.0, cp=1000.0,
                                 Tmax=1673.0, cost=0.35),
    "High-alumina 70 %":    dict(k0=1.90, k1=0.00025, rho=2500.0, cp=1050.0,
                                 Tmax=1873.0, cost=0.55),
    "Insulating castable":  dict(k0=0.42, k1=0.00028, rho=1100.0, cp=1050.0,
                                 Tmax=1573.0, cost=0.40),
    "Microporous board":    dict(k0=0.028, k1=0.00006, rho=320.0, cp=900.0,
                                 Tmax=1273.0, cost=0.80),
    "Ceramic fibre":        dict(k0=0.10, k1=0.00020, rho=190.0, cp=1050.0,
                                 Tmax=1523.0, cost=0.30),
    "Ramming mass":         dict(k0=2.20, k1=0.00020, rho=2600.0, cp=1000.0,
                                 Tmax=1873.0, cost=0.30),
    "Steel shell":          dict(k0=45.0, k1=-0.0150, rho=7850.0, cp=490.0,
                                 Tmax=873.0, cost=0.70),
    "Copper cooler":        dict(k0=380.0, k1=-0.0600, rho=8930.0, cp=385.0,
                                 Tmax=873.0, cost=4.00),
    "Freeze lining (slag)": dict(k0=1.60, k1=0.00020, rho=3000.0, cp=1150.0,
                                 Tmax=1773.0, cost=0.00),
}


def k_refractory(material: str, T: float) -> float:
    d = REFRACTORY_DB.get(material)
    if d is None:
        return 2.0
    return max(0.02, d["k0"] + d["k1"] * (T - 298.0))


# ==========================================================================
# CONVECTION CORRELATIONS
# ==========================================================================
def h_natural_vertical(T_s: float, T_inf: float, L: float) -> float:
    """Churchill-Chu natural convection on a vertical plate, air, W/m2/K."""
    dT = max(1.0, abs(T_s - T_inf))
    Tf = 0.5 * (T_s + T_inf)
    nu = 1.5e-5 * (Tf / 300.0) ** 1.75
    k = 0.0263 * (Tf / 300.0) ** 0.8
    beta = 1.0 / Tf
    Pr = 0.70
    Ra = G_ACC * beta * dT * L ** 3 / (nu * nu) * Pr
    Nu = (0.825 + 0.387 * Ra ** (1.0 / 6.0)
          / (1.0 + (0.492 / Pr) ** (9.0 / 16.0)) ** (8.0 / 27.0)) ** 2
    return max(2.0, Nu * k / L)


def h_forced_plate(v: float, T_s: float, T_inf: float, L: float) -> float:
    """Forced convection over a flat plate, W/m2/K."""
    Tf = 0.5 * (T_s + T_inf)
    nu = 1.5e-5 * (Tf / 300.0) ** 1.75
    k = 0.0263 * (Tf / 300.0) ** 0.8
    Pr = 0.70
    Re = max(1.0, v * L / nu)
    Nu = 0.037 * Re ** 0.8 * Pr ** (1.0 / 3.0) if Re > 5e5 \
        else 0.664 * Re ** 0.5 * Pr ** (1.0 / 3.0)
    return max(2.0, Nu * k / L)


def h_water_panel(v_w: float = 2.0, d_h: float = 0.04,
                  T_w: float = 313.0) -> float:
    """Dittus-Boelter for a cooling-water channel, W/m2/K."""
    rho, cp = 992.0, 4180.0
    mu = 6.5e-4
    k = 0.63
    Re = rho * v_w * d_h / mu
    Pr = cp * mu / k
    Nu = 0.023 * Re ** 0.8 * Pr ** 0.4
    return Nu * k / d_h


def h_bath_to_wall(eta: float, k_slag: float, L: float,
                   dT: float, rho: float, cp: float) -> float:
    """
    Natural-convection heat-transfer coefficient from a stirred slag bath
    to the sidewall.  Rayleigh number based on slag properties.
    """
    beta = 1.0e-4
    alpha = k_slag / (rho * cp)
    nu = eta / rho
    Ra = G_ACC * beta * max(dT, 1.0) * L ** 3 / (nu * alpha)
    Nu = 0.10 * Ra ** (1.0 / 3.0)
    return max(50.0, min(4000.0, Nu * k_slag / L))


def h_slag_metal(eta_s: float, k_s: float, dT: float, L: float,
                 rho_s: float, cp_s: float, stir: float = 1.0) -> float:
    """Slag/metal interfacial heat-transfer coefficient, W/m2/K."""
    h = h_bath_to_wall(eta_s, k_s, L, dT, rho_s, cp_s)
    return h * (1.0 + 1.5 * stir)


# ==========================================================================
# MASS TRANSFER
# ==========================================================================
def D_slag(species: str, T: float, eta: float) -> float:
    """
    Stokes-Einstein diffusivity in molten slag, m2/s.
    Effective ionic radii after Mills.
    """
    r = {"FeO": 0.78e-10, "SiO2": 0.42e-10, "MnO": 0.83e-10,
         "CaO": 1.00e-10, "MgO": 0.72e-10, "Al2O3": 0.54e-10}.get(species, 0.7e-10)
    kB = 1.380649e-23
    return kB * T / (6.0 * math.pi * eta * r)


def D_metal(species: str, T: float) -> float:
    """Diffusivity in liquid iron, m2/s (Arrhenius)."""
    par = {"C": (7.9e-7, 27000.0), "Si": (2.4e-8, 27000.0),
           "Mn": (2.6e-8, 27000.0), "S": (4.9e-8, 30000.0),
           "P": (3.0e-8, 29000.0), "O": (5.0e-8, 25000.0)}
    D0, Ea = par.get(species, (3.0e-8, 28000.0))
    return D0 * math.exp(-Ea / (8.3145 * T))


def k_mass_transfer(D: float, eta: float, rho: float, L: float,
                    eps_stir: float) -> float:
    """
    Mass-transfer coefficient from a turbulent-dissipation (surface-renewal)
    model:  k = 2 * sqrt(D / (pi * t_c)), t_c = (nu / eps)^0.5.
    eps_stir = specific stirring power, W/kg.
    """
    nu = eta / rho
    eps = max(1e-6, eps_stir)
    t_c = math.sqrt(nu / eps)
    return 2.0 * math.sqrt(D / (math.pi * max(t_c, 1e-4)))


def stirring_power_gas(Q_gas_Nm3s: float, m_bath: float, T: float,
                       H_bath: float) -> float:
    """
    Specific stirring power from CO evolution through the bath, W/kg
    (Pluschkell / Nakanishi form).
    """
    if m_bath <= 0:
        return 1e-4
    eps = 6.18e3 * Q_gas_Nm3s * T / m_bath * math.log(1.0 + H_bath / 1.46)
    return max(1e-4, eps)


__all__ = [n for n in dir() if not n.startswith("_")]
