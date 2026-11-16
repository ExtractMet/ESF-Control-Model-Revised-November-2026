# Coupled steady-state and transient modelling of the electric smelting furnace for hydrogen-DRI ironmaking

**Ajay Shukla**^1,2,\*^

^1^ Department of Metallurgical and Materials Engineering, and Centre for Pyrometallurgy, Indian Institute of Technology Madras, Chennai 600036, India

^2^ Extractmet Private Limited, IIT Madras Research Park, Chennai 600113, India

\* Corresponding author.

---

## Abstract

The electric smelting furnace (ESF), built as an open slag bath furnace, is the appropriate unit for melting direct reduced iron from high-gangue ores. Published models are mostly equilibrium balances, and the equilibrium datasets that exist disagree with one another. This paper presents a coupled steady-state and transient model built from conservation laws, measured properties and reaction kinetics. The steady-state solver closes the elemental and heat balances on 1000 kg of contained iron, with slag and metal equilibria for Si, Mn, P and S, an analytic freeze-lining criterion and a slag-resistance electrical model. The transient solver advances the feed pile, slag, metal, freeboard and lining with mass-transfer kinetics, electrode regulation and tapping cycles. [Because measured silicon, slag FeO and manganese lie far from equilibrium, three empirical constraints bound the approach to it; they are not kinetics.]{.mark} [Against 48 benchmarks the mean absolute relative deviation over 17 single-valued comparisons is 14.6 %, median 4.0 %, and 22 of 31 interval tests are satisfied; the two published equilibrium codes differ from each other by 14.6 to 16.0 %. On one heat-loss basis the two solvers agree within 10 % on eight of ten quantities and to 3.8 % on specific energy.]{.mark} Physical admissibility is verified over 178 configurations, and the code is released for further testing against plant data.

**Keywords:** electric smelting furnace; open slag bath furnace; hydrogen direct reduced iron; process modelling; reaction kinetics; freeze lining; slag valorisation

---

## 1. Introduction

Electric steelmaking accounted for about 29 % of the 1885 Mt of crude steel produced in 2024, while world DRI production reached 144 Mt and remained concentrated where natural gas is cheap [1,2]. [India is the largest DRI producer and most of its output comes from coal-based rotary kilns rather than gas-based shaft furnaces, so the feedstock reaching any future smelter there differs in both carbon content and gangue chemistry from the gas-based material most published work assumes.]{.mark} As integrated works plan to replace blast furnace ironmaking with hydrogen direct reduction, melting the resulting DRI becomes the critical step.

The choice of melting unit is governed by ore quality. DRI from DR-grade pellets can be melted in an electric arc furnace; DRI from the high-gangue ores that dominate remaining reserves cannot be melted economically there, because foaming slag practice requires a binary basicity B2 = CaO/SiO~2~ near 2. [Slag FeO above 20 wt % is ordinary in scrap-based steelmaking, where it lowers viscosity and supports foaming and the iron it ties up is accepted in return. The difficulty with high-gangue DRI is not the FeO level but the slag quantity that a basicity near 2 demands: the lime needed roughly doubles the slag made per tonne of metal, and the iron lost with it scales with that mass.]{.mark} Visuri and Echterhof conclude that low-quality DRI is more economically processed in an ESF with the hot metal refined in a basic oxygen furnace [1].

An ESF also operates at B2 near unity, close to blast furnace slag, so its slag is expected to be usable as a supplementary cementitious material [1], which makes valorisation part of the economic case rather than incidental to it. A pilot ESF has been commissioned in Pori, Finland, and the hydrogen direct reduction, ESF and BOF route announced for Duisburg [1], [while hydrogen direct reduction itself has reached demonstration scale in Sweden and Finland [3]]{.mark}.

### 1.1 Statement of the problem

Process modelling has not kept pace. Reviewing ESF modelling, and building on their survey of the furnace in ironmaking [4], Sabah et al. conclude that although an extensive body of work exists for submerged arc furnaces and EAFs, independent studies of open slag bath furnaces are limited, and that both the brush arc and the distribution of heat require modelling [5]. They further observe that commercial furnaces have not been independently characterised for productivity or energy efficiency, supplier research being unpublished.

What exists is predominantly equilibrium mass and energy balances. These establish energy envelopes reliably but cannot describe the state of the bath between taps, the response of the lining to an upset, or why measured product chemistry departs from thermodynamic prediction. That departure is substantial: Bae and Park, smelting simulated hydrogen DRI under ESF conditions, computed a final slag basicity of C/S = 1.2 but measured about 0.5, concluding that SiO~2~ reduction did not reach equilibrium [6].

### 1.2 Objectives and novelty

[Given a DRI analysis, a metallisation ratio, a carburiser, two fluxes, a tapping temperature and composition targets, the steady-state solver returns the hot metal and slag masses per tonne tapped and their compositions, the carbon and flux demand, the off-gas, the specific energy on a loss-free and a loss-inclusive basis, the loss through each lining zone, the freeze-layer thickness, and the electrical operating point in the terms a smelter operator uses: operating resistance, current, tap voltage and hearth power density. Given the feed as a rate, the transient solver returns the same quantities through tapping cycles, with bath inventories, lining temperatures and the power regulation needed to hold tapping temperature.]{.mark}

[What is new is not any single sub-model. Published ESF models return the energy envelope and the equilibrium product chemistry and do that well; none returns the state of the bath between taps, the response of the lining to an upset, or the electrical operating point, and none reproduces the measured departure of product chemistry from equilibrium. This model does those four things, and is assessed not only against published figures but against a physical-admissibility sweep that no reference data constrain.]{.mark}

Four aspects are believed to be new. First, a transient, physically resolved model of the open slag bath furnace, addressing the gap identified in [5]. Second, an analytic criterion for the sustainability of a freeze lining on a copper-cooled slag belt, converting a qualitative design requirement into a testable inequality. Third, [an empirical formulation bounding the approach to equilibrium]{.mark} for silicon, residual slag FeO and manganese, which reconciles two mutually inconsistent published datasets and reproduces industrial tapping practice. Fourth, verification of physical admissibility across the full input space, independently of agreement with reference data.

Section 2 reviews the literature and identifies the gaps addressed. Section 3 presents the model, Section 4 the numerical solution, Section 5 the validation methodology, Section 6 the results and Section 7 the conclusions.

---

## 2. Literature review

### 2.1 Process configuration and commercial status

Electric smelting furnaces have an established history in ferro-alloy and non-ferrous production [5]. High specific energy relative to the blast furnace historically excluded them from ironmaking, a position reversed by decarbonisation and declining ore quality. The open slag bath furnace (OSBF), in which a brush arc rather than a submerged arc transfers energy to the bath, is presented by suppliers as among the more promising routes to hot metal [5].

Four commercial offerings are documented [5]. Metso Outotec market a DRI smelter rated at 1.2 Mtpa and 112 MW, 35 m by 11 m [5,7]; Primetals offer a smelter accepting a wide input range with adjustable hot metal carbon [5,8]; SMS group propose a 2.5 Mt/year plant coupled to three circular or two rectangular OSBFs [5,9]; and the Tenova iBlue concept combines an OSBF with Energiron direct reduction, with a design specific energy of 0.5 to 1.2 MWh/t and a slag to metal ratio of 0.07 to 0.25 [5,10]. These envelopes are used as validation targets in Section 6.

### 2.2 Thermal design and the refractory lining

Zone-specific cooling is described only qualitatively in [5]: intensive cooling of the slag belt to hold a protective freeze layer, moderate cooling of the metal zone, and moderate to high cooling of freeboard and roof; Section 3.6 turns the first of these into a quantitative criterion. For an open bath the heat rejected to cooling is a first-order term, Pan et al. reporting 35 to 45 % of input absorbed by the cooling water of six-in-line sulphide smelting furnaces [5,11].

### 2.3 Steady-state mass and energy balance models

Shahabuddin et al. built an HSC Chemistry balance of a smelter to examine the influence of ore gangue [5,12], over 1077 to 1190 kg DRI per tonne Fe, 1300 to 1600 degC, 90 to 100 wt % metallisation, basicity 1.1 and 1 to 3.5 wt % carbon. Their principal results, as reported in the review, are given in Table 1.

**Table 1.** Steady-state modelling results of Shahabuddin et al. as reported in [5], used here as validation targets.

| Quantity | Reported value |
|---|---|
| SEC at 90 wt % metallisation, 1300 degC | 706 kWh/tHM |
| SEC at 90 wt % metallisation, 1600 degC | 850 kWh/tHM |
| SEC, cold DRI from 7 wt % gangue ore, 100 % MR | 572 kWh/tHM |
| SEC, cold DRI from 16 wt % gangue ore, 100 % MR | 684 kWh/tHM |
| Sensitivity to hot metal carbon at 1500 degC | 10 kWh/tHM per 1.0 wt % |
| Sensitivity to ore gangue | 13 to 20 kWh/tHM per 1.0 wt % |
| Sensitivity to metallisation ratio | 12 kWh/tHM per 1.0 wt % |
| Sensitivity to scrap in blend at 1500 degC | 2.5 kWh/tHM per 1.0 wt % |

The review also tabulates a complete stream-by-stream balance at 1600 degC [1, Table 3] and a blast-furnace against open-bath composition comparison [1, Table 1; 6], both used in Section 6.

[Owusu et al. have since published a FactSage 7.0 assessment covering three hydrogen-DRI grades from low-grade Australian ores [13], reporting specific energy and slag mass against metallisation, hot metal chemistry, carbon consumption, and the effects of Al~2~O~3~/SiO~2~ ratio and scrap blending; it is the source of the silicon against temperature and scrap data used here. Two points bear on Section 5. Its authors state that adequate industrial or pilot data for validation do not exist in the open literature and benchmark their model against the HSC model of [12], so agreement between the present work and [13] is agreement between thermochemical computations, not with measurement. They also report sensitivities differing markedly from Table 1: 12.15 kWh/tHM per 0.5 wt % carbon against 10 per 1.0 wt %, a factor of 2.4, and 51 kWh/tHM per 5 % metallisation against 12 per 1 %. Section 6.3 treats that disagreement as a result rather than averaging it away.]{.mark}

[Matino et al. report a flowsheet model of the ESF built for slag investigations, addressing downstream slag use rather than the furnace interior [14].]{.mark}

Being equilibrium formulations, these studies cannot represent rate-limited behaviour, which Section 2.4 shows is not a second-order effect here.

### 2.4 Experimental evidence on reaction behaviour

Bae and Park provide the only systematic experimental study of FeO reduction under ESF conditions [6]. With solid carbon as sole reductant, reduction passed through incubation, steady-state and degradation stages in a sigmoidal curve consistent with earlier work [15,16,17,18]. The incubation of about five minutes is attributed to confinement of the reaction to the carbon surface and to gas nucleation. Despite carbon at a 1:1 molar ratio to FeO, the final FeO fell only to about 32 wt % after 60 minutes, control having passed to FeO diffusion in the slag. A hot heel with 2 wt % dissolved carbon removed the incubation, gave a more nearly linear fall to about 3 wt % FeO and hot metal at 2.8 wt % C, and the carbon requirement for complete reduction with 3 wt % C in the metal was 66 kg-C/t-HM.

Three further observations bear on transient modelling: solid carbon, being less dense than slag, can float and form a barrier isolating it from the metal, so the charging method affects both reduction and carburisation; MgO dissolution from the refractory increases as basicity falls; and free MgO hydrates with a volume expansion that compromises slag reuse in cement.

The governing reactions and their standard Gibbs energies, as given in [6] after Turkdogan [19], are

$$\mathrm{FeO(l)} + \mathrm{C(s)} = \mathrm{Fe(l)} + \mathrm{CO(g)}, \qquad \Delta G^{\circ} = 141\,740 - 140\,T \ \mathrm{J\,mol^{-1}}$$

$$\mathrm{FeO(l)} + \mathrm{CO(g)} = \mathrm{Fe(l)} + \mathrm{CO_2(g)}, \qquad \Delta G^{\circ} = -24\,910 + 31.6\,T \ \mathrm{J\,mol^{-1}}$$

$$\mathrm{C(s)} + \mathrm{CO_2(g)} = 2\,\mathrm{CO(g)}, \qquad \Delta G^{\circ} = 166\,650 - 171\,T \ \mathrm{J\,mol^{-1}}$$

### 2.5 Electrical behaviour and computational fluid dynamics

Measurements and CFD establish that a 100 to 120 V interfacial drop accompanies an applied 180 to 230 V [5,20], that Joule heating rises with electrode immersion and with slag conductivity over 10 to 60 S/m [5,21,22], that 97.96 % of the heat is dissipated in the slag [5,23], [these last from sulphide smelting units,]{.mark} and [that electrode resistance falls from its arc-above-slag value through the brush-arc regime to full immersion [24], the dependence the resistance model of Section 3.7 reproduces]{.mark}. [Transient CFD treatments [25,26]]{.mark} resolve the arc and flow field but are too demanding for campaign-length simulation, whereas zone-based EAF models [27,28,29] reach campaign length for a different configuration; the present work adapts the zone-based architecture to the OSBF.

### 2.6 Gaps addressed in this work

**Table 2.** Gaps identified in the literature and their treatment in this work.

| Gap | Evidence | Addressed in |
|---|---|---|
| No transient, physically resolved OSBF model in the open literature | Stated explicitly in [5] | Sections 3 and 4 |
| Freeze-lining requirement stated qualitatively only | Zone descriptions in [5] | Section 3.6 |
| Equilibrium prediction departs systematically from measured product chemistry | C/S of 0.5 measured against 1.2 predicted [6] | Section 3.5 |
| Published equilibrium datasets mutually inconsistent | Codes differ by 14.6 to 16.0 % [5]; silicon data inconsistent with an endothermic reduction | Section 6.4 |
| Model behaviour outside benchmarked conditions not established | General to the field | Section 5.5 |

---

## 3. Model formulation

### 3.1 Modelling approach and assumptions

The model is formulated from conservation laws and measured thermophysical properties rather than from plant correlations, so that it can be applied to ore grades for which no operating history exists. This is a requirement of the application: the hydrogen direct reduction route is intended to process ores that have not previously been smelted, and a data-driven formulation cannot extrapolate to them. The cost of this choice is a small number of constants that must be calibrated, all of which are listed in Section 5.3.

The steady-state and transient formulations share a single library of thermochemical and physical property data, so that the two cannot diverge and a correction made to either propagates to both.

Table 3 states the assumptions on which the formulation rests.

**Table 3.** Principal modelling assumptions.

| No. | Assumption | Justification |
|---|---|---|
| A1 | Each control volume is well mixed and spatially uniform | Bath circulation driven by gas evolution and buoyancy is vigorous; spatial resolution requires CFD and is outside the present scope |
| A2 | The refractory lining is quasi-steady | Lining thermal response time is long relative to the time step but short relative to a campaign |
| A3 | The freeboard has negligible thermal mass | Gas residence time is of the order of seconds |
| A4 | Melting occurs at the pile and slag interface | Consistent with continuous surface feeding; a lumped-pile treatment produces a non-physical stall |
| A5 | Slag behaves as a single homogeneous liquid phase above its liquidus | Solid phases are treated through the liquidus temperature and freeze layer rather than explicitly |
| A6 | Phosphorus is fully reduced to the metal | No oxidising slag is present under ESF conditions [6] |
| A7 | Gas phase composition is set by a prescribed post-combustion ratio | Detailed freeboard chemistry is outside the present scope |
| A8 | Electrode current distribution is uniform between electrodes | Resolving it requires the electromagnetic models reviewed in [5,21,22,23] |

### 3.2 System definition

The steady-state formulation uses a basis of 1000 kg of contained iron, so results scale to unit hot metal production independently of furnace size. The transient formulation resolves five control volumes, the feed pile floating on the bath, the slag, the metal, the freeboard gas and the lining, and eleven elements (Fe, C, Si, Mn, P, S, Ti, Ca, Mg, Al, O) are tracked across charge, hot metal, slag, off-gas and dust. Figure 1 shows the furnace as the model represents it, and Table 4 gives the geometry and base-case conditions, which correspond to the commercial furnace of [5,7].

![**Figure 1.** Representation of the electric smelting furnace in the model. Bath levels, electrode immersion, brush arc gap, freeze-lining thickness, temperatures and compositions are taken from the current solution. The zone structure follows the configuration described in [5].](figures/Fig1_furnace_schematic.png)

**Table 4.** Furnace geometry and base-case operating conditions. [Every entry is an input; quantities the model computes are in Table 5.]{.mark}

| Parameter | Value | Parameter | Value |
|---|---|---|---|
| Hearth length | 35.0 m | Tapping temperature | 1500 degC |
| Hearth width | 11.0 m | Target hot metal carbon | 3.5 wt % |
| Hearth area | 385 m2 | [Target slag basicity B2]{.mark} | 1.10 |
| Number of electrodes | 6 | [Target slag MgO]{.mark} | 8.0 wt % |
| Electrode diameter | 1.70 m | Slag superheat | 60 K |
| Electrode pitch | 4.60 m | [Off-gas temperature at the uptake]{.mark} | 1450 degC |
| Electrode immersion | 0.45 m | Carburiser | metallurgical coke |
| Brush arc gap | 0.09 m | Carburiser yield | 92 % |
| Slag depth | 1.35 m | Primary flux | burnt lime |
| Metal depth | 0.90 m | Secondary flux | dolomitic lime |
| Freeboard height | 3.20 m | Electrical to bath efficiency | 0.90 |
| [Transformer secondary voltage, reference tap]{.mark} | 420 V | DRI feed rate, transient case | 160 t/h |
| Power factor | 0.86 | Rated power, transient case | [116 MW]{.mark} |

[**Table 5.** Quantities computed by the model at the base case, which appear in Figure 1 and in Section 6 and are not inputs.]{.mark}

| [Quantity]{.mark} | [Steady state, 110 MW]{.mark} | [Transient campaign, end of run]{.mark} |
|---|---:|---:|
| [Slag basicity B2 attained]{.mark} | [1.092]{.mark} | [1.063]{.mark} |
| [Slag MgO attained]{.mark} | [8.25 wt %]{.mark} | [7.70 wt %]{.mark} |
| [Freeboard gas temperature]{.mark} | [not resolved, taken as the 1450 degC input]{.mark} | [1471 degC]{.mark} |
| [Operating tap voltage selected]{.mark} | [496 V]{.mark} | [479 V]{.mark} |
| [Tap ratio to the 420 V reference tap]{.mark} | [1.18]{.mark} | [1.14]{.mark} |
| [Active power]{.mark} | [110.0 MW]{.mark} | [114.7 MW]{.mark} |
| [Operating resistance per phase]{.mark} | [4.59 mohm]{.mark} | [4.03 mohm]{.mark} |
| [Hearth power density]{.mark} | [286 kW/m2]{.mark} | [298 kW/m2]{.mark} |

[The basicity of 1.10 in Table 4 is a target; the solver attains 1.092 at steady state and 1.063 at the end of the campaign, because flux demand is computed against a slag mass that itself depends on the flux added. The 1450 degC in Table 4 is the uptake temperature and is an input to the steady-state balance; the 1471 degC is the freeboard temperature computed by the transient solver from the energy balance of Section 4.3.1. The two agree to 21 K, which is a check on the balance rather than a fitted result. The voltages are explained in Section 3.7.1.]{.mark}

Table 6 gives the DRI analyses. Grades A to C and HG are representative commercial analyses, and the two BP grades [are the simulated hydrogen DRI that Bae and Park smelted, at 85 and 88 % metallisation,]{.mark} reproduced exactly from [6]. Two grades are not taken unaltered. The Shahabuddin grade reproduces the feed of the stream balance [5,12], whose stated analysis sums to 99.80 wt %; the remaining 0.20 wt % is assigned to CaO, MgO, TiO~2~ and P~2~O~5~ so the analysis closes, and removing them changes the specific energy of Table S4 by 0.26 % and the slag mass by 0.19 %. The OSBF grade is back-calculated from the published industrial slag [5,9], with the consequences set out in Section 6.5. Titanium is carried because titaniferous DRI contains it, but no reference source reports it, so the TiO~2~ entries are representative and the titanium treatment is unvalidated.

**Table 6.** Analyses of the DRI grades used, in wt %.

| Grade | Fe | FeO | SiO~2~ | Al~2~O~3~ | CaO | MgO | MnO | TiO~2~ | P~2~O~5~ | S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DRI-A | 86.22 | | 8.82 | 3.10 | 0.55 | 0.35 | 0.75 | 0.10 | 0.09 | 0.02 |
| DRI-B | 84.50 | | 9.77 | 3.42 | 0.55 | 0.40 | 1.05 | 0.20 | 0.09 | 0.02 |
| DRI-C | 84.05 | | 9.73 | 4.20 | 0.55 | 0.40 | 0.90 | 0.06 | 0.09 | 0.02 |
| DRI-HG | 92.85 | | 4.35 | 1.60 | 0.40 | 0.25 | 0.45 | 0.05 | 0.03 | 0.02 |
| DRI-Shahabuddin [5,12] | 84.05 | | 9.76 | 4.88 | 0.10 | 0.05 | 1.07 (as Mn) | 0.03 | 0.02 | 0.04 |
| H2-DRI-BP85 [6] | 76.80 | 17.40 | 3.50 | 2.10 | 0.14 | 0.10 | | | | |
| H2-DRI-BP88 [6] | 78.50 | 14.00 | 3.90 | 1.40 | 1.60 | 0.50 | | | 0.18 | 0.02 |
| DRI-OSBF | 87.85 | | 8.72 | 2.19 | 0.40 | 0.30 | 0.21 | 0.05 | 0.05 | 0.08 |

### 3.3 Thermochemistry and energy

Species enthalpies are integrated from Shomate-form heat capacities referenced to the standard enthalpy of formation [30,31]:

$$H_i(T) = \Delta H^{\circ}_{f,i}(298) + \int_{298}^{T} c_{p,i}\,\mathrm{d}T + \sum \Delta H_{\text{trans}} \tag{1}$$

Solutes liquid only by virtue of dissolution require the undercooled liquid branch of Eq. (1). Iron in hot metal at 1500 degC with 3.5 wt % C lies 38 K below the melting point of pure iron, so the enthalpy is evaluated along the solid path to melting, through the latent heat, and back down the liquid heat capacity. Neglecting this under-predicts hot metal enthalpy by about 20 %.

Slag is not a mechanical mixture of pure oxides, and pure-oxide heats of fusion over-predict its heat content roughly threefold. Slag enthalpy is a sensible term to the liquidus, a latent term using effective heats of fusion in the silicate solution, and a superheat term:

$$h_{\text{slag}}(T) = \sum_i w_i\,[H_i(T_{\text{liq}}) - H_i(298)] + \sum_i w_i L_i^{\text{eff}} + c_p^{\ell}\,(T - T_{\text{liq}}) \tag{2}$$

A regular-solution mixing term is added to Eq. (2); the effective heats of fusion are well below pure-oxide values because the silicate network forms exothermically.

The process heat is the net enthalpy change between charge and tap together with the reaction enthalpies:

$$Q_{\text{process}} = \sum_{\text{out}} m_j h_j(T_j) - \sum_{\text{in}} m_j h_j(T_j) + \sum_k n_k \Delta H_k^{\text{rxn}} \tag{3}$$

Carbonate fluxes are charged as the carbonate rather than as the calcined oxide, so that the evolved CO~2~ and free moisture appear on the input side as well as in the off-gas:

$$H_{\text{in}} \mathrel{+}= n_{\mathrm{CO_2}} \Delta H^{\circ}_{f,\mathrm{CO_2}} - \Delta H_{\text{calc}} + m_{\mathrm{H_2O}}\!\left[h_{\mathrm{H_2O}}(T) - L_v\right] \tag{4}$$

The calcination endotherm then follows from the balance. Omitting Eq. (4) confers a spurious energy credit on carbonate fluxes.

Melting occurs at the interface between the feed pile and the slag:

$$\Delta h = c_p\,(T_{\text{soft}} - T_{\text{pile}}) + L, \qquad \dot{m}_{\text{melt}} = \frac{\dot{Q}_{\text{pile}}}{\Delta h} \tag{5}$$

The bulk pile temperature follows from an enthalpy balance over the incoming charge and the melt leaving, so a cold or rapid feed depresses it and retards melting.

#### [3.3.1 What each stream enthalpy contains]{.mark}

[Every contribution enters exactly once, through the absolute enthalpy of the stream that carries it. Because each species carries its standard enthalpy of formation in Eq. (1), the difference between the output and input sums already contains the enthalpy of every reaction that converted one species into another. The third term of Eq. (3) is therefore zero for all reactions whose reactants and products both appear as speciated streams, and is retained only for carbonate calcination, which Eq. (4) handles explicitly because the CO~2~ leaves the system; adding the reaction enthalpies again would count them twice. Two contributions sit outside the absolute enthalpies and are added once each: the slag mixing enthalpy, which arises from the silicate network and so belongs to no single oxide, and the dissolution enthalpy of C, Si, Mn, P and S in liquid iron, which the pure-element enthalpies do not contain. Table 7 states, stream by stream, what is inside each enthalpy and where the rest is added.]{.mark}

[**Table 7.** Contributions contained in each stream enthalpy. "In" means the contribution is inside the absolute enthalpy of that stream; "separate" means it is added once as its own term; "not applicable" means the stream has no such contribution.]{.mark}

| [Stream]{.mark} | [Formation]{.mark} | [Heating to T]{.mark} | [Melting]{.mark} | [Mixing]{.mark} | [Dissolution]{.mark} | [Where it enters]{.mark} |
|---|---|---|---|---|---|---|
| [DRI, metallic Fe and FeO]{.mark} | [in]{.mark} | [in, from 298 K to the charging temperature]{.mark} | [not applicable, charged solid]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [input sum of Eq. (3)]{.mark} |
| [Scrap]{.mark} | [in]{.mark} | [in]{.mark} | [not applicable, charged solid]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [input sum of Eq. (3)]{.mark} |
| [Carburiser]{.mark} | [in]{.mark} | [in]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [separate, as hot metal dissolution]{.mark} | [input sum of Eq. (3)]{.mark} |
| [Flux, oxide form]{.mark} | [in]{.mark} | [in]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [input sum of Eq. (3)]{.mark} |
| [Flux, carbonate form]{.mark} | [in]{.mark} | [in]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [input sum, with CO~2~ and moisture by Eq. (4)]{.mark} |
| [Hot metal]{.mark} | [in]{.mark} | [in, solid path, latent heat, liquid path]{.mark} | [in, through the undercooled liquid branch]{.mark} | [not applicable]{.mark} | [separate]{.mark} | [output sum, plus the dissolution term]{.mark} |
| [Slag]{.mark} | [in]{.mark} | [in, to the liquidus]{.mark} | [in, effective heats of fusion in solution, Eq. (2)]{.mark} | [separate, regular-solution term]{.mark} | [not applicable]{.mark} | [output sum, plus the mixing term]{.mark} |
| [Off-gas]{.mark} | [in]{.mark} | [in, to the off-gas temperature]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [output sum of Eq. (3)]{.mark} |
| [Dust]{.mark} | [in]{.mark} | [in]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [not applicable]{.mark} | [output sum of Eq. (3)]{.mark} |

[Table S1 of the supplementary material gives the term-by-term balance for a representative case, 94 % metallisation of DRI-B at 1500 degC, 3.4 wt % C and basicity 1.10, and confirms that the slag heat content of 1.97 MJ/kg sits in the 1.85 to 1.95 MJ/kg range reported for comparable slags at 1550 degC.]{.mark}

### 3.4 Slag and metal equilibria

Silica activity, referenced to pure liquid silica, is represented by

$$\log \gamma_{\mathrm{SiO_2}} = -2.05\,(B_3 - 1) - 0.42\,\frac{(\mathrm{Al_2O_3})}{(\mathrm{SiO_2})} - 0.35, \qquad a_{\mathrm{SiO_2}} = \gamma\, x_{\mathrm{SiO_2}} \tag{6}$$

with $B_3 = (\mathrm{CaO}+\mathrm{MgO})/\mathrm{SiO_2}$ and a temperature correction $\exp[-3100(1/T - 1/1773)]$.

[Equation (6) is an activity coefficient multiplying the mole fraction to the first power, as for FeO, MnO and TiO~2~. The coefficient is an empirical fit in basicity, alumina ratio and temperature rather than a solution-model result, and its values should not be compared with tabulated Raoultian coefficients; Section 5.3 lists it among the fitted quantities. With the reduction Gibbs energy fitted to the two silicon values printed in [13], it reproduces them to 1.2 % at 1400 degC and 0.9 % at 1525 degC (Table 12).]{.mark}

Solute activities in the metal use Wagner first-order interaction parameters [32]:

$$\log f_i = \sum_j e_i^{j}\,[\%j], \qquad h_i = f_i\,[\%i] \tag{7}$$

corrected to temperature by the factor $1873/T$. Silicon reduction is then

$$(\mathrm{SiO_2}) + 2[\mathrm{C}] = [\mathrm{Si}] + 2\{\mathrm{CO}\}, \qquad K = \frac{h_{\mathrm{Si}}\,p_{\mathrm{CO}}^{2}}{a_{\mathrm{SiO_2}}\,h_{\mathrm{C}}^{2}} \tag{8}$$

with $\Delta G^{\circ} = [596\,200]{.mark} - 329.5\,T$ J mol^-1^. [The A term of this expression is the one fitted quantity in the thermochemistry; Section 5.3 states what it was fitted to.]{.mark} Manganese, phosphorus [and titanium]{.mark} follow the analogous form.

$$(\mathrm{M_xO_y}) + y[\mathrm{C}] = x[\mathrm{M}] + y\{\mathrm{CO}\} \tag{9}$$

Sulphur partition uses the optical-basicity sulphide capacity correlation of Fincham and Richardson [33,34], converted through the oxygen activity fixed by the C-CO equilibrium. [In the standard logarithmic form the code evaluates,]{.mark}

$$\log L_S = \log\frac{(\%\mathrm{S})}{[\%\mathrm{S}]} = \log C_S + \log f_{\mathrm{S}} - \log a_{\mathrm{O}} + \frac{935}{T} + 1.375 \tag{10}$$

[The partition is capped at 20 (Table 9), the correlation being unreliable at the very low oxygen activities of carbon saturation.]{.mark}

### 3.5 [Empirical limits on the approach to equilibrium]{.mark}

[The three relations below contain no rate constant, residence time, mass-transfer coefficient or interfacial area. They are empirical bounds on the approach to equilibrium, fitted to published data and used by the steady-state solver only; the mass-transfer kinetics is in Section 3.8.]{.mark}

Three product variables are set in practice by how far the slag and metal reactions proceed within the available residence time rather than by equilibrium. The experimental basis is the observation of Bae and Park that SiO~2~ reduction did not reach equilibrium, their slag reaching C/S of 0.5 against 1.2 predicted [6]; the industrial basis is the open bath furnace composition of [5,9].

For silicon a saturating ceiling is imposed:

$$[\%\mathrm{Si}] = S_c\left(1 - \exp\!\left(-\frac{[\%\mathrm{Si}]_{\text{eq}}}{S_c}\right)\right) \tag{11}$$

Equation (11) leaves low-temperature values essentially unaltered and approaches the ceiling $S_c$ at high driving force; the default $S_c$ is 0.45 wt %, the industrial figure [5,9].

Equilibrium FeO in the slag is negligible at ESF carbon levels, whereas industrial slag contains 0.6 to 0.7 wt % [5,9]; a practical floor of 0.65 wt % is therefore applied. Equilibrium would transfer essentially all manganese to the metal, whereas industrial slag retains 0.15 to 0.30 wt % MnO [5,9]; manganese transfer is therefore bounded between 0.55 and 0.80 of that charged. [On the equilibrium basis the manganese bound is relaxed but not removed: a lower bound of 0.90 of the charged manganese remains, which is stated here because it affects the manganese comparisons in Section 6.]{.mark}

#### [3.5.1 Setting the three constants for an unfamiliar ore]{.mark}

[The three constants are fitted to one industrial furnace and cannot be transferred unchanged to another ore. Each, however, has a meaning measurable directly on a plant without any model: $S_c$ is the highest hot metal silicon the furnace produces at its normal tapping temperature, read from tapping records; the FeO floor is the residual slag FeO at tap, from routine slag analyses; and the manganese bounds are the fraction of charged manganese reporting to the metal, from a manganese balance over a tapping cycle. A plant with a few weeks of records has all three.]{.mark}

[Where no records exist, the constants should not be guessed. The model is instead run on both bases and the answer treated as a range: the equilibrium basis gives the thermodynamic ceiling on silicon and floor on slag FeO, the constrained basis what a furnace resembling the reference plant would produce. Section 6.4 shows these bound the behaviour by about a factor of five in silicon at 1600 degC, which is wide but honest, and narrower than assuming either limit without evidence.]{.mark}

All three limits are inputs, are reported beside their equilibrium values, and may be disabled to recover the thermodynamic result.

### 3.6 Refractory lining and freeze lining

Each of the five zones is solved as a one-dimensional multilayer wall. The heat flux through $n$ layers in series with an inner and an outer film is

$$\dot{q} = \frac{T_{\text{bath}} - T_{\text{sink}}}{\dfrac{1}{h_{\text{in}}} + \sum_{j=1}^{n} \dfrac{x_j}{k_j(\bar{T}_j)} + \dfrac{1}{h_{\text{out}}}} \tag{12}$$

Layer conductivities are evaluated at the mean temperature of each layer, so the node temperatures are obtained iteratively. The exposed slag surface radiates to the cooled panels above:

$$\dot{Q}_{\text{open}} = \varepsilon\,\sigma_{\text{SB}}\,A_{\text{bath}} \left(T_{\text{slag}}^{4} - T_{\text{hot face}}^{4}\right) \tag{13}$$

In the slag belt the bath delivers $h(T_{\text{bath}} - T_{\text{liq}})$ to the solidification front, and at steady state the same flux passes through the frozen layer and the lining behind it:

$$h\,(T_{\text{bath}} - T_{\text{liq}}) = \frac{T_{\text{liq}} - T_{\text{sink}}}{x/k_f + R_{\text{lining}}} \tag{14}$$

Solving Eq. (14) for the layer thickness gives

$$x = k_f\left[\frac{T_{\text{liq}} - T_{\text{sink}}}{h\,(T_{\text{bath}} - T_{\text{liq}})} - R_{\text{lining}}\right] \tag{15}$$

Equation (15) admits a positive solution only when

$$R_{\text{lining}} < \frac{T_{\text{liq}} - T_{\text{sink}}}{h\,(T_{\text{bath}} - T_{\text{liq}})} \tag{16}$$

Inequality (16) is a design criterion. A slag belt violating it cannot sustain a protective skull at any cooling intensity, and its refractory hot face necessarily operates above the slag liquidus, giving chemical wear in place of a frozen protective layer.

### 3.7 Electrical model

Current leaves an immersed electrode through two surfaces, the cylindrical side wall over the immersed length and the tip, and the two paths act in parallel.

For the side wall, current spreads radially outward from the electrode surface at radius $r$ to an effective boundary at radius $L_{\text{eff}}$, over the immersed length $h_{\text{imm}}$. Applying Ohm's law to a cylindrical shell of thickness $\mathrm{d}\rho$ and integrating,

$$R_{\text{cyl}} = \int_{r}^{L_{\text{eff}}} \frac{\mathrm{d}\rho}{\sigma\,2\pi\rho\,h_{\text{imm}}} = \frac{\ln(L_{\text{eff}}/r)}{2\pi\sigma\,h_{\text{imm}}} \tag{17}$$

$L_{\text{eff}}$ is taken as the lesser of half the electrode pitch, which sets the electrode-to-electrode path, and the distance from the electrode tip to the metal bath.

For the tip, the current constriction into the surrounding melt is the classical spreading resistance of a circular contact on a semi-infinite conductor, derived by Holm [35] and standard in contact and earthing theory:

$$R_{\text{tip}} = \frac{1}{4\sigma r} \tag{18}$$

The two paths combine in parallel, in series with the ohmic resistance of the electrode itself:

$$R_{\text{slag}} = \left(R_{\text{cyl}}^{-1} + R_{\text{tip}}^{-1}\right)^{-1} \tag{19}$$

The brush arc is represented by the standard linear arc characteristic, in which a fixed electrode fall is added to a column gradient proportional to arc length [36,37]:

$$U_{\text{arc}} = U_{\text{fall}} + E_{\text{col}}\,\ell_{\text{arc}} \tag{20}$$

with $U_{\text{fall}} = 40$ V for the combined cathode and anode falls and $E_{\text{col}} = 1250$ V m^-1^, within the 1000 to 1400 V m^-1^ range reported for arc columns at atmospheric pressure [36]. Equation (20) gives 100 to 120 V for arc gaps between 48 and 64 mm, which is the interface drop measured by Sheng et al. in an industrial furnace [20]. The base case uses a 90 mm gap and so a 152 V arc drop against a 496 V tap, so [20] constrains the form and coefficients of Eq. (20) rather than offering a direct comparison.

Slag electrical conductivity follows

$$\sigma = \sigma_0 \exp\!\left(-\frac{E_a}{RT}\right), \quad E_a = \left[110 - 55(\Lambda - 0.55) - 0.9\,((\mathrm{FeO}) + (\mathrm{MnO}))\right] \ \mathrm{kJ\,mol^{-1}} \tag{21}$$

calibrated to 20 to 45 S/m at 1550 degC, within the 10 to 60 S/m range employed in the CFD literature [21].

#### [3.7.1 The electrical operating point in smelter terms]{.mark}

[Smelter practice describes a furnace by its operating resistance, the total resistance seen by one phase (the slag path of Eq. (19) in series with electrode and secondary circuit), and its hearth power density, active power over bath area; both are reported. For the representative case of Table S1 the model gives an operating resistance of 4.30 mohm and a hearth power density of 316 kW/m2, both within the range reported for open slag bath furnaces of this size.]{.mark}

[Three voltages appear in this paper and they are consistent. The transformer has a nominal secondary voltage of 420 V on its reference tap. The solver selects the tap needed to deliver the power setpoint, searching to three times nominal, and reports the voltage of the tap selected, which exceeds the nominal whenever the furnace is pushed above the reference tap's duty: 496 V at the 110 MW point of Table 4, a ratio of 1.18, and 422 V at the 97.8 MW stream-balance case, a ratio of 1.01. Nominal and selected voltage are reported together throughout.]{.mark}

### 3.8 Reaction kinetics

Reaction rates in the transient formulation are expressed in mass-transfer form:

$$r = k\,A\,C\,\Delta, \qquad k = k_0\exp\!\left(-\frac{E_a}{RT}\right) \tag{22}$$

[The interfacial area $A$ is the plan area of the bath for slag-metal reactions, a flat interface that ignores enlargement by stirring or gas, and for reactions on solid carbon the geometric char surface $A_{\text{char}} = 6 m_{\text{char}} / (\rho_{\text{char}} d_{\text{p}})$ scaled by the contact efficiency $\eta_C$ below. The driving force $\Delta$ is the departure of the bulk composition from interfacial equilibrium: $1 - a_{\mathrm{FeO}}^{\text{eq}}/a_{\mathrm{FeO}}$ for FeO, the difference between interfacial equilibrium and bulk metal content for Si and Mn, and between saturation and bulk content for carbon. Interfacial equilibria come from the thermochemistry of Section 3.4, so the two solvers cannot drift apart thermodynamically. $C$ is the bulk density of the transporting phase.]{.mark}

[The activation energies are of the magnitude reported for these reactions in slag systems and ordered as expected, carbon dissolution the most facile and silica reduction the most difficult, but the values in Table 8 are not measured on this system. They were chosen so that the transient solver reproduces the timescales of [6], the approach of slag FeO to a few weight per cent over tens of minutes and the removal of the incubation period by a carbon-bearing hot heel. They are the least certain quantities in the model and should be re-fitted to plant data before the transient solver is used predictively; the last column of Table 8 states which quantities follow from a physical law, a published correlation, or estimation.]{.mark}

**Table 8.** Reactions resolved in the transient formulation.

| Reaction | Driving force | Interfacial area | $k_0$ (m s^-1^) | $E_a$ (kJ mol^-1^) | [Provenance of $k_0$ and $E_a$]{.mark} |
|---|---|---|---:|---:|---|
| (FeO) + [C] = Fe + CO | $C_{\mathrm{FeO}}(1 - a_{\mathrm{FeO}}^{\text{eq}}/a_{\mathrm{FeO}})$ | bath plan area | 3.0 | 155 | [estimated; fitted to the FeO trajectory of [6]]{.mark} |
| (FeO) + C(char) | as above | char surface, $\eta_C$-corrected | 0.90 | 160 | [estimated; fitted to the incubation behaviour of [6]]{.mark} |
| (SiO~2~) + 2[C] | $[\%\mathrm{Si}]^{*} - [\%\mathrm{Si}]$ | bath plan area | 20.0 | 190 | [estimated; constrained by the slow SiO~2~ reduction reported in [6]]{.mark} |
| (MnO) + [C] | $[\%\mathrm{Mn}]^{*} - [\%\mathrm{Mn}]$ | bath plan area | 5.5 | 180 | [estimated; no measurement available]{.mark} |
| C(s) = [C] | $[\%\mathrm{C}]_{\text{sat}} - [\%\mathrm{C}]$ | char surface, $\eta_C$-corrected | 0.02 | 110 | [estimated; fitted to the hot metal carbon of [6]]{.mark} |

[The interfacial equilibrium contents marked with an asterisk, the activities, the saturation carbon and the densities are all computed from the thermochemistry and property correlations of Sections 3.3, 3.4 and 3.6, which are used as published: slag viscosity after Urbain [38], slag thermophysical properties after Pang et al. [39], the carburisation rate of iron by solid carbon after Ono et al. [40], and the physicochemical treatment of ironmaking reactions after Turkdogan [41]. Magnesia dissolution from the lining, which Bae and Park observed to increase as basicity falls [6], follows the interfacial treatment of Heo and Park [42]. Only the five pairs of constants above, together with $\eta_C$ and $\tau_{\text{inc}}$, are estimated.]{.mark}

Two modifications follow from the experimental observations of [6]. Since part of the charged char floats on the slag, a contact efficiency $\eta_C$ reduces the effective char area, $A_{\text{char}}^{\text{eff}} = \eta_C A_{\text{char}}$. Since reduction by solid carbon requires prior nucleation of a gas film, the char reduction path is scaled by

$$f_{\text{inc}} = \theta + (1-\theta)\left[1 - \exp\!\left(-\frac{t}{\tau_{\text{inc}}}\right)\right], \qquad \theta = \min\!\left(1, \frac{[\%\mathrm{C}]}{[\%\mathrm{C}]_{\text{ref}}}\right) \tag{23}$$

Dissolved carbon in the hot heel drives $\theta$ towards unity and suppresses the incubation delay, reproducing the contrast between the two experimental conditions of [6]. Carbon consumed by reduction is drawn preferentially from floating char and only subsequently from carbon dissolved in the metal.

### 3.9 Flux demand

Two slag targets, binary basicity and MgO content, are met with two fluxes, and flux added for one target enlarges the slag and so shifts the other.

Let flux $j$ deliver, per kilogram charged and after calcination of any carbonate, masses $c_j$ of CaO, $g_j$ of MgO and $s_j$ of SiO~2~, with $b_j$ the total mass of slag-forming oxide it delivers. Let the slag present before any flux is added contain $S_{\mathrm{CaO}}$, $S_{\mathrm{MgO}}$ and $S_{\mathrm{SiO_2}}$ of those oxides and have total mass $S_0$. Here $S_{\mathrm{SiO_2}}$ is the silica remaining after the reduction of Eq. (8), not the silica charged.

The two targets are then simple statements of composition. Writing $m_1$ and $m_2$ for the unknown flux masses, the basicity target requires

$$S_{\mathrm{CaO}} + m_1 c_1 + m_2 c_2 = B_2\left(S_{\mathrm{SiO_2}} + m_1 s_1 + m_2 s_2\right) \tag{24}$$

and the MgO target, expressed as a mass fraction $x$ of the total slag, requires

$$S_{\mathrm{MgO}} + m_1 g_1 + m_2 g_2 = x\left(S_0 + m_1 b_1 + m_2 b_2\right) \tag{25}$$

The right-hand side of Eq. (25) contains the flux masses because the flux becomes part of the slag whose composition is being set. Collecting the unknowns on the left gives a linear system,

$$\begin{bmatrix} c_1 - B_2 s_1 & c_2 - B_2 s_2 \\[2pt] g_1 - x b_1 & g_2 - x b_2 \end{bmatrix} \begin{bmatrix} m_1 \\[2pt] m_2 \end{bmatrix} = \begin{bmatrix} B_2 S_{\mathrm{SiO_2}} - S_{\mathrm{CaO}} \\[2pt] x S_0 - S_{\mathrm{MgO}} \end{bmatrix} \tag{26}$$

which is solved directly for $m_1$ and $m_2$.

Here $c_j - B_2 s_j$ is the net basicity-raising power of flux $j$ after the silica it brings, and $g_j - x b_j$ its net MgO enrichment after the dilution it causes. If $g_j < x b_j$ for both fluxes the MgO target is unattainable with positive flux masses, and likewise for basicity if both fluxes are acid; the solution is accepted only when $m_1, m_2 \geq 0$, otherwise basicity is met with whichever flux can and the MgO target is reported as unattainable ([Algorithm S1]{.mark}, lines 5 to 7). Solving Eq. (26) directly, rather than iterating on an assumed slag mass, makes this explicit instead of appearing as a failure to converge.

### 3.10 Reported quantities

Closure is evaluated for every element:

$$\varepsilon_e = \frac{\left|\sum_{\text{in}} m_{e} - \sum_{\text{out}} m_{e}\right|}{\sum_{\text{in}} m_{e}} \times 100\,\% \tag{27}$$

#### [3.10.1 What "hot metal produced" means]{.mark}

[Every specific quantity in this paper is divided by the hot metal produced, which is not the mass leaving through the tap-hole. In the steady-state solver the furnace is a closed box on a basis of 1000 kg of contained iron, meaning all iron entering with the charge whether as metallic iron, as FeO, or as scrap; hot metal produced is the liquid metal phase leaving that box, the iron reporting to the metal plus the dissolved C, Si, Mn, P, S and Ti. Nothing accumulates at steady state, so produced and tapped coincide. The two bases differ by about 4 %: 1000 kg of contained iron yields about 1043 kg of hot metal, heavier than the iron it contains because of the solutes and lighter than the charge because the gangue leaves with the slag.]{.mark}

[In the transient solver the furnace is not closed and the two separate. Metal tapped is what is removed through the tap-hole on the tapping schedule; metal produced is that plus the change in liquid metal inventory over the campaign. Specific energy is cumulative electrical energy over metal produced, so that energy spent raising the bath inventory is not charged to the metal that happened to leave. Section 6.8 reports both. Section S10 of the supplementary material sets out how each element transfers between the phases; every transfer is tested by the closure of Eq. (27).]{.mark}

[Two]{.mark} specific energy consumptions are reported and are not interchangeable:

$$\mathrm{SEC}_{\text{rev}} = \frac{Q_{\text{process}}}{m_{\mathrm{HM}}}, \qquad \mathrm{SEC}_{\text{op}} = \frac{Q_{\text{process}} + Q_{\text{loss}}}{m_{\mathrm{HM}}\,\eta_{\text{el}}} \tag{28}$$

[The reversible value is the thermodynamic requirement, excluding furnace losses. The operating value is the electrical energy the transformer must deliver, including the lining and shell losses of Section 3.6 and the electrical-to-bath efficiency. A third, intermediate tier obtained by dividing the reversible requirement by a thermal utilisation factor of 0.887 has been withdrawn: the ratio it represents is not constant across the published cases, so it cannot be read as a physical efficiency, and the model is better without a fitted energy parameter. Published specific energies are compared against both remaining tiers, which bracket them.]{.mark}

The tapped slag is scored for use as a supplementary cementitious material on basicity, FeO content and free MgO, the last against an estimated saturation limit

$$(\mathrm{MgO})_{\text{sat}} \approx 4.0 + \frac{7.5}{B_2} + 0.08\,(\mathrm{Al_2O_3}) \tag{29}$$

Free MgO is penalised because it hydrates to Mg(OH)~2~ with a volume expansion that damages cement products [6].

---

## 4. Numerical solution

### 4.1 Structure of the solution

Figure 2 shows the solution procedure. The steady-state problem is a fixed point: flux demand depends on slag mass, slag mass depends on the extent of silica reduction, silica reduction depends on the silicon content of the metal, the silicon content depends on slag composition, and hot metal mass depends on all of them. The transient solution advances the five control volumes explicitly, calling the same property and equilibrium routines at each step.

![**Figure 2.** Solution procedure. Stage A establishes the physical basis, stage B closes the steady-state mass and energy balance, stage C advances the transient solution using the same property libraries, and stage D applies the verification described in Section 5. Equation numbers refer to Section 3.](figures/Fig2_solution_flowchart.png)

### 4.2 Steady-state solution

The steady-state solution iterates on four coupled state variables: hot metal mass, carbon demand, silicon content and slag mass. [Algorithm S1 of the supplementary material gives the procedure with numbered lines.]{.mark}

The convergence residual is the sum of relative changes in the four state variables between successive iterations:

$$\mathcal{R} = \sum_{i=1}^{4} \frac{\left|\phi_i^{(n)} - \phi_i^{(n-1)}\right|}{\max\!\left(\phi_i^{(n)}, \phi_i^{\min}\right)} \tag{30}$$

with $\phi_i^{\min}$ a floor preventing division by small quantities. The tolerance is $\mathcal{R} < 10^{-6}$.

Two features of [Algorithm S1]{.mark} matter. Line 5 obtains the flux demand in closed form, writing the induced slag growth into the constraint as in Eqs. (24) and (25); formulations targeting a lagged slag mass diverge whenever the flux dilutes MgO faster than it enriches it. Line 13 applies adaptive damping, because at high scrap fractions, where silicon is fixed by the scrap, the fixed point is approached in a limit cycle that a reduced relaxation factor removes.

### 4.3 Transient solution

The transient solution uses explicit Euler integration with a default step of 10 s, well within the stability limit set by the fastest process, which is melting at the pile interface. [Algorithm S2 of the supplementary material gives the procedure.]{.mark}

### [4.3.1 Freeboard gas temperature]{.mark}

[The freeboard gas holds negligible heat beside the baths (assumption A3 of Table 3), so its temperature follows from a steady balance. As a participating medium it absorbs from the slag surface, radiates to the water-cooled roof and upper sidewall, and is carried through at the rate the reactions and ingress air supply it, while post-combustion of CO releases heat within it. Against the hot-face temperatures of the lining network of Section 3.6,]{.mark}

$$\dot m c_p (T_g - T_{in}) = Q_{pc} + \varepsilon_g \sigma A_b (T_s^4 - T_g^4) - \varepsilon_g \sigma A_r (T_g^4 - T_r^4) - \varepsilon_g \sigma A_w (T_g^4 - T_w^4) + h A_b (T_s - T_g) - h A_r (T_g - T_r) - h A_w (T_g - T_w)$$

[in which the subscripts $b$, $r$ and $w$ denote the free bath surface, the roof and the upper sidewall, $\varepsilon_g$ is the grey-gas emissivity of the freeboard atmosphere, from a Hottel-type correlation evaluated at the mean beam length, and $T_{in}$ is the mass-weighted inlet temperature of the CO leaving the bath, the CO2 of calcination and the ingress air. Every term on the right falls as $T_g$ rises and the left side rises with it, so the balance has a single root, which is found by bisection. The gas is therefore bounded below by the coldest surface it sees and above by its inlet temperature plus the adiabatic post-combustion rise.]{.mark}

[The freeboard composition that sets $\varepsilon_g$ is computed from the gas streams rather than prescribed; ingress air is the larger part of the freeboard mass flow, giving about 28 % CO and 6 % CO2 by mole and an emissivity of 0.31 at the base case.]{.mark}

[One term is bounded rather than computed. The slag-side debit of Eq. (13) is taken as the smaller of the grey-body estimate and the duty the surfaces above the bath actually remove, net of arc radiation, since at steady state whatever the panels remove arrived either from the bath or from the arcs; without that bound the grey-body figure over-debits the slag by one to two megawatts. The gas-to-bath exchange is a gain to the gas and is not returned to the slag balance separately, an approximation admissible because the two settle within about 33 K.]{.mark}

### 4.4 Convergence and computational cost

The steady-state solution converges in 25 iterations or fewer for every case examined, and a seven-hour transient campaign at a 10 s step takes a few seconds, so parametric studies of the kind presented in Section 6 are inexpensive. [Convergence is declared against the same tolerance at which the iteration exits, namely a residual of 1e-6 in Eq. (30). All 178 admissibility cases satisfy the stricter test.]{.mark}

[The solution times, the iteration counts case by case, and the step-size independence study have been moved to the supplementary material, where they are set out in full, following a reviewer's suggestion that the numerical detail interrupts the argument. The result of the step-size study is that campaign specific energy varies by 0.006 % and productivity by 0.21 % between 5, 10 and 30 s steps, so the default step introduces no significant discretisation error. Algorithms 1 and 2 have been moved to the supplementary material for the same reason, and the text now refers to them there.]{.mark}

---

## 5. [Validation methodology and what each comparison can show]{.mark}

### 5.1 Reference datasets

[Four features of the available evidence limit what any comparison here can establish. First, there are almost no measurements: Owusu et al. state in their own validation section that adequate industrial or pilot data do not exist in the open literature, which is why they benchmark FactSage against an HSC model [13]. The same constraint applies here, and only the laboratory melts of [6] and the industrial composition of [5,9] rest on measurement. Second, the two published equilibrium codes disagree with one another, by 14.6 to 16.0 % on absolute specific energy [10, Table 3] and by a factor of 2.4 on the sensitivity to hot metal carbon; this paper compares against each separately rather than against an average, which would conceal the disagreement. Third, several sources state a quantity as a range, and those are tested as intervals and never reduced to a midpoint. Fourth, the sources frequently do not state the conditions behind a number, so Table S3 of the supplementary material records for each dataset the reference conditions beside the model inputs used to match them, and names what the source does not report and what was assumed in its place.]{.mark}

### 5.2 Basis of comparison

Each comparison is evaluated on the basis appropriate to the reference value, since a like-for-like comparison requires the model and the reference to describe the same condition.

Comparisons against the equilibrium codes are evaluated with the empirical limits of Section 3.5 disabled, because those values are reported as equilibrium computations; [all seven energy sensitivities are evaluated on that basis]{.mark}.

Comparisons against industrial [5,9] and laboratory [6] data are evaluated with the limits active, since both describe rate-limited systems.

[None of the sources states whether its specific energy includes furnace heat losses, and the model's two tiers differ by exactly that. Rather than guess the convention, each published specific energy is tested against the interval between the tiers: the test asks whether the published value is consistent with the model once the unknown convention is allowed for. That is a weaker claim than a percentage agreement and the strongest the sources support.]{.mark}

The stream balance of [5,12] requires a judgement: it is computed with an equilibrium code, but its silicon of 0.40 wt % at 1600 degC is lower than the 0.62 wt % reported at 1525 degC by the other code, and Section 6.4 shows the two cannot both describe equilibrium for an endothermic reduction. That silicon is therefore not an equilibrium value and is compared on the constrained basis. The basis used for every comparison is recorded in the supporting data.

### 5.3 [Fitted parameters, and which comparisons they compromise]{.mark}

Table 9 lists every fitted constant together with what it was fitted to. All other quantities, including heat capacities, enthalpies of formation, Gibbs energies, interaction parameters, transport correlations, the lining network and the electrical model, are used as published.

**Table 9.** [Fitted constants, what each was fitted to, and the consequence for the comparisons.]{.mark}

| Constant | Value | Fitted to | [Comparisons it compromises]{.mark} |
|---|---|---|---|
| Effective heats of fusion in slag solution | tabulated | slag heat content 1.85 to 1.95 MJ/kg at 1550 degC | [none directly; affects all energy results through the slag enthalpy]{.mark} |
| Slag mixing enthalpy scale | 0.15 | as above | [as above]{.mark} |
| SiO~2~ reduction, A term of $\Delta G^{\circ}$ | [596 200]{.mark} J mol^-1^ | [Si] at 1400 and 1525 degC [13] | [those two silicon comparisons; they are reported but excluded from the statistics]{.mark} |
| Slag conductivity, $\sigma_0$ and $E_a$ | Eq. (21) | 10 to 60 S/m [21] | [none; no conductivity comparison is made]{.mark} |
| Slag liquidus reference | 1673 K | CaO-SiO~2~-Al~2~O~3~-MgO liquidus surface | [none]{.mark} |
| Sulphide partition limit | 20 | hot metal sulphur in reducing smelting practice | [the industrial sulphur consistency check]{.mark} |
| Silicon ceiling, $S_c$ | 0.45 wt % | industrial hot metal [5,9] | [the industrial silicon check and the stream-balance silicon]{.mark} |
| Residual slag FeO floor | 0.65 wt % | industrial slag [5,9] | [the industrial FeO check]{.mark} |
| Manganese bounds | 0.55 to 0.80 | industrial slag MnO [5,9] | [the industrial MnO check and the stream-balance manganese]{.mark} |
| Carbon contact efficiency, $\eta_C$ | 0.55 | carbon flotation reported in [6] | [the laboratory carbon comparison]{.mark} |
| Kinetic pre-exponentials | Table 8 | timescales reported in [6] | [the two laboratory hot-heel comparisons]{.mark} |

[A twelfth constant, a thermal utilisation factor of 0.887 described as the fraction of heat delivered to the bath that is retained in the products, has been withdrawn. The ratio it represents is not constant: across the published specific energies that can be verified it is 0.883 for the stream balance at 1600 degC, 0.849 at 90 % metallisation and 1600 degC, 0.775 for cold DRI from 7 wt % gangue ore and 0.886 from 16 wt % gangue ore. A quantity ranging from 0.775 to 0.886 identifies nothing physical. What the factor was doing was splitting the difference between a loss-free and a loss-inclusive specific energy on sources that do not state which they report, and that difference is now handled openly by the interval test of Section 5.2. The model therefore contains no fitted energy parameter, and the absolute specific energies in Section 6 are predictions rather than the output of a one-parameter fit.]{.mark}

[Five comparisons remain compromised by fitting and are excluded from the headline statistics: hot metal silicon and manganese in the stream balance, set by the silicon ceiling and manganese bounds; hot metal carbon in that balance, an operating target rather than a prediction; and the silicon values at 1400 and 1525 degC, the anchors the silica reduction Gibbs energy is fitted to. The silicon at 1450 and 1500 degC was not used in that fit and is retained. Section 6.1 reports what the separation costs: the fitted comparisons agree about twice as closely as the independent ones.]{.mark}

### 5.4 Statistical measures

Agreement is quantified by the relative percentage deviation for each comparison $i$,

$$\mathrm{RPD}_i = 100 \times \frac{y_i^{\text{model}} - y_i^{\text{ref}}}{y_i^{\text{ref}}} \tag{31}$$

and by the mean absolute relative deviation over the $N$ comparisons,

$$\mathrm{MARD} = \frac{1}{N}\sum_{i=1}^{N} \left|\mathrm{RPD}_i\right| \tag{32}$$

[Comparisons are of two kinds. A single-valued comparison has a published number and is scored by Eq. (31). An interval test has either a published range, the test being whether the model value falls inside it, or an unstated energy convention, the test being whether the published value falls between the model's two tiers; interval tests cannot be scored by Eq. (31) and are reported as a count satisfied. One physical quantity contributes one benchmark, so where a quantity is reported on both tiers only the interval test is counted. Comparisons are further labelled by role: only independent comparisons enter the statistics, while those compromised by fitting, the industrial consistency check, the two-solver agreement and figures from other furnace classes are reported separately and excluded. Every role is recorded in the supporting data.]{.mark}

### 5.5 Verification of physical admissibility

Agreement with reference data establishes accuracy only where reference data exist, so for the ore grades and operating points the model is intended for, behaviour elsewhere in the input space must be established independently. A second procedure evaluates whether each solution is physically possible, without reference to any published value. The criteria are: elemental closure better than 1 % for every element, Eq. (27); absence of negative or indeterminate masses; phase compositions summing to 100 %; all reported quantities within physically attainable ranges; convergence of Eq. (30); positive net process heat; and, for the transient solution, non-negative inventories and no indeterminate values in any trajectory.

[A balance computed below the liquidus of its own slag closes correctly but describes a condition no furnace can tap. Such cases are detected, flagged in the model output and counted separately from failures. Two of the 178 configurations are of this kind: a hot metal at 1380 degC with 0.5 wt % carbon, below the liquidus of that metal; and a campaign charging DRI at 25 degC rather than 600 degC, which adds some 47 MW of sensible-heat demand that the furnace does not have, so the slag freezes.]{.mark}

The procedure covers 178 configurations: every DRI grade against every carburiser, every flux against every other flux, the operating envelope varied one parameter at a time, both heat-loss formulations, four furnace sizes, eight corner cases and thirteen transient campaigns. Configurations that are not physically operable, such as a flux pair in which neither member can raise slag basicity, are required to be rejected with a diagnostic rather than returned as a solution, and such rejection is recorded as correct behaviour.

## 6. Results and discussion

### 6.1 Overall agreement with reference data

[The comparison set is counted as follows, and the counts in this section, in Table 10 and in the supplementary table now agree with one another. The supplementary table lists 95 rows. Of these, 48 are benchmarks that enter the statistics: 17 single-valued comparisons scored by Eq. (31) and 31 interval tests. The remaining 47 rows are reported but excluded, each for a stated reason: 14 give a value on one energy tier where the interval test is the counted benchmark, 12 are the industrial consistency check of Section 6.5, 10 are the agreement between the two solvers of Section 6.9, 5 are compromised by fitting, 3 are figures from other furnace classes or from an unknown operating point, 2 are published values their own balance cannot support, and 1 is a formally valid result below the slag liquidus. ]{.mark}

[Across the 17 single-valued benchmarks the mean absolute relative deviation is 14.6 % and the median 4.0 %, with 12 within 10 % and 14 within 15 %. Of the 31 interval tests, 22 are satisfied. The mean now sits at the lower bound of the 14.6 to 16.0 % by which the two published equilibrium codes differ from one another on identical cases [10, Table 3], so the model lies at the edge of the present reproducibility of the field rather than comfortably inside it.  The gap between the mean and the median shows that the mean is carried by a few large deviations rather than by general disagreement; Sections 6.2 and 6.3 identify each of them.]{.mark}

Figure 3 shows specific energy against metallisation ratio for the three reference DRI grades, and Figure 7 presents the parity plot across the comparison set. 

**Table 10.** [Summary of agreement. Benchmarks counted in the statistics are listed first; every excluded group is listed below with the reason, so that the full set of 95 rows is accounted for.]{.mark}

| Measure | Value |
|---|---|
| [Single-valued comparisons scored by Eq. (31)]{.mark} | [17 ]{.mark} |
| [Interval tests]{.mark} | [31 ]{.mark} |
| [Benchmarks counted]{.mark} | [48 ]{.mark} |
| Mean absolute relative deviation, MARD | [14.6 %]{.mark} |
| Median absolute relative deviation | [4.0 %]{.mark} |
| Comparisons within 10 % | [12 of 17]{.mark} |
| Comparisons within 15 % | [14 of 17]{.mark} |
| Largest single deviation | [71.6 %, hot metal sulphur, Section 6.2]{.mark} |
| [Interval tests satisfied]{.mark} | [22 of 31]{.mark} |
| [Excluded: single tier reported beside an interval test]{.mark} | [14 ]{.mark} |
| [Excluded: industrial consistency check, Section 6.5]{.mark} | [12 ]{.mark} |
| [Excluded: agreement between the two solvers, Section 6.9]{.mark} | [10 ]{.mark} |
| [Excluded: compromised by fitting, Section 5.3]{.mark} | [5 ]{.mark} |
| [Excluded: other furnace class or unknown operating point]{.mark} | [3 ]{.mark} |
| [Excluded: published value unsupported by its own balance]{.mark} | [2 ]{.mark} |
| [Excluded: valid below the slag liquidus, Section 5.5]{.mark} | [1 ]{.mark} |
| Physically admissible configurations, Section 5.5 | 178 of 178 |

[The five comparisons compromised by fitting are worth a line of their own, because separating them was a reviewer's request and the separation turns out to matter. Taken together they agree to a mean of 6.8 %, against 14.6 % for the independent set. Counting them as validation would improve the headline figure without any improvement in the model.]{.mark}

![**Figure 3.** Specific energy consumption against metallisation ratio for three DRI grades on the equilibrium basis, with published FactSage values at 80 and 100 % metallisation [13]. The source reports only these two metallisation levels, so the reference line connects them directly.](figures/Fig3_SEC_vs_metallisation.png)

![**Figure 7.** Parity plot for specific energy consumption. [Each group of points is drawn with its own symbol, so that the composition of the comparison set can be read from the figure: three DRI grades at two metallisation ratios, and the scrap blending series for DRI-B at 90 % metallisation, annotated with the scrap fraction. The band is plus or minus 10 %.]{.mark}](figures/Fig7_parity_plot.png)

### 6.2 Reproduction of a complete published stream balance

The most stringent single test available is the reproduction of an entire published balance to which the model was not fitted. Table S4 of the supplementary material compares the predicted streams against the HSC-based balance at 1600 degC given in [5,12].

[Eight of the fifteen quantities agree within 6 %, and the published specific energy falls inside the interval between the two model tiers. The larger deviations divide into three groups, and the division matters because two of them are not model errors.]{.mark}

[Two published entries cannot be supported by the balance that prints them. Its feed contains no phosphorus, yet its hot metal contains 0.10 wt % P, about 1.1 kg appearing from nowhere. Its slag contains 0.17 wt % FeO although the feed is stated as fully metallised and no iron is oxidised anywhere in the balance. The present model gives 0.010 wt % P, carried by the 0.02 wt % P~2~O~5~ assigned when closing the feed in Section 3.2, and zero FeO. Both are reported for completeness and excluded from the statistics, since a comparison against an unsupported number tests nothing.]{.mark}

[The sulphur deviation is a genuine disagreement and is the largest in the whole comparison set. The published balance retains 88 % of the charged sulphur in the hot metal. This model partitions sulphur between slag and metal through the sulphide capacity of Eq. (10), and at a basicity of 1.10 and the low oxygen potential fixed by carbon saturation it predicts extensive desulphurisation, leaving 0.011 wt % in the metal. Desulphurisation under those conditions is well established in ironmaking practice, and the industrial open bath furnace of [5,9] reports 0.025 to 0.030 wt % sulphur in the hot metal from a feed of similar sulphur content, which lies between the two predictions and closer to this model than to the published balance. The deviation is therefore reported as a disagreement between the two calculations rather than as an error in this one.]{.mark}

[The off-gas difference follows from the carbon that each calculation oxidises. The published balance oxidises 4.6 kg of carbon, the balance of the 41.5 kg charged being dissolved in the metal; this model oxidises 6.5 kg. The extra 1.9 kg is the carbon consumed by the greater extent of silicon reduction and by the sulphur and phosphorus chemistry that the published balance does not carry. The comparison is made with post-combustion and air ingress switched off, so that both figures describe the same gas.]{.mark}

[Silicon and manganese are set by the fitted constants of Section 5.3 and cannot test the model; they are shown because they belong to the balance, and they are excluded.]{.mark}

### 6.3 Energy sensitivities

[The two published equilibrium studies disagree with each other on these derivatives by more than either disagrees with this model, which changes what the comparison can show. Table 11 therefore reports each sensitivity against both sources rather than against one, and on both energy tiers rather than one.]{.mark}

**Table 11.** [Sensitivity of specific energy consumption, equilibrium basis. The model gives a range because the two energy tiers bracket the unknown loss convention of the sources, as Section 5.2 explains. "Satisfied" means the published value lies inside the model range.]{.mark}

| Sensitivity | [Model, reversible tier]{.mark} | [Model, operating tier]{.mark} | [Owusu et al. [13]]{.mark} | [Shahabuddin et al. [5,12]]{.mark} | [Result]{.mark} |
|---|---:|---:|---:|---:|---|
| $\partial\, SEC/\partial [C]$ per 1.0 wt % | [8.43]{.mark} | [10.40]{.mark} | [24.3]{.mark} | 10.0 | [satisfied against [5,12]; not against [13]]{.mark} |
| $\partial\, SEC/\partial MR$ per 1 wt % | [-8.20]{.mark} | [-10.13]{.mark} | [-10.2]{.mark} | -12.0 | [just outside [13]; outside [5,12]]{.mark} |
| $\partial\, SEC/\partial(\text{scrap})$ per 1 wt % | [-2.83]{.mark} | [-3.49]{.mark} | [-2.7]{.mark} | -2.5 | [outside both, by 0.13 and 0.33]{.mark} |
| $\partial\, SEC/\partial T$ per 25 degC | [12.58]{.mark} | [15.53]{.mark} | [20.0]{.mark} | [not reported]{.mark} | [outside]{.mark} |
| $\partial\, SEC/\partial(\text{gangue})$ per 1 wt % in the DRI | [13.78]{.mark} | [17.02]{.mark} | [not reported]{.mark} | 13 to 20 | [satisfied]{.mark} |
| [$\partial\, SEC/\partial(\text{gangue})$ per 1 wt % in the ore]{.mark} | [18.11]{.mark} | [22.36]{.mark} | [not reported]{.mark} | [13 to 20]{.mark} | [satisfied, overlapping]{.mark} |
| [$\partial C/\partial MR$ per 5 % MR]{.mark} | [-10.28]{.mark} | [-10.28]{.mark} | [-10.7]{.mark} | [not reported]{.mark} | [-4.0 %]{.mark} |
| [$\partial C/\partial [C]$ per 0.5 wt %]{.mark} | [5.55]{.mark} | [5.55]{.mark} | [6 to 7]{.mark} | [not reported]{.mark} | [outside, by 0.45]{.mark} |

[Every sensitivity in Table 11 is evaluated on the equilibrium basis, as Section 5.2 requires; six of the seven were previously computed on the constrained basis in the supplementary table, which is why a carbon sensitivity of 9.42 appeared in the body of the paper against 8.38 in the supplement. The gangue sensitivity is an interval test against the published 13 to 20 rather than against its midpoint, and because the source does not say whether its 1 wt % refers to ore or to DRI, and removing oxygen concentrates the gangue by about a third, both are reported and both overlap. The temperature sensitivity is the quantity on which the model agrees least well with [13]: 12.6 to 15.5 against a published 20 kWh/tHM per 25 degC, low by 22 to 37 %, with no adjustment made to close the gap.]{.mark}

[Where the two sources disagree, the model sits near one and far from the other. On carbon, [13] gives 24.3 kWh/tHM per 1.0 wt % and [5,12] gives 10.0, a factor of 2.4 apart; the model gives 8.4 to 10.4 and matches [5,12]. That disagreement exceeds the 14.6 to 16.0 % inter-code difference in absolute energy used as a yardstick in Section 5.1, which suggests derivatives test a thermochemical database more severely than absolute values: absolute energies here agree with both sources within the bracket test, while their derivatives do not.]{.mark}

On the equilibrium basis the predicted specific energy at the reversible tier is 495.6, 519.3 and 520.5 kWh/tHM for grades DRI-A, DRI-B and DRI-C at full metallisation, rising to 659.7, 682.9 and 684.4 kWh/tHM at 80 % metallisation. Scrap blending at 90 % metallisation gives 601.1, 541.0, 484.5 and 431.5 kWh/tHM at 0, 20, 40 and 60 wt % scrap.

![**Figure 4.** Specific energy consumption and carbon consumption against tapping temperature (left), and hot metal silicon against tapping temperature (right), with published values from [13]. [In the right panel the silicon is drawn on both bases. The equilibrium curve is the like-for-like comparator for the published points, which are equilibrium computations; the constrained curve is what the model predicts for an operating furnace. Filled symbols are values printed in the conclusions of [13], the open symbol is read from its Figure 3a, and the vertical bar is the range that source gives at 1500 degC. ]{.mark}](figures/Fig4_SEC_and_Si_vs_temperature.png)

### 6.4 Silicon transfer and the limits of equilibrium

Two published silicon values cannot both describe equilibrium. FactSage gives 0.62 wt % Si at 1525 degC [13] and HSC gives 0.40 wt % Si at 1600 degC [5,12]. Reduction of silica by carbon is strongly endothermic, so equilibrium silicon must increase monotonically with temperature; a lower value at the higher temperature is therefore inconsistent with equilibrium. Industrial practice supports the lower figure, the open bath furnace specification being below 0.5 wt % [5,9] against 0.75 wt % for the blast furnace it replaces.

The experimental evidence resolves this. Bae and Park measured C/S of about 0.5 where equilibrium predicted 1.2 and concluded that SiO~2~ reduction does not reach equilibrium [6], so the discrepancy is not an error in either computation but a consequence of applying an equilibrium assumption to a rate-limited transfer.

Table 12 presents the model on both bases. [A reviewer asked how the silicon values were obtained and why they differ, so the provenance of every reference value is given in the table rather than left to the citation.]{.mark}

**Table 12.** Hot metal silicon on the equilibrium and constrained bases, wt %. [The last column states where each reference value comes from and whether it was used in fitting.]{.mark}

| Tapping temperature | Equilibrium, Eq. (8) | [Constrained]{.mark}, Eq. (11) | Reference value | [Provenance of the reference]{.mark} |
|---:|---:|---:|---|---|
| 1400 degC | 0.032 | 0.031 | 0.03 [13] | [printed in conclusion 2 of [13]; one of the two values Eq. (8) is fitted to]{.mark} |
| 1450 degC | 0.109 | 0.097 | 0.10 [13] | [read from Figure 3a of [13]; not used in any fit]{.mark} |
| 1500 degC | 0.350 | 0.242 | [0.30 to 0.40 [13]]{.mark} | [a range in the text of [13]; its conclusion 1 gives 0.30 to 0.36 across the three grades; not used in any fit]{.mark} |
| 1525 degC | 0.614 | 0.337 | 0.62 [13] | [printed in conclusion 2 of [13]; one of the two values Eq. (8) is fitted to]{.mark} |
| 1550 degC | 1.040 | 0.409 | below 0.5 [5,9] | [an industrial specification, not a measurement at this temperature]{.mark} |
| 1600 degC | 2.331 | 0.449 | 0.40 [5,12] | [a single value from the HSC stream balance]{.mark} |

[The 1500 degC comparison is an interval test against the range the source gives, not against a midpoint. The range printed here, 0.30 to 0.40, is from the body text of [13]; its conclusion 1 gives the narrower 0.30 to 0.36 across the three grades. The model value of 0.350 satisfies both.]{.mark}

On the equilibrium basis the model reproduces the anchors of [13] between 1400 and 1525 degC, matching both magnitude and slope over a range in which silicon varies twentyfold. [Two of those four points, at 1400 and 1525 degC, are the anchors the A term of the reduction Gibbs energy is fitted to, so they test the form of Eq. (6) and Eq. (8) rather than their accuracy; a single fitted constant cannot reproduce a twentyfold variation unless the functional form is right. The points at 1450 and 1500 degC were not used in the fit; the first agrees to 7.1 % and the second falls inside the published range.]{.mark}

[On the constrained basis]{.mark} the model reproduces the HSC value at 1600 degC to within 12.3 % and remains within the industrial specification at every temperature examined. [That agreement is not evidence, because the ceiling of Eq. (11) was fitted to the industrial figure and sets the value at this temperature almost entirely; it is listed among the comparisons compromised by fitting in Section 5.3.]{.mark} The two bases differ by a factor of five at 1600 degC, where the equilibrium result of 2.33 wt % exceeds any composition reported from an operating ESF.

The consequence is specific to the DRI, ESF and BOF route: hot metal silicon sets lime and oxygen demand in the converter, so a fivefold over-prediction propagates through the flowsheet. Both bases are reported rather than one selected, the equilibrium basis being the comparator for equilibrium-code benchmarking and the constrained basis the predictor of plant behaviour, with the separation showing how far an operating point lies from thermodynamic control. [For a user working with an unfamiliar ore, that separation is also the honest uncertainty band on silicon, as Section 3.5.1 sets out.]{.mark}

### 6.5 Consistency with industrial composition

The published industrial open bath furnace composition [5,9] is a tempting validation target but cannot serve as an independent test. Its feed analysis is not published and had to be back-calculated from the reported slag, so the feed gangue was chosen to reproduce the slag against which the model is then compared; and three model constants, the silicon ceiling of Eq. (11), the residual FeO floor and the manganese bounds, were calibrated against the same table, as Table 9 records.

[The full comparison, with the provenance of every quantity, is given as Table S2 of the supplementary material. Of its twelve entries only one, hot metal iron, is an independent prediction, and it lies 0.08 percentage points above a published range only 0.1 wt % wide. Three are operating targets set in the run, four are calibrated against this table and so circular by construction, and four follow from feed constituents chosen by the author. All twelve are therefore excluded from the validation statistics of Table 10.]{.mark}

What the exercise does show is that a single self-consistent feed, flux schedule and set of constants reproduces an entire industrial product specification to within a few per cent on every quantity at once, which is necessary for the model to be usable though not sufficient for validation. It also locates the residual tensions: slag SiO~2~ and Al~2~O~3~ exceed their ranges by 2.2 % and 1.3 % relative, so no single gangue ratio reproduces both, and the feed was not adjusted further to force agreement. Slag MnO falls 0.009 wt % below its range because the manganese bounds restrict transfer to at most 0.80 of the manganese charged. The equilibrium result is worse on the same test: without those bounds essentially all manganese transfers and slag MnO falls to 0.055 wt %.

### 6.6 Comparison against laboratory smelting

Table 13 compares the model against the laboratory smelting of low-grade hydrogen DRI reported in [6].

**Table 13.** Comparison against laboratory smelting of low-grade H2-DRI [6].

| Quantity | This work | Measured [6] | RPD |
|---|---:|---:|---:|
| Carbon for complete FeO reduction with 3 wt % C | 59.0 kg-C/tHM | 66 kg-C/tHM | -10.6 % |
| Slag FeO with a hot heel | 4.23 wt % | approximately 3.0 wt % | +41 % |
| Hot metal C with a hot heel | 3.23 wt % | 2.8 wt % | +15 % |

The carbon requirement, which follows from the stoichiometry of FeO reduction together with carburisation and the carburiser yield, agrees to 10.6 %. The remaining two comparisons set a 500 g laboratory melt against a model parameterised for a 112 MW furnace, and are reported as indicative. The qualitative effect of the hot heel, namely the elimination of the incubation period and a more rapid approach to low slag FeO, is reproduced by Eq. (23).

### 6.7 Thermal behaviour and the refractory lining

Table 14 gives the computed zone heat losses at base-case conditions, and Figure 5 the through-lining temperature profiles from which they follow. Figure 6 shows the response of the freeze layer to slag temperature.

**Table 14.** Zone heat losses at 1550 degC slag and 1500 degC metal.

| Zone | Area (m2) | Flux (kW m^-2^) | Duty (MW) | Hot face (degC) | Shell (degC) | Freeze layer (mm) |
|---|---:|---:|---:|---:|---:|---:|
| Hearth | 385.0 | 1.8 | 0.70 | 1499 | 178 | none |
| Metal wall | 82.8 | 2.2 | 0.18 | 1499 | 197 | none |
| Slag wall | 124.2 | 36.2 | 4.49 | 1405 | 40 | 53 |
| Roof | 404.2 | 37.7 | 15.23 | 1488 | 40 | none |
| Freeboard | 294.4 | 31.5 | 9.28 | 1493 | 39 | none |
| Total | | | 29.88 | | | |

Of the total, 97 % is rejected to the cooling water. At the design power of 110 MW the lining loss represents 27 % of the input.

[What the published figures in this section establish is limited, and both need qualification. The 35 to 45 % share of input reaching the cooling water comes from a six-in-line furnace for sulphide smelting [11], a different furnace class with a different lining, cooling arrangement, hearth power density and bath; the model gives 27 % at steady state and 24.5 % over the campaign, below that band, but the band was never a specification for this furnace, so the figure is reported for orientation and excluded from the statistics. The statement that 97.96 % of generated heat is dissipated in the slag likewise describes a circular matte smelting furnace [23]; the model's 97 % of lining loss rejected to cooling water is a different quantity and the two should not be read as agreeing. What the section does establish is internal: the slag wall hot face and the freeze thickness follow from the same calculation without being prescribed.]{.mark}

The slag wall hot face is computed at 1405 degC, coincident with the slag liquidus, confirming that the frozen layer rather than the refractory constitutes the working lining in that zone. No freeze layer develops in the metal zone. Both outcomes are consistent with the zone descriptions in [5] and were obtained without prescribing them.

Inequality (16) gives this design significance: it sets a limiting lining resistance above which no frozen layer can be sustained. A slag belt of conventional refractory thickness exceeds that limit, so its hot face must operate above the liquidus whatever the cooling intensity, and the protective mechanism assumed in the design cannot be realised. Since relining is a major capital event, a criterion evaluable at design stage from thickness, conductivity and coolant temperature has practical value.

![**Figure 5.** Through-lining temperature profiles for the five zones (left) and the resulting distribution of heat loss (right), computed from Eq. (12). The slag wall profile begins at the slag liquidus because the frozen layer constitutes the working lining in that zone.](figures/Fig5_lining_profiles_and_zone_losses.png)

![**Figure 6.** Freeze-layer thickness (left axis) and slag-wall hot-face temperature (right axis) against slag temperature, from Eq. (15). The layer thins as the bath is superheated. [Both curves are labelled and carry a legend. The hot face is drawn on an absolute scale and is almost constant at 1410 degC, because while a freeze layer is present its outer surface sits at the solidification temperature of the slag. The variation across the whole range is 0.3 K.]{.mark}](figures/Fig6_freeze_lining_response.png)

### 6.8 Transient behaviour over a tapping campaign

A seven-hour campaign was simulated at 160 t/h DRI feed and [116 MW]{.mark} rated power, with metal tapped hourly and slag half-hourly. [At 112 MW the temperature controller saturates at this feed rate and the hot metal settles about 24 K below setpoint, so 116 MW is the rating at which this duty is operable.]{.mark} Table 15 summarises the result and Figure 8 gives the trajectories.

**Table 15.** Seven-hour transient campaign at base-case conditions. [Every mean is taken over the final half of the campaign, 210 to 420 minutes, which excludes the initial heating transient; cumulative quantities cover the whole campaign including start-up. Both bases are stated in the model output as well as here.]{.mark}

| Quantity | Value | [Basis]{.mark} |
|---|---:|---|
| Hot metal tapped | [964.6 t]{.mark} | [whole campaign]{.mark} |
| Hot metal produced | [1001 t]{.mark} | [whole campaign, tapped plus the rise in bath inventory]{.mark} |
| Productivity | [143.0 tHM/h]{.mark} | [whole campaign]{.mark} |
| Operating specific energy consumption | [784 kWh/tHM]{.mark} | [whole campaign, cumulative energy over metal produced]{.mark} |
| Mean active power | [114.5 MW]{.mark} | [final half, 210 to 420 min]{.mark} |
| Mean lining loss | [28.0 MW (24.5 % of input)]{.mark} | [final half]{.mark} |
| Mean hot metal temperature | [1486 degC]{.mark} | [final half]{.mark} |
| [Mean slag temperature]{.mark} | [1504 degC]{.mark} | [final half]{.mark} |
| Final hot metal C, Si, Mn, S, P | [3.41, 0.18, 0.50, 0.011, 0.044 wt %]{.mark} | [end of campaign]{.mark} |
| Final slag FeO | [1.91 wt %]{.mark} | [end of campaign]{.mark} |
| Final slag basicity B2 | [1.063]{.mark} | [end of campaign]{.mark} |
| Freeze layer thickness | [86 mm]{.mark} | [end of campaign]{.mark} |
| Maximum shell temperature | 197 degC | [whole campaign maximum]{.mark} |

[Over this campaign 964.6 t left through the tap-hole while 1001 t was made, the difference accumulating in the bath. Specific energy is computed over metal produced, so energy spent filling the furnace is not charged to the metal that happened to leave; Section 3.10.1 defines both.]{.mark}

The operating specific energy of [784 kWh/tHM]{.mark} lies within the Tenova iBlue design envelope of 500 to 1200 kWh/tHM [5,10], as does the slag to metal ratio. [The Metso Outotec pilot figure of 762.6 kWh/tHM quoted in [13] is not used as a benchmark here, because [13] states that no metallisation, temperature, hot metal carbon or feed gangue is reported with it, so the operating point behind it is unknown. It is reported for magnitude only: a run at 80 % metallisation, the level [13] tabulates it at, gives 980 kWh/tHM against the pilot 762.6, a difference of 29 %.]{.mark} The campaign comprises seven metal taps and fourteen slag taps. [Following the initial heating transient, the feed-forward and PI control of Algorithm S~2~, lines 5 and 6, holds the hot metal temperature to a mean deviation of 13.6 K below setpoint, with a largest excursion of 19.9 K. The offset is a property of the tuning, not of the solver: the integral term is limited to plus or minus 2.0 x 10^4^ K s, which with the integral gain of 2.0 x 10^-4^ MW per K s caps its authority at 4.0 MW, so a steady bias larger than that cannot be removed. The tuning is reported as it stands rather than widened to close the offset.]{.mark}

The trajectories in Figure 8 show the characteristic behaviour of the continuous process. Slag FeO falls from its initial value and stabilises near [1.9 wt %]{.mark} once the carbon supply and the FeO input from the feed reach balance. Hot metal carbon approaches 3.4 wt % as carburisation and consumption by reduction equilibrate. Bath inventories exhibit the expected sawtooth from discrete tapping, and the freeze layer thickens to [86 mm]{.mark} as the campaign proceeds and the slag composition shifts towards its steady value.

![**Figure 8.** Trajectories over the seven-hour campaign of Table 15. Panels show bath temperatures, power split and lining loss, bath inventories, hot metal and slag chemistry, basicity, reaction rates, electrical operating point, superheat, lining state and cumulative production.](figures/Fig8_dynamic_campaign.png)

### [6.9 Agreement between the two solvers]{.mark}

[The two solvers are not fed the same way, so the comparison has to be set up rather than read off two earlier tables. The steady-state solver is given composition targets and returns the carbon and flux demand to meet them; the transient solver is given feed rates and returns whatever composition they produce. Running both on their own defaults compares two different operating points, which is why the silicon and FeO figures of Sections 6.5 and 6.8 appear irreconcilable: 0.414 wt % Si and 0.65 wt % FeO come from the industrial consistency case, 0.24 wt % Si and 1.80 wt % FeO from the base-case campaign, a different feed at a different metallisation with a different carbon target.]{.mark}

[For a like-for-like comparison the steady state was solved first, at 94 % metallisation of DRI-B, 1500 degC, basicity 1.10 and 3.4 wt % carbon in the metal. It returns a demand of 56.0 kg of carbon and 113.4 kg of flux per tonne of DRI. Those exact rates were then fed to the transient solver, which was run for 24 hours with tapping matched to the feed so that the bath neither fills nor empties, and the stationary state it reaches is compared against the steady-state solution in Table 16.]{.mark}

[**Table 16.** The two solvers under identical operating conditions. The transient column is the stationary state reached after 24 hours on the carbon and flux demand returned by the steady state. Both columns are computed on the same heat-loss basis, the geometry network of Section 3.6, with the steady-state productivity set from the feed rate and the yield.]{.mark}

| [Quantity]{.mark} | [Steady state]{.mark} | [Transient, stationary]{.mark} | [Difference]{.mark} |
|---|---:|---:|---:|
| [Operating specific energy, kWh/tHM]{.mark} | [823.7]{.mark} | [792.4]{.mark} | [-3.8 %]{.mark} |
| [Slag rate, kg/tHM]{.mark} | [270.6]{.mark} | [285.9]{.mark} | [+5.6 %]{.mark} |
| [Hot metal C, wt %]{.mark} | [3.400]{.mark} | [3.729]{.mark} | [+9.7 %]{.mark} |
| [Hot metal Si, wt %]{.mark} | [0.231]{.mark} | [0.203]{.mark} | [-12.0 %]{.mark} |
| [Hot metal Mn, wt %]{.mark} | [0.517]{.mark} | [0.510]{.mark} | [-1.4 %]{.mark} |
| [Hot metal S, wt %]{.mark} | [0.0093]{.mark} | [0.0091]{.mark} | [-2.2 %]{.mark} |
| [Hot metal P, wt %]{.mark} | [0.0437]{.mark} | [0.0427]{.mark} | [-2.2 %]{.mark} |
| [Slag FeO, wt %]{.mark} | [0.645]{.mark} | [1.716]{.mark} | [+166 %]{.mark} |
| [Slag basicity B2]{.mark} | [1.091]{.mark} | [1.103]{.mark} | [+1.1 %]{.mark} |
| [Hot metal temperature, degC]{.mark} | [1500]{.mark} | [1486]{.mark} | [-0.9 %]{.mark} |

[Eight of the ten quantities agree to within 10 %. The specific energies agree to 3.8 %, the transient being the lower of the two.]{.mark}

[Both columns must be computed on the same heat-loss basis for the comparison to mean anything: a steady state solved with an assumed loss fraction against a transient computing its own loss would differ by the two loss assumptions rather than by the two solvers. The transient bath settles 14 K below the steady-state tapping temperature, which is the controller offset of Section 6.8 and not a disagreement between the two thermochemical treatments, the steady-state solver being given the tapping temperature and meeting it by construction.]{.mark}

[Slag FeO is the exception, and the two numbers are not predictions of the same thing. The steady-state 0.645 wt % is the empirical floor of Section 3.5, which the solver cannot go below and has no mechanism to exceed. The transient 1.716 wt % is whatever the rate balance of Section 3.8 settles at for this feed and carbon supply, and is the physically meaningful one. That it exceeds the industrial floor by a factor of 2.7 suggests either that the kinetic constants of Table 8 are slow, which Section 3.8 identifies as the least certain part of the model, or that the reference furnace runs with more carbon or longer residence. The disagreement is reported rather than removed, since removing it would mean fitting one solver to the other.]{.mark}

[This comparison is excluded from the validation statistics of Section 6.1, since it tests the internal consistency of this work rather than its accuracy.]{.mark}

### [6.10]{.mark} Physical admissibility across the input space

All 178 configurations defined in Section 5.5 satisfy the admissibility criteria. Elemental closure is better than 1 part in 10^5^ per cent for the base case and better than 2 parts in 10^5^ per cent at 60 wt % scrap, the most demanding case examined. No configuration produced a negative or indeterminate quantity, and every case converged within the iteration limit.

The procedure also confirmed that infeasible configurations are correctly rejected. A flux pair in which both members are acid cannot raise slag basicity, and Eqs. (24) to (26) admit no non-negative solution; the solver returns a diagnostic identifying the cause rather than a converged but meaningless result.

### [6.11]{.mark} Limitations and uncertainty

Three classes of limitation apply.

The first is structural. Each control volume is spatially uniform, so the model cannot resolve current distribution between electrodes, the slag flow field, or local overheating near the electrode tips. Refractory wear driven by local conditions therefore lies outside its scope, and coupling to the electromagnetic and CFD approaches reviewed in [5,21,22,23] is the natural extension. Freeboard chemistry is represented by a prescribed post-combustion ratio and slag foaming by an index that is not fed back to the electrical operating point. Titanium is treated by an empirical reduction fraction rather than explicit Ti(III) and Ti(IV) speciation, and, since no reference source reports titanium, that treatment is carried by the model but is not validated by any comparison in this work; predictions of titanium partition should not be relied upon.

The second concerns parameter uncertainty. The three [empirical limits]{.mark} of Section 3.5 are calibrated against industrial composition specifications rather than derived from measured transport coefficients. Their values are therefore specific to the operating window from which those specifications derive, and extrapolation beyond it is not supported. Propagating the reported width of the industrial silicon specification through Eq. (11) gives a variation of approximately 0.1 wt % in predicted hot metal silicon at 1600 degC, which is the dominant uncertainty in that quantity. A mechanistic treatment based on measured slag and metal mass-transfer coefficients would remove this limitation and is the clearest route to improving the model.

The third concerns the reference data. The temperature sensitivity of specific energy remains approximately 30 % below the published slope, although absolute values at each temperature agree closely, and the cause has not been isolated. The laboratory comparisons of Table 13 compare scales differing by five orders of magnitude in mass. The industrial comparison of Table S2 relies on a back-calculated feed, since the corresponding analysis is not published.

### [6.12]{.mark} Implications for process design and operation

[A worked operating decision is given in Section S13 of the supplementary material: a plant whose DRI gangue rises from 15.5 to 19 wt % sees specific energy rise by only 5.3 % but slag by 26 %, and the model shows scrap blending rather than a lower basicity to be the remedy, on grounds of slag rate and freeze layer rather than energy.]{.mark}

Three further results bear directly on the design and operation of the DRI, ESF and BOF route.

Silicon must be predicted on a constrained rather than an equilibrium basis if the downstream converter is to be sized correctly, the difference reaching a factor of five at the top of the tapping range. The freeze-lining criterion of inequality (16) should be evaluated at the design stage: it is inexpensive and determines whether the protective mechanism assumed for the slag belt can operate at all. The slag valorisation index of Eq. (29) links operating settings to the reuse value of the slag; at base-case conditions the tapped slag satisfies all three criteria, whereas at the basicity of about 2 required by EAF foaming practice it fails on basicity, which quantifies the argument of [1] that the ESF route yields a cement-suitable slag where an EAF on the same feed does not.

---

## 7. Conclusions

A coupled steady-state and transient model of the electric smelting furnace has been formulated from conservation laws, measured thermophysical properties and reaction kinetics, resolving thermochemistry, heat and mass transfer, a five-zone refractory network with an analytic freeze-lining criterion, mass-transfer kinetics and a slag-resistance electrical circuit. It addresses the absence of independent transient models of the open slag bath furnace identified in the recent review literature.

1. [Against 48 benchmarks spanning two equilibrium codes, a published stream balance, a supplier design envelope, pilot figures and laboratory experiment, the model gives a mean absolute relative deviation of 14.6 % with a median of 4.0 % over 17 single-valued comparisons, 12 of them within 10 %, and satisfies 22 of 31 interval tests. The two published equilibrium codes differ from one another by 14.6 to 16.0 % on identical cases, so the model sits at the edge of the present reproducibility of the field. Comparisons compromised by fitting, the industrial composition check and figures from other furnace classes are reported separately and excluded.]{.mark}

2. [The model contains no fitted energy parameter. A thermal utilisation factor used in earlier work was withdrawn after the ratio it represents was found to vary from 0.775 to 0.886 across the checkable published cases, which is not the behaviour of a physical efficiency. Specific energy is reported on a loss-free and a loss-inclusive basis, and published figures, whose loss convention the sources do not state, are tested against the interval between them. A complete published stream balance at 1600 degC is reproduced with eight of its fifteen quantities within 6 % and its specific energy inside that interval.]{.mark}

3. [The published data are not mutually consistent, and reconciling them is part of the result. Two silicon datasets together require silicon to fall as temperature rises for an endothermic reduction, which cannot describe equilibrium. The two equilibrium codes differ by a factor of 2.4 on the sensitivity to hot metal carbon, a larger disagreement than their 14.6 to 16.0 % difference on absolute energy, suggesting that derivatives test a thermochemical database more severely than absolute values. One published balance carries phosphorus in its product that is absent from its feed, and FeO in its slag with no oxidation path to supply it.]{.mark}

4. [Measured hot metal silicon, residual slag FeO and slag manganese all lie far from equilibrium, and the model holds them to industrial ranges with three empirical constraints. Those constraints carry no rate, residence time or interfacial area and are not kinetics; they bound the approach to equilibrium and are fitted to one industrial furnace. Reporting both the equilibrium and the constrained result gives an honest band for an unfamiliar ore, a factor of about five in silicon at 1600 degC, and Section 3.5.1 sets out how a plant with tapping records can replace them with its own.]{.mark}

5. The freeze-lining energy balance yields inequality (16), a criterion determining whether a protective frozen layer can be sustained on a given slag belt; a belt violating it operates with its refractory hot face above the slag liquidus whatever the cooling intensity.

6. Physical admissibility was verified over 178 configurations spanning the full input space, independently of agreement with reference data. All satisfied the criteria and infeasible configurations were correctly rejected with a diagnostic. [Two returned valid balances at conditions below the liquidus of their own hot metal or slag; such cases are detected and flagged rather than reported as operating points.]{.mark}

7. At base-case conditions the tapped slag satisfies all three criteria for use as a supplementary cementitious material, whereas at the basicity required by EAF foaming practice it does not, which quantifies the slag valorisation argument for the ESF route.

8. [Run against each other under identical conditions and on one heat-loss basis, the two solvers agree within 10 % on eight of ten quantities and to 3.8 % on specific energy. Slag FeO is the exception, 0.65 wt % from the steady-state constraint against 1.72 wt % from the transient rate balance, because the two compute different things; the transient value is the physically meaningful one and indicates that the kinetic constants of Table 8 are the least settled part of the model.]{.mark}

Priorities for further work are direct measurement of slag and metal mass-transfer coefficients under ESF conditions to replace the [calibrated empirical limits]{.mark}; coupling to an electromagnetic representation of the brush arc; extension of the freeboard to a reacting gas-phase model; and calibration against a full industrial campaign, for which the kinetic pre-exponentials of Table 8 are the intended fitting parameters.

---

## Declarations

### Use of generative artificial intelligence

During the preparation of this work the author used Claude, a large language model developed by Anthropic, for the following purposes: writing and debugging the source code implementing the model described here; executing the numerical experiments, parametric studies and verification procedures, and tabulating their output; and drafting and editing the text of this manuscript.

The author defined the scope of the work, selected the physical formulation, chose and interpreted the validation data, and verified every numerical result reported. All output of the tool was reviewed and edited by the author, who takes full responsibility for the content of this paper. The tool does not satisfy the criteria for authorship and is not listed as an author, and no element of the scientific judgement reported here was delegated to it.

### Funding

To be completed by the author.

### Conflict of interest

The author is a director of Extractmet Private Limited, which develops and licenses software implementing the model described in this paper.

### Data availability

The validation tables, figures and trajectories reported here are generated directly from the model. Reference data are taken from the cited publications. Plant references are anonymised.

---

## References

1. Visuri, V.-V., Echterhof, T. (2025) Electric arc furnace steelmaking. *Metals* **15**, 1285. https://doi.org/10.3390/met15121285

2. World Steel Association (2025) *World Steel in Figures 2025*. World Steel Association, Beijing.

3. Pei, M., Petajaniemi, M., Regnell, A., Wijk, O. (2020) Toward a fossil free future with HYBRIT: development of iron and steelmaking technology in Sweden and Finland. *Metals* **10**, 972. https://doi.org/10.3390/met10090972

4. Sabah, S., Kudaru, U., Brooks, G., Rhamdhani, M.A., Owusu, K., Kumar, B., Chen, C., Guiraud, A. (2026) Application of electric smelting furnace to ironmaking. *Journal of Sustainable Metallurgy*. https://doi.org/10.1007/s40831-026-01459-2

5. Sabah, S., Kudaru, U., Brooks, G., Rhamdhani, M.A., Owusu, K., Kumar, B., Chen, C., Guiraud, A. (2026) Modeling of electric smelting furnaces for ironmaking: a review. *Journal of Sustainable Metallurgy*. https://doi.org/10.1007/s40831-026-01575-z

6. Bae, S.J., Park, J.H. (2025) Sustainable hot metal production by solid and liquid carbon from H2 direct reduced iron (H2-DRI) in electric smelting furnace (ESF) conditions. *Journal of Cleaner Production* **524**, 146490. https://doi.org/10.1016/j.jclepro.2025.146490

7. Metso (2024) DRI smelting furnace. https://www.metso.com/portfolio/dri-smelting-furnace/

8. Wimmer, G., Rosner, J., Fleischanderl, A. (2022) Two steps towards net zero carbon? Primetals Technologies Austria GmbH.

9. Belford, B., Reuter, L., Kleier, T. (2022) Green steel with open bath furnaces. *Steel Times International*, pp. 64-68.

10. Esterhuizen, A., Tenova (2024) iBlue open slag bath furnace: fundamental designs for a DRI smelter. In: *South African Pyrometallurgy 2024*, Southern African Institute of Mining and Metallurgy, Johannesburg.

11. Pan, Y., Sun, S., Jahanshahi, S. (2011) Mathematical modelling of heat transfer in six-in-line electric furnaces for sulphide smelting. *Journal of the Southern African Institute of Mining and Metallurgy* **111**(10), 717-732.

12. Shahabuddin, M., Rahbari, A., Sabah, S., Brooks, G., Pye, J., Rhamdhani, M.A. (2024) The performance and charge behaviour in melter/smelter for the production of hot metal in hydrogen DRI-based steelmaking. *Ironmaking & Steelmaking*. https://doi.org/10.1177/03019233241265179

13. [Owusu, K.B., Sabah, S., Brooks, G., Chen, C., Guiraud, A., Kudaru, U., Rhamdhani, M.A., Kumar, B. (2026) Thermodynamic assessment of gangue content in hydrogen-direct reduced iron smelting in electric smelting furnaces: Part 1. *Journal of Sustainable Metallurgy* **12**, 5257-5274. https://doi.org/10.1007/s40831-026-01622-9]{.mark}

14. [Matino, I., Branca, T.A., Guzzon, M., Colla, V. (2026) Electric smelting furnace flowsheet model for future slag investigations. In: *AISTech 2026 Proceedings*, D031S037R001. Association for Iron and Steel Technology, Warrendale.]{.mark}

15. Teasdale, S.L., Hayes, P.C. (2005) Kinetics of reduction of FeO from slag by graphite and coal chars. *ISIJ International* **45**(5), 642-650. https://doi.org/10.2355/isijinternational.45.642

16. Min, D.J., Fruehan, R.J. (1992) Rate of reduction of FeO in slag by Fe-C drops. *Metallurgical Transactions B* **23**, 29-37. https://doi.org/10.1007/BF02654033

17. Min, D.J., Han, J.W., Chung, W.S. (1999) A study of the reduction rate of FeO in slag by solid carbon. *Metallurgical and Materials Transactions B* **30**(2), 215-221. https://doi.org/10.1007/s11663-999-0050-5

18. Htet, T.T., Yan, Z., Khasraw, D., Hage, J., Meijer, K., Li, Z. (2023) Kinetic study on reduction of FeO in a molten HIsarna slag by various solid carbon sources. *Metallurgical and Materials Transactions B* **54**(1), 163-177. https://doi.org/10.1007/s11663-022-02677-1

19. Turkdogan, E.T. (1980) *Physical Chemistry of High Temperature Technology*. Academic Press, New York.

20. Sheng, Y., Irons, G.A., Tisdale, D.G. (1998) Transport phenomena in electric smelting of nickel matte: Part I. Electric potential distribution. *Metallurgical and Materials Transactions B* **29**, 77-83. https://doi.org/10.1007/s11663-998-0009-y

21. Karalis, K., Karkalos, N., Cheimarios, N., Antipas, G.S.E., Xenidis, A., Boudouvis, A.G. (2016) A CFD analysis of slag properties, electrode shape and immersion depth effects on electric submerged arc furnace heating in ferronickel processing. *Applied Mathematical Modelling* **40**(21-22), 9052-9066. https://doi.org/10.1016/j.apm.2016.05.045

22. Karalis, K., Karalis, N., Karkalos, N., Ntallis, N., Antipas, G.S.E., Xenidis, A. (2021) Three-dimensional computational fluid dynamics analysis of an electric submerged arc furnace. *Scientific Reports* **11**, 17637. https://doi.org/10.1038/s41598-021-96085-1

23. Bezuidenhout, J.J., Eksteen, J.J., Bradshaw, S.M. (2008) CFD modelling of molten matte and slag flows in a circular 3-phase smelting furnace. *Progress in Computational Fluid Dynamics*. https://doi.org/10.1504/PCFD.2009.027362

24. [Kudaru, U., Sabah, S., Brooks, G., Rhamdhani, M.A., Owusu, K., Chen, C., Guiraud, A. (2025) Modelling of electric smelting furnaces for hot metal production. In: *STIS-V 2025, Fifth International Conference on the Science and Technology of Ironmaking and Steelmaking*, Bengaluru, pp. 134-139.]{.mark}

25. Yu, Y., Li, B., Yun, C., Qi, F., Liu, Z. (2021) Modeling on reduction reaction of metal oxides for submerged arc furnace in ferrochrome pellets smelting process. *Metallurgical and Materials Transactions B* **52**, 3907-3919. https://doi.org/10.1007/s11663-021-02304-5

26. Chen, Y., Luo, Q., Silaen, A.K., Zhou, C.Q. (2020) Multi-physics modeling of steel ingot melting by electric arc plasma and its application to electric arc furnace. *Frontiers in Materials* **7**, 576831. https://doi.org/10.3389/fmats.2020.576831

27. Hay, T., Visuri, V.-V., Aula, M., Echterhof, T. (2021) A review of mathematical process models for the electric arc furnace process. *Steel Research International* **92**, 2000395. https://doi.org/10.1002/srin.202000395

28. Logar, V., Dovzan, D., Skrjanc, I. (2012) Modeling and validation of an electric arc furnace: Part 1, heat and mass transfer. *ISIJ International* **52**(3), 402-412. https://doi.org/10.2355/isijinternational.52.402

29. Logar, V., Dovzan, D., Skrjanc, I. (2012) Modeling and validation of an electric arc furnace: Part 2, thermo-chemistry. *ISIJ International* **52**(3), 413-423. https://doi.org/10.2355/isijinternational.52.413

30. Chase, M.W. (1998) *NIST-JANAF Thermochemical Tables*, 4th edn. Journal of Physical and Chemical Reference Data, Monograph 9. https://doi.org/10.18434/T42S31

31. Barin, I. (1995) *Thermochemical Data of Pure Substances*, 3rd edn. VCH, Weinheim. https://doi.org/10.1002/9783527619825

32. Sigworth, G.K., Elliott, J.F. (1974) The thermodynamics of liquid dilute iron alloys. *Metal Science* **8**(1), 298-310. https://doi.org/10.1179/msc.1974.8.1.298

33. Fincham, C.J.B., Richardson, F.D. (1954) The behaviour of sulphur in silicate and aluminate melts. *Proceedings of the Royal Society of London A* **223**(1152), 40-62. https://doi.org/10.1098/rspa.1954.0099

34. Park, G.H., Kang, Y.B., Park, J.H. (2011) Sulfide capacity of the CaO-SiO~2~-MnO slag at 1873 K. *ISIJ International* **51**(9), 1375-1382. https://doi.org/10.2355/isijinternational.51.1375

35. Holm, R. (1967) *Electric Contacts: Theory and Application*, 4th edn. Springer, Berlin. https://doi.org/10.1007/978-3-662-06688-1

36. Bowman, B., Kruger, K. (2009) *Arc Furnace Physics*. Verlag Stahleisen, Dusseldorf.

37. Jordan, G.R., Bowman, B., Wakelam, D. (1970) Electrical and photographic measurements of high-power arcs. *Journal of Physics D: Applied Physics* **3**(7), 1089-1099. https://doi.org/10.1088/0022-3727/3/7/305

38. Urbain, G. (1987) Viscosity estimation of slags. *Steel Research* **58**(3), 111-116. https://doi.org/10.1002/srin.198700595

39. Pang, Z., Liu, W., Zheng, J., Xue, Q., Wang, J., Zuo, H. (2025) Properties evaluation of electric smelting furnace slag: viscosity and sulfide capacity under different FeO content. *Ceramics International* **51**(1), 593-601. https://doi.org/10.1016/j.ceramint.2024.11.037

40. Ono, H., Tanizawa, K., Usui, T. (2011) Rate of iron carburization by carbon in slags through carbon/slag and slag/metal reactions at 1723 K. *ISIJ International* **51**(8), 1274-1278. https://doi.org/10.2355/isijinternational.51.1274

41. Turkdogan, E.T. (1984) Physicochemical aspects of reactions in ironmaking and steelmaking processes. *Transactions of the Iron and Steel Institute of Japan* **24**(8), 591-611. https://doi.org/10.2355/isijinternational1966.24.591

42. Heo, J.H., Park, J.H. (2022) Interfacial reactions between magnesia refractory and electric arc furnace (EAF) slag with use of direct reduced iron (DRI) as raw material. *Ceramics International* **48**(4), 4526-4538. https://doi.org/10.1016/j.ceramint.2021.10.238
