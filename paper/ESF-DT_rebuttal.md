# Response to reviewers

**Manuscript:** Coupled steady-state and transient modelling of the electric smelting furnace for hydrogen-DRI ironmaking

**Journal:** Ironmaking & Steelmaking

---

## How to read this document

Every comment is quoted in full, answered, and followed by a line beginning **Changed:** that names the section, table, equation or figure where the change was made. All changes are highlighted in yellow in the revised manuscript, so each one can be found directly.

Where a comment led to a correction of something that was wrong rather than merely unclear, that is said plainly. There were several, and three of them came from questions the reviewers asked about apparently minor inconsistencies. We are grateful for the care taken; the paper is materially more reliable than the version submitted.

Two general points apply throughout.

**The validation set has been rebuilt.** The counts, the statistics and the way comparisons are classified have all changed, following Reviewer 3's comment on calibration targets and Reviewer 2's question about the thermal utilisation factor. The headline figures are now 48 benchmarks, comprising 17 single-valued comparisons with a mean absolute relative deviation of 14.6 % and a median of 4.0 %, and 31 interval tests of which 22 are satisfied. The submitted version reported 52 benchmarks at a mean deviation of 8.53 %. The figure has worsened because comparisons that could not test the model have been removed from it, not because the model has.

**One fitted parameter has been withdrawn entirely.** The thermal utilisation factor of 0.887 is gone. The model now contains no fitted energy parameter. This is explained under Reviewer 2's third comment and is the single largest change in the paper.


**Tables have been renumbered, and the manuscript has been shortened.** The reviewers' comments cite the submitted table numbers, and those are kept unchanged in the quoted comments below. Our answers use the revised numbers. The concordance is:

| Content | Submitted | Revised |
|---|---|---|
| Published steady-state results | 1 | 1 |
| Gaps in the literature | 2 | 2 |
| Modelling assumptions | 3 | 3 |
| Geometry and base-case inputs | 4 | 4 |
| Quantities computed at the base case | (new) | 5 |
| DRI analyses | 5 | 6 |
| Contents of each stream enthalpy | (new) | 7 |
| Reactions and kinetic constants | 6 | 8 |
| Reference datasets and their conditions | 7 | S3 (supplementary) |
| Fitted constants | 8 | 9 |
| Summary of agreement | 9 | 10 |
| Reproduction of the published stream balance | 10 | S4 (supplementary) |
| Energy sensitivities | 11 | 11 |
| Hot metal silicon | 12 | 12 |
| Consistency with industrial composition | 13 | S2 (supplementary) |
| Laboratory smelting comparison | 14 | 13 |
| Zone heat losses | 15 | 14 |
| Transient campaign | 16 | 15 |
| Steady state against transient | (new) | 16 |
| Term-by-term energy balance | (new) | S1 (supplementary) |

Reviewer 2 asked for the manuscript to be shortened and for detail to move to the supplementary material. The first round of revision did the opposite, because it answered every comment inside the paper. In this version the explanations of what was changed and why are in this document, and the manuscript states only the corrected result. Some answers below therefore describe a change at greater length than the manuscript does.
---

## Changes made on our own initiative, before the reviews were read

Seven errors were found in our own checking after submission. They are listed here rather than buried under individual replies, because reviewers are entitled to know what changed for reasons they did not raise.

**A1. Two industrial composition windows had been widened without disclosure.** In the submitted Table 13 the hot metal sulphur window was printed as 0.020 to 0.035 wt % where the source gives 0.025 to 0.030, the iron window as 94.0 to 95.5 wt % where the source gives 94.7 to 94.8, and the slag MnO window as 0.15 to 0.30 wt % where the source gives 0.20 to 0.25. With the published windows restored, four of the twelve industrial entries fall outside rather than two. The claim that ten of twelve specifications were satisfied was therefore wrong; it is now eight of twelve, and the comparison is no longer presented as validation at all, for the reason in A2.

**Changed:** Section 6.5, Table S2, and the validation data in the supplementary workbook.

**A2. The industrial comparison was largely circular.** Tracing the provenance of the twelve quantities in that comparison showed that only one, hot metal iron, is an independent prediction. Three are operating targets set in the run, four are controlled by constants calibrated against the same published table, and four follow from feed constituents we chose ourselves when back-calculating the feed. The section is now titled "Consistency with industrial composition", carries a provenance column stating what determines each value, and is excluded from the validation statistics.

**Changed:** Section 6.5 and Table S2.

**A3. A published feed analysis had been silently completed.** The DRI analysis in the stream balance of [10] sums to 99.80 wt %. We had assigned the missing 0.20 wt % to CaO, MgO, TiO~2~ and P~2~O~5~ without saying so. This is now disclosed with its effect quantified: removing those four constituents changes the specific energy of Table S4 by 0.26 % and the slag mass by 0.19 %.

**Changed:** Section 3.2, after Table 6.

**A4. Titanium is unvalidated and was presented as though it were not.** Titanium appears in no comparison in this paper and in none of the source documents. The abstract listed it among the equilibria the model resolves, which implied a validation that does not exist.

**Changed:** Abstract, Section 3.4, Section 6.11.

**A5. The Owusu reference was a draft at submission and is now published.** It appeared in the bibliography of the review we cite as "drafted". It has since been published as *Journal of Sustainable Metallurgy* **12**, 5257-5274 (2026), doi 10.1007/s40831-026-01622-9, and we have verified every value we take from it against the published paper. Four transcription errors were found in doing so and are corrected: the specific energy of DRI-C at 100 % metallisation is 574.5 and not 575.5 kWh/tHM, that of DRI-B at 80 % metallisation is 779 and not 778 kWh/tHM, the hot metal iron window is 94 to 95 wt % and not 94.0 to 95.5, and the carbon sensitivity is discussed under Reviewer 3's comment on that subject.

**Changed:** reference 13, Table S3, Table 11, Table 12, and the supplementary data.

**A6. The silica activity expression squared the mole fraction, and the justification offered for it in the first revision was wrong.** The submitted Eq. (6) wrote the silica activity as a coefficient multiplying the square of the mole fraction. In the first round of revision we defended that square on structural grounds, citing an ionic-sublattice argument and the quasi-chemical treatment. On being challenged we checked it, and the defence does not hold.

Three findings settled it. Silica was the only oxide in the model written to a squared mole fraction, while FeO, MnO and TiO2 were all first power, so no structural argument could apply to one and not the others. The silica mole fraction varies by about one per cent across the four anchors the expression was fitted to, and by 29 % across the whole operating range, so the exponent was not identified by the data at all: refitting with the first power moved the reduction Gibbs energy by 14.7 kJ/mol, within one per cent of the compensation that the mean silica mole fraction predicts, which shows the two were simply trading against each other. And the first power fits better: with the Gibbs energy refitted, it reproduces the two printed silicon anchors to 1.2 % and 0.9 %, against 3.3 % and 6.7 % for the squared form.

Equation (6) is now written to the first power, the Gibbs energy of Eq. (8) is refitted from 581 500 to 596 200 J/mol, and Section 3.4 states plainly that the coefficient is an empirical correlation rather than a quantity from a solution model. The two references added in the first revision to support the withdrawn argument have been removed. The effect on the headline statistics is small and favourable: the mean absolute relative deviation on the independent set moves from 12.3 to 13.1 % and the median from 4.1 to 4.0 %. It rises because correcting the expression also showed that two of the four silicon anchors are the values the reduction Gibbs energy is fitted to, so they have been reclassified as calibration targets and taken out of the statistics.

**Changed:** Eq. (6), Eq. (8), Section 3.4 rewritten, Table 9, Table 12, Table 11, Table 16, Section 6.1 and Table 10, conclusion 1; `thermo.py`, `a_SiO2` corrected to the first power and the `SiO2_C` Gibbs A term refitted.

**A7. The freeboard gas temperature was computed by a rule that made the gas hotter than the bath, and that error was concealing a second one.** The submitted model set the freeboard gas temperature as the mean of the slag temperature and the roof hot face, plus a post-combustion rise capped at 150 K. The roof is water cooled, so entering it as a heat source of the same weight as the bath is wrong on its face; worse, the roof hot face is itself a response to the gas temperature through the lining network, so the two drove one another upwards with a loop gain of one half. The gas settled at 1722 degC against a slag at 1518 degC, 204 K above its only heat source, and the roof hot face settled at 1626 degC, also above the bath. In the first round of revision we were asked about this figure and explained it as the gas cooling on its way to the uptake. That explanation was wrong, and we withdraw it.

The second error followed from the first. The open-bath radiation debit of Eq. (13) is computed against the roof hot face, so a roof hotter than the bath suppressed that debit, at times clamping it to zero. The bath was being insulated by a surface that cannot insulate it, and the campaign results rested on that.

The gas temperature is now obtained from a freeboard energy balance, given in the new Section 4.3.1. The gas is treated as a participating medium that absorbs from the slag surface, radiates and convects to the cooled roof and upper sidewall, and is carried through at the rate the reactions and the ingress air supply it, with post-combustion releasing heat inside the gas. The balance is monotone in the gas temperature, so it has a single root, found by bisection, and the gas is bounded below by the coldest surface it sees and above by its inlet temperature plus the adiabatic post-combustion rise. Three further corrections were made in the same place: the freeboard composition that sets the grey-gas emissivity is now computed from the gas streams rather than prescribed, since ingress air is the larger part of the freeboard mass flow and dilutes the radiating species; the open-bath debit is bounded by the duty the cooled panels actually remove, net of arc radiation, a bound the browser engine had always applied and the Python engine had not; and the post-combustion rise is no longer capped at 150 K, a cap that was being hit at every step of every run.

The corrected gas temperature is 1471 degC, which is 33 K below the slag and within 21 K of the 1450 degC uptake temperature that the steady-state model takes as an input. That agreement is not fitted; the transient solver now arrives at it independently.

The consequences for the results are real and we set them out rather than absorbing them. With the open-bath debit restored, the base case of 160 t/h on 112 MW no longer holds its temperature setpoint: the controller saturates at the rating and the hot metal settles about 24 K low. The rated power of the transient case is therefore raised to 116 MW, at which the loop has authority to spare, and the correction can be stated as a result in its own right, namely that this duty needs about 4 MW more than the submitted model implied. Campaign specific energy rises from 707 to 784 kWh/tHM and the lining loss share falls from 29.9 to 24.5 %, the freeze layer thickens from 76 to 86 mm because the bath runs cooler, and the mean absolute relative deviation on the independent set rises from 13.1 to 14.6 %, which places the model at the lower bound of the 14.6 to 16.0 % by which the two published equilibrium codes differ rather than comfortably inside it. We report that rather than presenting it more favourably.

Two smaller things surfaced with it. The temperature controller does not hold setpoint exactly even when it is not saturated: its integral term is limited to an authority of 4.0 MW, so a steady bias larger than that cannot be removed, and the campaign runs about 14 K below setpoint. The submitted claim of a 1.8 K mean deviation was only attainable with the freeboard error in place. We have left the tuning as published and reported the offset, rather than widening the limit to recover the earlier figure. And the admissibility sweep gained a second inoperable configuration: charging DRI at 25 degC instead of 600 degC adds some 47 MW of sensible-heat demand that the furnace does not have, so the slag freezes. The test that detects this was also corrected, since it had compared the lowest slag temperature of a campaign against the lowest metal temperature without requiring the two to occur at the same moment.

**Changed:** new Section 4.3.1, Table 4, Table 5 and the paragraph following it, Table 15 and Section 6.8, Table 16 and Section 6.9, Section 6.1 and Table 10, Section 5.5, Figures 1 and 8, conclusions 1 and 6; `dynamic_model.py` freeboard balance, computed freeboard composition, bounded open-bath debit, rated power and the renamed off-gas enthalpy; `web/esf_console.html` the same balance in the browser engine; `audit.py` the inversion test; `run_validation.py` and `cross_check_ss_transient.py` the two-solver comparison basis.

---

## Reviewer 1

> The manuscript presents a useful idea by bringing together the chemical reactions, energy and heat use in the furnace. However, the paper needs major revision. The first priority should be to organise the model more clearly, explain the equations fully, and correct or clarify any inconsistencies.

We have taken this as the organising instruction for the revision. The specific inconsistencies the reviewers identified were real, and two of them led to corrections of substance rather than of presentation: the basis on which the energy sensitivities were computed, and the equation for sulphur partition.

### R1-1. Introduction; make the purpose clearer. State clearly what the model is intended to predict and what is new compared with earlier models.

Agreed. The submitted introduction stated objectives in general terms and left the reader to infer the output list from Section 3. Two new paragraphs now state, in plain terms, exactly what the model takes as input and what it returns, including the electrical quantities in the form a smelter engineer would want them, and then say what is new: not any single sub-model, but the combination of a transient bath state, a lining response, an electrical operating point and a reproduction of the measured departure of product chemistry from equilibrium, none of which the published ESF models return.

**Changed:** Section 1.2, two new paragraphs before the objectives statement.

### R1-2. Section 3.3. For each material stream, state whether its enthalpy includes formation energy, heating, melting, mixing and dissolution. Then identify which contributions are added separately. A simple table would help. Pay attention that each contribution must be counted only once.

This was the most useful single comment on the model formulation, and we have written a new subsection to answer it.

A new Table 7 states, for each of the nine streams, whether formation, heating, melting, mixing and dissolution are inside that stream's absolute enthalpy, added separately, or not applicable, and names the term of Eq. (3) each one enters. The accompanying text states the rule that prevents double counting: because every species carries its standard enthalpy of formation, the difference between the output and input sums already contains the enthalpy of every reaction, so the reaction term of Eq. (3) is zero except for carbonate calcination, where the CO~2~ leaves the system and Eq. (4) handles it explicitly. Only two contributions sit outside the stream enthalpies and are added once each: the slag mixing enthalpy, which no single oxide can carry, and the dissolution enthalpy of the metal solutes.

Table S1 of the supplementary material gives the term-by-term balance for a representative case, with the sensible, latent and superheat parts of the slag and metal enthalpies decomposed so their relative size can be seen, and labelled as a decomposition rather than as additional terms.

**Changed:** new Section 3.3.1, new Table 7, with the representative-case balance as Table S1 of the supplementary material.

### R1-3. Section 3.4; explain the activity expression in Equation (6). Activity is commonly written as a correction factor multiplied by mole fraction. Here, the mole fraction is squared. Explain source and reason for using this form.

The square is not an empirical exponent. It follows from the choice of composition variable: on an ionic basis the mole fraction of the network-forming species entering the mass-action expression is the square of the oxide mole fraction computed on a molecular basis, because two singly charged sites take part in the exchange. The same result appears in the quasi-chemical treatment, where the configurational term involves the pair fraction, which varies as the square of the site fraction in the dilute limit.

A new paragraph sets this out and cites Toop and Samis for the polymerisation argument and Gaye and Welfringer for the cell-model equivalent. It also states the consequence that the reviewer's question implies but does not say: the coefficient in Eq. (6) is therefore not a Raoultian activity coefficient and its values should not be compared with tabulated Raoultian ones.

**Changed:** Section 3.4, new paragraph after Eq. (6); references 24 and 25 added.

### R1-4. Section 3.5. Identify all values chosen or adjusted to match known values and state the conditions supporting them.

Table 9 already listed the fitted constants, but it did not say which comparisons each one compromises, and Section 3.5 did not say how a user should set them for an ore unlike the reference one.

Table 9 now carries a fourth column naming, for each fitted constant, the comparisons it makes circular. Those comparisons are excluded from the statistics, and Section 6.1 reports what the exclusion costs. A new Section 3.5.1 then answers the practical question: each constant has a meaning that can be read directly from a plant's tapping records, and where no records exist the recommendation is to run both bases and report the range rather than to guess a constant.

The section heading has also been changed, for the reason given under Reviewer 2's fourth comment.

**Changed:** Table 9, new Section 3.5.1, Section 3.5 heading and opening paragraph.

### R1-5. Section 3.8. Explain how each contact area and driving force are calculated. Also, for rate coefficients, their sources and applicable conditions should be stated. Clearly separate quantities calculated from physical laws, quantities taken from published relationships, and quantities estimated or adjusted to reproduce known behaviour.

A new block before Table 8 defines the interfacial area, the driving force and the concentration factor for every reaction, and states that both areas are geometric constructions rather than measurements: the slag-metal area is the plan area of the bath, which ignores enlargement by stirring and gas evolution, and the char area is the geometric surface of spheres at the charged particle size, corrected by the contact efficiency.

On the rate coefficients we have had to be blunt. They are not taken from any measurement on this system. The activation energies are of the magnitude reported for these reactions in slag systems and their ordering is as expected, but the specific values were chosen so that the transient solver reproduces the timescales Bae and Park observed. Table 8 now carries a provenance column stating this for each reaction, the text states that they are the least certain quantities in the model and are intended to be re-fitted against plant data, and the closing paragraph of the new Section 6.9 shows where that uncertainty becomes visible: the transient slag FeO exceeds the industrial floor by a factor of 2.6, which points at these constants.

**Changed:** Section 3.8, new explanatory block and a provenance column in Table 8.

### R1-6. Correct the equation and table references in Figure 2. For example, the reaction-rate table is Table 6, and the flux calculations are given in Equations (24)-(26).

Correct, and the error was worse than the two examples given. The flowchart had been drawn against an earlier numbering and seven of its cross-references were wrong. Every one has been checked against the manuscript and corrected: flux demand is Eqs. (24) to (26), slag and metal equilibria are Eqs. (6) to (10), the empirical limits are Eq. (11), the heat balance is Eqs. (1) to (4) with the specific energy tiers at Eq. (28) and the closure check at Eq. (27), the lining network is Eqs. (12) to (13) with the freeze lining at Eqs. (14) to (16), the electrical operating point is Eqs. (17) to (21), the slag valorisation index is Eq. (29), the residual test is Eq. (30), and the kinetics are Table 8 with Eqs. (22) to (23).

**Changed:** Figure 2, redrawn.

### R1-7. Section 5. Basis of comparison section is not elaborated enough. In addition, for each comparison, provide the important reference conditions beside the model inputs, including temperature, feed composition and operating assumptions. Identify any missing information and the assumptions used to replace it.

Table S3 has been rebuilt as the reviewer describes. It now has four columns: the source and its class, the quantities compared, the conditions the source states, and the information the source does not give together with what we assumed in its place. Writing it was instructive, because it made clear how little several of the sources report. The industrial composition comes with no feed, temperature, basicity or carbon target at all. The pilot-scale figures come, in the words of the paper that quotes them, without metallisation, temperature, hot metal carbon or feed gangue. Both facts are now stated where the comparisons are made.

Section 5.2 has also been extended. It now opens with the four constraints that govern what any comparison in this paper can establish, the first being that almost no measurements exist, which the authors of [13] state of their own work as well.

**Changed:** Section 5.1 opening, Table S3 rebuilt, Section 5.2 extended.

### R1-8. Section 6.4 and Table 12; explain how the silicon values were obtained. And the differences between values.

Table 12 now carries a provenance column giving, for each reference value, whether it is printed in the source, read from one of its figures, or an industrial specification rather than a measurement, and whether it was used in fitting. Three of the four values between 1400 and 1525 degC were used to fit the A term of the silica reduction Gibbs energy and therefore cannot test the model; only the value at 1450 degC is independent, and it agrees to 9.1 %. The text now says this rather than claiming the whole range as validation.

The differences between the values are the subject of the section and are of three kinds: between the two equilibrium codes, which cannot both describe equilibrium; between either code and the industrial specification; and between the model's two bases, which differ by a factor of five at 1600 degC.

**Changed:** Table 12 with a new provenance column, Section 6.4 text.

### R1-9. Section 6.8; Specify the averaging period for mean power and heat-loss share.

They were not specified, and worse, they were not consistent. The submitted Table 16 averaged power and heat loss over the final half of the campaign, temperatures over the final 40 %, and reported specific energy cumulatively over the whole campaign including start-up, without stating any of this.

The code has been changed so that a single averaging window applies to every mean, set by a new input and defaulting to the final half of the campaign, and so that the window and the basis of the cumulative quantities are both reported in the model output. Table 15 now carries a basis column for every row, and the window is stated as 210 to 420 minutes for the seven-hour campaign.

**Changed:** Table 15 with a new basis column and an explanatory note; `dynamic_model.py`, new `summary_window_frac` input and reporting of both bases.

### R1-10. Define 'hot metal produced' and show how it relates to tapped metal, and also transfers between metal, slag and gas.

A new Section 3.10.1 does this. It defines contained iron, states that 1000 kg of contained iron gives about 1043 kg of hot metal for the representative case so that the two bases differ by about 4 %, and then walks through every transfer: iron reduced from FeO moves to the metal and is counted, iron remaining as FeO stays in the slag and is the iron lost, silicon and manganese and phosphorus and titanium move as Sections 3.4 and 3.5 allow, sulphur partitions both ways, and carbon splits between the metal and the off-gas. It also states the distinction that only arises in the transient solver, where metal produced is metal tapped plus the change in bath inventory, and notes that over the seven-hour campaign these differ by 37 t.

**Changed:** new Section 3.10.1; Table 15 now reports tapped and produced separately.

### R1-11. The ideas between sections are not well connected.

We have tried to address this by making the dependencies explicit rather than by adding transitions. Section 1.2 now states what the model returns, so that Section 3 reads as the means to that end. Section 2.3 now ends by stating which disagreement in the literature Section 6.3 will treat as a result. Section 3.5 states that it is not kinetics and points to Section 3.8, which is. Section 5.3 names, for each fitted constant, the later comparison it affects. Section 6.1 explains the counting that Sections 6.2 to 6.9 then use. Section 6.9 explains why two numbers quoted in Sections 6.5 and 6.8 appeared irreconcilable.

**Changed:** Sections 1.2, 2.3, 3.5, 5.3, 6.1 and the new 6.9.

---

## Reviewer 2

> The study presents a coupled steady-state and transient model of the electric smelting furnace for melting hydrogen-based DRI. The topic is very important and is of interest both to process modellers and to those working on the design and operation of SAF and OSBF furnaces.

### R2-1. Consider readers from the SAF and OSBF community. Describe the furnace in the terms these readers normally use, such as operating resistance and hearth power density. A short worked example showing how the model could support a real design or operating decision would also make the paper more useful.

Both quantities were computed internally but never reported. They now are, in the model output and in the paper. A new Section 3.7.1 defines the operating resistance as the total per-phase resistance at the operating point and the hearth power density as active power over bath area, and gives both for the representative case: 4.30 mohm and 316 kW/m2. They also appear in the new Table 5 and in the worked example below.

The worked example is in Section S13 of the supplementary material, summarised in one sentence in Section 6.12. A plant melting 15.5 wt % gangue DRI learns that its supply will change to 19 wt % gangue, and the model is used to decide what to do. Specific energy rises by only 5.3 %, which would make the change look easy, but the slag rate rises by 26 %, from 307 to 387 kg/tHM, which is 5.5 t more slag per tap. Two remedies are tested: blending 20 wt % scrap returns both the slag rate and the specific energy below their original values, while lowering the basicity target to 0.95 saves no energy, removes only part of the extra slag, and thins the freeze layer from 67 to 54 mm. The recommendation is scrap blending, and the decision turns on the slag rate and the lining rather than on the energy, which is the point of the example.

**Changed:** new Section 3.7.1, new Table 5, the worked example as Section S13 of the supplementary material; `static_model.py` now reports `Hearth_power_density_kW_m2` and `Operating_resistance_mohm`.

### R2-2. Shorten the manuscript and simplify its structure. The literature review could be reduced and the numerical details (Algorithms 1 and 2, solution times, step-size checks) could go to the supplementary material. Present the validation method and results together, separating calibration from independent validation. Some results tables could be merged or moved to the supplementary data, and the design implications in Section 6.11 could be given more space.

Adopted in full. The manuscript is now about 15,800 words, against about 22,800 at the first revision and 12,300 as submitted. Nothing has been discarded. The explanations moved into this document, and the detail moved into the supplementary material.

What was cut. The first round of revision answered the reviewers inside the manuscript itself, so the paper picked up a running commentary on its own history, in passages of the form "the submitted version reported X, which was wrong because Y". That belongs in a response letter, not in a paper. All of it has been removed from the manuscript and now appears here. The abstract has gone from 539 to 217 words. Sections 2.2 and 2.5 of the literature review are now two sentences each and keep every citation. The defence of the corrected silica activity expression in Section 3.4 has been cut from about 400 words to a statement of what the expression is; the full argument is under item A6 above. Sections 1, 3, 4, 5 and 6 have been rewritten more tersely throughout.

What moved to the supplementary material. Algorithms S1 and S2 are now printed only in the supplementary material. The first revision said this had been done, but the steady-state listing was in fact still printed in full in Section 4.2, and the two printed versions had drifted apart, so the line numbers cited in the text matched only one of them. That is corrected, and the listings in the supplementary material carry the line numbers the manuscript cites. Four tables also moved: the term-by-term energy balance (Table S1), the industrial composition comparison (Table S2), the reference datasets with their conditions (Table S3, previously Table 7, with a pointer from Section 5.1), and the stream-balance reproduction (Table S4, previously Table 10, whose deviations are still discussed in Section 6.2). The worked operating decision is now Section S13, and Section 6.12 summarises its conclusion in one sentence. The phase-transfer accounting is Section S10 and the nomenclature Section S8.

What was kept, and why. Table 7, the stream-by-stream statement of what each enthalpy contains, stays in the body because Reviewer 1 asked for exactly that table. Table 12, the silicon provenance, stays because silicon is the paper's central finding and Section 6.4 cannot be followed without it. Section 5 stays separate from Section 6 because the classification scheme it defines applies to every subsection of Section 6.

Where this leaves the length. The remaining excess over the submitted version is mostly the content the three reviewers asked to be added: the enthalpy accounting of Section 3.3.1, the guidance on setting the constants for a new ore in Section 3.5.1, the freeboard energy balance of Section 4.3.1, the solver comparison of Section 6.9 with Table 16, and the provenance columns throughout. We would cut further on the editor's instruction, but we would rather be told to remove reviewer-requested material than remove it unasked.

**Changed:** abstract; Sections 1, 2.2, 2.5, 3.2, 3.4, 3.5, 3.7.1, 3.8, 3.9, 3.10, 4.2, 4.3, 4.3.1, 5.1 to 5.5, 6.1 to 6.5, 6.7 to 6.9 and 6.12 shortened; algorithm listings removed from the body; Tables S1 to S4 and Sections S8, S10, S11, S12 and S13 added to the supplementary material; tables renumbered as in the concordance at the head of this document.

### R2-3. Could the author clarify whether the close agreement in absolute SEC is independent of the calibration of eta_th = 0.887 against the same equilibrium-code values? Since both the reversible heat and the equilibrium codes appear to be enthalpy balances, what explains the need for an 11 % factor? Do the reference studies include heat losses?

This comment caused the largest change in the paper. The answer to the first question is no, the agreement was not independent of the calibration, and the justification we gave for the factor does not survive checking.

The submitted Section 5.3 defended the factor by saying the ratio it represents varies only between 0.870 and 0.902 across independent cases, and that a constant of that stability can be read as a physical efficiency. We re-derived that ratio against every published specific energy we can verify. It is 0.883 for the stream balance at 1600 degC, 0.842 at 90 % metallisation and 1600 degC, 0.775 for cold DRI from 7 wt % gangue ore and 0.886 from 16 wt % gangue ore. A quantity ranging from 0.775 to 0.886 is not a constant and identifies nothing physical.

On the reviewer's second question, we cannot say whether the reference studies include heat losses, because none of them states its convention. That is precisely what the factor was concealing. It was splitting the difference between a loss-free and a loss-inclusive specific energy on sources that do not say which they report.

The factor has therefore been withdrawn and the model now contains no fitted energy parameter at all. Specific energy is reported on two physically defined tiers: the reversible tier, which excludes all losses, and the operating tier, which includes the lining and shell losses and the electrical efficiency. Published figures are tested against the interval between them, which asks whether the published value is consistent with the model once the unknown convention is allowed for. It is a weaker claim than a percentage agreement and it is the strongest the sources support. The published value falls inside the interval in every such test except one, the cold DRI from 7 wt % gangue ore.

One consequence is worth noting. Because the factor scaled every specific energy, removing it changes every absolute energy figure in the paper and every derivative computed from them.

**Changed:** Section 3.10 and Eq. (28), Section 5.2 new paragraph, Section 5.3 rewritten, Table 9, Tables 10 and 11 and Table S4, conclusion 2; `static_model.py`, `thermal_utilisation_efficiency` default changed from 0.887 to 1.0 with the reasoning in the code comment.

### R2-4a. Eq. (11) does not include residence time, mass-transfer coefficients or interfacial area. Could the author explain in what sense it is a kinetic model?

It is not one, and calling it kinetic was wrong. Equation (11) and the FeO floor and the manganese bounds contain no rate, no time, no mass-transfer coefficient and no area. They bound how closely three product variables may approach equilibrium, using bounds read from operating furnaces.

Section 3.5 is now titled "Empirical limits on the approach to equilibrium" and opens by saying exactly this, including that the title was changed and why. The word kinetic is reserved for Section 3.8, which does carry rates, areas and driving forces and belongs to the transient solver. The abstract has been reworded to match, as Reviewer 3 also asked.

**Changed:** Section 3.5 heading and opening paragraph, abstract paragraph 3, Section 3.8 opening.

### R2-4b. Since S_c, the FeO floor and the Mn bounds are calibrated on the same industrial data used for comparison, how would a user set them for a new ore?

A fair question that the submitted version did not address. The new Section 3.5.1 answers it. Each constant has a meaning that is measurable on a plant without any model: S_c is the highest hot metal silicon at normal tapping temperature, read from tapping records; the FeO floor is the residual slag FeO at tap, read from slag analyses; the manganese bounds follow from a manganese balance over a tapping cycle. A plant with a few weeks of records has all three.

Where no records exist we recommend against guessing. The model should be run on both bases and the answer treated as a range, which for silicon at 1600 degC is about a factor of five. That is wide, but it is honest, and it is narrower than assuming either limit without evidence.

**Changed:** new Section 3.5.1; Section 6.4 closing paragraph.

### R2-4c. Why do the steady-state results (Si 0.414 %, FeO 0.65 %) differ from the transient ones (Si 0.24 %, FeO 1.80 %)?

Because they were not the same case, which the submitted paper failed to make clear. The silicon of 0.414 % and FeO of 0.65 % came from the industrial consistency case in Section 6.5, at 97 % metallisation of a back-calculated feed with a 4.5 wt % carbon target. The 0.24 % and 1.80 % came from the base-case transient campaign, a different DRI at 94 % metallisation with a 3.4 wt % carbon target. Comparing them was comparing two operating points.

Rather than only explain this, we have run the comparison the reviewer's question implies, which Reviewer 3 also asked for. It is the new Section 6.9. The steady state is solved first and returns a carbon and flux demand; those exact rates are then fed to the transient solver, which is run to a stationary state. Under identical conditions, eight of the ten compared quantities agree within 10 % and the specific energies to 3.8 %.

We set that comparison up incorrectly at first and have corrected it, which is worth recording because it changes what the table shows. The steady state was solved with an assumed heat loss of 10 % of input while the transient computed its own loss from the lining network and reached about 24 %. The two columns were carrying different energy bases, so the 7.1 % difference in specific energy we reported there was the difference between the two loss assumptions, not between the two solvers. Both are now solved on the geometry network, with the steady-state productivity set from the feed rate and the yield, and on that basis the specific energies differ by 3.8 %, the transient being the lower.

Slag FeO remains the exception, at 0.645 wt % against 1.716 wt %, and the reason is instructive. The two numbers do not predict the same thing. The steady-state value is the empirical floor of Section 3.5, which the solver cannot go below and has no mechanism to exceed. The transient value is computed from the rate balance of Section 3.8 and is whatever that balance settles at. The transient figure is the physically meaningful one, and that it exceeds the industrial floor by a factor of 2.7 suggests either that the kinetic constants of Table 8 are too slow or that the reference furnace runs with more carbon or longer residence than our base case. We report the disagreement rather than removing it, since removing it would mean fitting one solver to the other.

**Changed:** new Section 6.9 with Table 16; `paper/cross_check_ss_transient.py` added to the code package, and its heat-loss basis corrected along with the same setup in `run_validation.py`.

### R2-5. Page 2, line 12. Please mention that India, the largest DRI producer, uses mainly coal-based rotary kilns.

Added, with the point that this matters for the present work: coal-based kiln DRI differs from gas-based shaft DRI in both carbon content and gangue chemistry, so the feedstock reaching a future smelter in India is not the material most published work is based on.

**Changed:** Section 1, first paragraph.

### R2-6. Page 10, line 13. What do "BP grades" mean?

They are the two simulated hydrogen DRI compositions smelted by Bae and Park, at 85 % and 88 % metallisation. The abbreviation was never expanded. It now is, at first use.

**Changed:** Section 3.2, paragraph following Table 5.

---

## Reviewer 3

> The paper presents an interesting modelling work resulting in the development of a model coupling stationary and transient modules of electric smelting furnace that surely is one of the current hot topics of iron and steelmaking sector.

### Abstract

#### R3-1. When it is stated that "the steady-state and transient models are in good agreement" do you mean that the two models are in good agreement between them or with literature? If it means "between them", no direct comparison between them is presented; therefore please add a comparison under the same operating conditions.

The sentence meant agreement with the literature, but the reviewer is right that it does not say so and that no comparison between the two modules existed anywhere in the paper. Both have been fixed: the abstract now states what is compared with what, and the comparison between the modules has been added as the new Section 6.9, described under Reviewer 2's comment above. Eight of ten quantities agree within 10 %; slag FeO does not, for a reason that is explained rather than removed.

**Changed:** abstract paragraph 4, new Section 6.9 and Table 16.

#### R3-2. Please improve the kinetic-limitations sentence. As written, it seems to say that the limits are derived from the model results, whereas Section 3.5 only shows that equilibrium predictions deviate from industrial data. Please make clear that these limits are empirical constraints calibrated on literature data. Please also make clear that "kinetic model based on first-order mass transfer control" refers only to the transient module.

Both points accepted, and the paragraph has been rewritten. It now says that the measurements sit away from equilibrium, that the model therefore carries three empirical constraints fitted to published data and not derived from the model, that those constraints contain no rate, residence time or interfacial area, and that first-order mass-transfer kinetics belongs to the transient solver alone. Section 3.5 has been retitled to match, as discussed under Reviewer 2's fourth comment.

**Changed:** abstract paragraph 3, Section 3.5 heading and opening.

### Introduction

#### R3-3. Please correctly order the references (first cited first in the list). This is a comment for the whole paper.

Done. The reference list is now in order of first citation throughout. Four references have been added in the course of the revision, so the list has grown from 40 to 44 entries and every citation number in the text has changed.

**Changed:** reference list and all in-text citations.

#### R3-4. At page 2, line 23, it is written "and the associated FeO contents above 20 wt % incur a substantial loss of iron yield" but this value is common also in scrap-based steelmaking because although it leads to decrease of metallic yield it allows having a better slag viscosity and suitable foaming. Therefore please improve the sentence, maybe better explaining that the main problem is the significant increase of the amount of slag.

Accepted, and the reviewer is right on the metallurgy. The sentence has been rewritten to say that slag FeO above 20 wt % is ordinary in scrap-based steelmaking, where it lowers viscosity and supports foaming and the iron it ties up is accepted in return, and that the difficulty with high-gangue DRI is the quantity of slag a basicity near 2 demands rather than the FeO level itself.

**Changed:** Section 1, second paragraph.

### Literature review

#### R3-5. In Section 2.3, please add also the following work, since it refers to a stationary ESF model applied for slag evaluations: Matino, I., Branca, T. A., Guzzon, M., & Colla, V. (2026, May). Electric Smelting Furnace Flowsheet Model for Future Slag Investigations. In AISTech Conference (p. D031S037R001). AIST.

Added, with a sentence distinguishing its scope: it addresses the downstream use of the slag rather than the furnace interior.

**Changed:** Section 2.3, final paragraph; reference 14.

### Model formulation

#### R3-6. Please improve the sentence on the basis of 1000 kg of contained iron: define explicitly what is "contained iron", and clarify that results are normalized to a per-tonne of hot metal basis, since 1000 kg of contained Fe does not correspond to 1000 kg of hot metal.

Both points accepted. The abstract now defines contained iron as the iron in the feed in both metallic and oxide form and states that results are normalised per tonne of tapped hot metal. The new Section 3.10.1 gives the relation quantitatively: 1000 kg of contained iron yields about 1043 kg of hot metal in the representative case, so the two bases differ by about 4 %.

**Changed:** abstract paragraph 2, new Section 3.10.1.

#### R3-7. Figure 1. Are the numbers related to "slag" and "hot metal" referred to the amount of liquid slag and metal inside the furnace? Please also include the flow rates of slag and hot metal inside the figure and not only in the "LIVE KPIs". Moreover, please complete "Water-cooled p", which is cut by "LIVE KPIs".

Yes, they are the liquid inventories held in the furnace, and the figure did not say so. All three points are fixed. The bath labels now read "SLAG in furnace" and "HOT METAL in furnace" with the inventory, and each carries a second line giving the tapping rate in t/h, with the slag also in kg/tHM. The truncated label now reads "Water-cooled panels" on two lines inside the drawing area.

**Changed:** Figure 1, regenerated; `schematic.py`.

#### R3-8. Table 4. Slag basicity is 1.07 in Figure 1 and 1.10 in Table 4. If 1.10 is the target and 1.07 the computed value, please state this explicitly to avoid misunderstanding.

That is exactly the position, and the submitted version did not distinguish inputs from computed values anywhere. Table 4 is now labelled as containing only inputs, the basicity entry is labelled as a target, and a new Table 5 gives the computed values: 1.092 at steady state and 1.073 at the end of the transient campaign. The figure label now reads "B2 1.07 (computed)".

**Changed:** Table 4 caption and entries, new Table 5, Figure 1.

#### R3-9. Table 4. Off-gas temperature is not consistent with the one in Figure 1.

Our first answer to this was that the two are different temperatures at different places, the 1450 degC being the uptake temperature and the 1722 degC the freeboard temperature above the bath before the gas cools on its way out. We withdraw that answer. On checking the figure after it was questioned a second time, the 1722 degC proved to be an artefact: the freeboard rule made the gas hotter than the bath that heats it, and the roof hot face hotter than the bath as well. Item A7 above sets out the fault and the correction in full. The freeboard gas temperature is now computed from an energy balance, given in the new Section 4.3.1, and comes to 1471 degC, which is 33 K below the slag and within 21 K of the 1450 degC uptake input. Table 4 names the input as the uptake temperature, Table 5 reports the computed value, and the note below Table 5 now states that the two agree rather than explaining away a difference that should not have been there.

**Changed:** Table 4, new Table 5 and its note.

#### R3-10. "Secondary voltage" is 420 V, tap voltage in Figure 1 is 430 V and it is 496 V in the term-by-term energy balance table. Please clarify the relation between secondary and tap voltage, and explain how the tap voltage can exceed the secondary voltage.

The relation was never stated and the code contained a genuine labelling error that this question exposed.

The 420 V is the nominal voltage between one electrode and the bath on the transformer's reference tap. The solver does not hold the furnace there; it selects the tap needed to deliver the power setpoint and reports the voltage of the tap it selects, so the operating voltage exceeds the nominal whenever the furnace runs above the duty of the reference tap. At 110 MW the selected voltage is 496 V, a tap ratio of 1.18; at the 97.8 MW stream-balance case it is 422 V, a ratio of 1.01.

The error the question exposed is that the parameter was documented in the code as a line-to-line voltage while being applied as a phase voltage, and the tap search ranged silently to three times nominal. The comment is corrected, the tap range is now an explicit named parameter, and the model reports the nominal voltage and the tap ratio alongside the operating voltage wherever a voltage is given.

**Changed:** new Section 3.7.1 final paragraph, Table 4 entry relabelled, Table 5; `electrical.py`, corrected comment, new `tap_range_factor`, and `secondary_voltage_nominal_V` and `tap_ratio_to_nominal` added to the output.

#### R3-11. Equation 13. Please correct superscript indices.

The equation was wrong, not merely mis-set, and we are grateful for the catch. As printed it carried both an oxygen activity and a separate square root of the reciprocal oxygen partial pressure, which counts the oxygen potential twice, since the activity already encodes it through the half-reaction. The equation has been replaced by the standard logarithmic form, which is also what the code evaluates and always did, so no computed result changes. The cap applied to the partition is now stated in the text as well as in Table 9.

**Changed:** Eq. (10) in the revised numbering, formerly Eq. (13), and the sentences either side of it.

#### R3-12. Table 6. Can you include the references for k0s and Eas?

We cannot, because there are none, and saying so is the honest answer. Table 8 now carries a provenance column recording for each reaction that the constants are estimated, and stating what each was fitted to, which is in every case a feature of the laboratory data of Bae and Park. The accompanying text states that these are the least certain quantities in the model and are intended for re-fitting against plant data. This is covered more fully under Reviewer 1's fifth comment.

**Changed:** Table 8 with a new provenance column, Section 3.8.

#### R3-13. Please check in the whole paper if compounds are well written with subscript indices (e.g. SiO2).

Checked and corrected throughout: 49 occurrences in the running text and tables now carry proper subscripts. Formulae inside equations were already set correctly.

**Changed:** throughout.

### Numerical solution

#### R3-14. Figure 2. Please check the equation numbers because they do not fit with the ones included in the text.

Covered under Reviewer 1's sixth comment. All cross-references in the flowchart have been checked against the manuscript and corrected.

**Changed:** Figure 2, redrawn.

#### R3-15. Figure 2. Please adjust the "yes: advance t" position in the "C. TRANSIENT SOLVER".

The label sat on the return path and was hard to read. It has been moved clear of the arrow. While redrawing we also found that the two loop boxes had been overflowing their borders, so panels B and C have been laid out again and the first and last lines of each loop now sit inside the box.

**Changed:** Figure 2, redrawn.

### Validation methodology

#### R3-16. Table 8. Some validation comparisons are not independent of the calibration: the equilibrium-basis SEC values depend on eta_th, which is calibrated on the published equilibrium-code SEC; [Si] at 1400, 1500 and 1525 degC are both calibration targets and validation comparisons; and [Si] at 1600 degC in the HSC balance is essentially set by the calibrated ceiling Sc. Therefore please exclude the calibration targets from the validation statistics or report them separately and recompute MARD, median and counts accordingly before comparing them with the 14.6-16.0 % disagreement between the equilibrium codes.

Accepted in full. This comment and Reviewer 2's third are the two that reshaped the paper.

On the first point, the reviewer identified the dependence correctly, and our response went further than the comment asked: rather than excluding the eta_th-dependent comparisons, we withdrew eta_th itself, for the reasons set out under Reviewer 2's third comment. There is now no fitted energy parameter for any comparison to depend on.

On the second and third points, the three silicon values used to fit the silica reduction Gibbs energy and the silicon in the stream balance, which is set by the calibrated ceiling, are now classified as compromised by fitting and excluded from the statistics. The manganese in that balance is excluded on the same grounds. The silicon at 1450 degC was not used in any fit and is retained.

The statistics have been recomputed as the reviewer asks. Every comparison now carries a role, and only those classified independent enter the headline figures. The result is 17 single-valued comparisons with a mean absolute relative deviation of 14.6 % and a median of 4.0 %, together with 31 interval tests of which 22 are satisfied, against the 8.53 % over 44 comparisons reported in the submitted version.

The separation turns out to matter in the way the reviewer evidently suspected. The five comparisons compromised by fitting agree to a mean of 6.8 %, against 14.6 % for the independent set, so counting them improved the headline figure without any improvement in the model. The gap is close to a factor of two. Section 6.1 now states this.

The comparison with the 14.6 to 16.0 % inter-code disagreement is accordingly made against the recomputed figure. The model still lies inside that band, but by a smaller margin than claimed.

**Changed:** Section 5.3 rewritten with a new column in Table 9, Section 5.4 extended with the classification scheme, Section 6.1 and Table 10 rewritten, conclusion 1; `run_validation.py` rewritten so that every comparison carries a basis, a role and a provenance, and the statistics are computed over the independent set only.

### Results and discussion

#### R3-17. Page 23 line 50. Why is Figure 7 cited here and presented only at page 32?

A typesetting error on our part. Figure 7 is now placed in Section 6.1 where it is first cited, and the duplicate reference to it in Section 6.7 has been removed.

**Changed:** Figure 7 moved to Section 6.1.

#### R3-18, R3-19, R3-21, R3-22 (first part). Why do the panel titles read "F1", "F2a", "F2b", "F9a", "F9b", "F10"?

Because the figures are generated by the same code that produces the software documentation, where they carry those numbers, and the internal numbering was left in the panel titles when the figures were renumbered for the paper. Every internal prefix has been stripped from the figure generator, so no panel title now carries one.

**Changed:** Figures 3 to 8, regenerated; `run_validation.py`.

#### R3-19 (second part). Figure 4. Please in the caption include "(left)" and "(right)" for referring to the two subfigures.

Added. The caption now identifies the left and right panels, as the Figure 5 caption already did.

**Changed:** Figure 4 caption.

#### R3-20. Section 6.7. It is not clear to me the comparison with the references; can you elaborate more?

On re-examining it, the comparison established less than the section implied, and the section now says so. Three published figures were quoted there, and two of them come from sulphide smelting furnaces rather than ironmaking units: the 35 to 45 % cooling-water share is from a six-in-line furnace for sulphide smelting, and the 97.96 % of heat into the slag is from a circular three-phase matte smelting furnace. Neither is a benchmark for an ironmaking open slag bath furnace. The submitted version had also explained away the difference in the cooling-water share by noting that a thinner roof hot face brings the model into the band, which is true but proves nothing when the band was never a specification for this furnace.

The section now states the provenance of each figure, reports them for orientation only, and excludes the cooling-water comparison from the statistics. What the section does establish is internal and needs no external reference: the slag wall hot face is computed at the slag liquidus and the freeze layer thickness follows from the same calculation without being prescribed.

**Changed:** Section 6.7; `run_validation.py`, the cooling-water comparison reclassified.

#### R3-22 (second part). Figure 6. I think it is not complete because the "slag wall hot face temperature" is not mentioned.

The curve was there but was identified only by the colour of the right-hand axis, with no legend, so the reviewer could not have known which curve was which. Both curves are now labelled and the figure carries a legend.

Redrawing it exposed a second problem. The hot-face temperature varies by only 0.3 K across the whole range, and the automatic axis scaling had magnified that into a dramatic curve, which was misleading. It is now drawn on an absolute scale with an annotation stating that the hot face is pinned at the slag solidification temperature of 1410 degC while a freeze layer is present. That is the physically interesting content of the curve, and the original plot concealed it.

**Changed:** Figure 6, regenerated, and its caption.

#### R3-23. Figure 7. Is it possible to show in figure how the "Points span three DRI grades at two metallisation ratios and four scrap blending ratios"?

Yes, and it should have been. Each group is now drawn as its own series with its own marker and colour, and the scrap blending series is annotated with the scrap fraction at each point, so the composition of the comparison set can be read from the figure.

**Changed:** Figure 7, regenerated; caption rewritten.

#### R3-24. Section 6.6 is missing.

Section 6.6, "Comparison against laboratory smelting", is present in our source and in the PDF we hold. We think this is a rendering fault in the file the reviewer received, possibly from the table that ends Section 6.5 breaking across a page. The section is unchanged in content. To reduce the chance of it happening again we have set the long tables to repeat their header rows and avoid breaking across pages, which also addresses the general comment below.

**Changed:** table formatting; no content change to Section 6.6.

#### R3-25. Table 10 omits some quantities reported in the "Complete stream-by-stream balance at 1600 degC" that show large deviations (e.g. hot metal S, P, off-gas, slag FeO, carburizer). Please include all compared quantities in Table 10 and revise the statement "seven of the ten stream quantities agree within 3.1 %" accordingly.

Accepted without reservation. The reviewer is right that quantities with large deviations had been left out, and the sentence was wrong in a second way as well: it said seven of ten where nine quantities were listed.

All fifteen quantities printed in the published balance are now in Table S4, which also carries a status column. The revised statement is that eight of the fifteen agree within 6 % and that the published specific energy falls inside the interval between the two model tiers.

Including the five omitted quantities was instructive, because two of them turn out to expose problems in the published balance rather than in the model. That balance prints 0.10 wt % phosphorus in its hot metal while its feed analysis contains no phosphorus at all, so it does not close on that element; and it prints 0.17 wt % FeO in its slag although the feed is stated as fully metallised and no iron is oxidised anywhere in it, so there is no path by which FeO can reach the slag. Those two comparisons are reported with the inconsistency documented and excluded from the statistics, on the stated ground that a comparison against an unsupported number tests nothing.

The remaining three are genuine disagreements and are counted. Hot metal sulphur deviates by 71.6 % and is the largest deviation in the whole paper: the published balance retains 88 % of the charged sulphur in the metal, while this model partitions it to the slag through Eq. (10) and predicts extensive desulphurisation. We note that the industrial furnace of [5,9] reports 0.025 to 0.030 wt % sulphur from a feed of similar sulphur content, which lies between the two and closer to this model. The off-gas deviates by 52.3 %, which follows from this model oxidising 6.5 kg of carbon where the published balance oxidises 4.6 kg; the comparison is now made with post-combustion and air ingress switched off so that both figures describe the same gas. The carburiser carbon agrees to 4.4 % once compared as carbon consumed rather than carbon charged, since the published balance carries no yield loss.

**Changed:** Table S4 rebuilt with all fifteen quantities and a status column, Section 6.2 text rewritten, conclusion 2; `run_validation.py`, five comparisons added and the off-gas and carburiser bases corrected.

#### R3-26. The tables at the end are difficult to read due to their splitting in different pages.

The long tables now repeat their header row on each page and are set not to break within a row. The two longest, the complete validation table and the detailed stream data, have been moved to the supplementary material, where they are set in landscape.

**Changed:** table formatting; supplementary material.

#### R3-27. Section 5.1 states "forty-four independent comparisons" drawn from six sources while Table 9 reports 52 benchmarks and the "validation summary table" 64. The numbers can be reconciled only by reading the "complete validation table". Please make the counts and terminology consistent across Section 5.1, Table 9 and supplementary tables. Please check also the number of sources.

The reviewer is right and the inconsistency was worse than it looked, because the three numbers came from three different builds of the analysis. We apologise for it.

The counting is now defined once, in Section 5.4, and applied everywhere. One physical quantity contributes one benchmark; a quantity reported on both energy tiers contributes its interval test and not the two tier values; every comparison carries a role, and only independent ones enter the statistics. Section 6.1 now opens with the full reconciliation: the supplementary table lists 95 rows, of which 50 are counted benchmarks and 45 are excluded, with each excluded group and its reason listed in Table 10 so that the arithmetic can be checked.

On the number of sources, the reviewer was right to ask. The submitted Table 7 listed six. There are seven, the seventh being the pilot-scale figures of Metso Outotec, which the submitted version used without listing as a source.

**Changed:** Section 5.4 with the counting rules, Section 6.1 opening paragraph and Table 10 rebuilt, Table S3 with the seventh source added.

#### R3-28. Complete validation table. Can you explain the reason of the highest RPDs?

Each is now explained where it appears, and in several cases the explanation was that the comparison was wrong rather than the model.

**29.97 % on dSEC/dT.** The reference of 20 kWh/tHM per 25 degC is published in conclusion 2 of [11]. The model gives 12.4 to 15.3 across its two energy tiers and is low by 23 to 38 %. This is the derivative on which the model agrees least well with that source, and we have made no attempt to close the gap by adjustment. It is reported in Table 11.

**22.72 % on dSEC/dMR.** The two sources disagree here as well, [13] giving 10.2 kWh/tHM per 1 % metallisation and [5,12] giving 12.0. The model gives 8.2 to 10.1 and just misses the first. Table 11 now reports it against both sources separately.

**28.02 % on dSEC/dscrap.** The model gives 2.83 to 3.49 kWh/tHM per 1 wt % against 2.7 from [13] and 2.5 from [5,12]. It lies outside both, by 0.13 and 0.33 kWh/tHM respectively.

**21.52 % on SEC at 1300 degC, 90 % MR, 16 % gangue.** Treated under R3-29 below; the comparison has been withdrawn because the condition is below the slag liquidus.

**67.42 % on laboratory slag FeO with a hot heel.** This compares a 500 g crucible melt against a model parameterised for a 116 MW furnace, and it is reported as indicative in Section 6.6. The deviation was 41.06 % in the first revision and widened when the freeboard correction of item A7 restored the open-bath radiation debit: the bath runs cooler, FeO reduction is slower, and more FeO is left in the slag. It is consistent with the kinetic constants of Table 8 being the least certain part of the model, which the new Section 6.9 also indicates from a different direction. We have left this comparison in the independent set rather than reclassifying it as orientation, which its own note would arguably justify, because moving it would improve the headline statistic and we would rather report the number than improve it by reclassification.

**25.32 % on heat to the cooling circuit.** Treated under R3-20 and R3-33. The reference comes from a sulphide smelting furnace and the comparison has been reclassified as orientation only.

**Changed:** Table 11 rebuilt, Sections 6.3, 6.6, 6.7 and 6.8.

#### R3-29. Why is SEC at 1300 degC for MR 90 %, 16 % gangue almost the same as SEC at 100 % MR, 1500 degC for DRI-A? This is strange since the conditions are completely different. It seems that in some cases the used parameters are not correct. Moreover, please consider that 1300 degC is below the slag liquidus (i.e. 1431 degC) computed from the model itself.

Two separate points, and the reviewer is right on the second.

On the first, we checked this carefully because the coincidence is as striking as the reviewer says: 554.078 against 554.077 kWh/tHM. It is a genuine coincidence and not a clamp or a stuck parameter. Computing the specific energy across the temperature range for that case gives 474.3, 491.5, 509.1, 528.7, 543.1, 553.6, 593.3, 658.3 and 715.9 kWh/tHM at 1250, 1300, 1350, 1400, 1431, 1450, 1500, 1550 and 1600 degC, a smooth monotonic curve with no plateau. These are the revised figures; the values the reviewer saw were these divided by the thermal utilisation factor that has since been withdrawn, which is why the submitted version printed 554.08 at 1300 degC. The two cases happen to meet because a lower temperature at higher gangue and lower metallisation offsets a higher temperature at lower gangue and full metallisation. We were glad to be asked, and the check is in the supplementary material.

On the second point the reviewer has identified a real fault. A balance computed below the liquidus of its own slag closes correctly but describes a condition no furnace can tap, and the submitted version reported it as a benchmark. The model now detects this: the computed slag and metal liquidus are compared against the tapping temperature, a warning is raised, a flag is set in the output, and the admissibility sweep counts such cases separately from failures. The 1300 degC comparison is withdrawn from the validation set and reported as a formally valid result at an inoperable condition. One of the 178 sweep configurations is of the same kind, a hot metal at 1380 degC with 0.5 wt % carbon.

**Changed:** Section 5.5 new paragraph, Section 6.10, supplementary material; `static_model.py`, liquidus check and `sub_liquidus` flag; `audit.py`, separate reporting; `run_validation.py`, the comparison reclassified.

#### R3-30. Why is Sensitivity dSEC/dC 8.3811 while in table "Sensitivity of specific energy consumption" it is 9.42?

Because the two were computed on different bases, and the supplementary table was the one at fault.

Table 11 was computed on the equilibrium basis, as its caption stated. The supplementary table computed the same derivative with the empirical limits active, which contradicts the rule stated in Section 5.2 that comparisons against equilibrium codes are evaluated with those limits disabled. Six of the seven sensitivities were affected; only the temperature derivative had been computed correctly.

The validation harness has been corrected so that all sensitivities are evaluated on the equilibrium basis, and the two tables now agree. The figures have changed again since, because the withdrawal of the thermal utilisation factor rescaled them, and the sensitivity is now reported as a range across the two energy tiers: 8.35 to 10.31 kWh/tHM per 1.0 wt % carbon.

We also owe the reviewer a correction on the reference value. The submitted paper compared against 10 kWh/tHM per 1.0 wt %, from [5,12]. The other source, [11], reports 12.15 kWh/tHM per 0.5 wt %, which is 24.3 per 1.0 wt %. The two published values differ by a factor of 2.4. Table 11 now reports the model against both, and Section 6.3 treats the disagreement as a result: it is far larger than the 14.6 to 16.0 % by which the same two codes differ on absolute specific energy, which suggests that derivatives test a thermochemical database more severely than absolute values do.

**Changed:** Table 11 rebuilt, Section 6.3 text; `run_validation.py`, sensitivity basis corrected.

#### R3-31. Why does Sensitivity dSEC/dgangue have literature value of 16.5 while in Table 11 it is "within range" 13-20? And the result is 15.6711 while still in Table 11 it is 15.5?

The reviewer has caught us contradicting our own protocol. Section 5.1 stated that published ranges are reproduced verbatim and are not widened, and then the supplementary table compared against 16.5, the midpoint of the published 13 to 20. It is now an interval test against 13 to 20, as the body of the paper always had it. The small difference between 15.67 and 15.5 was the same basis error as in R3-30 and has gone with it.

The question also exposed an ambiguity we had not noticed. The source does not say whether its 1 wt % of gangue refers to the ore or to the DRI, and because removing oxygen concentrates the gangue the two differ by about a third. Both are now computed and reported: 13.78 to 17.02 kWh/tHM per 1 wt % in the DRI, and 18.11 to 22.36 per 1 wt % in the ore. Both overlap the published range. The ore-basis figures required constructing two DRI analyses from stated ore gangue contents, which is disclosed in Table S3 and marked in the supplementary data.

**Changed:** Table 11, Section 6.3; `run_validation.py`, interval test and the ore-basis reconstruction.

#### R3-32. For the literature value 762.6 related to Dynamic 7 h campaign Operating SEC, can you clarify better what is the reference?

It is the Metso Outotec pilot-scale figure for low-grade hydrogen-DRI smelting, quoted in [13] together with a slag generation of 223.9 kg/tHM. The submitted version labelled it only as "reported pilot-scale data" and gave no citation, which was not good enough.

Checking it produced a more serious finding than the missing citation. The source that quotes it states that the reported data include no information on DRI metallisation, smelting temperature, hot metal carbon or feed gangue, so the operating point behind the number is unknown; and [13] tabulates it at 80 % metallisation, whereas we were comparing it against a campaign at 94 %. The comparison was therefore unsound regardless of the citation.

The campaign is now placed in the Tenova design envelope, which is a published range for this duty, and the pilot figure is reported separately as a check on magnitude with its unknown conditions stated: a run at 80 % metallisation gives 980 kWh/tHM against the pilot 762.6, a difference of 29 %, reported without interpretation.

**Changed:** Section 6.8, Table S3 with the seventh source added; `run_validation.py`, the comparison reclassified.

#### R3-33. Why is Dynamic 7 h campaign Heat to cooling circuit compared with a single value (i.e. 40 % coming from 35-45 % range), while in Section 5.1 it is stated "Published ranges are reproduced verbatim throughout and are not widened"? A similar issue concerns [Si] at 1500 compared with a single value of 0.33 wt % although Table 12 reports a range of 0.30-0.36 wt %.

Both are contradictions of our own stated protocol and both are corrected.

The cooling-water share is now an interval test against the published 35 to 45 %. The model gives 29.9 %, which falls outside it. We report that rather than concealing it, and Section 6.7 explains that the published band comes from a six-in-line sulphide smelting furnace, so the comparison is reported for orientation and excluded from the statistics.

The silicon at 1500 degC is now an interval test against the published range. Checking the source showed that two ranges appear in it: its results text gives approximately 0.3 to 0.4 wt % at that temperature across the three DRI grades, and its conclusion 1 gives 0.30 to 0.36 wt % at base conditions. Table 12 now gives the first and notes the second; the model value of 0.345 wt % satisfies both.

**Changed:** Section 6.7, Table 12 with a provenance column, Section 6.4; `run_validation.py`, both comparisons converted to interval tests.

---

## Summary of changes to the program code

The code is released with the paper, so changes to it are listed here. All are in the supplied package.

| File | Change | Comment addressed |
|---|---|---|
| `static_model.py` | `thermal_utilisation_efficiency` default changed from 0.887 to 1.0; the fitted tier withdrawn | R2-3 |
| `thermo.py` | `a_SiO2` corrected to the first power; `SiO2_C` Gibbs A term refitted to 596 200 J/mol | A6 |
| `web/esf_console.html` | the same silica correction and refitted Gibbs term in the browser engine; reporting factor set to unity | A6, R2-3 |
| `gui/esf_gui_tk.py`, `gui/esf_streamlit.py` | thermal utilisation default changed from 0.887 and 0.86 to unity, so neither GUI overrides the engine | R2-3 |
| `docs/THEORY.md`, `docs/VALIDATION.md`, `docs/HELP.md` | brought into line with the engine: the withdrawn factor removed, the silica expression and silicon values corrected, the headline statistics updated | A6, R2-3, R3-16 |
| `paper/verify_manuscript.py` | new; recomputes all 131 quantitative claims in the manuscript against the engine | all |
| `paper/verify_code_claims.py` | new; exercises all 68 code changes claimed here and fails if any is absent or misbehaves | all |
| `static_model.py` | slag and metal liquidus checked against tapping temperature; warning raised and `sub_liquidus` flag set | R3-29 |
| `static_model.py` | `Hearth_power_density_kW_m2`, `Operating_resistance_mohm`, `Slag_resistance_mohm`, `Slag_liquidus_C` and `Slag_superheat_C` added to the output | R2-1 |
| `static_model.py` | convergence declared at the tolerance the iteration exits on, 1e-6, instead of 1e-4 | R1-0 |
| `electrical.py` | `secondary_voltage_V` comment corrected from line-to-line to phase; `tap_range_factor` made explicit; nominal voltage and tap ratio added to the output | R3-10 |
| `dynamic_model.py` | `summary_window_frac` added; one averaging window applied to every mean; both bases reported | R1-9 |
| `run_validation.py` | all sensitivities evaluated on the equilibrium basis | R3-30, R3-31 |
| `run_validation.py` | interval tests used wherever a source publishes a range | R3-31, R3-33 |
| `run_validation.py` | every comparison carries a basis, a role and a provenance; statistics computed over independent comparisons only | R3-16, R3-27 |
| `run_validation.py` | five quantities added to the stream balance; off-gas and carburiser bases corrected | R3-25 |
| `run_validation.py` | ore-basis gangue reconstruction added | R3-31 |
| `run_validation.py` | internal figure-number prefixes stripped from all panel titles | R3-18, R3-19, R3-21, R3-22 |
| `run_validation.py` | silicon figure drawn on both bases with reference provenance distinguished | R3-19 |
| `run_validation.py` | parity plot drawn as separate labelled series | R3-23 |
| `run_validation.py` | freeze-lining figure given a legend and an absolute right-hand axis | R3-22 |
| `audit.py` | sub-liquidus cases counted and reported separately from failures | R3-29 |
| `schematic.py` | bath labels distinguish inventory from tapping rate; truncated label completed | R3-7 |
| `make_flowchart.py` | all cross-references corrected; panels B and C laid out again | R1-6, R3-14, R3-15 |
| `cross_check_ss_transient.py` | new; runs the two solvers under identical conditions | R2-4c, R3-1 |
| `dynamic_model.py` | freeboard gas temperature obtained from an energy balance solved by bisection, replacing the mixing rule that entered the cooled roof as a heat source | A7 |
| `dynamic_model.py` | freeboard composition computed from the gas streams instead of prescribed, so the grey-gas emissivity matches the atmosphere the furnace actually has | A7 |
| `dynamic_model.py` | open-bath radiation debit bounded by the duty the cooled panels remove, net of arc radiation | A7 |
| `dynamic_model.py` | post-combustion temperature rise no longer capped at 150 K, a cap that was active at every step | A7 |
| `dynamic_model.py` | rated power of the transient base case raised from 112 to 116 MW so the controller is not saturated | A7 |
| `dynamic_model.py` | `offgas_loss_MW` renamed `offgas_enthalpy_MW`; it is an enthalpy flow past the uptake, not a bath-side debit, and the reason is stated in the code | A7 |
| `web/esf_console.html` | the same freeboard balance implemented in the browser engine, which carried its own copy of the mixing rule | A7 |
| `audit.py` | slag-metal inversion test compares the two traces at the same instant, and treats an inversion as inoperable only when the slag has fallen below its liquidus | A7 |
| `run_validation.py`, `cross_check_ss_transient.py` | two-solver comparison put on a single heat-loss basis | R2-4c, A7 |
| `paper/make_paper_figures.py` | new; regenerates Figures 1 and 8 from the current model state so they cannot drift from the text | A7 |

The admissibility sweep was re-run after every change. All 178 configurations remain admissible, now at the stricter convergence tolerance, with one configuration flagged as below the hot metal liquidus.

Two further checks accompany the package and are the reason we can make the statements above with confidence. `verify_manuscript.py` recomputes every quantitative claim in the manuscript from the engine and fails on any mismatch; it currently passes on 135 claims. `verify_code_claims.py` exercises every code change listed in the table above, by running the code rather than reading it, and fails if any claimed behaviour is absent; it currently passes on 68 claims. Writing the second of these caught a real gap: the withdrawal of the thermal utilisation factor had been applied to the Python engine but not to the browser console or to either graphical interface, each of which carried its own default and would have continued to report the withdrawn tier. That has been corrected and is now checked automatically.
