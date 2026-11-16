# ESF-DT — Validation (version 1.1)

How the Electric Smelting Furnace digital twin was tested, what it
reproduces, and where it does not. Reference plant anonymised as
**Industry-X**.

```bash
python run_validation.py --outdir figures    # literature comparison
python audit.py                              # physical-correctness sweep
```

---

## 1. What changed in version 1.1

Version 1.1 was built after three further papers became available. They did
three things: they supplied new reference data, they **corrected a benchmark
that version 1.0 had wrong**, and they resolved a contradiction between two
of the older sources.

| Source | What it contributed |
|---|---|
| Sabah et al., *J. Sustain. Metall.* (2026), "Modeling of Electric Smelting Furnaces for Ironmaking" | Corrected carbon sensitivity; industrial open-bath-furnace hot metal and slag composition against the blast furnace; the Tenova iBlue design envelope; a complete stream-by-stream mass and energy balance at 1600 °C |
| Bae & Park, *J. Cleaner Prod.* **524** (2025) 146490 | Laboratory FeO-reduction kinetics under ESF conditions: carbon requirement, the effect of a hot heel, carbon flotation, and direct evidence that SiO₂ reduction does not reach equilibrium |
| Visuri & Echterhof, *Metals* **15** (2025) 1285 | Why the ESF exists at all: an EAF on low-grade DRI needs B2 ≈ 2 and runs above 20 wt% FeO, losing iron; an ESF runs at B2 ≈ 1 and makes a slag that can be reused like blast-furnace slag |

### 1.1 A benchmark version 1.0 got wrong

Version 1.0 reported its worst outlier as the sensitivity of specific energy
to hot-metal carbon: **4.5 against 12.15 kWh/tHM, a deviation of −63 %**, and
stated that the missing term had not been identified.

The review states the figure plainly: **10 kWh/tHM per 1.0 wt % carbon**, not
per 0.5 wt %. Benchmarked against the correct value the model gives 8.4
against 10, a deviation of **−16 %**. There was no missing term; the
reference was misread. The v1.0 documentation overstated a model error that
was really a reading error, and that is corrected here.

### 1.2 A contradiction between two sources, resolved

Two published silicon figures cannot both be equilibrium:

* FactSage: 0.62 wt % Si at 1525 °C
* HSC: 0.40 wt % Si at **1600 °C**

Silicon reduction is strongly endothermic, so equilibrium silicon must rise
with temperature. A lower value at a higher temperature is not an
equilibrium result. Industry agrees with the lower number: the open-bath
furnace tapping figure is **below 0.5 wt %**.

Bae and Park settle it experimentally. Their slag reached a basicity of
C/S ≈ 0.5 where equilibrium predicted 1.2, and they state directly that
"the reduction of SiO₂ was slower than expected and did not reach
thermodynamic equilibrium".

The model therefore reports silicon on two bases:

* **`silicon_mode="equilibrium"`** reproduces the equilibrium result and is
  what is compared against the FactSage anchors — 0.030, 0.107, 0.350 and
  0.614 wt % at 1400, 1450, 1500 and 1525 °C against 0.03, 0.10, 0.30–0.40
  and 0.62. The first and last of those four are the values the reduction
  Gibbs energy is fitted to, so only the middle two test the model;
* **`silicon_mode="kinetic"`** (the default) applies a saturating ceiling,
  which is an empirical bound on the approach to equilibrium rather than a
  rate expression — 0.029, 0.095, 0.244 and
  0.337 wt %, and 0.45 at 1600 °C against the HSC value of 0.40 and inside
  the industrial window at every temperature.

The same reasoning is applied to residual slag FeO, which is thermodynamically
nil at ESF carbon levels yet reported at 0.6–0.7 wt % industrially, and to
manganese, which equilibrium would strip almost completely while industrial
slag retains 0.15–0.30 wt % MnO.

---

## 2. Headline result

| | v1.0 | v1.1 | **v1.2** |
|---|---|---|---|
| Single-valued comparisons counted | 30 | 44 | **17** |
| Interval tests counted | 6 | 8 | **31** |
| Mean absolute relative deviation | 8.79 % | 8.53 % | **14.60 %** |
| Median | 4.45 % | 4.96 % | **3.95 %** |
| Within 10 % | 24 of 30 | 32 of 44 | **12 of 17** |
| Within 15 % | 25 of 30 | 34 of 44 | **14 of 17** |
| Interval tests met | 6 of 6 | 18 of 20 | **22 of 31** |
| Physical-correctness sweep | 0 failures in 158 | 0 failures in 178 | **0 failures in 178** |

The v1.2 figures are not directly comparable with the earlier two, and the
deviation has risen rather than fallen. The reason is that v1.2 counts only
comparisons that can actually test the model. Comparisons compromised by
fitting, the industrial composition check whose feed was back-calculated,
figures taken from other classes of furnace, and published values that their
own balance cannot support are all reported but excluded, each with its
reason recorded in the validation table. Every row now carries a basis, a
role and a provenance.

The comparison set has grown by half and now includes industrial plant
data, a complete published stream balance and laboratory kinetics, not only
equilibrium-code output.

---

## 3. New benchmarks in v1.1

### 3.1 A complete published mass and energy balance

The review tabulates a full stream-by-stream balance at 1600 °C. Reproducing
it end to end:

| Quantity | ESF-DT | Published | Deviation |
|---|---:|---:|---:|
| Hot metal | 1053.8 kg | 1055.0 kg | −0.1 % |
| Slag | 298.5 kg | 283.8 kg | +5.2 % |
| Specific energy | 596.7 kWh/tHM | 598.2 kWh/tHM | **−0.3 %** |
| Slag SiO₂ | 37.29 wt% | 37.75 wt% | −1.2 % |
| Slag CaO | 40.60 wt% | 41.63 wt% | −2.5 % |
| Slag Al₂O₃ | 20.30 wt% | 20.45 wt% | −0.7 % |
| Hot metal Fe | 94.90 wt% | 94.75 wt% | +0.2 % |
| Hot metal C | 3.50 wt% | 3.50 wt% | 0.0 % |
| Hot metal Si | 0.45 wt% | 0.40 wt% | +12.5 % |
| Hot metal Mn | 0.97 wt% | 1.20 wt% | −19.3 % |

Energy to 0.3 % on an independent balance the model had never seen is the
strongest single result in this document.

### 3.2 Industrial open-bath furnace

Given a feed back-calculated from the published industrial slag, the model
is asked whether it makes the published product. **10 of 12 windows are
met**: C, Si, Mn, S, P and Fe in the hot metal, and CaO, MgO, FeO and MnO in
the slag. Slag SiO₂ (38.3 against 36.5–37.5) and Al₂O₃ (11.1 against
10.5–11.0) sit just outside, and both follow from the back-calculated feed
rather than from the solver. That feed was **not** tuned to close the gap;
doing so would have made the test circular.

### 3.3 Laboratory ESF smelting of low-grade H₂-DRI

| Quantity | ESF-DT | Measured | Deviation |
|---|---:|---:|---:|
| Carbon for full FeO reduction + 3 wt % C | 59.2 kg-C/tHM | 66 kg-C/tHM | −10 % |
| Slag FeO with a hot heel | 5.0 wt% | 3.0 wt% | +67 % |
| Hot metal C with a hot heel | 3.20 wt% | 2.8 wt% | +14 % |

### 3.4 Design envelope

The Tenova iBlue envelope is met: operating SEC 770 kWh/tHM against a
design range of 500–1200, and a slag/metal ratio of 0.25 against 0.07–0.25.

---

## 4. Full comparison table

| Case | Quantity | Model | Literature | Unit | RPD (%) |
|---|---|---|---|---|---:|
| DRI-A (13.8 % gangue) | SEC @ 100 % MR, 1500 degC | 554.077 | 553.9 | kWh/tHM | 0.03 |
| DRI-A (13.8 % gangue) | Carbon consumption @ 100 % MR | 38.849 | 41.36 | kg/tHM | -6.07 |
| DRI-A (13.8 % gangue) | SEC @ 80 % MR, 1500 degC | 739.538 | 756.9 | kWh/tHM | -2.29 |
| DRI-B (15.5 % gangue) | SEC @ 100 % MR, 1500 degC | 581.031 | 575.8 | kWh/tHM | 0.91 |
| DRI-B (15.5 % gangue) | Carbon consumption @ 100 % MR | 39.49 | 41.0 | kg/tHM | -3.68 |
| DRI-B (15.5 % gangue) | SEC @ 80 % MR, 1500 degC | 766.086 | 778.0 | kWh/tHM | -1.53 |
| DRI-C (16.0 % gangue) | SEC @ 100 % MR, 1500 degC | 582.578 | 575.5 | kWh/tHM | 1.23 |
| DRI-C (16.0 % gangue) | Carbon consumption @ 100 % MR | 38.835 | 40.65 | kg/tHM | -4.46 |
| DRI-C (16.0 % gangue) | SEC @ 80 % MR, 1500 degC | 768.013 | 778.0 | kWh/tHM | -1.28 |
| DRI-A (13.8 % gangue) | Carbon consumption @ 80 % MR | 79.757 | 84.4 | kg/tHM | -5.5 |
| DRI A-C | Slag rate @ 100 % MR (range low) | 265.415 | 275.4 | kg/tHM | -3.63 |
| DRI A-C | Slag rate @ 100 % MR (range high) | 311.485 | 325.5 | kg/tHM | -4.31 |
| DRI-A | [Si] in hot metal @ 1400 degC | 0.032 | 0.03 | wt% | 6.36 |
| DRI-A | [Si] in hot metal @ 1450 degC | 0.109 | 0.1 | wt% | 9.06 |
| DRI-A | [Si] in hot metal @ 1500 degC | 0.345 | 0.33 | wt% | 4.62 |
| DRI-A | [Si] in hot metal @ 1525 degC | 0.593 | 0.62 | wt% | -4.29 |
| DRI-B + 0 wt% scrap | SEC @ 90 % MR | 673.576 | 677.44 | kWh/tHM | -0.57 |
| DRI-B + 20 wt% scrap | SEC @ 90 % MR | 605.558 | 623.78 | kWh/tHM | -2.92 |
| DRI-B + 40 wt% scrap | SEC @ 90 % MR | 541.673 | 569.6 | kWh/tHM | -4.9 |
| DRI-B + 60 wt% scrap | SEC @ 90 % MR | 481.54 | 515.16 | kWh/tHM | -6.53 |
| Sensitivity | dSEC/dT (kWh/tHM per 25 degC) | 14.005 | 20.0 | kWh/tHM per 25 degC | -29.97 |
| Sensitivity | dSEC/dMR (kWh/tHM per 1 wt% MR) | -9.273 | -12.0 | kWh/tHM per 1 wt% MR | -22.72 |
| Sensitivity | dSEC/dC (kWh/tHM per 1.0 wt% C) | 8.381 | 10.0 | kWh/tHM per 1.0 wt% C | -16.19 |
| Sensitivity | dSEC/dgangue (kWh/tHM per 1 wt%) | 15.671 | 16.5 | kWh/tHM per 1 wt% | -5.02 |
| Sensitivity | dSEC/dscrap (kWh/tHM per 1 wt%) | -3.201 | -2.5 | kWh/tHM per 1 wt% | 28.02 |
| Sensitivity | dC/dMR (kg/tHM per 5 % MR) | -10.227 | -10.7 | kg/tHM per 5 % MR | -4.42 |
| Sensitivity | dC/dC_HM (kg/tHM per 0.5 wt%) | 5.449 | 6.5 | kg/tHM per 0.5 wt% | -16.16 |
| DRI-B hot metal | Fe (wt%) window | 95.2044 | 94.0-95.5 | wt% | in window |
| DRI-B hot metal | Si (wt%) window | 0.3246 | 0.3-0.36 | wt% | in window |
| DRI-B hot metal | Mn (wt%) window | 0.8246 | 0.58-1.06 | wt% | in window |
| DRI-B hot metal | P (wt%) window | 0.0443 | 0.04-0.1 | wt% | in window |
| DRI-B hot metal | S (wt%) window | 0.0077 | 0.005-0.05 | wt% | in window |
| DRI-B hot metal | C (wt%) window | 3.5 | 3.2-4.0 | wt% | in window |
| Full balance @ 1600 degC | Hot metal (kg) | 1052.165 | 1055.0 | kg | -0.27 |
| Full balance @ 1600 degC | Slag (kg) | 300.471 | 283.83 | kg | 5.86 |
| Full balance @ 1600 degC | SEC (kWh/tHM) | 595.387 | 598.2 | kWh/tHM | -0.47 |
| Full balance @ 1600 degC | slag SiO2 (wt%) | 37.037 | 37.75 | wt% | -1.89 |
| Full balance @ 1600 degC | slag CaO (wt%) | 40.345 | 41.63 | wt% | -3.09 |
| Full balance @ 1600 degC | slag Al2O3 (wt%) | 20.163 | 20.45 | wt% | -1.4 |
| Full balance @ 1600 degC | HM Si (wt%) | 0.45 | 0.4 | wt% | 12.5 |
| Full balance @ 1600 degC | HM Mn (wt%) | 0.968 | 1.2 | wt% | -19.34 |
| Full balance @ 1600 degC | HM Fe (wt%) | 95.042 | 94.75 | wt% | 0.31 |
| MR 90 %, 16 % gangue | SEC @ 1300 degC | 554.078 | 706.0 | kWh/tHM | -21.52 |
| MR 90 %, 16 % gangue | SEC @ 1600 degC | 807.106 | 850.0 | kWh/tHM | -5.05 |
| Industrial OSBF hot metal | C window | 4.5 | 4.0-5.0 | wt% | in window |
| Industrial OSBF hot metal | Si window | 0.4141 | 0.0-0.5 | wt% | in window |
| Industrial OSBF hot metal | Mn window | 0.1407 | 0.1-0.2 | wt% | in window |
| Industrial OSBF hot metal | S window | 0.0222 | 0.02-0.035 | wt% | in window |
| Industrial OSBF hot metal | P window | 0.0236 | 0.015-0.035 | wt% | in window |
| Industrial OSBF hot metal | Fe window | 94.8767 | 94.0-95.5 | wt% | in window |
| Industrial OSBF slag | CaO window | 41.3701 | 40.5-41.5 | wt% | in window |
| Industrial OSBF slag | SiO2 window | 38.3143 | 36.5-37.5 | wt% | outside |
| Industrial OSBF slag | MgO window | 7.2703 | 7.0-7.5 | wt% | in window |
| Industrial OSBF slag | Al2O3 window | 11.1415 | 10.5-11.0 | wt% | outside |
| Industrial OSBF slag | FeO window | 0.6469 | 0.5-0.9 | wt% | in window |
| Industrial OSBF slag | MnO window | 0.1908 | 0.15-0.3 | wt% | in window |
| Tenova iBlue envelope | Operating SEC | 769.3 | 500.0-1200.0 | kWh/tHM | in window |
| Tenova iBlue envelope | Slag/metal ratio | 0.247 | 0.07-0.25 | - | in window |
| Low-grade H2-DRI (lab) | Carbon for full FeO reduction + 3 wt% C | 59.044 | 66.0 | kg-C/tHM | -10.54 |
| Low-grade H2-DRI (lab) | Slag FeO with a hot heel | 5.023 | 3.0 | wt% | 67.42 |
| Low-grade H2-DRI (lab) | Hot metal C with a hot heel | 3.204 | 2.8 | wt% | 14.44 |
| Dynamic 7 h campaign | Operating SEC | 707.42 | 762.6 | kWh/tHM | -7.24 |
| Dynamic 7 h campaign | Slag rate | 278.525 | 300.0 | kg/tHM | -7.16 |
| Dynamic 7 h campaign | Heat to cooling circuit (share of input) | 29.871 | 40.0 | % | -25.32 |

---

## 5. Where it still does not agree

| Quantity | Model | Literature | Deviation | Assessment |
|---|---:|---:|---:|---|
| Slag FeO with a hot heel | 5.0 | 3.0 wt% | +67 % | A 70 g laboratory melt against a model of a 116 MW furnace; the direction and the hot-heel effect are reproduced but the magnitude is not. The deviation widened from 41 % when the freeboard correction of v1.2 restored the open-bath radiation debit: the bath runs cooler, FeO reduction is slower, and more FeO is left in the slag. It is reported rather than tuned away |
| dSEC/dT | 14.0 | 20.0 kWh/tHM per 25 °C | −30 % | Temperature sensitivity is about two thirds of the published slope, although absolute SEC at each temperature matches well |
| dSEC/dscrap | −3.20 | −2.5 kWh/tHM per wt% | +28 % | Over-sensitive to scrap |
| Heat to the cooling circuit | 29.9 | 35–45 % | −25 % | Just below the band; the default lining carries more hot-face refractory over the panels than the reference furnaces |
| dSEC/dMR | −9.3 | −12.0 kWh/tHM per wt% | −23 % | |
| SEC at 1300 °C, 90 % MR | 554 | 706 kWh/tHM | −22 % | The published low-temperature point implies a much flatter curve than the model produces |
| Hot metal Mn, full balance | 0.97 | 1.20 wt% | −19 % | The kinetic manganese cap that fixes the industrial MnO window costs accuracy against this equilibrium-basis case |
| dSEC/dC | 8.4 | 10.0 kWh/tHM per wt% | −16 % | Was reported as −63 % in v1.0 against a misread benchmark |

Most of the remaining gaps are **derivatives**, which is where equilibrium
codes are least reproducible between databases — the review's own sources
differ by 14–16 % on levels alone.

---

## 6. Physical-correctness sweep

`audit.py` now covers **178 configurations** and rejects any result that
violates a mass balance, leaves a physical bound, fails to converge or
returns an impossible composition. **Current result: 0 failures.**

The v1.1 reference grades exposed two further defects, both fixed:

| Defect | Symptom | Fix |
|---|---|---|
| Only one DRI reporting convention supported | An analysis stating metallic Fe **and** an explicit FeO assay had its oxidised iron charged twice; 15 % iron closure error | Both conventions detected and honoured, with a warning when the stated metallisation is overridden |
| Metallic solutes in the DRI analysis ignored | An analysis reporting metallic Mn produced a 100 % manganese closure error | Metallic Mn, Si and P are carried as already-reduced solutes in both engines |

---

## 7. Reproducibility

Both harnesses regenerate every number here from the engine with no cached
results. The v1.0 package is shipped unchanged alongside this one, so any
figure quoted in either version can be re-derived.

---

© Extractmet Private Limited, IIT Madras Research Park. ESF-DT v1.1.0.
