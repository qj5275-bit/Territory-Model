# Recommended Git Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the reproducible code, documentation, compact audit artifacts, and project reports from `/Users/amber/Desktop/Territory` to the configured GitHub repository while keeping raw and bulky generated data local only.

**Architecture:** A root `.gitignore` enforces the approved tracking boundary. The workflow proves the ignore rules red/green, stages only an explicit allowlist, rejects forbidden paths, credentials, and oversized files, runs the Phase 1 tests, pushes the first content commit without force, then records and pushes an audit completion entry.

**Tech Stack:** Git 2.39+, GitHub HTTPS remote, Markdown, `.gitignore`, POSIX shell checks, Python 3.10+ `unittest`, `openpyxl==3.1.5`.

## Global Constraints

- Preserve every file under `/Users/amber/Desktop/Territory`; ignoring a file must never delete or move it.
- Track code, tests, configuration, documentation, source links, compact QA/decision/manifest artifacts, and Markdown reports.
- Keep `Data/HH Data/`, `Data/Crosswalk/*.xlsx`, generated `artifacts/tables/`, generated `artifacts/exceptions/`, ZIP archives, caches, bytecode, virtual environments, and `.DS_Store` out of Git.
- Reject any staged credential or file larger than 25 MB.
- Use only the configured `origin` URL `https://github.com/qj5275-bit/Territory-Model.git` and branch `main`.
- Never force-push. Stop on authentication failure or a non-fast-forward result.
- Do not change analytical methods, raw data, checkpoint decisions, or candidate-grouping status.

---

### Task 1: Enforce and verify the recommended tracking boundary

**Files:**

- Create: `/Users/amber/Desktop/Territory/.gitignore`
- Read: `/Users/amber/Desktop/Territory/docs/superpowers/specs/2026-08-14-recommended-git-upload-design.md`

**Interfaces:**

- Consumes: the approved tracked/ignored rules in the design specification.
- Produces: a root `.gitignore` whose behavior is validated against representative ignored and tracked paths.

- [ ] **Step 1: Run the failing ignore-behavior test**

Run from `/Users/amber/Desktop/Territory`:

```bash
test ! -e .gitignore
! git check-ignore -q 'Data/HH Data/ACSDT5Y2024.B19013-Data.csv'
! git check-ignore -q 'Data/Crosswalk/ZIPCodetoZCTACrosswalk2024UDS.xlsx'
! git check-ignore -q 'Phase1_Output/phase1_foundation/artifacts/tables/clean_zcta_income.csv'
```

Expected: the precondition passes and each `git check-ignore` returns nonzero because the desired rules do not exist yet.

- [ ] **Step 2: Create the minimal `.gitignore`**

Create exactly:

```gitignore
.DS_Store
**/.DS_Store
__pycache__/
*.py[cod]
.venv/

Data/HH Data/
Data/Crosswalk/*.xlsx

Phase1_Output/*.zip
Phase1_Output/archive/
Phase1_Output/phase1_foundation/artifacts/tables/
Phase1_Output/phase1_foundation/artifacts/exceptions/
```

- [ ] **Step 3: Run the green ignore-behavior test**

Run:

```bash
git check-ignore -q 'Data/HH Data/ACSDT5Y2024.B19013-Data.csv'
git check-ignore -q 'Data/Crosswalk/ZIPCodetoZCTACrosswalk2024UDS.xlsx'
git check-ignore -q 'Phase1_Output/phase1_foundation/artifacts/tables/clean_zcta_income.csv'
git check-ignore -q 'Phase1_Output/phase1_foundation/artifacts/exceptions/mapping_exceptions.csv'
git check-ignore -q 'Phase1_Output/phase1_foundation_checkpoint.zip'
! git check-ignore -q 'COMPLETION_REPORT_LOG.md'
! git check-ignore -q 'Phase1_Output/phase1_foundation/pipeline/phase1_with_crosswalk.py'
! git check-ignore -q 'Phase1_Output/phase1_foundation/artifacts/reports/phase1_checkpoint.md'
```

Expected: every intended local-only path is ignored and every intended tracked path remains eligible.

### Task 2: Validate, commit, and publish the approved project content

**Files:**

- Stage: `/Users/amber/Desktop/Territory/.gitignore`
- Stage: `/Users/amber/Desktop/Territory/COMPLETION_REPORT_LOG.md`
- Stage: `/Users/amber/Desktop/Territory/pet_insurance_territory_modeling_project_brief.md`
- Stage: `/Users/amber/Desktop/Territory/Data/Crosswalk/SOURCE_LINKS.md`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/README.md`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/requirements.txt`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/config/`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/pipeline/`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/tests/`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/artifacts/*.csv`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/artifacts/run_metadata.json`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/artifacts/qa/`
- Stage: `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation/artifacts/reports/`
- Stage: `/Users/amber/Desktop/Territory/docs/superpowers/`

**Interfaces:**

- Consumes: the validated `.gitignore` from Task 1 and locally retained Phase 1 inputs.
- Produces: the first remote `main` commit containing only the approved content boundary.

- [ ] **Step 1: Verify repository identity, remote emptiness, and raw hashes**

Run:

```bash
test "$(git branch --show-current)" = main
test "$(git remote get-url origin)" = 'https://github.com/qj5275-bit/Territory-Model.git'
test "$(git ls-remote origin --heads --tags | wc -l | tr -d ' ')" -eq 0
test "$(shasum -a 256 'Data/HH Data/ACSDT5Y2024.B19013-Data.csv' | awk '{print $1}')" = 'b4f59c2a023b40f150df20ad2a54a29d4d3daa6f1128e7a90981951a02983915'
test "$(shasum -a 256 'Data/Crosswalk/ZIPCodetoZCTACrosswalk2024UDS.xlsx' | awk '{print $1}')" = '29e5a007c6825a17336dde863ea35ae35de8b142fe224279f2ec241bd69a249f'
```

Expected: all checks exit 0.

- [ ] **Step 2: Run the full Phase 1 test suite**

Run from `/Users/amber/Desktop/Territory/Phase1_Output/phase1_foundation`:

```bash
python3 -m unittest discover -s tests -v
```

Expected: 14 tests pass with 0 failures and 0 errors.

- [ ] **Step 3: Stage the explicit allowlist**

Run from `/Users/amber/Desktop/Territory`:

```bash
git add -- \
  .gitignore \
  COMPLETION_REPORT_LOG.md \
  pet_insurance_territory_modeling_project_brief.md \
  'Data/Crosswalk/SOURCE_LINKS.md' \
  Phase1_Output/phase1_foundation/README.md \
  Phase1_Output/phase1_foundation/requirements.txt \
  Phase1_Output/phase1_foundation/config \
  Phase1_Output/phase1_foundation/pipeline \
  Phase1_Output/phase1_foundation/tests \
  Phase1_Output/phase1_foundation/artifacts/*.csv \
  Phase1_Output/phase1_foundation/artifacts/run_metadata.json \
  Phase1_Output/phase1_foundation/artifacts/qa \
  Phase1_Output/phase1_foundation/artifacts/reports \
  docs/superpowers
```

- [ ] **Step 4: Reject unsafe staged content**

Run:

```bash
git -c core.whitespace=-blank-at-eol diff --cached --check
! git diff --cached --name-only | rg -q '^(Data/HH Data/|Data/Crosswalk/.*\.xlsx$|Phase1_Output/.*\.zip$|Phase1_Output/archive/|Phase1_Output/phase1_foundation/artifacts/(tables|exceptions)/)'
! git grep --cached -nE '(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY)'
git diff --cached --name-only -z | while IFS= read -r -d '' path; do
  test "$(stat -f '%z' "$path")" -le 26214400
done
```

Expected: no whitespace errors, forbidden paths, credential patterns, or file over 25 MB.

- [ ] **Step 5: Review and record the exact staged list**

Run:

```bash
git diff --cached --stat
git diff --cached --name-status
```

Expected: only the explicit allowlist is staged. Stop if anything unexpected appears.

- [ ] **Step 6: Create the first content commit**

Run:

```bash
git commit -m 'Initialize Territory modeling project'
```

Expected: one root commit on `main`.

- [ ] **Step 7: Push without force and verify the remote commit**

Run:

```bash
GIT_TERMINAL_PROMPT=0 git push -u origin main
test "$(git rev-parse HEAD)" = "$(git ls-remote origin refs/heads/main | awk '{print $1}')"
```

Expected: push succeeds and local `HEAD` equals remote `main`. If authentication or non-fast-forward fails, stop without force-pushing.

### Task 3: Record and publish the upload completion report

**Files:**

- Modify: `/Users/amber/Desktop/Territory/COMPLETION_REPORT_LOG.md`

**Interfaces:**

- Consumes: the verified first content commit ID and test/push evidence from Task 2.
- Produces: completion report `CR-20260814-005` and a second audit commit on remote `main`.

- [ ] **Step 1: Update the current snapshot and append `CR-20260814-005`**

Record:

- first content commit ID;
- remote URL and successful remote-main verification;
- 14 passing tests;
- tracked/ignored boundary and raw-source hash verification;
- `U-013` as `RESOLVED` with the user's recommended-upload approval; and
- unchanged analytical checkpoint issues and next work.

- [ ] **Step 2: Validate the completion-log update**

Run:

```bash
test "$(rg -c '^### CR-[0-9]{8}-[0-9]{3}' COMPLETION_REPORT_LOG.md)" -eq 5
rg -q '^### CR-20260814-005 — Recommended Git upload completed$' COMPLETION_REPORT_LOG.md
rg -q '^\| U-013 \| `RESOLVED`' COMPLETION_REPORT_LOG.md
rg -q 'Initialize Territory modeling project' COMPLETION_REPORT_LOG.md
if rg -q '[T]BD|[T]O DO|[P]LACEHOLDER|[F]IXME' COMPLETION_REPORT_LOG.md; then exit 1; fi
```

Expected: five report entries, U-013 resolved with evidence, no placeholders.

- [ ] **Step 3: Commit and push the audit update**

Run:

```bash
git add -- COMPLETION_REPORT_LOG.md
git -c core.whitespace=-blank-at-eol diff --cached --check
git commit -m 'Record recommended Git upload completion'
GIT_TERMINAL_PROMPT=0 git push origin main
test "$(git rev-parse HEAD)" = "$(git ls-remote origin refs/heads/main | awk '{print $1}')"
```

Expected: remote `main` equals local `HEAD` after the audit commit.

- [ ] **Step 4: Final repository verification**

Run:

```bash
test -z "$(git status --porcelain --untracked-files=no)"
test "$(git rev-list --count HEAD)" -eq 2
git log --oneline --decorate -2
git status --short --branch --ignored
```

Expected: two commits, no tracked-file changes, local `main` tracking and equal to `origin/main`; ignored raw/generated files remain present locally.
