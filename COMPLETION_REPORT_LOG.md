# Territory Project Completion Report Log

**Canonical location:** `/Users/amber/Desktop/Territory/COMPLETION_REPORT_LOG.md`  
**Current as of:** 2026-08-14 23:57 EDT  
**Latest report:** `CR-20260814-006`  
**Analytical checkpoint:** **COMPLETE WITH DOCUMENTED EXCEPTIONS — APPROVAL REQUIRED BEFORE CANDIDATE GROUPS**

## How to maintain this log

After every meaningful completion:

1. Verify the relevant outputs and confirm raw-source immutability.
2. Update **Current Snapshot**, including the unresolved-item register and next action.
3. Append one report to **Completion History**; never rewrite or delete an older report.
4. Use report IDs in the form `CR-YYYYMMDD-NNN`.
5. Give each open or historical issue exactly one status: `BLOCKED`, `NEEDS DECISION`, `WARNING`, or `RESOLVED`.
6. Never mark an item `RESOLVED` without citing the evidence or decision that resolved it.

## Current Snapshot

### Current project status

Section 8's immediate assignment has completed its external-data foundation through the crosswalk/state-statistics checkpoint. The pipeline used the 2024 ACS 5-Year B19013 income table and the HRSA 2024 ZIP-to-ZCTA crosswalk, preserved raw inputs unchanged, produced an auditable ZCTA-to-state mapping, calculated within-state ranks for all eligible exact-income rows, and issued a reproducible checkpoint package.

No internal policy, premium, exposure, claim, or loss data have been used. No candidate groups, final territories, territory counts, or rating factors have been produced. Candidate grouping remains paused until the checkpoint decisions below receive explicit approval.

### Current data structure

```text
/Users/amber/Desktop/Territory/
├── .git/                                        # local Git metadata; origin configured
├── COMPLETION_REPORT_LOG.md                     # this durable status/history log
├── pet_insurance_territory_modeling_project_brief.md
├── Data/
│   ├── HH Data/
│   │   ├── ACSDT5Y2020.B19013-{Data,Column-Metadata,Table-Notes}.*
│   │   ├── ACSDT5Y2021.B19013-{Data,Column-Metadata,Table-Notes}.*
│   │   ├── ACSDT5Y2022.B19013-{Data,Column-Metadata,Table-Notes}.*
│   │   ├── ACSDT5Y2023.B19013-{Data,Column-Metadata,Table-Notes}.*
│   │   └── ACSDT5Y2024.B19013-{Data,Column-Metadata,Table-Notes}.*
│   └── Crosswalk/
│       ├── SOURCE_LINKS.md
│       └── ZIPCodetoZCTACrosswalk2024UDS.xlsx
└── Phase1_Output/
    ├── phase1_foundation/
    │   ├── README.md
    │   ├── requirements.txt
    │   ├── config/phase1_config.json
    │   ├── pipeline/{phase1_pipeline.py,phase1_with_crosswalk.py}
    │   ├── tests/{test_phase1_pipeline.py,test_phase1_with_crosswalk.py}
    │   └── artifacts/
    │       ├── {data_dictionary,decision_log,output_manifest,source_inventory_manifest,source_links}.csv
    │       ├── run_metadata.json
    │       ├── tables/       # canonical income, raw/resolved mappings, ranks, summaries
    │       ├── exceptions/   # mapping, income, uncertainty, identifier, and outlier records
    │       ├── qa/           # QA checks and processing-stage row counts
    │       └── reports/      # checkpoint, QA, and crosswalk-input reports
    ├── phase1_foundation_checkpoint.zip
    └── archive/
        └── phase1_foundation_provisional_before_crosswalk.zip
```

Raw/source files remain under `Data/`. Generated tables, reports, exceptions, code, tests, and manifests remain under `Phase1_Output/`. This log is deliberately outside the generated package so a pipeline cleanup cannot erase it.

### Git repository status

- Local repository: `/Users/amber/Desktop/Territory`
- Branch: `main`
- Remote name: `origin`
- Remote URL: `https://github.com/qj5275-bit/Territory-Model.git`
- Remote state: `main` published; independent verification confirmed remote `main` and local `HEAD` both at `6763ae6baba8ac2224ecebecfb668cb58ad5b6cc` before this audit entry
- Published content: root commit `a5c71b1` (`Initialize Territory modeling project`) and audit commit `6763ae6` (`Record blocked Git upload attempt`)
- Upload state: `COMPLETE` for the approved code/docs/reports scope
- Authentication result: GitHub accepted HTTPS PAT authentication; no token or other secret was written to the project or this report

### Latest verified results

- Run ID: `phase1_acs2024_b4f59c2a02_xw_29e5a007c6_v1_1_0`
- Generated: 2026-08-15T02:59:00Z (2026-08-14 22:59 EDT)
- ACS reconciliation: 33,774 physical rows = 1 header + 1 annotation + **33,772 canonical ZCTAs**.
- Income reconciliation: **30,414 exact valid** + 3,225 not computed + 118 top open-ended + 15 bottom open-ended = 33,772.
- Crosswalk reconciliation: **41,061 rows / unique ZIPs** = 41,053 ZIPs with ZCTA + 8 territory ZIPs without ZCTA.
- State resolution: **33,770 resolved** + **2 unresolved** (`32026`, `97258`) = 33,772; coverage 99.9941%.
- Cross-state relationships: `45202` and `45209` include OH/KY relationships; OH was selected by direct ZIP=ZCTA priority and the ambiguity was retained.
- Within-state results: all **30,414** eligible exact-income rows ranked; **52** state/jurisdiction summaries produced.
- Automated QA: **22 PASS**, **3 WARN**, **0 BLOCK**.
- QA warnings: no allocation weights; 2 unresolved ACS ZCTAs; 8 territory ZIPs without ZCTA.
- Raw-source immutability: verified before and after the final pipeline run.
- Candidate groups produced: **No**.

### Source identity and provenance

- Census: 2024 ACS 5-Year Detailed Table B19013, ZCTA geography, 2024 inflation-adjusted dollars, 90% MOE.
  - Local: `/Users/amber/Desktop/Territory/Data/HH Data/ACSDT5Y2024.B19013-Data.csv`
  - SHA-256: `b4f59c2a023b40f150df20ad2a54a29d4d3daa6f1128e7a90981951a02983915`
- Crosswalk: HRSA 2024 ZIP Code to ZCTA Crosswalk; notes identify Census TIGER 2023 ZCTA boundaries and June 2023 ZIP boundaries.
  - Local: `/Users/amber/Desktop/Territory/Data/Crosswalk/ZIPCodetoZCTACrosswalk2024UDS.xlsx`
  - SHA-256: `29e5a007c6825a17336dde863ea35ae35de8b142fe224279f2ec241bd69a249f`
  - Download/provenance links: `/Users/amber/Desktop/Territory/Data/Crosswalk/SOURCE_LINKS.md`

### Unresolved-item register

| ID | Status | Item and impact | Evidence / resolution condition |
|---|---|---|---|
| U-001 | `BLOCKED` | Candidate 4/5/6 within-state grouping work cannot begin until checkpoint approval. | Section 8 checkpoint rule and decision `D009`; resolve only with explicit reviewer approval of the checkpoint decisions. |
| U-002 | `NEEDS DECISION` | Accept or revise HRSA's pre-resolved, unweighted mapping and its underlying TIGER 2023 ZCTA / June 2023 ZIP vintages. This affects the accepted mapping basis. | Checkpoint §10; decisions `D002`–`D003`. |
| U-003 | `NEEDS DECISION` | Accept or revise direct ZIP=ZCTA state priority for cross-state ZCTAs `45202` and `45209` (OH selected; OH/KY ambiguity retained). | Checkpoint §5 and §10; decisions `D004`–`D005`. |
| U-004 | `NEEDS DECISION` | Accept leaving `32026` and `97258` unresolved unless a second approved source is provided. Both have non-exact income, so no exact row is lost from ranking. | Mapping exceptions and decision `D006`. |
| U-005 | `NEEDS DECISION` | Accept excluding `250,000+` and `2,500-` open-ended values from exact-value ranks while retaining their bounds and directions. | Checkpoint §4, §6, and §10; decision `D007`. |
| U-006 | `NEEDS DECISION` | Accept percentile `(midrank-1)/(n-1)` for `n>1`, `0.5` for `n=1`, with identical incomes sharing rank and percentile. | Checkpoint §8 and §10; decision `D008`. |
| U-007 | `WARNING` | HRSA has no address/population allocation weights. One-to-many relationships therefore cannot be proportionally allocated from this source. | QA warning and crosswalk schema review. |
| U-008 | `WARNING` | ZCTAs `32026` and `97258` lack supported state assignments. | `resolved_zcta_state_mapping.csv` and `mapping_exceptions.csv`. |
| U-009 | `WARNING` | Eight territory ZIPs have no ZCTA in HRSA's file. | QA warning and `mapping_exceptions.csv`. |
| U-010 | `WARNING` | One HRSA special row is internally inconsistent: ZIP/PO name indicates `32026`, but its ZCTA field is `32076`; it was preserved and not silently corrected. | QA report and `mapping_exceptions.csv`. |
| U-011 | `RESOLVED` | The earlier missing-crosswalk blocker is closed. | HRSA workbook downloaded with source links and SHA-256; final run processed 41,061 rows. |
| U-012 | `RESOLVED` | State statistics previously blocked by the missing crosswalk are complete with documented exceptions. | 33,770 state-resolved rows, 30,414 exact rows ranked, 52 summaries, and 0 blocking QA failures. |
| U-013 | `RESOLVED` | First-commit scope was selected as code/docs/reports only; raw and bulky generated data remain local and ignored. | User approved “按推荐上传”; `.gitignore` passed red/green path tests and the 24-file staged allowlist passed safety review. |
| U-014 | `RESOLVED` | GitHub authentication was completed and the approved local commits were published to remote `main`. | User push completed without force; independent `git ls-remote` verification matched local `HEAD` and remote `main` at `6763ae6baba8ac2224ecebecfb668cb58ad5b6cc`. |

### Decisions required before candidate grouping

The reviewer must explicitly accept or revise all five analytical choices:

1. HRSA's pre-resolved/unweighted mapping and underlying 2023 boundary vintages.
2. Direct-match priority for `45202` and `45209`.
3. Keeping `32026` and `97258` unresolved absent another approved source.
4. Excluding open-ended income values from exact ranks.
5. The midrank percentile and tie formula.

Approval should be recorded in the decision log before any candidate scenarios are generated.

### Next planned work

1. Obtain and record analytical checkpoint approval or requested revisions.
2. If revisions are requested, update the mapping/ranking rules, rerun the full QA package, and append a new completion report.
3. Only after analytical approval, generate exploratory 4/5/6 within-state candidate grouping scenarios for sensitivity comparison, without splitting income ties and without labeling a scenario final.
4. Keep final territories and indicated rating factors out of scope until internal experience data and the later project stages authorize them.

## Completion History

### CR-20260814-001 — Provisional ACS-only foundation

- **Completed:** 2026-08-14 22:40 EDT (2026-08-15T02:40:25Z)
- **Run ID:** `phase1_acs2024_b4f59c2a023b_v1_0_0`
- **Status at completion:** `BLOCKED` for state-based analysis because no documented crosswalk was present.
- **Completed work:** Inventoried 2020–2024 source files; validated and ingested the 2024 ACS B19013 data read-only; preserved five-character ZCTAs; parsed exact, missing, open-ended, and MOE values; produced national diagnostics, exceptions, manifests, data dictionary, QA, tests, and rerun instructions.
- **Verification:** 33,774 physical rows reconciled to 33,772 canonical unique ZCTAs; 30,414 exact values; 2,577 leading-zero ZCTAs preserved; source immutability verified.
- **Files:** Historical package retained at `/Users/amber/Desktop/Territory/Phase1_Output/archive/phase1_foundation_provisional_before_crosswalk.zip`.
- **Unresolved at that time:** `BLOCKED` missing versioned ZIP/ZCTA/state crosswalk; `NEEDS DECISION` future mapping hierarchy, open-ended-value treatment, percentile formula, and tie handling.
- **Next action at that time:** Obtain a documented crosswalk, rerun mapping QA, and stop again for checkpoint review before candidate grouping.
- **Later resolution:** The crosswalk blocker was resolved in `CR-20260814-002`; the analytical decisions remain pending reviewer approval.

### CR-20260814-002 — Crosswalk/state-statistics checkpoint

- **Completed:** 2026-08-14 22:59 EDT (2026-08-15T02:59:00Z)
- **Run ID:** `phase1_acs2024_b4f59c2a02_xw_29e5a007c6_v1_1_0`
- **Status at completion:** **Complete with documented exceptions; checkpoint approval required.**
- **Completed work:** Downloaded and registered the HRSA 2024 crosswalk; added crosswalk/state-resolution processing; produced raw and resolved mappings, ZCTA-state assignments, within-state ranks/percentiles, 52 state summaries, mapping exceptions, source links, decisions, manifests, QA, tests, reports, and a reproducible checkpoint archive.
- **Verification:** 41,061 crosswalk rows reconciled; 33,770 of 33,772 ACS ZCTAs resolved; 30,414 eligible exact rows ranked; 22 PASS / 3 WARN / 0 BLOCK; both raw-source hashes reverified.
- **Files:** Current package at `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/`; checkpoint archive at `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation_checkpoint.zip`; source registry at `/Users/amber/Desktop/Territory/Data/Crosswalk/SOURCE_LINKS.md`.
- **Unresolved:** `NEEDS DECISION` U-002 through U-006; `WARNING` U-007 through U-010; candidate grouping remains `BLOCKED` under U-001.
- **Next action:** Reviewer accepts or revises the checkpoint decisions. Do not generate candidate groups before that decision is recorded.

### CR-20260814-003 — Durable completion-report log initialized

- **Completed:** 2026-08-14 23:08 EDT (2026-08-15T03:08:44Z)
- **Run ID:** Not applicable; no analytical rerun occurred.
- **Status at completion:** Log initialized; analytical checkpoint status unchanged.
- **Completed work:** Created the project-level completion-report log with a current snapshot, data structure, latest verified results, source hashes, unresolved-item register, required decisions, next work, and chronological history.
- **Verification:** Re-read the final checkpoint, QA report, decision log, run metadata, output manifest, source registry, and archived provisional reports; validated required facts and references before installation.
- **Files:** `/Users/amber/Desktop/Territory/COMPLETION_REPORT_LOG.md`.
- **Unresolved:** No analytical issue was closed by creating the log. U-001 through U-010 remain as shown in the current register.
- **Next action:** Record checkpoint approval or revisions, then append the next completion report after that work is verified.

### CR-20260814-004 — GitHub remote connected

- **Completed:** 2026-08-14 23:20 EDT (2026-08-15T03:20:12Z)
- **Run ID:** Not applicable; no analytical rerun occurred.
- **Status at completion:** Local repository connected to the empty GitHub remote; no commit or upload performed.
- **Completed work:** Configured `origin` for `/Users/amber/Desktop/Territory` as `https://github.com/qj5275-bit/Territory-Model.git`.
- **Verification:** `git remote get-url origin` matched the supplied URL; `git ls-remote origin --heads --tags` completed successfully and returned 0 refs; local branch remains `main` with no commits.
- **Files:** `/Users/amber/Desktop/Territory/.git/config` and `/Users/amber/Desktop/Territory/COMPLETION_REPORT_LOG.md`.
- **Unresolved:** `NEEDS DECISION` U-013 — first-commit tracking scope and `.gitignore`; analytical U-001 through U-010 are unchanged.
- **Next action:** Approve the tracked-file scope before any `git add`, commit, or push.

### CR-20260814-005 — Recommended Git upload prepared; authentication blocked

- **Completed:** 2026-08-14 23:30 EDT (2026-08-15T03:30:44Z)
- **Run ID:** Not applicable; no analytical rerun occurred.
- **Status at completion:** `BLOCKED` at GitHub authentication; local content preparation and commit completed, remote transfer did not begin.
- **Completed work:** Created and red/green-tested the recommended `.gitignore`; created local `.venv`; installed `openpyxl==3.1.5`; staged the explicit code/docs/reports allowlist; created root commit `a5c71b1` with message `Initialize Territory modeling project`.
- **Verification:** 14/14 unit tests passed; 24 staged files passed forbidden-path, credential-pattern, and 25 MB size checks; largest tracked file was 64,233 bytes; ACS and HRSA source hashes remained unchanged; remote had 0 refs before the push attempt.
- **Files:** `.gitignore`, the 24 approved tracked project files, local Git commit `a5c71b1`, and this completion-log update. Ignored raw/generated files remain present locally.
- **Unresolved:** `RESOLVED` U-013 (upload scope); `BLOCKED` U-014 (GitHub authentication). Analytical U-001 through U-010 are unchanged.
- **Next action:** Complete GitHub authentication without storing secrets in the repository, then push `main` without force and verify remote `main` equals local `HEAD`.

### CR-20260814-006 — Recommended Git upload completed

- **Completed:** 2026-08-14 23:57 EDT (2026-08-15T03:57:31Z)
- **Run ID:** Not applicable; no analytical rerun occurred.
- **Status at completion:** `COMPLETE` — approved code/docs/reports scope published to GitHub `main`.
- **Completed work:** Completed HTTPS PAT authentication and pushed the two prepared local commits to `https://github.com/qj5275-bit/Territory-Model.git` without force. Raw source data, generated tables/exceptions, archives, local environment files, and macOS metadata remained local and ignored.
- **Verification:** User push reported 43 objects written and remote branch `main` created; independent verification found local `HEAD` and remote `main` equal at `6763ae6baba8ac2224ecebecfb668cb58ad5b6cc`; 14/14 unit tests passed; the 24-file approved tracked scope remained intact; ACS and HRSA source SHA-256 values remained `b4f59c2a...3915` and `29e5a007...49f`; no token or other secret was written to the project.
- **Files:** GitHub remote `https://github.com/qj5275-bit/Territory-Model.git` and `/Users/amber/Desktop/Territory/COMPLETION_REPORT_LOG.md`.
- **Unresolved:** `RESOLVED` U-014 (GitHub authentication/upload). Analytical U-001 through U-010 are unchanged; candidate grouping remains blocked pending checkpoint approval.
- **Next action:** Obtain and record explicit analytical checkpoint approval or requested revisions before generating any candidate groups.

## Future Report Template

```markdown
### CR-YYYYMMDD-NNN — Short completion title

- **Completed:** YYYY-MM-DD HH:MM TZ (UTC timestamp)
- **Run ID:** Exact run ID, or “Not applicable”
- **Status at completion:** Complete / complete with exceptions / blocked
- **Completed work:** What changed, stated concretely
- **Verification:** Tests, reconciliations, hashes, review evidence
- **Files:** Exact paths created or modified
- **Unresolved:** IDs, statuses, impacts, and carried-forward items
- **Decisions:** Decisions made or still required, with owner/evidence
- **Next action:** One concrete next step and any gating condition
```
