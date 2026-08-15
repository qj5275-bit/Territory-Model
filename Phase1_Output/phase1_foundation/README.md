# Phase 1 External-Data Foundation

This package implements the Section 8 immediate assignment through the crosswalk/state-statistics checkpoint. It stops before candidate territory groupings, as required.

## Inputs

- `HH Data/ACSDT5Y2024.B19013-Data.csv`
- `HH Data/ACSDT5Y2024.B19013-Column-Metadata.csv`
- `HH Data/ACSDT5Y2024.B19013-Table-Notes.txt`
- `Crosswalk/ZIPCodetoZCTACrosswalk2024UDS.xlsx`

Source links, vintages, and checksums are recorded in `artifacts/source_links.csv`, `artifacts/source_inventory_manifest.csv`, and the raw crosswalk folder's `SOURCE_LINKS.md`.

## Reproduce

Requirements: Python 3.10+ and `openpyxl==3.1.5`.

From this package directory:

```bash
python3 -m unittest discover -s tests -v
python3 pipeline/phase1_with_crosswalk.py \
  --input-root "/path/to/Territory/Data" \
  --config config/phase1_config.json \
  --output-root artifacts \
  --clean
```

The pipeline opens all source files read-only, records their hashes before execution, verifies them again afterward, and writes derivatives only to the specified output directory. `--clean` refuses unsafe targets such as `/`, the input root, an ancestor of the input root, or a directory nested inside the input root.

## Principal outputs

- `artifacts/tables/clean_zcta_income.csv`: canonical ZCTA income, state mapping, rank, percentile, tie, and audit fields.
- `artifacts/tables/raw_zip_zcta_state_relationships.csv`: all 41,061 HRSA source records without arbitrary deduplication.
- `artifacts/tables/resolved_zip_zcta_state_mapping.csv`: implementation-oriented ZIP mapping with join method and exceptions.
- `artifacts/tables/resolved_zcta_state_mapping.csv`: one row per ACS ZCTA with assignment hierarchy, ambiguity, candidates, and reason code.
- `artifacts/tables/within_state_income_rank.csv`: calculated rank, midrank percentile, empirical CDF, and tie count.
- `artifacts/tables/state_summary.csv`: 52 state/jurisdiction summaries.
- `artifacts/exceptions/mapping_exceptions.csv`: unmatched, cross-state, no-ZCTA, vintage, and source-field exceptions.
- `artifacts/reports/qa_report.md`: complete QA findings and limitations.
- `artifacts/reports/phase1_checkpoint.md`: required checkpoint summary.
- `artifacts/output_manifest.csv`: checksums and row counts for generated artifacts.

## Current checkpoint result

- 33,770 of 33,772 ACS ZCTAs received a supportable state assignment.
- All 30,414 exact valid income records received within-state ranks.
- Two ACS ZCTAs remain unresolved and two cross-state ZCTAs remain explicitly flagged.
- QA result: 22 PASS, 3 WARN, 0 BLOCK.
- No internal experience, candidate territories, final territories, or rating factors were produced.
