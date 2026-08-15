# Pet Insurance Territory Modeling
## Actuarial Project Brief and Codex Execution Instructions

**Project status:** Phase 1 — external-data foundation  
**Immediate analytical scope:** 2024 ACS 5-Year B19013 median household income at the ZCTA level  
**Ultimate business objective:** Develop supportable, state-specific territory rating factors suitable for actuarial review and regulatory filing  
**Important constraint:** Do **not** use internal policy, premium, exposure, claim, or loss data during Phase 1

---

## 1. Purpose of This Document

This document is the governing project brief for the pet insurance territory modeling work. It provides:

- the business and actuarial objective;
- the role of external and internal data;
- the intended phased workflow;
- explicit instructions for the current phase;
- quality assurance and documentation requirements;
- reproducibility and coding standards; and
- guardrails against premature or unsupported actuarial conclusions.

Codex should treat this document as the primary execution specification. When a requirement is genuinely ambiguous and could materially change the actuarial result, Codex should document the issue and ask for a decision rather than silently selecting an assumption. For routine technical choices that do not alter the intended methodology, Codex may proceed using a reasonable, documented approach.

---

## 2. Project Objective

The long-term objective is to develop **state-specific geographic territories and territory rating factors** for pet insurance. The final factors should be:

- actuarially supportable;
- based on expected loss-cost differences rather than demographic characteristics alone;
- sufficiently credible and stable for prospective use;
- operationally implementable using policy ZIP codes;
- internally consistent within each state;
- explainable to management, actuarial reviewers, and regulators; and
- supported by a complete, reproducible filing record.

Territories may ultimately group ZIP codes or ZIP-based geographic units with similar expected pet insurance loss costs. Territory definitions and relativities will be evaluated separately by state because geographic cost levels, experience volume, regulation, and competitive considerations can differ materially across states.

Phase 1 is **not** intended to estimate final rating factors. Its purpose is to build and evaluate an external geographic segmentation candidate based on median household income, establish a robust ZIP/ZCTA/state crosswalk, and produce transparent candidate groupings for later testing with internal experience.

---

## 3. Actuarial Principles

All work should follow these principles:

1. **Risk relationship, not proxy assumption.** Median household income is an exploratory external variable that may correlate with veterinary utilization, treatment selection, local prices, or other geographic characteristics. It must not be presumed to cause loss-cost differences or to equal the appropriate rating relativity.
2. **Internal experience determines actuarial support.** Final territories and factors must ultimately be supported by internal frequency, severity, pure premium, and/or loss-cost analysis, with appropriate controls for mix of business.
3. **State-specific analysis.** Income ranks, candidate territories, model results, credibility, and filing selections must be assessed within state unless a separately justified multistate framework is approved.
4. **Prospective relevance.** Historical relationships must be evaluated for stability and suitability for the future rating period.
5. **Homogeneity and separation.** A useful territory structure should produce reasonable homogeneity within territories and meaningful, stable differences between territories.
6. **Credibility and stability.** Apparent differences based on limited exposure or volatile claims must be tempered, pooled, constrained, or otherwise treated appropriately.
7. **Parsimony.** Use no more complexity than is supported by the data and business need. Territory count is a model-selection decision, not a preset target.
8. **Operational integrity.** Territory definitions must be mappable from rating inputs available at quote, issuance, renewal, and filing implementation.
9. **Fairness and regulatory defensibility.** Potential proxy effects, prohibited factors, unfair discrimination concerns, and state-specific regulatory restrictions must be evaluated before adoption. An external socioeconomic variable is not automatically acceptable as a rating variable merely because it is predictive.
10. **Traceability.** Every material data transformation, exclusion, mapping decision, assumption, model choice, and manual override must be reproducible and documented.

---

## 4. Scope

### 4.1 Current scope: Phase 1

Phase 1 includes only external-data preparation and exploratory geographic segmentation:

- ingest the 2024 ACS 5-Year B19013 ZCTA-level data;
- identify and retain the median household income estimate;
- retain and assess the associated margin of error where available;
- standardize five-digit ZCTA identifiers;
- obtain or ingest a documented ZIP/ZCTA/state crosswalk appropriate for rating implementation;
- assign geographic units to states using an explicit, reproducible rule;
- calculate income ranks and percentiles within state;
- summarize data quality and state distributions;
- create **candidate** within-state territory groupings for comparison only after the clean base table has been reviewed; and
- produce analysis-ready data, QA reports, and documentation.

### 4.2 Explicitly out of scope for Phase 1

Do not:

- ingest or analyze internal loss, claim, premium, policy, or exposure data;
- estimate loss frequency, severity, pure premium, or indicated relativities;
- label income bands as final rating territories;
- select final territory counts;
- produce filing factors;
- infer causation from income;
- make regulatory acceptability claims;
- optimize territory definitions against internal outcomes; or
- overwrite raw source files.

---

## 5. Data Sources

### 5.1 Required Phase 1 source

**U.S. Census Bureau, 2024 American Community Survey 5-Year Estimates, Detailed Table B19013:** Median Household Income in the Past 12 Months (in 2024 inflation-adjusted dollars), for all five-digit ZIP Code Tabulation Areas in the United States.

Expected key fields include:

- ZCTA geographic identifier;
- geographic label/name;
- B19013 estimate for median household income; and
- B19013 margin of error, if included in the download.

Codex must verify the actual file metadata, table identifier, year, survey/product, geography, estimate column, and units rather than relying only on a filename.

### 5.2 ZIP/ZCTA/state mapping source

A separate crosswalk will generally be required because Census ZCTAs and USPS ZIP codes are not interchangeable. Use a source that is documented, versioned, and suitable for the analysis purpose. Record:

- source organization and URL or file provenance;
- release/effective date;
- geographic vintage;
- fields used;
- whether the relationship is one-to-one, one-to-many, or many-to-many;
- the allocation basis, if any (for example, address, population, residential ratio, or area); and
- the rule used to select a state or ZCTA when multiple matches exist.

Do not silently choose an arbitrary first match. Preserve the full raw relationship and create a separate resolved mapping with flags and reason codes.

### 5.3 Later internal sources — not authorized in Phase 1

Later phases are expected to use policy-level or appropriately aggregated internal experience, including as available:

- earned exposure;
- earned or written premium;
- claim counts;
- paid and incurred losses;
- allocated loss adjustment expense, if relevant;
- policy ZIP code and state;
- coverage and limit variables;
- deductible and reimbursement percentage;
- species, breed, age, and other approved risk characteristics;
- distribution channel, product/program, and time variables; and
- large-loss, catastrophe, recovery, and claim-development fields.

Their inclusion, valuation date, experience period, data definitions, and actuarial adjustments will be specified before Phase 2 begins.

---

## 6. Key Assumptions and Geographic Limitations

The following must be reflected in the analysis and documentation:

- A **USPS ZIP code** is a mail-delivery construct; a **Census ZCTA** is a generalized statistical area. They do not have a perfect one-to-one relationship.
- Some ZIP codes have no ZCTA, including certain PO Box, unique, military, or nonresidential ZIP codes.
- A ZCTA may cross state boundaries, and mapping sources may assign different states depending on the allocation basis.
- ZIP codes and ZCTA definitions change over time. Source vintage must be retained.
- ACS estimates are survey estimates and have sampling uncertainty. Margins of error should be preserved and summarized where available.
- Some ACS values may be missing, suppressed, unavailable, negative-coded, or represented by special symbols. These must be parsed explicitly rather than automatically treated as zero.
- Median household income is not a measure of veterinary price, pet ownership, claim propensity, or insured loss cost. It is only a candidate geographic descriptor in this phase.
- Within-state percentile is a relative rank within that state's available geography; it is not directly comparable to a national percentile and is not itself a rating factor.
- The unit used to develop a grouping may be a ZCTA, while the production rating key may be a USPS ZIP code. Both levels and the bridge between them must be retained.

---

## 7. Phased Workflow

### Phase 1 — External-data foundation and candidate segmentation

1. Inventory and validate source files.
2. Ingest ACS B19013 without modifying the raw source.
3. Parse, clean, and standardize ZCTA and income fields.
4. Preserve margins of error and Census metadata.
5. Ingest and evaluate the ZIP/ZCTA/state crosswalk.
6. Create both unresolved and resolved mapping tables with audit flags.
7. Build a canonical ZCTA-level income table.
8. Calculate within-state ranks, percentile measures, and descriptive statistics.
9. Produce QA reports and state-level distribution summaries.
10. After review, create multiple candidate grouping structures for sensitivity testing. These are candidates, not selections.

### Phase 2 — Internal experience integration

1. Establish a written data specification and experience-period definition.
2. Validate policy, exposure, premium, claim, and loss data.
3. Map policy ZIP codes to the Phase 1 geographic framework using effective-date-aware logic where feasible.
4. Quantify unmapped, ambiguous, and non-geographic ZIP exposure.
5. Build modeling records at an appropriate policy, exposure, or aggregated level.
6. Apply documented actuarial treatments such as claim development, trend, large-loss treatment, and on-level adjustments as required by the modeling objective.

### Phase 3 — Loss-cost modeling

1. Define target measures and exposure offsets.
2. Evaluate frequency and severity models and/or a pure-premium framework.
3. Fit loss-cost GLMs using approved controls for mix of business.
4. Test geographic candidates and alternative territory counts or structures.
5. Examine interactions only when credible, interpretable, and justified.
6. Use appropriate training, validation, temporal holdout, and diagnostic methods.
7. Compare predictive lift, deviance, residual patterns, calibration, stability, and operational complexity.

Potential model families may include Poisson or negative binomial frequency models, Gamma or inverse Gaussian severity models, Tweedie pure-premium models, or other methods justified by the data. Model family and link function must be selected from diagnostics and actuarial reasoning, not by convention alone.

### Phase 4 — Territory evaluation and refinement

1. Convert modeled geographic effects into interpretable candidate relativities.
2. Review exposure, claims, and loss-cost distributions within each territory.
3. Assess credibility, volatility, monotonicity where relevant, and temporal stability.
4. Identify sparse or anomalous areas and consider pooling or constraints.
5. Evaluate boundary effects and operational mapping exceptions.
6. Compare alternate territory counts and grouping algorithms.
7. Conduct fairness, proxy, legal, compliance, and state-specific regulatory review.

### Phase 5 — Selection, implementation, and filing support

1. Select state-specific territory definitions and factors using actuarial judgment supported by model results.
2. Apply credibility, tempering, capping, balancing, or revenue-neutral normalization as appropriate and document each adjustment.
3. Quantify premium impact and dislocation at policy and portfolio levels.
4. Produce final ZIP-to-territory implementation tables with effective dates and exception handling.
5. Create filing exhibits, methodology documentation, factor support, and reconciliation controls.
6. Establish monitoring for drift, emerging experience, mapping changes, and future refreshes.

No phase should be treated as automatic authorization to proceed to the next. Phase gates require review of the stated outputs and any material decisions.

---

## 8. Immediate Codex Assignment

### 8.1 First execution goal

Create a clean, reproducible Phase 1 analytical foundation and show data quality results **before** producing candidate territory groups.

### 8.2 Required first tasks

Perform the following in order:

1. **Inspect the workspace.** Identify candidate ACS and crosswalk files. Report filenames, formats, sizes, and apparent vintages. Do not assume the first CSV is correct.
2. **Validate the ACS source.** Confirm that it is 2024 ACS 5-Year Detailed Table B19013 and that the geography is all five-digit ZCTAs in the United States. Identify the estimate and margin-of-error columns.
3. **Create a data dictionary.** Record original field names, definitions, source, type, transformation, and final field names.
4. **Ingest raw data read-only.** Retain source files unchanged. Make the ingestion robust to common Census download layouts, including annotation or metadata rows when present.
5. **Standardize ZCTA.** Extract a five-character string and preserve leading zeros. Retain the original geography identifier and label.
6. **Clean income.** Convert the estimate to numeric using explicit rules for commas, blanks, suppression symbols, and Census special values. Never convert missing or suppressed values to zero.
7. **Preserve uncertainty.** Clean and retain the margin of error when available; derive a relative-MOE diagnostic where mathematically valid, but do not use it to alter income without an approved rule.
8. **Check uniqueness.** Verify whether there is exactly one B19013 record per ZCTA. Investigate and report duplicates before resolving them.
9. **Ingest the crosswalk, if provided.** Retain all raw relationships. Determine its direction and cardinality and document its allocation fields.
10. **Resolve state assignments.** Use an explicit hierarchy based on the best supported allocation field. Retain assignment method, ambiguity flag, candidate count, and reason code. Do not discard cross-border cases.
11. **Build a canonical ZCTA table.** At minimum include ZCTA, state, income estimate, income MOE, mapping status, ambiguity flag, source vintage, and transformation flags.
12. **Calculate within-state statistics.** For valid income values, calculate deterministic rank, percentile rank, empirical percentile or cumulative distribution measure, and state descriptive statistics. Clearly specify the percentile formula and tie handling.
13. **Produce QA outputs.** Complete every check listed in Section 9.
14. **Present a Phase 1 checkpoint.** Summarize findings, exceptions, and decisions required. Do not create final territories at this checkpoint.

### 8.3 Behavior when a required file is missing

If the ACS file is absent, stop data execution after producing a precise request for the required download. Do not fabricate data. If a crosswalk is absent, complete ACS-only cleaning and QA if possible, clearly mark state-based results as blocked, and specify the required crosswalk characteristics. Do not infer state solely from the first digit of a ZIP or ZCTA.

### 8.4 Candidate grouping work after the checkpoint

Only after the clean data and QA checkpoint are accepted, create a comparison set of candidate within-state groupings. The candidate set may include 4, 5, and 6 quantile-oriented groups as initial sensitivity scenarios, but these numbers are **not** predetermined final territory counts.

Candidate grouping work must:

- state the grouping algorithm exactly;
- explain tie handling and small-state behavior;
- avoid splitting identical income values merely to force equal record counts unless explicitly approved;
- show ZCTA count and, when later available, appropriate exposure weight by group;
- report income ranges, medians, and boundary values;
- identify discontinuities, tiny groups, or unstable cut points;
- retain scenario IDs and versioned mapping tables; and
- avoid terms such as “indicated factor” or “final territory” in Phase 1 outputs.

---

## 9. Required Phase 1 QA Checks

### 9.1 Source and schema QA

- Confirm Census year, product, table, geography, and units.
- Record row and column counts at each processing stage.
- Compare observed columns with expected columns.
- Retain a source-file checksum where practical.
- Record run timestamp and code/configuration version.

### 9.2 Identifier QA

- Count valid five-digit ZCTAs.
- Count malformed, blank, duplicated, and non-five-digit identifiers.
- Confirm leading zeros are preserved.
- List duplicate ZCTAs and their source rows.
- Reconcile unique ZCTA counts before and after cleaning.

### 9.3 Income QA

- Count valid, missing, suppressed, special-coded, zero, and nonpositive estimates separately.
- Report minimum, selected percentiles, median, mean, maximum, and outliers nationally and by state.
- Check for implausible parsing results.
- Summarize MOE and relative MOE where available.
- Identify states or ZCTAs with unusually high uncertainty.
- Do not winsorize, impute, cap, or exclude outliers without approval; initially flag them.

### 9.4 Mapping QA

- Report matched, unmatched, and ambiguous ZCTAs and ZIPs.
- Report one-to-one, one-to-many, and many-to-one relationship counts.
- List cross-state and multi-state relationships.
- Explain every resolution rule and quantify affected records.
- Preserve unmapped records in exception outputs.
- Compare state counts to reasonable source totals and investigate material anomalies.
- If weights are present, test whether they sum to their expected basis within tolerance.

### 9.5 Within-state calculation QA

- Report valid-income ZCTA count by state and excluded count with reasons.
- Verify percentile bounds and monotonicity.
- Verify deterministic results under ties.
- Confirm that state calculations do not inadvertently mix jurisdictions.
- Recalculate a sample independently or through assertions.
- Identify states or jurisdictions with too few observations for proposed candidate grouping counts.

### 9.6 Reconciliation QA

For every major table, provide a reconciliation such as:

`input records = retained records + excluded records + unresolved records`,

with mutually exclusive reason codes wherever possible. Any unexplained difference is a blocking QA issue.

---

## 10. Expected Phase 1 Outputs

Use clear, stable filenames. Exact file type may be adjusted to the environment, but CSV or Parquet should be used for machine-readable analytical tables and Markdown or HTML for reports.

1. **README / run instructions** — how to reproduce the Phase 1 pipeline.
2. **Data dictionary** — source-to-final field definitions and transformations.
3. **Source inventory and manifest** — provenance, vintage, checksums, and row counts.
4. **Clean ZCTA income table** — one auditable record per ZCTA where possible.
5. **Raw relationship crosswalk extract** — no arbitrary deduplication.
6. **Resolved ZIP/ZCTA/state mapping** — assignment method and exception flags included.
7. **Within-state income rank table** — rank, percentile, tie fields, and validity flags.
8. **State summary table** — counts, missingness, income distribution, and MOE diagnostics.
9. **Mapping exception table** — unmatched, ambiguous, cross-state, and special ZIP records.
10. **QA report** — all checks, reconciliations, warnings, and blocking issues.
11. **Phase 1 checkpoint memo** — concise actuarial interpretation, limitations, and decisions needed.
12. **Candidate grouping tables and comparison report** — only after checkpoint approval.

Machine-readable tables must contain stable keys, explicit types, documented units, and run/scenario version fields. Reports should distinguish facts, assumptions, analytical choices, and actuarial judgments.

---

## 11. Recommended Canonical Fields

The clean ZCTA-level table should include, where available:

| Field | Purpose |
|---|---|
| `zcta5` | Standardized five-digit ZCTA string |
| `geo_id_raw` | Original Census geographic identifier |
| `geo_label_raw` | Original Census geography label |
| `state_code` | Resolved two-character state or jurisdiction code |
| `state_assignment_method` | Rule/source used to assign state |
| `state_assignment_ambiguous` | Indicator for multiple plausible state assignments |
| `mapping_status` | Matched, unmatched, ambiguous, or exception status |
| `median_household_income` | Clean B19013 estimate in 2024 inflation-adjusted dollars |
| `income_moe` | B19013 margin of error, if available |
| `income_relative_moe` | MOE divided by estimate when valid |
| `income_value_status` | Valid, missing, suppressed, special-coded, or other status |
| `income_rank_in_state` | Deterministic within-state rank |
| `income_percentile_in_state` | Documented within-state percentile measure |
| `tie_count` | Number of records sharing the same income value within state |
| `acs_year` | 2024 |
| `acs_product` | ACS 5-Year Detailed Tables |
| `acs_table` | B19013 |
| `crosswalk_vintage` | Mapping release/effective vintage |
| `run_id` | Pipeline execution identifier |

Do not treat this list as permission to invent unavailable fields. Add fields when needed for auditability and document them.

---

## 12. Coding and Reproducibility Standards

- Use a scripted, rerunnable pipeline; do not rely on undocumented spreadsheet edits.
- Separate raw, interim, processed, report, and configuration artifacts.
- Treat raw inputs as immutable.
- Keep business rules in configuration or clearly named functions rather than scattered literals.
- Use relative project paths in code and avoid user-specific hard-coded paths.
- Preserve identifiers as strings where leading zeros matter.
- Use explicit schemas and validate types after ingestion.
- Write small, testable functions with descriptive names and concise documentation.
- Add assertions or automated tests for critical invariants, including uniqueness, reconciliation, valid state codes, and percentile bounds.
- Make tie-breaking and sorting deterministic.
- Set random seeds for any stochastic method.
- Log row counts, exceptions, warnings, source versions, and runtime parameters.
- Version scenario outputs and never silently overwrite an accepted result.
- Avoid unnecessary dependencies; record all required package versions.
- Keep analytical code separate from presentation code where practical.
- Ensure rerunning the same inputs and configuration produces the same outputs.
- Do not expose confidential internal information in logs or external services in later phases.

Before completing any phase, run the pipeline from a clean starting point and verify that all promised outputs can be regenerated.

---

## 13. Guardrails and Prohibited Shortcuts

Codex must not:

- choose a final territory count merely because 4, 5, or 6 groups were requested as candidate scenarios;
- convert income percentiles or income ratios directly into rating factors;
- describe income as an actuarially indicated loss-cost variable before internal validation;
- combine states when computing ranks unless specifically authorized;
- use national cut points while labeling the result “within-state”;
- treat ZIP codes and ZCTAs as interchangeable;
- discard ambiguous, unmatched, cross-state, PO Box, unique, or military ZIP records without reporting them;
- resolve one-to-many mappings by arbitrary row order;
- replace missing or suppressed income with zero;
- impute, cap, smooth, winsorize, or remove observations without a documented and approved rule;
- use internal experience during Phase 1;
- proceed past a material reconciliation failure;
- present correlation as causation;
- claim regulatory compliance without jurisdiction-specific review;
- alter source files; or
- make manual output edits that cannot be reproduced in code.

If a shortcut seems necessary, document the limitation, quantify its impact if possible, propose alternatives, and request approval.

---

## 14. Phase Gates and Decision Log

Maintain a decision log with at least:

- decision ID and date;
- issue or question;
- alternatives considered;
- selected approach;
- rationale;
- approver or decision owner;
- affected outputs; and
- whether rerunning prior work is required.

The minimum Phase 1 gate requires:

- validated ACS source;
- documented crosswalk or a clearly stated crosswalk blocker;
- clean and reconciled ZCTA income data;
- complete mapping and missingness diagnostics;
- correct within-state ranks/percentiles;
- reproducible code and run instructions;
- reviewed QA report; and
- an explicit decision before candidate groupings are treated as modeling inputs.

---

## 15. Definition of Done for the Immediate Assignment

The immediate assignment is complete when Codex has:

1. validated the available Phase 1 sources;
2. produced a reproducible clean ZCTA-level B19013 table;
3. produced and documented the best supportable state mapping available from the provided crosswalk;
4. calculated transparent within-state income rankings and percentiles;
5. completed all applicable QA checks and reconciliations;
6. provided the required machine-readable outputs and documentation;
7. explicitly listed unresolved records, limitations, and decisions needed; and
8. stopped at the Phase 1 checkpoint without selecting final territories or rating factors.

The deliverable should enable an actuary to review the data foundation, reproduce every result, and decide whether to authorize candidate grouping analysis and, later, internal loss-cost validation.

---

## 16. Required Checkpoint Summary Format

At the end of the immediate assignment, report:

1. **What was completed**
2. **Sources used and vintages**
3. **Record-count reconciliation**
4. **Key data-quality findings**
5. **Mapping coverage and exceptions**
6. **Income missingness and uncertainty findings**
7. **ZCTA counts and income distribution by state**
8. **Method used for ranks, percentiles, and ties**
9. **Files produced and how to reproduce them**
10. **Blocking issues or decisions required**
11. **Recommended next step — without selecting final territories**

Any result that is provisional because of missing or uncertain source data must be labeled prominently as provisional.
