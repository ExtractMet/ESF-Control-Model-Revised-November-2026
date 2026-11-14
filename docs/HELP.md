# ESF-DT — Help

Operator and engineer guide to the Electric Smelting Furnace digital twin.
Reference plant anonymised as **Industry-X**.

---

## 1. Which interface should I use?

| Interface | Start it with | Best for |
|---|---|---|
| **Web workbench** | `streamlit run gui/esf_streamlit.py` | Day-to-day engineering: full input set, 13 work areas, CSV export |
| **Desktop application** | `python gui/esf_gui_tk.py` | Control-room use on a machine with no browser or network |
| **Browser console** | open `web/esf_console.html` | Demonstration, training, sharing a case by email — no installation |
| **Python API** | `from esf_dt.static_model import run_static` | Batch studies, optimisation, integration with plant historians |

All four solve the same physics. The browser console runs a reduced-order
form of the engine; see the fidelity note in section 10.

---

## 2. The workflow

1. **Describe the feed** — DRI grade (or paste your own analysis),
   metallisation, charging temperature, scrap fraction, carburiser and fluxes.
2. **Set the product targets** — tapping temperature, carbon in the hot metal,
   slag basicity B2, slag MgO, slag superheat, off-gas temperature.
3. **Describe the furnace** — hearth dimensions, electrode count, diameter,
   pitch, immersion, brush-arc length, bath depths, freeboard height.
4. **Set the electrical system** — secondary voltage, power factor,
   electrical-to-bath efficiency.
5. **Read the static answer** on the schematic, mass balance, energy, slag and
   metal, refractory and electrical pages.
6. **Run the dynamic case** when you need the time behaviour: feed programme,
   power control, tapping schedule, initial bath.
7. **Read the trajectories and the event log**, then export.

The static solver runs on every input change. The dynamic solver runs on
demand and takes a few seconds for a full shift.

---

## 3. Reading the results

### 3.1 The SEC hierarchy

Three specific energy consumptions are reported and they mean different
things. Quoting the wrong one is the commonest way to mislead yourself.

| Figure | Definition | Use it for |
|---|---|---|
| **SEC reversible** | Process heat ÷ hot metal. The thermodynamic minimum. | Understanding where the energy physically goes |
| **SEC equilibrium basis** | Reversible ÷ an optional reporting factor, which now defaults to 1 and so equals the reversible tier | Retained only so a user can reproduce a particular code's reporting convention; the fitted factor that used to sit here has been withdrawn |
| **SEC operating** | (Process heat + lining losses) ÷ (hot metal × electrical-to-bath efficiency) | What the transformer must deliver — the number for a power contract |

On the reference case the reversible and operating figures are roughly 492
and 769 kWh/tHM. The gap between them is not waste in the model; it is the
real furnace. A published specific energy whose loss convention is not
stated should be read against that interval rather than against either end
of it.

### 3.2 Elemental closure

The mass balance page reports the closure error per element. Anything above
about 0.5 % means the case has been pushed outside the solver's comfortable
range — usually an extreme basicity or a metallisation below 75 %.

### 3.3 The schematic

Every level, colour, thickness and number on the drawing is the live solution,
not decoration. Watch particularly:

* the **freeze lining** band in the slag zone — it is the working lining;
* the **brush-arc glow** under each electrode tip — its size is the arc gap;
* the **feed pile** — if it grows, melting is limited, not the chemistry;
* the **alarm banner** at the foot.

---

## 3.4 Silicon, FeO and manganese: which basis?

Three product variables are set in practice by kinetics, not equilibrium.
The **Silicon basis** control decides which you see.

| Setting | Use it when |
|---|---|
| `kinetic` (default) | You want what the furnace will actually tap. Silicon is capped by a saturating ceiling, slag FeO carries a practical floor of 0.65 wt%, and manganese is bounded so some MnO always stays in the slag. |
| `equilibrium` | You are comparing against FactSage, HSC or another equilibrium code, which report the thermodynamic limit. |

The difference is small below 1500 °C and large above it: at 1600 °C the
equilibrium result is 2.2 wt% Si, which no ESF has ever tapped, against
0.45 wt% on the kinetic basis.

---

## 3.5 Slag valorisation

The **Slag & metal** page scores the tapped slag for reuse as a
supplementary cementitious material. Three things decide it: basicity in the
0.85–1.30 band, FeO below 2 wt%, and free MgO below saturation. A
high-basicity foaming practice (B2 ≈ 2, as an EAF needs) scores as marginal;
that is precisely why the ESF route exists.

---

## 4. The operating window

| Variable | Window | Why |
|---|---|---|
| Tapping temperature | 1480–1520 °C | Below: tap-hole and ladle risk. Above: refractory wear and silicon |
| Slag superheat | 60–120 K | Below 40 K the bath starts to freeze |
| Basicity B2 | 1.0–1.2 | Below: aggressive, corrosive slag. Above: short and viscous |
| Slag MgO | 7–9 wt% | Saturates the magnesia-chrome lining and protects it |
| Slag FeO | below 3 wt% | Iron loss and severe refractory attack above 8 wt% |
| Hot metal C | 3.2–4.0 wt% | Below 3: poor for the BOF. At saturation: kish graphite |
| Hot metal Si | 0.2–0.5 wt% | Drives BOF lime and oxygen demand |
| Slag viscosity | below 1.0 Pa·s | Above 1.2 the bath stirs poorly and melting slows |
| Shell temperature | below 200 °C | Above 220 °C, inspect the lining |

**Silicon is the lever to watch.** It roughly doubles for every 25 °C of extra
superheat. Between 1400 and 1525 °C the model moves [Si] from 0.03 to 0.62
wt%. Nothing else the operator controls has that much leverage over the
downstream BOF.

---

## 5. The dynamic model

### 5.1 What is being marched

Five well-mixed control volumes: the **feed pile** on the bath surface, the
**slag**, the **metal**, the **freeboard gas** and the quasi-steady **lining**.

### 5.2 Power control

* **temperature** (default) — feed-forward from the melting demand and the
  measured lining loss, plus a gentle PI trim on the hot-metal temperature.
  This is how real furnaces run and it is the mode to use.
* **fixed** — hold the rated power. Use it to see what the furnace does when
  the operator does nothing.
* **schedule** — piecewise-constant power programme.

If the power saturates at the rating and the temperature still falls, the
furnace is genuinely undersized for that feed rate. Reduce the feed.

### 5.3 Melting is usually the constraint

Melting happens at the pile/slag interface. The heat arriving raises the
material that melts from the bulk pile temperature to the softening
temperature and then supplies its latent heat. A cold, fast feed depresses the
pile temperature and slows melting exactly as it does in the plant. If the
pile mass grows past about 260 t the model raises an advisory: the answer is
more power or less feed, not more flux.

### 5.4 Tapping

Metal and slag tap-holes open on independent schedules and drain at a set
rate for a set duration. Every opening and closing is logged with the bath
state at that moment. Bath inventories are floored so the furnace is never
drained below a safe heel.

---

## 6. The event log

Every entry is time-stamped against the furnace clock and carries the process
state at the moment it was raised.

| Type | Meaning |
|---|---|
| `FEED` | Campaign start and end, charge programme in force |
| `TAP-METAL` / `TAP-SLAG` | Tap-hole opened, with temperature and analysis |
| `TAP-…-CLOSE` | Tap-hole closed, with the cumulative tonnage |
| `WARNING` | Drifting out of the window — correctable |
| `ALARM` | Acting now avoids damage or a lost heat |

Alarms fire once on the transition into the condition, not repeatedly, so the
log stays readable over a long campaign.

---

## 7. Calibrating to your furnace

The engine is first-principles except for the kinetic pre-exponentials, which
are the plant calibration handles:

| Constant | Governs | Typical range |
|---|---|---|
| `k0_FeO_C` | FeO reduction by dissolved carbon | 1–8 |
| `k0_FeO_char` | FeO reduction on floating char | 0.3–2 |
| `k0_SiO2` | Silicon pickup | 5–40 |
| `k0_MnO` | Manganese pickup | 2–12 |
| `k0_C_diss` | Carburiser dissolution | 0.005–0.06 |
| `melt_htc_pile` | Melting rate at the pile | 800–4000 W/m²/K |

Procedure: run a week of tapped analyses through the dynamic model with the
recorded feed and power, then adjust `k0_SiO2` to the mean [Si],
`k0_FeO_C` to the mean slag FeO and `melt_htc_pile` to the observed
productivity. Three constants, one afternoon. Everything else stays physics.

---

## 8. Parametric studies

Sweep any input against every KPI. The studies that repay the effort most:

* **Metallisation** — the single largest lever on energy and carbon.
  Roughly −48 kWh and −10 kg C per tonne for every 5 % of metallisation.
* **Scrap blending** — about −2.9 kWh/tHM per wt% of scrap in the metallic
  charge, because scrap brings no gangue.
* **Tapping temperature** — about +19 kWh/tHM per 25 °C, and the silicon.
* **Gangue content** — about +15 kWh/tHM per wt% of gangue in the DRI.
* **Basicity and MgO** — flux cost against refractory life and viscosity.

---

## 9. Economics

Conversion cost covers power, carburiser, fluxes and electrode paste. Power
dominates: at 55 USD/MWh and 764 kWh/tHM it is around 42 USD/tHM of a
roughly 60–70 USD/tHM total. CO₂ is reported as direct (process carbon) and
indirect (grid), so the effect of a renewable power contract is explicit.

---

## 10. Fidelity of the browser console

Measured against the Python reference on the standard case, the console
reproduces charge and product masses within 0.1 % (0.3 % for slag, 5 % for
flux), slag composition within 1 wt% absolute, the lining heat-loss network
within 0.5 %, and the dynamic campaign within 6 % on energy and power.
Static specific energy runs about 6 % high at 100 % metallisation and 9 % at
80 %.

Every trend carries the correct slope and sign, and the console enforces the
same conservation rules and the same refusals as the reference engine.

Use the console for screening, training and demonstration. Use the Python
package for engineering studies, licence-basis calculations and plant
deployment.

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Configuration rejected: neither flux can raise the slag basicity" | Both flux slots hold an acid flux (quartzite, bauxite) | Put a lime, limestone, dolomitic or magnesian flux in at least one slot |
| "Target slag MgO cannot be met together with basicity" | The chosen fluxes carry too little MgO: they dilute the slag faster than they enrich it. Basicity is honoured and the MgO target dropped | Use dolomitic lime, raw dolomite or calcined magnesia in the secondary slot |
| Specific energy jumps when switching to limestone or raw dolomite | Correct behaviour: a raw carbonate must be calcined in the furnace, costing about 112 and 62 kWh/tHM respectively | Use burnt or dolomitic lime if the calcination is cheaper in a kiln |
| Static solver will not converge | Target unreachable with the chosen fluxes | Widen the target or change the flux |
| Bath cools despite full power | Feed rate above the furnace's melting capacity | Reduce feed or raise the rating |
| Feed pile grows without limit | Same, or the charge is very cold | Reduce feed, preheat the DRI |
| Slag FeO climbs | Carburiser short or too coarse | Raise `carbon_feed_kg_t_dri`, reduce particle size |
| [Si] far above target | Tapping temperature too high, or basicity too low | Lower superheat, raise B2 |
| Freeze lining vanishes | Slag zone under-cooled or bath too hot | Increase slag-zone cooling, lower superheat |
| Shell above 220 °C | Lining worn or wrongly specified | Check the lining stack on the refractory page |

---

© Extractmet Private Limited, IIT Madras Research Park. ESF-DT v1.0.0.
