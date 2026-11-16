# ESF-DT — Theory manual

Governing equations, closures and assumptions of the Electric Smelting
Furnace digital twin. Reference plant anonymised as **Industry-X**.

---

## 1. The process

The Electric Smelting Furnace is a rectangular, six-in-line, open slag bath
furnace. Söderberg electrodes dip into a molten oxide slag; current passes
between them mainly through the slag itself, with a small brush arc at each
tip. DRI, carburiser and flux are fed continuously onto the bath surface,
melt at the pile/slag interface, and the residual FeO is reduced by carbon
dissolved in the metal and by char floating in the slag. Hot metal collects
under the slag and is tapped periodically.

Unlike a submerged-arc furnace there is no burden column: the bath surface is
open, so radiation from the slag to the water-cooled roof and upper sidewall
is a first-order energy term, not a correction. Between 30 and 45 % of the
input energy leaves in the cooling water.

---

## 2. Thermochemistry

### 2.1 Enthalpy

Species enthalpies are integrated from Shomate-form heat capacities,

$$H_i(T) = \Delta H^\circ_{f,i}(298) + \int_{298}^{T} c_{p,i}\,\mathrm{d}T
  + \sum \Delta H_{\text{trans}}$$

For a solute that is liquid only because it is dissolved — iron in 3.5 wt% C
hot metal at 1500 °C is 38 K below the melting point of pure iron — the
**undercooled liquid** branch is used: the solid path to $T_m$, the latent
heat, then the liquid heat capacity back down to $T$. Ignoring this
under-predicts the hot-metal enthalpy by about 20 %.

### 2.2 Slag enthalpy

A slag is not a mechanical mixture of pure oxides, and pure-oxide heats of
fusion over-predict its heat content by a factor of three. The model uses

$$h_{\text{slag}}(T) = \underbrace{\sum_i w_i\,[H_i(T_{\text{liq}}) - H_i(298)]}_{\text{sensible, solid path}}
  + \underbrace{\sum_i w_i L_i^{\text{eff}}}_{\text{latent in solution}}
  + \underbrace{c_p^{\ell}\,(T - T_{\text{liq}})}_{\text{superheat}}$$

where $L_i^{\text{eff}}$ are effective latent heats *in the silicate
solution*, markedly lower than the pure-oxide values because the network
forms exothermically. They are calibrated so that a typical smelter slag
carries 1.85–1.95 MJ/kg at 1550 °C, in line with published blast-furnace and
smelter slag heat contents. A small regular-solution mixing term is added on
top.

### 2.3 Activities

Silica activity, referenced to pure liquid silica, is fitted to the
CaO–SiO₂–Al₂O₃–MgO sections used in the hydrogen-DRI smelting literature:

$$\log \gamma_{\mathrm{SiO_2}} = -2.05\,(B_3 - 1) - 0.42\,\frac{(\mathrm{Al_2O_3})}{(\mathrm{SiO_2})} - 0.35,
\qquad a_{\mathrm{SiO_2}} = \gamma\, x_{\mathrm{SiO_2}}$$

with $B_3 = (\mathrm{CaO}+\mathrm{MgO})/\mathrm{SiO_2}$ and a temperature
correction $\exp[-3100(1/T - 1/1773)]$. The coefficient is an empirical
correlation in basicity, alumina ratio and temperature; it is not taken from
a solution model, and its values are not comparable with tabulated Raoultian
activity coefficients.

Earlier versions squared the mole fraction and described the exponent as
quasi-chemical. That was wrong and has been removed. Silica was the only
oxide in the model treated that way, FeO, MnO and TiO₂ all being first power;
the silica mole fraction varies by only about 1 % across the four anchors the
expression was fitted to, so the exponent was absorbed into the reduction
Gibbs energy rather than being identified by the data; and refitting that
Gibbs energy with the first power reproduces the published anchors to 1.2 %
and 0.9 % against 3.3 % and 6.7 % for the squared form.

Optical basicity follows the standard mole-fraction-weighted form over the
oxygen contributed by each oxide.

### 2.4 The metal phase

Solute activities use Wagner first-order interaction parameters,

$$\log f_i = \sum_j e_i^j\,[\%j],\qquad h_i = f_i\,[\%i]$$

corrected to temperature by the $1873/T$ factor. Carbon saturation follows
the standard Fe–C liquidus expression with corrections for Si, P and Mn.

### 2.5 Reduction equilibria

For silicon,

$$(\mathrm{SiO_2}) + 2[\mathrm{C}] = [\mathrm{Si}] + 2\{\mathrm{CO}\},
\qquad K = \frac{h_{\mathrm{Si}}\;p_{\mathrm{CO}}^{2}}{a_{\mathrm{SiO_2}}\,h_{\mathrm{C}}^{2}}$$

with $\Delta G^\circ = 583\,000 - 329.5\,T$ J/mol. The strong temperature
dependence of this reaction is what makes silicon such a sensitive indicator
of superheat: the model reproduces 0.03 wt% at 1400 °C and 0.62 wt% at
1525 °C. Manganese, titanium and phosphorus follow analogous expressions.
Phosphorus is essentially fully reduced under ESF conditions; there is no
oxidising slag to hold it.

### 2.6 Sulphur

Sulphide capacity from the optical-basicity correlation, converted to a
partition ratio through the oxygen activity fixed by the C–CO equilibrium:

$$L_S = \frac{(\%\mathrm{S})}{[\%\mathrm{S}]} = C_S\,\frac{1}{a_{\mathrm{O}}}\sqrt{\frac{1}{p_{\mathrm{O_2}}}}$$

capped at 25 to stay inside the range observed in reducing smelting slags.

---

## 3. Heat transfer and the lining

### 3.1 The zone network

Five zones are solved as one-dimensional multilayer walls: **hearth**,
**metal wall**, **slag wall**, **freeboard** and **roof**. Each is a series
of conduction resistances with an inner film coefficient and an outer film
that is forced air or water, with radiation added for air-cooled surfaces.
Layer conductivities are evaluated at each layer's own mean temperature and
the node temperatures are iterated to convergence.

### 3.2 The freeze lining

Modern slag zones are built deliberately **thin and cold**: a ramming skim
directly against copper coolers, so that a layer of solidified slag forms and
becomes the working lining. The steady balance is

$$h\,(T_{\text{bath}} - T_{\text{liq}})
  = \frac{T_{\text{liq}} - T_{\text{sink}}}{x/k_f + R_{\text{lining}}}$$

which solves analytically for the thickness,

$$x = k_f\left[\frac{T_{\text{liq}} - T_{\text{sink}}}{h\,(T_{\text{bath}} - T_{\text{liq}})} - R_{\text{lining}}\right]$$

A negative $x$ means no freeze layer can be sustained and the refractory hot
face runs above the slag liquidus — chemical wear rather than a protective
skull. This is the design criterion for the slag zone, and it is why a
heavily brick-lined slag belt cannot hold a skull however hard it is cooled.

On the reference case the model gives a 49–75 mm skull with the hot face
sitting at the slag liquidus, and the shell below 200 °C.

### 3.3 Open-bath radiation

The exposed slag radiates to the cooled panels above,

$$\dot{Q}_{\text{open}} = \varepsilon\,\sigma\,A_{\text{bath}}
  \left(T_{\text{slag}}^{4} - T_{\text{hot face}}^{4}\right)$$

This is a slag-side debit; the panels remove it. At steady state whatever the
panels take must have arrived either from the bath or from the brush arcs,
which is the closure used to keep the freeboard energy balance consistent
without double-counting.

### 3.4 The feed pile

Melting occurs at the pile/slag interface, not by heating the whole pile to
its melting point. The specific enthalpy of melting is

$$\Delta h = c_p\,(T_{\text{soft}} - T_{\text{pile}}) + L,
\qquad \dot{m}_{\text{melt}} = \frac{\dot{Q}_{\text{pile}}}{\Delta h}$$

and the bulk pile temperature follows from an enthalpy balance on the pile
including the incoming cold feed and the enthalpy leaving with the melt. A
cold, fast feed therefore depresses the pile temperature and slows melting,
which is the behaviour seen in the plant. Modelling the pile as a lumped mass
that must be uniformly heated before any melting occurs produces a spurious
stall and was rejected.

---

## 4. Reaction kinetics

All rates are written in mass-transfer form, $r = k\,A\,C\,\Delta$, with
$k = k_0\exp(-E_a/RT)$ in m/s.

| Reaction | Driving force | Area |
|---|---|---|
| (FeO) + [C] → Fe + CO | $C_{\mathrm{FeO}}\,(1 - a_{\mathrm{FeO}}^{\text{eq}}/a_{\mathrm{FeO}})$ | slag/metal interface |
| (FeO) + C(char) | as above | char surface, from mass and particle size |
| (SiO₂) + 2[C] | $[\%\mathrm{Si}]^{*} - [\%\mathrm{Si}]$ | slag/metal interface |
| (MnO) + [C] | $[\%\mathrm{Mn}]^{*} - [\%\mathrm{Mn}]$ | slag/metal interface |
| C(s) → [C] | $[\%\mathrm{C}]_{\text{sat}} - [\%\mathrm{C}]$ | char particle surface |
| Lime dissolution | first-order relaxation, product-layer control | — |

Carbon consumed by reduction is drawn preferentially from floating char and
only then from the dissolved carbon, which is what keeps the bath carburised
in a well-run furnace and lets it decarburise in a starved one.

---

## 5. Electrical model

Each electrode sees a slag path resistance combining a cylindrical spreading
term and a tip term in parallel,

$$R_{\text{cyl}} = \frac{\ln(L_{\text{eff}}/r)}{2\pi\sigma\,h_{\text{imm}}},
\qquad R_{\text{tip}} = \frac{1}{4\sigma r},
\qquad R_{\text{slag}} = \left(R_{\text{cyl}}^{-1} + R_{\text{tip}}^{-1}\right)^{-1}$$

in series with the electrode's own ohmic resistance. The brush arc adds a
voltage drop $U_{\text{arc}} = 40 + 1250\,\ell_{\text{arc}}$ volts, giving the
100–120 V interface drop reported for 180–230 V applied. The tap voltage is
solved by bisection to hit a power setpoint.

Slag electrical conductivity follows

$$\sigma = \sigma_0\exp(-E_a/RT),\quad
E_a = 110 - 55(\Lambda - 0.55) - 0.9\,[(\mathrm{FeO})+(\mathrm{MnO})]\ \text{kJ/mol}$$

calibrated to 20–45 S/m at 1550 °C for a typical CaO–SiO₂–Al₂O₃–MgO smelting
slag. This matters more than it looks: an early version at 2 S/m starved the
furnace of power and produced a spurious cold-slag runaway, which is exactly
the real failure mode the correlation has to reproduce correctly.

---

## 6. The static solver

The static model closes simultaneously, on a basis of 1000 kg contained iron:

1. metallic and oxidised iron from the metallisation ratio;
2. gangue oxides from the DRI and the carburiser ash;
3. reduction of FeO, SiO₂, MnO, TiO₂ and P₂O₅ from the equilibria of §2.5,
   with a kinetic floor on manganese;
4. carbon demand for reduction and carburisation, divided by the carburiser
   yield;
5. flux addition solved as one exact two-variable linear system,

   $$m_1(c_1 - B_2 s_1) + m_2(c_2 - B_2 s_2) = B_2\,\mathrm{SiO_2}_g - \mathrm{CaO}_g$$
   $$m_1(g_1 - x b_1) + m_2(g_2 - x b_2) = x\,S_{\text{base}} - \mathrm{MgO}_g$$

   where $c,g,s,b$ are the CaO, MgO, SiO₂ and total oxide delivered per
   kilogram of each flux. Writing the slag growth that the flux itself
   causes into the constraint is what makes the system exact; targeting a
   lagged slag-mass estimate instead makes the iteration diverge whenever a
   flux cannot actually deliver the MgO target. A non-negative solution may
   not exist — a flux whose MgO content is below $x b$ dilutes the slag
   faster than it enriches it — in which case basicity is honoured and the
   MgO target is reported as unreachable;
6. sulphur partition;
7. the heat balance, from which the three specific energies follow.

Convergence is on the hot metal mass, the carbon demand and the silicon
level, typically to 1 part in 10⁹ in under 30 iterations.

---

## 7. The dynamic solver

Explicit Euler over five control volumes with a default 10 s step; a seven
hour campaign solves in a few seconds. Per step:

1. solve the electrical operating point at the current slag conductivity,
   immersion and arc length;
2. add the feed to the pile;
3. update the quasi-steady lining network every few minutes;
4. heat and melt the pile, and route the melt to metal, slag and char;
5. advance the kinetics of §4 and the sulphur, phosphorus and titanium
   partitions;
6. close the energy balances on slag, metal and freeboard;
7. service the tapping schedule;
8. test the alarm conditions and log any transition;
9. write the trajectory.

The freeboard has negligible thermal mass and is treated as quasi-steady. Its
temperature follows from an energy balance rather than from a mixing rule: the
gas is a participating medium that absorbs from the slag surface below,
radiates and convects to the water-cooled roof and upper sidewall above, and
is carried through at the rate the reactions and the ingress air supply it,
with post-combustion of CO releasing heat inside the gas itself,

$$\dot m c_p (T_g - T_{in}) = Q_{pc}
  + \varepsilon_g \sigma A_b (T_s^4 - T_g^4)
  - \varepsilon_g \sigma A_r (T_g^4 - T_r^4)
  - \varepsilon_g \sigma A_w (T_g^4 - T_w^4)
  + h A_b (T_s - T_g) - h A_r (T_g - T_r) - h A_w (T_g - T_w)$$

Every term on the right falls as \(T_g\) rises while the left side rises, so
the balance has a single root, found by bisection. The gas is bounded below by
the coldest surface it sees and above by its inlet temperature plus the
adiabatic post-combustion rise.

The grey-gas emissivity is evaluated on the freeboard composition computed
from the gas streams themselves, not on a prescribed one. Ingress air is the
larger part of the freeboard mass flow on a furnace of this size and dilutes
the radiating species: about 28 % CO and 6 % CO2 by mole at the base case,
giving an emissivity near 0.31.

Earlier versions of this model took the gas temperature as the mean of the
slag temperature and the roof hot face plus a post-combustion rise capped at
150 K. That rule entered the water-cooled roof as a heat source of the same
weight as the bath, and the roof hot face is itself a response to the gas
temperature through the lining network, so the two drove one another upwards
with a loop gain of one half. The gas settled about 204 K above the bath that
is its only heat source and the roof hot face above the bath as well, which
in turn suppressed the open-bath radiation debit of section 3.3, at times to
zero. Both faults are removed by the balance above.

---

## 8. What is calibrated, and to what

Being explicit about this is the point of the section.

| Constant | Value | Calibrated against |
|---|---|---|
| Effective latent heats in slag solution | table in `thermo.py` | molten slag heat content 1.85–1.95 MJ/kg at 1550 °C |
| Slag mixing enthalpy scale | 0.15 | as above |
| SiO₂ reduction Gibbs energy, A term | 596.2 kJ/mol | the two published [Si] values printed at 1400 and 1525 °C |
| Slag electrical conductivity | $\sigma_0$, $E_a$ | 10–60 S/m band reported for smelting slags |
| Slag liquidus base | 1673 K | CaO–SiO₂–Al₂O₃–MgO liquidus surface |
| Sulphide partition cap | 20 | hot-metal sulphur in reducing smelting practice |
| Kinetic pre-exponentials | see `HELP.md` §7 | plant data — these are the handles left for the user |

Everything else — heat capacities, enthalpies of formation, Gibbs energies,
Wagner parameters, transport correlations, the lining solver, the electrical
network — is used as published, without adjustment.

A thermal-utilisation factor of 0.887 appeared in earlier versions of this
table, described as the fraction of heat delivered to the bath that ends up
in the products. It has been withdrawn. The ratio it represented is not
constant: across the published specific energies that can be verified it
runs from 0.775 to 0.886, which is not the behaviour of a physical
efficiency. What it was doing was splitting the difference between a
loss-free and a loss-inclusive specific energy on sources that do not state
which of the two they report.

The model therefore now reports two physically defined tiers and no fitted
one. The reversible tier excludes all furnace losses; the operating tier
includes the lining and shell losses and the electrical-to-bath efficiency.
A published figure whose convention is unknown is tested against the
interval between them.

---

## 9. Empirical limits on the approach to equilibrium

Three product variables are set in practice not by equilibrium but by how
far the slag/metal reactions actually get in the residence time available.
Bae and Park measured this directly under ESF conditions: their slag reached
a basicity of C/S = 0.5 where equilibrium predicted 1.2, because SiO2
reduction is sluggish.

**Silicon.** Equilibrium silicon rises steeply with temperature and, above
about 1525 degC, exceeds anything an ESF taps. The model therefore offers
two bases. `silicon_mode="equilibrium"` returns the thermodynamic result and
is what equilibrium codes report. `silicon_mode="kinetic"`, the default,
applies a saturating ceiling

$$[\%\mathrm{Si}] = S_c\left(1 - e^{-[\%\mathrm{Si}]_{\text{eq}}/S_c}\right)$$

which leaves the low-temperature values untouched and asymptotes to the
ceiling $S_c$ (default 0.45 wt%, the industrial open-bath-furnace figure).

**Residual FeO.** At the carbon levels an ESF runs, equilibrium FeO in the
slag is essentially nil, yet industrial slag is reported at 0.6-0.7 wt%. A
practical floor is applied in kinetic mode; setting it to zero recovers the
equilibrium result.

**Manganese.** Equilibrium would strip almost all the manganese into the
metal. Industrial slag retains 0.15-0.30 wt% MnO, so manganese is bounded
both ways in kinetic mode.

All three are inputs, all three are reported alongside their equilibrium
values, and all three default to the industrial basis rather than the
thermodynamic one.

---

## 10. Two DRI reporting conventions

A DRI analysis states either total iron with a separate metallisation ratio,
or metallic iron together with an explicit iron-oxide assay. The second
convention already fixes the metallisation, so applying the ratio again
charges the oxidised iron twice. Both engines detect which convention an
analysis uses; when an assay is present the metallisation input is ignored
and the user is told. Metallic Mn, Si and P reported in an analysis are
carried as already-reduced solutes and never counted as something reduced
out of the slag.

---

## 11. Slag valorisation

The commercial case for the ESF route rests partly on its slag being usable
as a supplementary cementitious material, which blast-furnace slag already
is and a high-basicity foaming EAF slag is not. An EAF melting low-grade DRI
needs a basicity near 2 for its foaming practice and runs above 20 wt% FeO,
which both loses iron and destroys the hydraulic value of the slag. An ESF
runs near B2 = 1, close to blast-furnace slag.

The model scores the tapped slag on three criteria: basicity in the
0.85-1.30 band, FeO below 2 wt%, and free MgO below saturation, estimated as

$$(\mathrm{MgO})_{\text{sat}} \approx 4.0 + \frac{7.5}{B_2} + 0.08\,(\mathrm{Al_2O_3})$$

Free MgO matters because it hydrates to Mg(OH)2 with a volume expansion that
cracks cement products.

---

## 12. Known limitations

* Zero-dimensional in each zone. There is no spatial resolution of the
  electrode-to-electrode current distribution, the slag flow field or
  local overheating near the tips. A CFD or resistance-network extension is
  the natural next step for refractory-life work.
* The freeboard chemistry is a single post-combustion ratio, not a reacting
  gas-phase model.
* Titanium is treated with an empirical reduction fraction rather than a full
  Ti³⁺/Ti⁴⁺ speciation.
* Foaming is reported as an index, not coupled back to the electrical
  operating point.
* Electrode consumption is a specific rate, not a paste-baking model.
* The sensitivity of specific energy to carbon in the hot metal is about
  half the published value and the missing term has not been identified;
  see `VALIDATION.md` §6. The absolute energy at any given carbon level is
  unaffected.

---

## 13. Correctness harness

`audit.py` sweeps the full input space and rejects any result that is not
physically possible, independently of whether it matches a benchmark. It
covers every material against every other, the operating envelope one
variable at a time, both heat-loss modes, four furnace sizes, corner cases
and the dynamic engine — 158 configurations, currently with no failures.
The defects it found in earlier builds are listed in `VALIDATION.md` §7.

Two configurations are refused outright rather than answered:

* neither flux can raise the slag basicity (both are acid);
* a flux charge above 1.2 t per tonne of contained iron, which means the
  algebra is running away rather than describing an operating point.

---

© Extractmet Private Limited, IIT Madras Research Park. ESF-DT v1.0.0.
