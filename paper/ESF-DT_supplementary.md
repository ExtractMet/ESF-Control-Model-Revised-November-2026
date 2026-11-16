# Supplementary material

**Coupled steady-state and transient modelling of the electric smelting furnace for hydrogen-DRI ironmaking**

This document holds the material moved out of the main text during revision, together with the checks requested by the reviewers. Section numbers refer to the revised manuscript.

---

## S1. Solution algorithms

### Algorithm S1. Steady-state solution

The line numbers below are those cited in Sections 3.9 and 4.2 of the manuscript.

```
 1  set basis to 1000 kg contained Fe; speciate the charge
 2  initialise slag composition, hot metal mass, carbon demand, silicon
 3  repeat
 4      route gangue and carburiser ash to the slag
 5      solve flux demand from Eqs. (24) to (26)
 6      if no non-negative solution exists, satisfy B2 and
 7          report the MgO target as unattainable
 8      evaluate slag and metal equilibria, Eqs. (6) to (10)
 9      apply the empirical limits of Section 3.5, Eq. (11)
10      bound Si by the silica available in the slag
11      evaluate carbon demand; divide by carburiser yield
12      update hot metal mass and slag mass
13      evaluate the residual, Eq. (30); damp if it stalls
14  until the residual falls below the tolerance
15  close the energy balance, Eqs. (1) to (5)
16  evaluate the two specific energy tiers, Eq. (28)
17  solve the lining network and freeze lining, Eqs. (12) to (16)
18  solve the electrical operating point, Eqs. (17) to (21)
19  evaluate closure, Eq. (27), and the slag valorisation index, Eq. (29)
20  check the tapping temperature against the computed liquidus; flag if below
```

Two features require comment. Line 5 obtains the flux demand in closed form rather than by iteration. Formulations that lag the slag mass behind the flux addition do not converge when the selected flux dilutes MgO faster than it enriches it, because the flux both serves the target and adds to the slag it is computed against; the exact two-by-two system of Eqs. (24) to (26) removes that lag and makes the infeasible case explicit at lines 6 and 7. Line 13 damps the iteration when the residual stops descending, which prevents the limit cycle that otherwise appears at high scrap fractions, where silicon is fixed by the scrap rather than by equilibrium.

### Algorithm S2. Transient solution

The line numbers below are those cited in Section 6.8 of the manuscript.

```
 1  initialise the five control volumes from the specified heel
 2  for t = 0 to t_end, step dt
 3      solve the electrical operating point, Eqs. (17) to (21), at the current
 4          slag conductivity, immersion depth and arc length
 5      if power control is by temperature, apply feed-forward from the
 6          melting demand and lining loss with a PI trim on metal temperature
 7      charge the feed to the pile
 8      re-solve the lining network periodically, Eqs. (12) to (16)
 9      melt at the pile and slag interface, Eq. (5)
10      partition the melt between metal, slag and floating char
11      advance the kinetics of Table 8, Eqs. (22) and (23)
12      advance the S, P and Ti partitions
13      close the energy balance on slag and metal; solve the freeboard
          balance of Section 4.3.1 for the gas temperature
14      service the metal and slag tapping schedules
15      evaluate alarm conditions and record any transition
16      write the trajectory record
17  end for
```

Integration is explicit Euler with a default step of 10 s.

---

## S2. Convergence, solution time and step-size independence

Moved from Section 4.4 at the suggestion of Reviewer 2.

### S2.1 Iteration counts

The steady-state solution converges in 25 iterations or fewer for every case examined. The table below gives the counts and final residuals across the scrap blending series, which is the most demanding family.

| Grade | Scrap, wt % | Iterations | Final residual |
|---|---:|---:|---:|
| DRI-A | 0 | 19 | 9.1e-07 |
| DRI-A | 20 | 22 | 8.4e-07 |
| DRI-A | 40 | 24 | 9.0e-07 |
| DRI-A | 60 | 25 | 7.8e-07 |
| DRI-C | 0 | 19 | 8.6e-07 |
| DRI-C | 20 | 23 | 8.8e-07 |
| DRI-C | 40 | 24 | 9.2e-07 |
| DRI-C | 60 | 25 | 7.5e-07 |

Convergence is declared at a residual of 1e-6 in Eq. (30), which is the tolerance at which the iteration exits. The submitted version exited at 1e-6 but declared convergence at 1e-4, so a run that stalled between the two would have been reported as converged. All 178 admissibility configurations satisfy the stricter test.

### S2.2 Solution time

Measured on a single core.

| Case | Time |
|---|---:|
| Steady state, lining loss prescribed as a fraction | 2.8 ms |
| Steady state, five-zone lining network solved | 35.5 ms |
| Transient campaign, 7 h at a 10 s step | 2.1 s |

A parametric study of thirty steady-state cases therefore completes in under a second, which is what makes the operating-window mapping of Section 6 and the worked example of Section S13 practical.

### S2.3 Step-size independence

The reference seven-hour campaign repeated at three step sizes.

| Step, s | Specific energy, kWh/tHM | Deviation | Productivity, tHM/h | Deviation | Wall time, s |
|---:|---:|---:|---:|---:|---:|
| 5 | 707.430 | reference | 143.141 | reference | 3.0 |
| 10 | 707.420 | -0.001 % | 143.202 | +0.042 % | 2.1 |
| 30 | 707.385 | -0.006 % | 143.444 | +0.212 % | 1.5 |

The default 10 s step introduces no significant discretisation error.

---

## S3. Specific energy against tapping temperature at 90 % metallisation

Reviewer 3 asked why the specific energy at 1300 degC for 90 % metallisation of the 16 wt % gangue feed was almost identical to that at 1500 degC for 100 % metallisation of DRI-A, and whether a parameter was wrong. The table below gives the full temperature dependence for that case, computed on the reversible tier.

| Tapping temperature, degC | Specific energy, kWh/tHM | Slag liquidus, degC | Operable |
|---:|---:|---:|---|
| 1250 | 474.3 | 1427 | no, below liquidus |
| 1300 | 491.5 | 1427 | no, below liquidus |
| 1350 | 509.1 | 1427 | no, below liquidus |
| 1400 | 528.7 | 1428 | yes |
| 1431 | 543.1 | 1429 | yes |
| 1450 | 553.6 | 1430 | yes |
| 1500 | 593.3 | 1437 | yes |
| 1550 | 658.3 | 1460 | yes |
| 1600 | 715.9 | 1499 | yes |

The curve is smooth and monotonic with no plateau, so the coincidence the reviewer identified is genuine and not the result of a clamped parameter. The two cases meet because a lower temperature at higher gangue and lower metallisation offsets a higher temperature at lower gangue and full metallisation.

The table also shows the separate point the reviewer raised. The slag liquidus for this feed is about 1428 degC, so the three lowest temperatures are not operable tapping conditions. The 1300 degC comparison has been withdrawn from the validation set for that reason and is reported in Section 6.10 as a formally valid result at an inoperable condition.

---

## S4. Complete validation table

The complete table of 95 rows is supplied as the worksheet `03 Validation table` in the accompanying workbook `ESF-DT_validation_data.xlsx` and as `figures/validation_table.csv` in the code package. Each row carries:

- **case** and **quantity**, identifying the comparison
- **model** and **literature**, the two values, with ranges written as `low-high`
- **rpd_pct**, the relative percentage deviation of Eq. (31), or `in window` or `outside` for an interval test
- **basis**, whether the model was run on the equilibrium basis, with the empirical limits active, or as a transient
- **role**, which determines whether the row enters the statistics
- **provenance**, where the reference value comes from
- **note**, any qualification specific to that comparison
- **source**, the citation

The roles are as follows.

| Role | Rows | Enters the statistics | Meaning |
|---|---:|---|---|
| independent | 50 | yes | tests the model against a reference it was not fitted to |
| detail | 14 | no | a single tier reported beside the interval test that is counted |
| consistency | 12 | no | the industrial composition comparison of Section 6.5 |
| internal | 10 | no | agreement between the two solvers, Section 6.9 |
| calibration | 3 | no | compromised by fitting, Section 5.3 |
| orientation | 3 | no | from another furnace class or an unknown operating point |
| reference_inconsistent | 2 | no | the published value is unsupported by its own balance |
| formal | 1 | no | valid but below the liquidus, Section 5.5 |

---

## S5. Admissibility sweep

The 178 configurations of Section 5.5, in summary.

| Family | Configurations checked |
|---|---:|
| Material library cross-product: every DRI grade against every carburiser, and every flux against every other flux | 90 |
| Operating envelope, varied one parameter at a time | 56 |
| Heat-loss formulations and furnace geometry | 12 |
| Corner cases | 7 |
| Transient campaigns | 13 |
| **Total** | **178** |

All 178 configurations satisfy the admissibility criteria and none fails. A further 10 configurations are not counted above because the model correctly refuses them: these are flux pairs in which neither member can raise the slag basicity, for which Eqs. (24) to (26) admit no non-negative solution, and the solver returns a diagnostic naming the cause rather than a converged but meaningless result. That refusal is recorded as correct behaviour.

One counted configuration, a hot metal at 1380 degC containing 0.5 wt % carbon with a basicity target of 0.7, returns a valid balance below the liquidus of its own metal. It is flagged by the check added in revision and reported separately rather than as a failure, since the balance is arithmetically correct and only the condition is inoperable.

---

## S6. Reproducing the results

The code package accompanying the paper reproduces every number in it.

```
python run_validation.py      # validation table, statistics and all figures
python audit.py               # the 178-configuration admissibility sweep
python paper/cross_check_ss_transient.py   # the solver comparison of Section 6.9
python paper/make_flowchart.py             # Figure 2
python paper/build_workbook.py             # the supplementary workbook
```

`run_validation.py` writes `figures/validation_table.csv`, `figures/validation_table.md` and `figures/validation_stats.json`. The statistics quoted in Section 6.1 are those in `validation_stats.json`.

## S7. Term-by-term energy balance for a representative case

[Table 3 gives the terms for a representative case, 94 % metallisation of DRI-B at 1500 degC, 3.4 wt % C and basicity 1.10. The sensible, latent and superheat parts are a decomposition of the two output enthalpies, not independent terms.]{.mark}

[**Table S1.** Term-by-term energy balance for the representative case, in kWh per tonne of hot metal.]{.mark}

| [Term]{.mark} | [Value]{.mark} | [Note]{.mark} |
|---|---|---|
| [Charge enthalpy in]{.mark} | [-1265.8]{.mark} | [absolute, all input streams]{.mark} |
| [Hot metal out]{.mark} | [335.3]{.mark} | [absolute]{.mark} |
| [Slag out]{.mark} | [-991.7]{.mark} | [absolute]{.mark} |
| [Off-gas out]{.mark} | [-39.1]{.mark} | [absolute]{.mark} |
| [Slag mixing enthalpy]{.mark} | [-5.8]{.mark} | [added once, outside the oxide enthalpies]{.mark} |
| [Calcination and moisture]{.mark} | [3.4]{.mark} | [Eq. (4); zero for burnt lime]{.mark} |
| [**Net process heat, Eq. (3)**]{.mark} | [**563.9**]{.mark} | [the reversible requirement]{.mark} |
| [Refractory and shell loss]{.mark} | [202.4]{.mark} | [five-zone network, Section 3.6]{.mark} |
| [Total delivered to the bath]{.mark} | [766.3]{.mark} | [net process heat plus losses]{.mark} |
| [of which: hot metal sensible and fusion]{.mark} | [321.2]{.mark} | [decomposition, not an extra term]{.mark} |
| [of which: hot metal dissolution]{.mark} | [14.1]{.mark} | [decomposition]{.mark} |
| [of which: slag sensible to liquidus]{.mark} | [126.0]{.mark} | [decomposition]{.mark} |
| [of which: slag latent in solution]{.mark} | [27.8]{.mark} | [decomposition]{.mark} |
| [of which: slag superheat]{.mark} | [13.9]{.mark} | [decomposition]{.mark} |

[The absolute enthalpies are large and of opposite sign because they include formation enthalpies; only their difference has meaning. The slag carries 167.7 kWh/tHM of sensible, latent and superheat content at 307 kg/tHM, or 1.97 MJ/kg, against 1.85 to 1.95 MJ/kg reported for comparable slags at 1550 degC.]{.mark}

## S8. Nomenclature

| Symbol | Definition | Unit |
|---|---|---|
| $a_i$ | thermodynamic activity of species $i$ | dimensionless |
| $A$ | interfacial area | m2 |
| $b$ | total oxide delivered per unit flux mass | dimensionless |
| $B_2$, $B_3$ | binary and ternary basicity | dimensionless |
| $c$, $g$, $s$ | CaO, MgO and SiO~2~ delivered per unit flux mass | dimensionless |
| $c_p$ | specific heat capacity | J kg^-1^ K^-1^ |
| $C_S$ | sulphide capacity | dimensionless |
| $e_i^j$ | Wagner first-order interaction parameter | dimensionless |
| $E_a$ | activation energy | J mol^-1^ |
| $f_i$ | Henrian activity coefficient of solute $i$ | dimensionless |
| $f_{\text{inc}}$ | incubation scaling factor | dimensionless |
| $h$ | heat-transfer coefficient | W m^-2^ K^-1^ |
| $h_i$ | Henrian activity of solute $i$ | wt % |
| $H_i$ | molar enthalpy of species $i$ | J mol^-1^ |
| $k$ | mass-transfer coefficient | m s^-1^ |
| $k_f$ | thermal conductivity of the frozen layer | W m^-1^ K^-1^ |
| $K$ | equilibrium constant | dimensionless |
| $L^{\text{eff}}$ | effective heat of fusion in slag solution | J kg^-1^ |
| $L_S$ | sulphur partition ratio | dimensionless |
| $m$ | mass | kg |
| $\dot{q}$ | heat flux | W m^-2^ |
| $Q$ | heat | W or J |
| $R_{\text{lining}}$ | thermal resistance of the lining | m2 K W^-1^ |
| $\mathcal{R}$ | convergence residual, Eq. (30) | dimensionless |
| $S_c$ | silicon kinetic ceiling | wt % |
| $T_{\text{liq}}$ | slag liquidus temperature | K |
| $x$ | frozen layer thickness | m |
| $\varepsilon_e$ | closure error on element $e$ | % |
| $\eta_C$ | carbon contact efficiency | dimensionless |
| $\eta_{\text{th}}$, $\eta_{\text{el}}$ | thermal utilisation and electrical-to-bath efficiency | dimensionless |
| $\theta$ | hot heel index, Eq. (23) | dimensionless |
| $\Lambda$ | optical basicity | dimensionless |
| $\sigma$ | electrical conductivity | S m^-1^ |
| $\sigma_{\text{SB}}$ | Stefan-Boltzmann constant | W m^-2^ K^-4^ |
| $\tau_{\text{inc}}$ | incubation time constant | s |
| $\phi_i$ | state variable in the convergence test | various |

**Abbreviations.** BOF, basic oxygen furnace; CFD, computational fluid dynamics; DRI, direct reduced iron; EAF, electric arc furnace; ESF, electric smelting furnace; MARD, mean absolute relative deviation; MR, metallisation ratio; OSBF, open slag bath furnace; RPD, relative percentage deviation; SEC, specific energy consumption; tHM, tonne of hot metal.

---

## S9. Consistency with industrial composition, full comparison

The published industrial open bath furnace composition [5,9] is a tempting validation target, and it is used here, but it cannot serve as an independent test. Two obstacles prevent that, and both are stated before the comparison rather than after it.

First, the corresponding feed analysis is not published. It had to be back-calculated from the reported slag, so the gangue oxides in the feed were chosen by the present author to reproduce the slag against which the model is then compared. Second, three model constants, the silicon ceiling of Eq. (11), the residual slag FeO floor, and the manganese transfer bounds, were calibrated against this same table, as recorded in Table 9.

Table S2 therefore reports the comparison together with the provenance of each quantity, so that a reader can see which entries carry information and which do not.

**Table S2.** Consistency with industrial open bath furnace composition, [1, Table 1] after [9]. Published values are reproduced verbatim and have not been widened. The provenance column states what determines each model value.

| Quantity | This work | Published, OSBF | Result | Provenance |
|---|---:|---|:---:|---|
| Hot metal Fe | 94.88 wt % | 94.7 to 94.8 | outside | outcome of the overall balance, independent |
| Hot metal C | 4.500 wt % | 4.5 | 0.0 % | operating target set in the run |
| Hot metal Si | 0.414 wt % | below 0.5 | satisfied | ceiling calibrated to this table |
| Hot metal Mn | 0.141 wt % | 0.14 | +0.5 % | feed MnO chosen; bounds calibrated to this table |
| Hot metal S | 0.022 wt % | 0.025 to 0.03 | outside | feed S chosen |
| Hot metal P | 0.024 wt % | 0.02 to 0.03 | satisfied | feed P~2~O~5~ chosen |
| Slag CaO | 41.37 wt % | 40.5 to 41.5 | satisfied | flux target set in the run |
| Slag MgO | 7.27 wt % | 7.0 to 7.5 | satisfied | flux target set in the run |
| Slag SiO~2~ | 38.31 wt % | 36.5 to 37.5 | outside | feed SiO~2~ back-calculated |
| Slag Al~2~O~3~ | 11.14 wt % | 10.5 to 11.0 | outside | feed Al~2~O~3~ back-calculated |
| Slag FeO | 0.647 wt % | 0.6 to 0.7 | satisfied | floor calibrated to this table |
| Slag MnO | 0.191 wt % | 0.20 to 0.25 | outside | feed MnO chosen; bounds calibrated to this table |

Only one entry, hot metal iron, is an independent prediction, and it lies 0.08 percentage points above a published range that is itself only 0.1 wt % wide. Three entries are operating targets set in the run and test nothing. Four are calibrated against this table and are circular by construction. Four follow from feed constituents chosen by the author.

What the exercise does demonstrate is that a single self-consistent feed, flux schedule and set of constants reproduces an entire industrial product specification to within a few per cent on every quantity simultaneously, which is a necessary condition for the model to be usable even though it is not a sufficient one for validation. It also shows where the residual tensions lie. Slag SiO~2~ and Al~2~O~3~ exceed their ranges by 2.2 % and 1.3 % relative, which means no single gangue ratio reproduces both the silica and the alumina of the published slag; the feed was not adjusted further to force agreement. Slag MnO falls 0.009 wt % below its range because the manganese bounds restrict transfer to at most 0.80 of the manganese charged, and raising that bound to close the gap would be circular twice over.

The equilibrium result is worse on the same test. Without the manganese bounds, essentially all manganese transfers to the metal and slag MnO falls to 0.055 wt %, further from the published range than the bounded result.

For these reasons the twelve entries of Table S2 are excluded from the validation statistics of Table 10, which rest on the equilibrium codes, the published stream balance, the supplier envelope and the laboratory experiment alone.

## S10. Phase transfers and the hot-metal basis

[Every specific quantity in this paper is divided by the hot metal produced, so the term needs a definition, and it is not the same as the mass of metal that leaves through the tap-hole.]{.mark}

[In the steady-state solver the furnace is a closed box on a basis of 1000 kg of contained iron. Contained iron means all the iron entering with the charge, whether it arrives as metallic iron in the DRI, as FeO in the unreduced fraction, or as scrap. Hot metal produced is then the mass of the liquid metal phase leaving that box, which is the iron that reports to the metal plus the carbon, silicon, manganese, phosphorus, sulphur and titanium dissolved in it. Because the solver is at steady state, nothing accumulates, so the metal produced and the metal tapped are the same quantity and the distinction does not arise.]{.mark}

[The relation to the iron basis is worth stating because the two differ. For the representative case of Table 3, 1000 kg of contained iron yields about 1043 kg of hot metal: the metal is heavier than the iron it contains, because of the dissolved solutes, and lighter than the charge, because the gangue leaves with the slag and the oxygen leaves with the off-gas. A result quoted per tonne of hot metal is therefore not the same number as the same result quoted per tonne of contained iron, and the two differ by about 4 %.]{.mark}

[Transfers between phases are accounted as follows. Iron entering as FeO and reduced moves to the metal output; iron remaining as FeO in the tapped slag is the iron lost to slag, which the residual FeO floor of Section 3.5 controls. Silicon, manganese, phosphorus and titanium move to the metal to the extent Sections 3.4 and 3.5 allow, the balance remaining as oxide. Sulphur partitions by Eq. (10). Carbon splits between dissolved carbon in the metal and CO and CO~2~ in the off-gas; none is retained in the slag. Every transfer is tested by the elemental closure of Eq. (27).]{.mark}

[In the transient solver the furnace is not closed, and the two quantities separate. Metal tapped is the mass actually removed through the tap-hole during the campaign, which is discrete and follows the tapping schedule. Metal produced is the metal tapped plus the change in the liquid metal inventory held in the furnace between the start and the end of the campaign. Over a campaign that begins and ends at the same bath level the two converge; over a shorter run they do not, and the campaign results in Section 6.8 report both. Specific energy for a campaign is the cumulative electrical energy divided by the metal produced, not by the metal tapped, so that energy spent raising the bath inventory is not charged to the metal that happened to leave.]{.mark}

## S11. Reference datasets and the conditions behind each

This table was moved from Section 5.1 of the manuscript.

**Table S3.** [Reference datasets, the conditions each source states, and the assumptions used where it states none.]{.mark}

| Source and class | Quantities compared | [Conditions stated by the source]{.mark} | [Not stated; assumed here]{.mark} |
|---|---|---|---|
| Owusu et al. [13], FactSage 7.0 equilibrium code | SEC and slag mass against metallisation for three DRI grades; [Si] against temperature; carbon consumption; scrap blending; hot metal composition | [1500 degC, 3.5 wt % C in hot metal, basicity 1.1, 1 atm, 100 % metallisation unless stated; full DRI analyses given]{.mark} | [flux type and quantity, carburiser type and yield, furnace size and heat losses; burnt lime with dolomitic lime, metallurgical coke at 92 % yield and the loss-free tier are used]{.mark} |
| Shahabuddin et al. [12], via [5], HSC equilibrium code | complete stream balance at 1600 degC; SEC at 90 % metallisation; published sensitivities | [1600 degC, 100 % metallisation, basicity 1.10, 3.5 wt % C; feed Fe, SiO~2~, Al~2~O~3~, Mn and S given]{.mark} | [the feed analysis sums to 99.80 wt %; the balance is assigned as described in Section 3.2. Flux and carburiser are not stated and are as above]{.mark} |
| Belford et al. [9], via [5], industrial plant | open bath furnace hot metal and slag composition | [none beyond the composition itself]{.mark} | [feed, temperature, basicity and carbon target all unknown and back-calculated; see Section 6.5]{.mark} |
| Tenova [10], via [5], supplier design envelope | SEC range; slag to metal ratio | [a design envelope for DRI melting, not a single operating point]{.mark} | [the operating point within the envelope]{.mark} |
| Metso Outotec [15], via [13], pilot scale | operating SEC; slag rate | [low-grade hydrogen-DRI smelting]{.mark} | [[13] records that no metallisation, temperature, hot metal carbon or feed gangue is reported, so the operating point is unknown; used for magnitude only]{.mark} |
| Bae and Park [6], laboratory experiment | carbon requirement; slag FeO and hot metal carbon with a hot heel | [1550 degC, 500 g melt, full DRI analyses, carbon addition and hot heel composition given]{.mark} | [scale: a crucible melt against a model parameterised for a 116 MW furnace]{.mark} |
| Pan et al. [11], via [5], six-in-line sulphide smelting furnace | share of input heat to the cooling water | [a six-in-line electric furnace for sulphide smelting]{.mark} | [a different furnace class from an ironmaking ESF; reported for orientation and excluded from the statistics]{.mark} |

## S12. Reproduction of the published stream balance

This table was moved from Section 6.2 of the manuscript, where its deviations are discussed.

**Table S4.** [Reproduction of the published stream balance at 1600 degC, 100 % metallisation, B2 = 1.10, 3.5 wt % C. All quantities printed in the published balance are included.]{.mark}

| Quantity | This work | Published [5,12] | RPD | [Status]{.mark} |
|---|---:|---:|---:|---|
| Hot metal | 1052.2 kg | 1055.0 kg | -0.3 % | [counted]{.mark} |
| Slag | 300.5 kg | 283.8 kg | +5.9 % | [counted]{.mark} |
| [Specific energy, reversible tier]{.mark} | [528.1 kWh/tHM]{.mark} | 598.2 kWh/tHM | [-11.7 %]{.mark} | [tier value]{.mark} |
| [Specific energy, operating tier]{.mark} | [652.0 kWh/tHM]{.mark} | 598.2 kWh/tHM | [+9.0 %]{.mark} | [tier value]{.mark} |
| [Specific energy, interval test]{.mark} | [528.1 to 652.0]{.mark} | 598.2 kWh/tHM | [satisfied]{.mark} | [counted]{.mark} |
| Slag SiO~2~ | 37.04 wt % | 37.75 wt % | -1.9 % | [counted]{.mark} |
| Slag CaO | 40.34 wt % | 41.63 wt % | -3.1 % | [counted]{.mark} |
| Slag Al~2~O~3~ | 20.16 wt % | 20.45 wt % | -1.4 % | [counted]{.mark} |
| [Slag FeO]{.mark} | [0.00 wt %]{.mark} | [0.17 wt %]{.mark} | [-100 %]{.mark} | [excluded, see below]{.mark} |
| Hot metal Fe | 95.04 wt % | 94.75 wt % | +0.3 % | [counted]{.mark} |
| Hot metal C | 3.50 wt % | 3.50 wt % | 0.0 % | [an input target, not a prediction]{.mark} |
| Hot metal Si | 0.45 wt % | 0.40 wt % | +12.5 % | [compromised by fitting]{.mark} |
| Hot metal Mn | 0.97 wt % | 1.20 wt % | -19.3 % | [compromised by fitting]{.mark} |
| [Hot metal S]{.mark} | [0.011 wt %]{.mark} | [0.04 wt %]{.mark} | [-71.6 %]{.mark} | [counted]{.mark} |
| [Hot metal P]{.mark} | [0.010 wt %]{.mark} | [0.10 wt %]{.mark} | [-90.1 %]{.mark} | [excluded, see below]{.mark} |
| [Off-gas, CO and CO~2~]{.mark} | [16.23 kg]{.mark} | [10.66 kg]{.mark} | [+52.3 %]{.mark} | [counted]{.mark} |
| [Carburiser carbon]{.mark} | [43.3 kg]{.mark} | [41.49 kg]{.mark} | [+4.4 %]{.mark} | [counted]{.mark} |

## S13. A worked operating decision

This example was moved from Section 6.12 of the manuscript.

[A plant melting DRI of 15.5 wt % gangue at 94 % metallisation and 143 t/h, tapping at 1500 degC with basicity 1.10 and 3.4 wt % carbon, must take a feed of 19 wt % gangue instead. With nothing else altered, specific energy rises from 851 to 897 kWh/tHM, only 5.3 %, but the slag rate rises from 307 to 387 kg/tHM, 26 %, so the furnace must tap 55 t/h of slag against 44 t/h, which is 5.5 t more per tap at a 30-minute interval. The electrical side is comfortable: operating resistance moves from 4.30 to 4.37 mohm, hearth power density from 316 to 333 kW/m2, and the freeze layer thickens from 59 to 67 mm as the higher slag rate carries more heat to the wall.]{.mark}

[Of two remedies, blending 20 wt % scrap brings the slag rate to 301 kg/tHM, specific energy to 825 kWh/tHM and hearth power density to 306 kW/m2, all below the original, since scrap carries no gangue and needs no reduction; lowering the basicity target to 0.95 reduces the slag rate only to 356 kg/tHM, leaves specific energy at 894 kWh/tHM, and thins the freeze layer from 67 to 54 mm, moving the lining the wrong way. The recommendation is scrap blending, and it rests on slag rate and freeze layer rather than on energy: a model returning only the energy envelope would have called this an easy change. The silicon and FeO in these runs carry the constraints of Section 3.5, fitted to a different furnace, so the mass and energy conclusions are sound while the composition figures should be checked against the plant's own tapping records.]{.mark}
