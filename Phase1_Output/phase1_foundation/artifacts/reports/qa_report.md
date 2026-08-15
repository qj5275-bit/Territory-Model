# Phase 1 QA Report — Crosswalk and State Statistics Checkpoint

**Run ID:** `phase1_acs2024_b4f59c2a02_xw_29e5a007c6_v1_1_0`  
**Generated (UTC):** 2026-08-15T02:59:00+00:00  
**Status:** **COMPLETE WITH DOCUMENTED EXCEPTIONS — CHECKPOINT REVIEW REQUIRED**

## Sources and vintages

- Census: 2024 ACS 5-Year Detailed Table B19013, ZCTA geography, 2024 inflation-adjusted dollars, 90% MOE; SHA-256 `b4f59c2a023b40f150df20ad2a54a29d4d3daa6f1128e7a90981951a02983915`.
- HRSA: 2024 ZIP Code to ZCTA Crosswalk; workbook notes identify **Census TIGER 2023 ZCTA boundaries** and **June 2023 ZIP boundaries**; SHA-256 `29e5a007c6825a17336dde863ea35ae35de8b142fe224279f2ec241bd69a249f`.
- Source URLs are retained in `source_links.csv` and in the raw-data folder's `SOURCE_LINKS.md`.

## ACS reconciliation and identifier QA

- 33,774 physical rows = 1 header + 1 annotation + 33,772 data rows.
- 33,772 unique valid five-character ZCTAs; 2,577 leading-zero ZCTAs preserved; no duplicate ZCTA excess records.
- Income: 30,414 exact valid + 3,225 not computed (`-`) + 118 top open-ended + 15 bottom open-ended = 33,772.
- No missing/special value was converted to zero; no observation was imputed, capped, winsorized, or removed.

## Crosswalk schema and cardinality

- Raw HRSA rows / unique ZIPs: 41,061 / 41,061.
- ZIPs with nonblank ZCTA: 41,053; territory ZIPs with no ZCTA: 8.
- Unique crosswalk ZCTAs: 33,790.
- ZCTAs linked to one ZIP: 29,266; linked to multiple ZIPs: 4,524.
- Join types: {'Spatial join to ZCTA': 7263, 'Zip matches ZCTA': 33788, 'populated ZCTA, missing zip': 2, 'territory zip, no ZCTA available': 8}.

The HRSA source is already resolved to one record per ZIP and provides a categorical join method, not address/population allocation weights. This limitation is recorded as a warning rather than concealed.

## State-resolution hierarchy

1. Select the unique state from an HRSA `Zip matches ZCTA` record where ZIP equals the canonical ZCTA.
2. If absent, select the state from an exact-code special source record where ZIP equals ZCTA.
3. If absent, select only when all retained ZCTA relationships have one unique state.
4. Otherwise leave unresolved; never select the first row or infer from digits.

Results: 33,770 of 33,772 ACS ZCTAs resolved (99.9941%); 2 unresolved; 2 cross-state relationships assigned by direct-match priority and flagged. The cross-state ZCTAs are 45202 and 45209 (OH selected; OH/KY candidate states retained). Unresolved ZCTAs are 32026 and 97258.

One HRSA source inconsistency is preserved and flagged: the special row whose ZIP/PO name indicates 32026 contains ZCTA field 32076. No silent correction was applied.

## Mapping exceptions

Exception counts by type: {'acs_zcta_state_unresolved': 2, 'cross_state_zcta_relationship': 2, 'crosswalk_zcta_not_in_acs': 20, 'source_field_inconsistency': 1, 'territory_zip_no_zcta': 8}. Every exception has a reason code and source-row trace in `mapping_exceptions.csv`.

## Income and uncertainty

- Exact income coverage: 90.06%.
- National exact-value-only median: 71916.5; mean: 78058.6311567042; p05: 38860.5; p95: 138567.75.
- Numeric MOE count: 30,414; relative-MOE median: 0.1570948313; relative MOE ≥50%: 2,983; ≥100%: 0.
- National IQR outliers flagged: 1,328; within-state IQR outliers flagged: 1,086. These are flags only.

## Within-state calculations

All 30,414 exact valid income records received a state rank. There are 52 state/jurisdiction summaries. The largest resolved geography is TX with 1,990 ZCTAs; the smallest is DC with 57.

Within each state, valid exact incomes are sorted ascending. Identical incomes share minimum rank and tie count. Midrank percentile is `(midrank - 1)/(n - 1)` for `n>1`, with `0.5` for `n=1`; empirical CDF is maximum tied rank divided by `n`. Bounds, monotonicity, tie consistency, and state separation passed automated checks.

## QA status

- PASS: 22
- WARN: 3
- BLOCK: 0

Warnings concern the absence of allocation weights, two unresolved ACS ZCTAs, and eight territory ZIPs with no ZCTA. There is no unexplained reconciliation difference and no blocking QA failure.

## Guardrails

No internal policy, premium, exposure, claim, or loss data were used. No candidate groups, final territories, territory counts, rating factors, causal conclusions, or regulatory-acceptability claims were produced.
