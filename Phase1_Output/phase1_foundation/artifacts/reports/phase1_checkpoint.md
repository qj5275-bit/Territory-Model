# Phase 1 Checkpoint Memo — External Data Foundation

**Run ID:** `phase1_acs2024_b4f59c2a02_xw_29e5a007c6_v1_1_0`  
**Checkpoint status:** **COMPLETE WITH DOCUMENTED EXCEPTIONS — APPROVAL REQUIRED BEFORE CANDIDATE GROUPS**

## 1. What was completed

The 2024 ACS B19013 source and HRSA 2024 ZIP-to-ZCTA crosswalk were validated and processed read-only. A canonical ZCTA income table, raw and resolved crosswalk tables, auditable ZCTA-state assignments, within-state ranks/percentiles, state summaries, uncertainty diagnostics, exceptions, decision log, source links, QA checks, and rerunnable code were produced.

## 2. Sources used and vintages

The income source is 2024 ACS 5-Year Detailed Table B19013. The mapping source is HRSA's 2024 ZIP Code to ZCTA Crosswalk; its internal notes specify TIGER 2023 ZCTA boundaries and June 2023 ZIP boundaries. Source hashes are `b4f59c2a023b40f150df20ad2a54a29d4d3daa6f1128e7a90981951a02983915` and `29e5a007c6825a17336dde863ea35ae35de8b142fe224279f2ec241bd69a249f` respectively.

## 3. Record-count reconciliation

ACS: 33,774 physical rows = 1 header + 1 annotation + 33,772 canonical ZCTA rows. Crosswalk: 41,061 rows = 41,053 ZIPs with ZCTA + 8 ZIPs without ZCTA. Canonical mapping: 33,772 = 33,770 resolved + 2 unresolved.

## 4. Key data-quality findings

All ACS identifiers are valid and unique. All crosswalk ZIPs are unique and valid. Exact income is available for 30,414 ZCTAs; 3,225 are not computed, 118 are top open-ended, and 15 are bottom open-ended. The HRSA file contains one internally inconsistent special row involving 32026/32076; it is preserved and flagged.

## 5. Mapping coverage and exceptions

State assignment coverage is 99.9941%. ZCTAs 32026 and 97258 remain unresolved. ZCTAs 45202 and 45209 contain OH/KY relationships; OH is selected using the direct ZIP=ZCTA record and the alternate KY relationships remain flagged. Eight territory ZIPs have no ZCTA. The HRSA file is pre-resolved and has no allocation ratios; this is a documented limitation.

## 6. Income missingness and uncertainty findings

Exact income coverage is 90.06%. Numeric MOE and relative MOE are available for 30,414 exact-income rows. 2,983 have relative MOE ≥50%; none have relative MOE ≥100%. Open-ended values are excluded from exact-value ranks but retained with bound and direction.

## 7. ZCTA counts and income distribution by state

`state_summary.csv` contains counts, missingness, selected percentiles, median, mean, extrema, MOE diagnostics, and outlier flags for 52 states/jurisdictions. It reconciles to all 33,770 resolved ZCTAs. The two unresolved ZCTAs both have non-exact income and therefore do not remove an exact income from state ranking.

## 8. Method used for ranks, percentiles, and ties

Valid exact incomes are ranked ascending within resolved state. ZCTA controls deterministic record order, but identical income values are not split: they share minimum rank, midrank percentile, empirical CDF, and tie count. Percentile is `(midrank-1)/(n-1)` for `n>1`, otherwise `0.5`; empirical CDF is maximum tied rank / `n`.

## 9. Files produced and how to reproduce them

See `README.md` and `output_manifest.csv`. The final pipeline is `pipeline/phase1_with_crosswalk.py`; it requires Python 3.10+ and `openpyxl`. Inputs are opened read-only, their hashes are verified before and after execution, and outputs are regenerated in a separate directory.

## 10. Blocking issues or decisions required

There is no blocking reconciliation failure. Before authorizing candidate groupings, the reviewer should explicitly accept or revise: (a) HRSA's pre-resolved, unweighted mapping source and 2023 underlying vintages; (b) direct-match priority for the two cross-state ZCTAs; (c) leaving 32026 and 97258 unresolved unless a second approved source is provided; (d) exclusion of open-ended medians from exact ranks; and (e) the midrank percentile formula.

## 11. Recommended next step — without selecting final territories

Review and approve this checkpoint and decision log. Only after approval should 4/5/6 within-state candidate grouping scenarios be generated for sensitivity comparison. Those candidates will remain exploratory and will not be labeled final territories or indicated rating factors.
