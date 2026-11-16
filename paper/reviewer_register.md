# Reviewer comment register — ESF-DT manuscript (Ironmaking & Steelmaking)

Classification: **T** text/explanation only · **N** requires a number re-derived from the engine ·
**C** requires a code or parameter change · **F** requires a figure change · **S** structural.

## Reviewer 1

| ID | Target | Class | Comment |
|---|---|---|---|
| R1-1 | §1 | T | Make the purpose clearer: state what the model predicts and what is new versus earlier models. |
| R1-2 | §3.3 | T | For each material stream state whether its enthalpy includes formation, heating, melting, mixing, dissolution; identify which are added separately; a table would help; each contribution counted once. |
| R1-3 | §3.4, Eq. (6) | T | Explain the activity expression; mole fraction is squared; give source and reason for that form. |
| R1-4 | §3.5 | T | Identify all values chosen or adjusted to match known values, and state the conditions supporting them. |
| R1-5 | §3.8 | T | Explain how each contact area and driving force is calculated; give rate-coefficient sources and applicable conditions; separate quantities from physical laws, from published relationships, and estimated/adjusted. |
| R1-6 | Fig. 2 | F | Correct equation and table references: reaction-rate table is Table 6, flux calculations are Eqs. (24)–(26). |
| R1-7 | §5 | T | Basis of comparison not elaborated enough; for each comparison give reference conditions beside model inputs (temperature, feed composition, operating assumptions); identify missing information and the assumptions replacing it. |
| R1-8 | §6.4, Table 12 | T/N | Explain how the silicon values were obtained and the differences between values. |
| R1-9 | §6.8 | N | Specify the averaging period for mean power and heat-loss share. |
| R1-10 | §3.10 | T/N | Define "hot metal produced"; show how it relates to tapped metal and to transfers between metal, slag and gas. |
| R1-11 | whole | S | The ideas between sections are not well connected. |

## Reviewer 2

| ID | Target | Class | Comment |
|---|---|---|---|
| R2-1 | whole | T/N | Address SAF/OSBF readers: describe the furnace in their terms (operating resistance, hearth power density). Add a short worked example showing how the model supports a real design or operating decision. |
| R2-2 | whole | S | Shorten and simplify: reduce the literature review; move Algorithms 1–2, solution times and step-size checks to supplementary; present validation method and results together, separating calibration from independent validation; merge or move some results tables; give §6.11 more space. |
| R2-3 | §5.3 | T/N | Is the close agreement in absolute SEC independent of calibrating eta_th = 0.887 against the same equilibrium-code values? If both are enthalpy balances, what explains an 11 % factor? Do the reference studies include heat losses? |
| R2-4 | §3.5, Eq. (11), §6.8 | T/N | Eq. (11) has no residence time, mass-transfer coefficient or interfacial area — in what sense is it kinetic? If S_c, the FeO floor and the Mn bounds are calibrated on the same industrial data used for comparison, how would a user set them for a new ore? Why do steady-state (Si 0.414 %, FeO 0.65 %) and transient (Si 0.24 %, FeO 1.80 %) results differ? |
| R2-5 | §1 | T | Mention that India, the largest DRI producer, uses mainly coal-based rotary kilns. |
| R2-6 | §3 | T | What does "BP grades" mean? |

## Reviewer 3

| ID | Target | Class | Comment |
|---|---|---|---|
| R3-1 | Abstract | T/N | "steady-state and transient models are in good agreement" — with each other or with literature? If with each other, add a direct comparison under identical operating conditions; otherwise reformulate. |
| R3-2 | Abstract | T | Reword the kinetic-limitation sentence: the limits are empirical constraints calibrated on literature data, not derived from the model; and first-order mass-transfer control applies only to the transient module. |
| R3-3 | whole | S | Order references in order of first citation. |
| R3-4 | §1 | T | "FeO above 20 wt % incurs substantial loss of iron yield" — high FeO is also normal in scrap-based steelmaking (viscosity, foaming); the main problem is the increase in slag quantity. |
| R3-5 | §2.3 | T | Add Matino, Branca, Guzzon & Colla (2026), *Electric Smelting Furnace Flowsheet Model for Future Slag Investigations*, AISTech, D031S037R001, AIST. |
| R3-6 | §3.2 | T | Define "contained iron"; clarify that results are normalised per tonne of hot metal, since 1000 kg Fe is not 1000 kg hot metal. |
| R3-7 | Fig. 1 | F | Are the slag and hot metal numbers in-furnace liquid inventories? Add slag and hot metal flow rates to the figure itself. Complete the truncated "Water-cooled p…" label. |
| R3-8 | Table 4 | T/N | Basicity is 1.07 in Fig. 1 and 1.10 in Table 4; state explicitly which is target and which computed. |
| R3-9 | Table 4 | N | Off-gas temperature inconsistent with Fig. 1. |
| R3-10 | Table 4 | T/N | Secondary voltage 420 V, tap voltage 430 V in Fig. 1, 496 V in the energy-balance table; clarify the relation and explain how tap voltage can exceed secondary voltage. |
| R3-11 | Eq. (13) | T | Correct the superscript indices. |
| R3-12 | Table 6 | T | Give references for k0 and Ea. |
| R3-13 | whole | T | Check compound subscripts throughout (e.g. SiO2). |
| R3-14 | Fig. 2 | F | Equation numbers do not match the text. |
| R3-15 | Fig. 2 | F | Adjust the "yes: advance t" position in panel C. |
| R3-16 | Table 8 | C/N | Some comparisons are not independent of calibration: equilibrium-basis SEC depends on eta_th calibrated on the same equilibrium-code SEC; [Si] at 1400/1500/1525 degC are calibration targets as well as validation points; [Si] at 1600 degC is essentially set by the calibrated ceiling S_c. Exclude calibration targets from the statistics or report them separately, and recompute MARD, median and counts before comparing with the 14.6–16.0 % inter-code disagreement. |
| R3-17 | §6 | S | Figure 7 is cited on page 23 but appears on page 32. |
| R3-18 | Fig. 3 | F | Panel title reads "F1". |
| R3-19 | Fig. 4 | F | Panel titles read "F2a"/"F2b"; add "(left)" and "(right)" to the caption. |
| R3-20 | §6.7 | T | The comparison against the references is unclear; elaborate. |
| R3-21 | Fig. 5 | F | Panel titles read "F9a"/"F9b". |
| R3-22 | Fig. 6 | F | Panel title reads "F10"; the figure is incomplete because the slag wall hot face temperature is not shown. |
| R3-23 | Fig. 7 | F | Show in the figure how the points span three DRI grades, two metallisation ratios and four scrap ratios. |
| R3-24 | §6.6 | S | Section 6.6 is missing. |
| R3-25 | Table 10 | C/N | Table 10 omits compared quantities that deviate strongly (hot metal S and P, off-gas, slag FeO, carburiser). Include all of them and revise "seven of the ten stream quantities agree within 3.1 %". |
| R3-26 | tables | S | End tables are hard to read because they split across pages. |
| R3-27 | §5.1, Table 9 | C/N | §5.1 says forty-four comparisons from six sources, Table 9 says 52 benchmarks, the summary table 64. Make counts and terminology consistent, and check the number of sources. |
| R3-28 | validation table | N | Explain the largest RPDs: 29.97 (dSEC/dT), 22.72 (dSEC/dMR), 28.02 (dSEC/dscrap), 21.52 (SEC at 1300 degC, 90 % MR, 16 % gangue), 41.06 (lab slag FeO with hot heel), 25.32 (heat to cooling circuit). |
| R3-29 | validation table | C/N | Why is SEC at 1300 degC (90 % MR, 16 % gangue) almost identical to SEC at 1500 degC (100 % MR, DRI-A)? And 1300 degC is below the slag liquidus of 1431 degC that the model itself computes. |
| R3-30 | Table 11 | C/N | dSEC/dC is 8.3811 in the validation table but 9.42 in the sensitivity table. |
| R3-31 | Table 11 | C/N | dSEC/dgangue is compared with a single literature value of 16.5 while Table 11 says "within range 13–20"; and the result is 15.6711 against 15.5 in Table 11. |
| R3-32 | validation table | C | Clarify the reference for the 762.6 kWh/tHM operating SEC. |
| R3-33 | validation table | C/N | Heat to cooling circuit is compared against a single 40 % drawn from a 35–45 % range, contradicting the claim that published ranges are reproduced verbatim; same for [Si] at 1500 degC compared against a single 0.33 wt % although Table 12 reports 0.30–0.36 wt %. |

## Authors' own post-submission corrections (disclosed, not reviewer-raised)

| ID | Target | Class | Issue |
|---|---|---|---|
| A-1 | Table 13, §6.5 | C/N | The industrial windows printed in the submitted Table 13 were wider than those published in the source. Restored verbatim; four of twelve now fall outside. |
| A-2 | §6.5 | C/N | The industrial comparison is largely not an independent prediction. Reclassified as a consistency check with a provenance column and excluded from the statistics. |
| A-3 | Table 5 | T | The published Shahabuddin feed analysis sums to 99.80 wt %; the closing 0.20 wt % was added by the authors. Now disclosed with a sensitivity. |
| A-4 | Table 5, §3.4, §6.10 | T | Titanium appears in no comparison and in no source; its predictions are unvalidated. Now stated. |
| A-5 | §5.1, references | T | Reference [10] is listed as "drafted" in the review's bibliography and its data cannot be substantiated from the available sources. |
