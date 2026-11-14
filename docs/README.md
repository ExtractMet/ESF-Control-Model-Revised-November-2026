# ESF-DT — Electric Smelting Furnace Digital Twin

**Extractmet Private Limited** · IIT Madras Research Park · **version 1.1.0**

A first-principles process model, digital twin and operator workbench for the
**Electric Smelting Furnace** (ESF, open slag bath furnace) used to melt and
reduce direct-reduced iron made from **low-grade, high-gangue iron ores** into
blast-furnace-grade hot metal.

All plant references in this package are anonymised as **Industry-X**.

---

## Why this exists

The DRI–ESF–BOF route is the leading way to decarbonise steelmaking from ores
that cannot economically be pelletised to DR grade. Australian, Indian and
Brazilian ores carry 12–19 wt% gangue, which means slag volumes of
250–330 kg per tonne of hot metal — three to four times a blast furnace. That
changes everything: the energy bill, the refractory life, the electrode
regulation, the silicon in the metal and the load the BOF sees downstream.

There is no blast furnace to hide behind. Every tonne of gangue must be
melted with electricity, and the operator has to hold basicity, superheat and
carbon simultaneously while the feed grade moves underneath them.

ESF-DT answers two questions:

| | Question | Model |
|---|---|---|
| **Static** | What does a tonne of hot metal cost in energy, carbon, flux and slag? | Simultaneous closure of the elemental mass balance and the heat balance, with slag/metal equilibria, a multilayer lining network and a slag-resistance electrical model |
| **Dynamic** | What does the furnace actually do over a shift? | Five coupled control volumes marched in time with reaction kinetics, interfacial heat and mass transfer, electrode regulation, tapping cycles and an alarm system |

---

## What is in the box

```
esf/
├── esf_dt/                  the engine (pure Python + NumPy)
│   ├── thermo.py            Shomate enthalpies, Gibbs energies, activities,
│   │                        Wagner interaction parameters, partition ratios
│   ├── properties.py        slag and metal density, viscosity, electrical and
│   │                        thermal conductivity, liquidus, emissivity,
│   │                        foaming index, diffusivities, transfer correlations
│   ├── geometry.py          furnace envelope, multilayer lining, freeze-lining
│   │                        solver, coupled conduction/convection/radiation
│   ├── electrical.py        slag path resistance, brush arc, electrode
│   │                        regulation, power setpoint solver
│   ├── static_model.py      steady-state mass and heat balance
│   ├── dynamic_model.py     transient multi-zone solver with kinetics
│   └── schematic.py         parametric SVG reactor drawing
├── gui/
│   ├── esf_streamlit.py     13-tab web workbench
│   └── esf_gui_tk.py        native desktop application (Tkinter)
├── web/
│   └── esf_console.html     self-contained browser console, no install
├── run_validation.py        regenerates the validation tables and 19 figures
├── audit.py                 physical-correctness sweep of the input space
├── figures/                 validation tables, statistics, figure set
├── data/                    sample feed and campaign data
└── docs/                    README · HELP · THEORY · VALIDATION · INSTALL
```

---

## Quick start

```bash
pip install -r docs/requirements.txt

python run_validation.py          # tables + 19 figure sets in figures/
python audit.py                   # physical-correctness sweep
streamlit run gui/esf_streamlit.py
python gui/esf_gui_tk.py
```

Or simply open `web/esf_console.html` in any browser — it needs no Python, no
server and no network.

Programmatically:

```python
from esf_dt.static_model import run_static
from esf_dt.dynamic_model import run_dynamic

r = run_static(dri_name="DRI-B (15.5 % gangue)", metallisation_pct=94,
               tap_temperature_C=1500, target_basicity_B2=1.10)
print(r["KPI"]["SEC_operating_kWh_tHM"], r["hot_metal_wt_pct"])

d = run_dynamic(duration_min=420, dri_feed_t_h=160, power_MW=112)
print(d["summary"])
```

---

## Physics resolved

* **Thermochemistry** — Shomate heat capacities and enthalpies of formation
  for every species; Gibbs energies for FeO, SiO₂, MnO, TiO₂ and P₂O₅
  reduction by carbon; optical basicity, silica and manganese oxide
  activities; Wagner first-order interaction parameters for the metal phase;
  sulphide capacity and the sulphur and phosphorus partition ratios.
* **Heat** — charge heating and melting at the pile/slag interface,
  slag-to-metal interfacial transfer, coupled conduction, natural and forced
  convection and radiation through five lining zones, an analytic freeze
  lining, open-bath radiation to the water-cooled panels, off-gas sensible
  heat and post-combustion return.
* **Mass** — elemental balances on Fe, C, Si, Mn, P, S, Ti, Ca, Mg, Al and O
  across pile, slag, metal, gas and dust, with a per-element closure check.
* **Kinetics** — FeO reduction by dissolved carbon and by floating char,
  SiO₂ and MnO reduction under mixed control, carburiser dissolution, lime
  dissolution with a product layer, Boudouard and freeboard post-combustion.
* **Electrical** — slag path and electrode resistance, brush-arc voltage,
  power setpoint solved on the tap voltage, electrode consumption.

---

## Validation

Forty-four independent comparisons against published FactSage and HSC
studies, a complete published stream-by-stream balance, industrial
open-bath-furnace plant data, a supplier design envelope and laboratory
smelting experiments:

| | |
|---|---|
| Independent comparisons | **44** |
| Mean absolute relative deviation | **8.5 %** |
| Median | **5.0 %** |
| Within 10 % | 32 of 44 |
| Composition and envelope windows | **18 of 20 met** |

A second harness, `audit.py`, asks a different question: is every answer
*physically possible*? It sweeps the whole input space — 158 configurations
— 178 configurations — and rejects anything that violates a mass balance,
leaves a physical bound or fails to converge. **Current result: 0 failures.**

### New in version 1.1

* Silicon, residual slag FeO and manganese reported on a **kinetic** basis
  by default, with the equilibrium basis retained as an option. This
  resolves a genuine contradiction between two published silicon figures
  and matches what furnaces actually tap.
* **Slag valorisation scoring** for reuse as a cementitious material.
* Support for **both DRI reporting conventions**, and for metallic Mn, Si
  and P in a DRI analysis.
* Hot-heel effect, carbon flotation and the FeO-reduction incubation period
  in the dynamic engine, after laboratory measurements under ESF conditions.
* Four new reference feeds, including two low-grade H₂-DRI grades actually
  smelted in the laboratory and an industrial open-bath-furnace reference.
* A benchmark correction: the carbon sensitivity v1.0 reported as its worst
  outlier (−63 %) was measured against a misread figure and is −16 %.

For context, the two published equilibrium studies of the same cases differ
from **each other** by 14.6–16.0 %. See `VALIDATION.md` for the full table,
the six residual outliers and an honest account of what is calibrated.

---

## Licence and contact

Commercial software of Extractmet Private Limited. Evaluation, pilot and
licence terms on request.

© Extractmet Private Limited, IIT Madras Research Park.
