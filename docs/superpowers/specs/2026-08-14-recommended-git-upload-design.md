# Recommended Git Upload Design

## Goal

Publish a reproducible, reviewable version of `/Users/amber/Desktop/Territory` to `https://github.com/qj5275-bit/Territory-Model.git` without uploading raw source data or bulky generated datasets. Ignored files remain unchanged and available locally.

## Repository state

- Local repository: `/Users/amber/Desktop/Territory`
- Branch: `main`
- Remote: `origin` → `https://github.com/qj5275-bit/Territory-Model.git`
- Remote state at design time: empty (0 branch/tag refs)
- Current local state at design time: no commits and no staged files

## Content to track

The first upload will track:

- root project documentation: `COMPLETION_REPORT_LOG.md` and `pet_insurance_territory_modeling_project_brief.md`;
- source provenance: `Data/Crosswalk/SOURCE_LINKS.md`;
- reproducible pipeline materials: `README.md`, `requirements.txt`, configuration, Python pipeline code, and tests;
- compact audit materials: data dictionary, decision log, output manifest, run metadata, source inventory, source links, QA CSVs, and Markdown reports; and
- the approved design and implementation-plan documents under `docs/superpowers/`.

## Content to keep local only

The following content will remain in `/Users/amber/Desktop/Territory` but will not enter Git history:

- all raw ACS files under `Data/HH Data/`;
- the HRSA XLSX under `Data/Crosswalk/`;
- generated tables under `Phase1_Output/phase1_foundation/artifacts/tables/`;
- row-level exception and outlier files under `Phase1_Output/phase1_foundation/artifacts/exceptions/`;
- checkpoint ZIP files and the provisional archive;
- macOS `.DS_Store` files; and
- Python caches, bytecode, and local virtual environments.

The `.gitignore` rules will be:

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

## Validation before the first commit

Before committing:

1. Verify every local raw-source hash still matches the completion log.
2. Confirm representative raw/generated paths are ignored with `git check-ignore`.
3. Confirm required code, documentation, QA, manifest, and report paths are not ignored.
4. Review the full staged-file list and sizes; reject any staged raw data, XLSX, ZIP, generated table, exception file, credential, or file larger than 25 MB.
5. Run the complete Phase 1 test suite using the locally retained raw inputs.
6. Confirm the completion log agrees with repository status.

## Commit and push flow

1. Create and validate `.gitignore`.
2. Stage only the approved tracked content.
3. Create the first local commit with message `Initialize Territory modeling project`.
4. Push `main` to `origin` without force.
5. Verify the remote branch points to the new commit.
6. Append a completion-history entry recording the commit ID, remote verification, tracked/ignored boundary, tests, and any unresolved authentication issue.
7. Commit and push that completion-report update as a second, small audit commit.

If authentication or a non-fast-forward condition prevents pushing, stop without force-pushing and preserve all local commits for recovery.

## Scope boundaries

- This operation changes Git metadata and publishes the approved tracked files only.
- It does not delete, move, transform, or upload ignored local data.
- It does not change the analytical checkpoint, approve candidate grouping, or generate new territories.
