"""
ESF-DT :: geometry.py
=====================
Furnace design, refractory lining stack, and the coupled
conduction / convection / radiation heat-loss network of the
Electric Smelting Furnace.

The furnace is discretised into five thermal zones, following the cooling
philosophy described for commercial open-slag-bath furnaces (slag zone gets
intensive cooling and grows a freeze layer, metal zone gets moderate cooling,
freeboard and roof are shielded against bath and arc radiation):

    Z1  hearth       (below the metal bath)
    Z2  metal-zone sidewall
    Z3  slag-zone sidewall      -> freeze lining solved for
    Z4  freeboard sidewall      -> receives radiation from the open bath
    Z5  roof                    -> receives radiation from bath + brush arc

Each zone carries an ordered list of `Layer` objects from hot face to cold
face.  For every zone the model solves the 1-D steady conduction problem with
temperature-dependent conductivities, an outer film (natural convection +
radiation to the shop, or forced water cooling), and, for Z3, an inner
solidified-slag layer whose thickness is found from the condition that its
hot face sits exactly at the slag liquidus.

Both rectangular (6-in-line) and circular (3-electrode) furnaces are
supported.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .properties import (REFRACTORY_DB, k_refractory, h_natural_vertical,
                         h_forced_plate, h_water_panel, h_bath_to_wall,
                         slag_thermal_conductivity, slag_viscosity,
                         slag_density, slag_cp, slag_emissivity,
                         slag_liquidus, gas_emissivity, SIGMA_SB)

ZONES = ["hearth", "metal_wall", "slag_wall", "freeboard", "roof"]
ZONE_LABEL = {
    "hearth": "Z1 Hearth",
    "metal_wall": "Z2 Metal-zone sidewall",
    "slag_wall": "Z3 Slag-zone sidewall",
    "freeboard": "Z4 Freeboard sidewall",
    "roof": "Z5 Roof / off-take",
}


# --------------------------------------------------------------------------
@dataclass
class Layer:
    material: str
    thickness: float          # m

    @property
    def rho(self) -> float:
        return REFRACTORY_DB.get(self.material, {}).get("rho", 2500.0)

    @property
    def cp(self) -> float:
        return REFRACTORY_DB.get(self.material, {}).get("cp", 1000.0)

    def k(self, T: float) -> float:
        return k_refractory(self.material, T)


def default_lining() -> Dict[str, List[Layer]]:
    """Reference lining package for a DRI open-slag-bath smelter."""
    return {
        "hearth": [
            Layer("Carbon block", 0.400),
            Layer("Ramming mass", 0.100),
            Layer("High-alumina 70 %", 0.230),
            Layer("Insulating castable", 0.100),
            Layer("Microporous board", 0.025),
            Layer("Steel shell", 0.060),
        ],
        "metal_wall": [
            Layer("MgO-C (20 %C)", 0.400),
            Layer("Ramming mass", 0.080),
            Layer("High-alumina 70 %", 0.115),
            Layer("Microporous board", 0.030),
            Layer("Steel shell", 0.045),
        ],
        # The slag zone is deliberately built "thin and cold": a ramming
        # skim directly against copper coolers, so that a protective freeze
        # lining of solidified slag forms and becomes the working lining.
        "slag_wall": [
            Layer("Ramming mass", 0.015),
            Layer("Copper cooler", 0.090),
            Layer("Steel shell", 0.040),
        ],
        # freeboard and roof are water-cooled panel construction: a thin
        # hot-face refractory backed directly by copper coolers.  This is
        # what limits the hot-face temperature against open-bath and brush-arc
        # radiation, and it is why 30-45 % of the furnace energy ends up in
        # the cooling water.
        "freeboard": [
            Layer("Alumina-spinel", 0.120),
            Layer("Copper cooler", 0.050),
            Layer("Steel shell", 0.030),
        ],
        "roof": [
            Layer("Alumina-spinel", 0.100),
            Layer("Copper cooler", 0.050),
            Layer("Steel shell", 0.025),
        ],
    }


# --------------------------------------------------------------------------
@dataclass
class FurnaceGeometry:
    """
    Physical envelope of the smelter.

    `shape` is 'rectangular' (in-line Soderberg electrodes) or 'circular'
    (three electrodes on a pitch circle).  Reference case follows the
    published commercial DRI smelting furnace envelope (35 m x 11 m,
    112 MW design power, 1.2 Mt/a hot metal).
    """
    shape: str = "rectangular"
    length: float = 35.0            # m (rectangular)
    width: float = 11.0             # m (rectangular)
    diameter: float = 20.0          # m (circular)
    wall_height: float = 6.5        # m total internal height
    metal_depth: float = 0.90       # m  design metal bath depth
    slag_depth: float = 1.35        # m  design slag bath depth
    n_electrodes: int = 6
    electrode_diameter: float = 1.70    # m
    electrode_pitch: float = 4.60       # m (in-line spacing)
    electrode_immersion: float = 0.45   # m into slag
    arc_length: float = 0.09            # m brush-arc gap (OSBF)
    tap_hole_metal: int = 2
    tap_hole_slag: int = 2
    freeboard_height: float = 3.2       # m above slag surface to roof
    lining: Dict[str, List[Layer]] = field(default_factory=default_lining)
    # cooling configuration per zone
    cooling: Dict[str, str] = field(default_factory=lambda: {
        "hearth": "forced-air",     # air | forced-air | water
        "metal_wall": "forced-air",
        "slag_wall": "water",
        "freeboard": "water",
        "roof": "water",
    })
    water_inlet_T: float = 308.0    # K
    ambient_T: float = 313.0        # K
    shop_air_velocity: float = 1.5  # m/s

    # ---------------- derived geometry ----------------
    @property
    def bath_area(self) -> float:
        """Horizontal cross-sectional (bath) area, m2."""
        if self.shape == "circular":
            return math.pi * self.diameter ** 2 / 4.0
        return self.length * self.width

    @property
    def perimeter(self) -> float:
        if self.shape == "circular":
            return math.pi * self.diameter
        return 2.0 * (self.length + self.width)

    def wall_area(self, height: float) -> float:
        return self.perimeter * max(0.0, height)

    @property
    def area_hearth(self) -> float:
        return self.bath_area

    @property
    def area_metal_wall(self) -> float:
        return self.wall_area(self.metal_depth)

    @property
    def area_slag_wall(self) -> float:
        return self.wall_area(self.slag_depth)

    @property
    def area_freeboard(self) -> float:
        return self.wall_area(self.freeboard_height)

    @property
    def area_roof(self) -> float:
        return self.bath_area * 1.05

    def zone_area(self, zone: str) -> float:
        return {
            "hearth": self.area_hearth,
            "metal_wall": self.area_metal_wall,
            "slag_wall": self.area_slag_wall,
            "freeboard": self.area_freeboard,
            "roof": self.area_roof,
        }[zone]

    @property
    def slag_volume(self) -> float:
        return self.bath_area * self.slag_depth

    @property
    def metal_volume(self) -> float:
        return self.bath_area * self.metal_depth

    @property
    def freeboard_volume(self) -> float:
        return self.bath_area * self.freeboard_height

    @property
    def mean_beam_length(self) -> float:
        V = self.freeboard_volume
        A = self.area_roof + self.area_freeboard + self.bath_area
        return 3.6 * V / max(A, 1.0)

    @property
    def electrode_area(self) -> float:
        """Total immersed electrode surface, m2."""
        d = self.electrode_diameter
        return self.n_electrodes * (math.pi * d * self.electrode_immersion
                                    + math.pi * d ** 2 / 4.0)

    @property
    def bath_area_free(self) -> float:
        """Open slag-bath area radiating to the freeboard."""
        d = self.electrode_diameter
        return max(1.0, self.bath_area
                   - self.n_electrodes * math.pi * d ** 2 / 4.0)

    def lining_thickness(self, zone: str) -> float:
        return sum(l.thickness for l in self.lining[zone])

    def lining_mass(self, zone: str) -> float:
        A = self.zone_area(zone)
        return sum(l.rho * l.thickness * A for l in self.lining[zone])

    def total_refractory_mass(self) -> float:
        return sum(self.lining_mass(z) for z in ZONES)

    def summary(self) -> Dict[str, float]:
        return {
            "Bath area (m2)": self.bath_area,
            "Slag volume (m3)": self.slag_volume,
            "Metal volume (m3)": self.metal_volume,
            "Freeboard volume (m3)": self.freeboard_volume,
            "Wall perimeter (m)": self.perimeter,
            "Immersed electrode area (m2)": self.electrode_area,
            "Open bath area (m2)": self.bath_area_free,
            "Total refractory mass (t)": self.total_refractory_mass() / 1000.0,
            "Mean beam length (m)": self.mean_beam_length,
        }


# --------------------------------------------------------------------------
def _outer_film(zone: str, geo: FurnaceGeometry, T_shell: float
                ) -> Tuple[float, float]:
    """Return (h_conv, T_sink) for the cold face of a zone."""
    mode = geo.cooling.get(zone, "air")
    if mode == "water":
        return h_water_panel(2.0, 0.04, geo.water_inlet_T), geo.water_inlet_T
    if mode == "forced-air":
        L = geo.wall_height
        return h_forced_plate(geo.shop_air_velocity, T_shell,
                              geo.ambient_T, L), geo.ambient_T
    L = geo.wall_height if zone != "hearth" else math.sqrt(geo.bath_area)
    return h_natural_vertical(T_shell, geo.ambient_T, L), geo.ambient_T


def _series_resistance(zone: str, geo: FurnaceGeometry,
                       T_hot_face: float, T_sink: float,
                       extra: List[Layer] | None = None
                       ) -> Tuple[float, List[float], List[float]]:
    """Conduction + outer-film resistance of a zone, m2.K/W, with node temps."""
    stack = (extra or []) + list(geo.lining[zone])
    n = len(stack)
    T_nodes = [T_hot_face - (T_hot_face - T_sink) * i / n for i in range(n + 1)]
    R = 0.0
    Rl: List[float] = []
    for _ in range(40):
        R = 0.0
        Rl = []
        for i, lay in enumerate(stack):
            Tm = 0.5 * (T_nodes[i] + T_nodes[i + 1])
            r = lay.thickness / max(lay.k(Tm), 1e-4)
            Rl.append(r)
            R += r
        h_out, T_s2 = _outer_film(zone, geo, T_nodes[-1])
        if geo.cooling.get(zone) != "water":
            eps = 0.85
            h_out += eps * SIGMA_SB * (T_nodes[-1] ** 2 + T_s2 ** 2) \
                * (T_nodes[-1] + T_s2)
        R_out = 1.0 / max(h_out, 1e-3)
        q = (T_hot_face - T_s2) / max(R + R_out, 1e-6)
        T = T_hot_face
        newT = [T]
        for r in Rl:
            T -= q * r
            newT.append(T)
        T_nodes = [0.5 * (a + b) for a, b in zip(T_nodes, newT)]
    return R + R_out, Rl, T_nodes


def solve_wall(zone: str, geo: FurnaceGeometry, T_hot: float,
               h_in: float, eps_shell: float = 0.85,
               freeze: bool = False, T_freeze: float = 1650.0,
               max_iter: int = 60) -> Dict[str, object]:
    """
    Solve the 1-D steady multilayer wall of one zone.

    Parameters
    ----------
    T_hot   bulk temperature of the fluid (slag, metal, gas) at the wall
    h_in    inner-side heat-transfer coefficient, W/m2/K (for the freeboard
            and roof this already contains the linearised radiation part)
    freeze  grow a solidified-slag layer.  The classical freeze-lining
            balance is used: the bath delivers h*(T_bath - T_liq) to the
            solidification front, and the same flux must pass through the
            frozen layer and the lining,

                h (T_bath - T_liq) = (T_liq - T_sink) / (x/k_f + R_lining)

            giving      x = k_f [ (T_liq - T_sink)/(h (T_bath - T_liq))
                                  - R_lining ].
            A negative x means no freeze layer can be sustained and the
            refractory hot face runs above the slag liquidus.
    """
    A = geo.zone_area(zone)
    _, T_sink0 = _outer_film(zone, geo, 400.0)
    x_freeze = 0.0

    if freeze:
        R_lin, _, _ = _series_resistance(zone, geo, T_freeze, T_sink0)
        k_f = k_refractory("Freeze lining (slag)", 0.5 * (T_freeze + 600.0))
        dT_bath = max(1.0, T_hot - T_freeze)
        x = k_f * ((T_freeze - T_sink0) / max(h_in * dT_bath, 1e-6) - R_lin)
        x_freeze = max(0.0, min(0.20, x))

    extra = [Layer("Freeze lining (slag)", x_freeze)] if x_freeze > 1e-5 else []

    # solve the complete wall including the inner film
    T_hf = T_hot - 50.0
    q = 0.0
    for _ in range(max_iter):
        R_tot, Rl, T_nodes = _series_resistance(zone, geo, T_hf, T_sink0, extra)
        q_new = (T_hot - T_sink0) / max(R_tot + 1.0 / max(h_in, 1e-3), 1e-6)
        T_hf_new = T_hot - q_new / max(h_in, 1e-3)
        if abs(T_hf_new - T_hf) < 0.5:
            T_hf, q = T_hf_new, q_new
            break
        T_hf = 0.5 * T_hf + 0.5 * T_hf_new
        q = q_new
    _, _, T_nodes = _series_resistance(zone, geo, T_hf, T_sink0, extra)

    stack = extra + list(geo.lining[zone])
    return {
        "zone": zone,
        "area_m2": A,
        "q_flux_W_m2": q,
        "Q_W": q * A,
        "T_nodes_K": T_nodes,
        "T_hotface_K": T_nodes[0],
        "T_shell_K": T_nodes[-1],
        "T_sink_K": T_sink0,
        "freeze_thickness_m": x_freeze,
        "layers": [(l.material, l.thickness) for l in stack],
    }


# --------------------------------------------------------------------------
def heat_loss_network(geo: FurnaceGeometry, T_slag: float, T_metal: float,
                      T_gas: float, slag_wt: Dict[str, float],
                      gas_y: Dict[str, float] | None = None,
                      arc_power_W: float = 0.0,
                      f_arc_radiation: float = 0.35) -> Dict[str, object]:
    """
    Full coupled heat-loss calculation for all five zones.

    Conduction through the multilayer lining, convection from bath / gas to
    the hot face, and radiation exchange in the freeboard (open bath + brush
    arc -> roof and upper sidewall) are treated together.

    Returns per-zone results plus totals and the radiative split.
    """
    gas_y = gas_y or {"CO": 0.85, "CO2": 0.10, "N2": 0.05}

    eta_s = slag_viscosity(slag_wt, T_slag)
    k_s = slag_thermal_conductivity(slag_wt, T_slag)
    rho_s = slag_density(slag_wt, T_slag)
    cp_s = slag_cp(slag_wt)
    eps_slag = slag_emissivity(slag_wt)
    T_liq = slag_liquidus(slag_wt)

    # inner film coefficients
    # CO evolution and electro-vortex flow stir the slag bath strongly, so
    # the wall-side coefficient is well above the pure natural-convection
    # value; a factor of 2 is used, with a floor for a quiescent bath.
    h_slag_wall = max(250.0, 2.0 * h_bath_to_wall(
        eta_s, k_s, geo.slag_depth, max(20.0, T_slag - T_liq), rho_s, cp_s))
    h_metal_wall = 1800.0          # vigorous natural convection in metal bath
    h_hearth = 1500.0

    # ---- freeboard radiation ---------------------------------------------
    L_beam = geo.mean_beam_length
    eps_g = gas_emissivity(gas_y, L_beam, T_gas)
    A_bath = geo.bath_area_free
    A_roof = geo.area_roof
    A_fb = geo.area_freeboard
    eps_ref = 0.75

    # view factors: bath -> roof and bath -> upper sidewall (enclosure rule)
    F_bath_roof = A_roof / (A_roof + A_fb)
    F_bath_wall = 1.0 - F_bath_roof

    # arc radiation is emitted from the brush-arc zone straight into freeboard
    Q_arc_rad = arc_power_W * f_arc_radiation

    def rad_exchange(T1, T2, A1, eps1, eps2, F):
        return (SIGMA_SB * A1 * F * (T1 ** 4 - T2 ** 4)
                / (1.0 / eps1 + 1.0 / eps2 - 1.0))

    results: Dict[str, Dict] = {}

    # Z1 hearth
    results["hearth"] = solve_wall("hearth", geo, T_metal, h_hearth)
    # Z2 metal wall
    results["metal_wall"] = solve_wall("metal_wall", geo, T_metal, h_metal_wall)
    # Z3 slag wall with freeze lining
    results["slag_wall"] = solve_wall("slag_wall", geo, T_slag, h_slag_wall,
                                      freeze=True, T_freeze=T_liq)

    # Z4/Z5 freeboard and roof - iterate hot-face temperature against radiation
    T_hf_roof = 0.5 * (T_gas + 1200.0)
    T_hf_wall = 0.5 * (T_gas + 1100.0)
    r_roof = r_fb = None
    for _ in range(40):
        q_rad_roof = (rad_exchange(T_slag, T_hf_roof, A_bath, eps_slag,
                                   eps_ref, F_bath_roof)
                      + Q_arc_rad * F_bath_roof
                      + eps_g * SIGMA_SB * A_roof * (T_gas ** 4 - T_hf_roof ** 4))
        q_rad_wall = (rad_exchange(T_slag, T_hf_wall, A_bath, eps_slag,
                                   eps_ref, F_bath_wall)
                      + Q_arc_rad * F_bath_wall
                      + eps_g * SIGMA_SB * A_fb * (T_gas ** 4 - T_hf_wall ** 4))
        h_conv_gas = 22.0
        h_eff_roof = max(5.0, q_rad_roof / max(A_roof * (T_gas - T_hf_roof), 1.0)
                         + h_conv_gas)
        h_eff_wall = max(5.0, q_rad_wall / max(A_fb * (T_gas - T_hf_wall), 1.0)
                         + h_conv_gas)
        r_roof = solve_wall("roof", geo, T_gas, h_eff_roof)
        r_fb = solve_wall("freeboard", geo, T_gas, h_eff_wall)
        newT_roof = r_roof["T_hotface_K"]
        newT_wall = r_fb["T_hotface_K"]
        if abs(newT_roof - T_hf_roof) < 2.0 and abs(newT_wall - T_hf_wall) < 2.0:
            T_hf_roof, T_hf_wall = newT_roof, newT_wall
            break
        T_hf_roof = 0.6 * T_hf_roof + 0.4 * newT_roof
        T_hf_wall = 0.6 * T_hf_wall + 0.4 * newT_wall

    results["roof"] = r_roof
    results["freeboard"] = r_fb

    total = sum(v["Q_W"] for v in results.values())
    water = sum(v["Q_W"] for z, v in results.items()
                if geo.cooling.get(z) == "water")

    return {
        "zones": results,
        "Q_total_W": total,
        "Q_to_cooling_water_W": water,
        "water_fraction": water / total if total > 0 else 0.0,
        "freeze_thickness_m": results["slag_wall"]["freeze_thickness_m"],
        "T_shell_max_K": max(v["T_shell_K"] for v in results.values()),
        "gas_emissivity": eps_g,
        "slag_liquidus_K": T_liq,
        "h_slag_wall": h_slag_wall,
    }


def lining_life_index(res: Dict[str, object], slag_wt: Dict[str, float],
                      T_slag: float) -> Dict[str, float]:
    """
    Simple wear indices for the campaign-life narrative:
      * chemical wear   ~ (FeO + MnO) x (1/B3) x exp(-Ea/RT)
      * thermal wear    ~ hot-face temperature above the material limit
      * freeze-lining protection factor
    """
    from .thermo import basicity_B3
    feo = slag_wt.get("FeO", 3.0) + slag_wt.get("MnO", 0.5)
    B3 = max(0.4, basicity_B3(slag_wt))
    chem = feo / B3 * math.exp(-38000.0 / (8.3145 * T_slag)) * 1e3
    zw = res["zones"]["slag_wall"]
    protect = min(1.0, zw["freeze_thickness_m"] / 0.05)
    hot = zw["T_hotface_K"]
    thermal = max(0.0, (hot - 1723.0) / 100.0)
    wear = chem * (1.0 - 0.75 * protect) + thermal
    return {
        "chemical_index": chem,
        "thermal_index": thermal,
        "freeze_protection": protect,
        "wear_index": wear,
        "est_campaign_months": max(6.0, 120.0 / max(wear, 0.05)),
    }


__all__ = [n for n in dir() if not n.startswith("_")]
