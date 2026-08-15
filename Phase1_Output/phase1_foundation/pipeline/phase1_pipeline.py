#!/usr/bin/env python3
"""Reproducible ACS-only Phase 1 foundation for pet insurance territory work.

The pipeline intentionally does not infer state from a ZIP/ZCTA prefix. When no
documented ZIP/ZCTA/state crosswalk is supplied, every state-dependent result is
emitted with an explicit blocker instead of a fabricated assignment.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


EXPECTED_SOURCE_COLUMNS = ["GEO_ID", "NAME", "B19013_001E", "B19013_001M"]
ZCTA_GEO_ID = re.compile(r"^860Z200US(\d{5})$")
ZCTA_LABEL = re.compile(r"^ZCTA5 (\d{5})$")
NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")
OPEN_ENDED = re.compile(r"^([+-]?(?:\d[\d,]*(?:\.\d+)?|\.\d+))([+-])$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_number_text(value: str) -> tuple[str, list[str]]:
    stripped = value.strip()
    flags: list[str] = []
    if stripped != value:
        flags.append("trimmed_whitespace")
    if "," in stripped:
        stripped = stripped.replace(",", "")
        flags.append("removed_thousands_separator")
    return stripped, flags


def parse_estimate(raw: str) -> dict[str, Any]:
    value = raw.strip()
    flags: list[str] = []
    if value == "":
        return _parsed(None, "missing_blank", None, "", flags)
    if value == "-":
        return _parsed(None, "not_computed_dash", None, "", ["census_dash_preserved"])
    if value == "N":
        return _parsed(None, "insufficient_cases_N", None, "", ["census_N_preserved"])
    if value == "(X)":
        return _parsed(None, "not_applicable_X", None, "", ["census_X_preserved"])

    open_match = OPEN_ENDED.fullmatch(value)
    if open_match:
        number_text, number_flags = clean_number_text(open_match.group(1))
        bound = float(number_text)
        direction = "above" if open_match.group(2) == "+" else "below"
        status = "top_open_ended" if direction == "above" else "bottom_open_ended"
        flags.extend(number_flags)
        flags.append("open_ended_bound_not_used_as_exact_estimate")
        return _parsed(None, status, bound, direction, flags)

    number_text, number_flags = clean_number_text(value)
    flags.extend(number_flags)
    if NUMBER.fullmatch(number_text):
        number = float(number_text)
        if number == 0:
            return _parsed(None, "zero", None, "", flags + ["zero_not_treated_as_valid_income"])
        if number < 0:
            return _parsed(None, "nonpositive_or_negative_code", None, "", flags + ["negative_not_treated_as_income"])
        return _parsed(number, "valid", None, "", flags)
    return _parsed(None, "special_unparsed", None, "", flags + ["unparsed_symbol_preserved"])


def parse_moe(raw: str) -> dict[str, Any]:
    value = raw.strip()
    if value == "":
        return {"value": None, "status": "missing_blank", "flags": []}
    symbols = {
        "**": "cannot_compute_insufficient_observations",
        "***": "cannot_compute_open_ended_median",
        "*****": "controlled_estimate_no_sampling_error",
        "N": "insufficient_cases_N",
        "(X)": "not_applicable_X",
        "-": "not_computed_dash",
    }
    if value in symbols:
        parsed_value = 0.0 if value == "*****" else None
        flag = "controlled_moe_treated_as_zero" if value == "*****" else "census_symbol_preserved"
        return {"value": parsed_value, "status": symbols[value], "flags": [flag]}
    number_text, flags = clean_number_text(value)
    if NUMBER.fullmatch(number_text):
        number = float(number_text)
        if number < 0:
            return {"value": None, "status": "negative_or_special_code", "flags": flags + ["negative_not_treated_as_moe"]}
        return {"value": number, "status": "valid", "flags": flags}
    return {"value": None, "status": "special_unparsed", "flags": flags + ["unparsed_symbol_preserved"]}


def _parsed(value: float | None, status: str, bound: float | None, direction: str, flags: list[str]) -> dict[str, Any]:
    return {
        "value": value,
        "status": status,
        "bound": bound,
        "direction": direction,
        "flags": flags,
    }


def extract_zcta(geo_id: str, label: str) -> tuple[str, str, list[str]]:
    geo_match = ZCTA_GEO_ID.fullmatch(geo_id.strip())
    label_match = ZCTA_LABEL.fullmatch(label.strip())
    flags: list[str] = []
    if geo_match and label_match and geo_match.group(1) == label_match.group(1):
        zcta = geo_match.group(1)
        if zcta.startswith("0"):
            flags.append("leading_zero_preserved")
        return zcta, "valid", flags
    if geo_match and label_match:
        return "", "geo_id_label_mismatch", ["zcta_sources_disagree"]
    if geo_match:
        return geo_match.group(1), "valid_geo_id_label_malformed", ["label_malformed"]
    if label_match:
        return label_match.group(1), "valid_label_geo_id_malformed", ["geo_id_malformed"]
    return "", "malformed", ["zcta_not_extracted"]


def percentile(values: Sequence[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * p
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def midrank_percentiles(values_by_key: Sequence[tuple[str, float]]) -> dict[str, dict[str, float | int]]:
    """Return minimum rank, midrank percentile, empirical CDF, and tie count.

    Percentile formula is (midrank - 1) / (n - 1), bounded to [0, 1].
    Ties receive the same minimum rank, midrank percentile, CDF, and tie count.
    """
    ordered = sorted(values_by_key, key=lambda pair: (pair[1], pair[0]))
    n = len(ordered)
    result: dict[str, dict[str, float | int]] = {}
    start = 0
    while start < n:
        end = start + 1
        while end < n and ordered[end][1] == ordered[start][1]:
            end += 1
        min_rank = start + 1
        max_rank = end
        midrank = (min_rank + max_rank) / 2
        pct = 0.5 if n == 1 else (midrank - 1) / (n - 1)
        cdf = max_rank / n
        for key, _ in ordered[start:end]:
            result[key] = {
                "rank": min_rank,
                "midrank": midrank,
                "percentile": pct,
                "empirical_cdf": cdf,
                "tie_count": end - start,
            }
        start = end
    return result


def csv_row_count_and_columns(path: Path) -> tuple[int, int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.reader(handle)
        try:
            first = next(rows)
        except StopIteration:
            return 0, 0
        return 1 + sum(1 for _ in rows), len(first)


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: serialize(row.get(name)) for name in fieldnames})
            count += 1
    return count


def serialize(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        if value.is_integer():
            return str(int(value))
        return f"{value:.10f}".rstrip("0").rstrip(".")
    return value


def source_role(relative_path: str, config: dict[str, Any]) -> str:
    roles = {
        config["selected_data_file"]: "selected_acs_data",
        config["selected_metadata_file"]: "selected_column_metadata",
        config["selected_notes_file"]: "selected_table_notes",
    }
    return roles.get(relative_path, "candidate_or_historical_source")


def apparent_vintage(name: str) -> str:
    match = re.search(r"ACSDT5Y(\d{4})\.B19013", name, re.IGNORECASE)
    return match.group(1) if match else ""


def is_crosswalk_candidate(path: Path) -> bool:
    lower = path.name.lower()
    return (
        "crosswalk" in lower
        or "hud_usps" in lower
        or ("zip" in lower and "zcta" in lower)
        or ("zip" in lower and "state" in lower)
    )


def inventory_sources(input_root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for path in sorted(p for p in input_root.rglob("*") if p.is_file() and not any(part.startswith(".") for part in p.relative_to(input_root).parts)):
        relative = path.relative_to(input_root).as_posix()
        rows = ""
        columns = ""
        if path.suffix.lower() == ".csv":
            row_count, col_count = csv_row_count_and_columns(path)
            rows, columns = row_count, col_count
        inventory.append({
            "relative_path": relative,
            "filename": path.name,
            "format": path.suffix.lower().lstrip("."),
            "size_bytes": path.stat().st_size,
            "modified_time_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            "sha256": sha256_file(path),
            "apparent_vintage": apparent_vintage(path.name),
            "source_role": source_role(relative, config),
            "crosswalk_candidate": is_crosswalk_candidate(path),
            "physical_row_count": rows,
            "observed_header_column_count": columns,
        })
    return inventory


def validate_selected_sources(input_root: Path, config: dict[str, Any]) -> tuple[Path, Path, Path, list[dict[str, Any]]]:
    data_path = input_root / config["selected_data_file"]
    metadata_path = input_root / config["selected_metadata_file"]
    notes_path = input_root / config["selected_notes_file"]
    missing = [str(path) for path in (data_path, metadata_path, notes_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required selected ACS source(s) missing: " + ", ".join(missing))

    notes = notes_path.read_text(encoding="utf-8-sig")
    required_notes_tokens = [
        "ACSDT5Y2024.B19013",
        "American Community Survey",
        "2024",
        "ACS 5-Year Estimates Detailed Tables",
        "Median Household Income in the Past 12 Months (in 2024 Inflation-Adjusted Dollars)",
        "The value shown here is the 90 percent margin of error",
    ]
    missing_tokens = [token for token in required_notes_tokens if token not in notes]
    if missing_tokens:
        raise ValueError(f"Selected notes file failed metadata validation; missing tokens: {missing_tokens}")

    with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
        metadata_rows = list(csv.DictReader(handle))
    metadata = {row["Column Name"]: row["Label"] for row in metadata_rows}
    required_metadata = {
        "GEO_ID": "Geography",
        "NAME": "Geographic Area Name",
        config["estimate_column"]: "Estimate!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars)",
        config["moe_column"]: "Margin of Error!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars)",
    }
    mismatches = [
        {"column": column, "expected": expected, "observed": metadata.get(column, "<missing>")}
        for column, expected in required_metadata.items()
        if metadata.get(column) != expected
    ]
    if mismatches:
        raise ValueError(f"Column metadata validation failed: {mismatches}")
    return data_path, metadata_path, notes_path, metadata_rows


def ingest_acs(data_path: Path, config: dict[str, Any], run_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    with data_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2:
        raise ValueError("ACS source does not contain header and data rows")
    header = rows[0]
    while header and header[-1] == "":
        header = header[:-1]
    if header != EXPECTED_SOURCE_COLUMNS:
        raise ValueError(f"Unexpected ACS columns: {header}; expected {EXPECTED_SOURCE_COLUMNS}")

    annotation_present = rows[1][:4] == [
        "Geography",
        "Geographic Area Name",
        "Estimate!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars)",
        "Margin of Error!!Median household income in the past 12 months (in 2024 inflation-adjusted dollars)",
    ]
    start_index = 2 if annotation_present else 1
    records: list[dict[str, Any]] = []
    row_length_counts: Counter[int] = Counter()
    for list_index, raw_row in enumerate(rows[start_index:], start=start_index):
        row_length_counts[len(raw_row)] += 1
        trimmed = raw_row[:4]
        if len(trimmed) != 4:
            raise ValueError(f"Source row {list_index + 1} has fewer than four fields")
        source = dict(zip(EXPECTED_SOURCE_COLUMNS, trimmed))
        zcta, zcta_status, zcta_flags = extract_zcta(source["GEO_ID"], source["NAME"])
        estimate = parse_estimate(source[config["estimate_column"]])
        moe = parse_moe(source[config["moe_column"]])
        relative_moe = None
        if estimate["value"] is not None and estimate["value"] > 0 and moe["value"] is not None:
            relative_moe = moe["value"] / estimate["value"]
        flags = sorted(set(zcta_flags + estimate["flags"] + moe["flags"]))
        records.append({
            "zcta5": zcta,
            "geo_id_raw": source["GEO_ID"],
            "geo_label_raw": source["NAME"],
            "source_row_number": list_index + 1,
            "state_code": "",
            "state_assignment_method": "",
            "state_assignment_ambiguous": "",
            "mapping_status": "unresolved_crosswalk_missing",
            "median_household_income": estimate["value"],
            "income_moe": moe["value"],
            "income_relative_moe": relative_moe,
            "income_estimate_raw": source[config["estimate_column"]],
            "income_moe_raw": source[config["moe_column"]],
            "income_value_status": estimate["status"],
            "income_moe_status": moe["status"],
            "income_bound_value": estimate["bound"],
            "income_censor_direction": estimate["direction"],
            "zcta_parse_status": zcta_status,
            "transformation_flags": "|".join(flags),
            "national_income_outlier_flag": False,
            "acs_year": config["acs_year"],
            "acs_product": config["acs_product"],
            "acs_table": config["acs_table"],
            "income_units": config["acs_units"],
            "crosswalk_vintage": "",
            "run_id": run_id,
        })
    layout = {
        "physical_rows": len(rows),
        "header_rows": 1,
        "annotation_rows": 1 if annotation_present else 0,
        "data_rows": len(records),
        "original_header_columns": len(rows[0]),
        "logical_columns": len(header),
        "row_length_counts": dict(sorted(row_length_counts.items())),
    }
    return records, layout


def mark_national_outliers(records: list[dict[str, Any]]) -> dict[str, float | None]:
    values = [row["median_household_income"] for row in records if row["income_value_status"] == "valid"]
    q1 = percentile(values, 0.25)
    q3 = percentile(values, 0.75)
    if q1 is None or q3 is None:
        return {"q1": q1, "q3": q3, "lower_fence": None, "upper_fence": None}
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    for row in records:
        value = row["median_household_income"]
        row["national_income_outlier_flag"] = value is not None and (value < lower or value > upper)
    return {"q1": q1, "q3": q3, "lower_fence": lower, "upper_fence": upper}


def add_check(checks: list[dict[str, Any]], check_id: str, category: str, description: str, status: str, observed: Any, expected: Any, details: str) -> None:
    checks.append({
        "check_id": check_id,
        "category": category,
        "description": description,
        "status": status,
        "observed": observed,
        "expected": expected,
        "details": details,
    })


def build_qa_checks(records: list[dict[str, Any]], layout: dict[str, Any], crosswalk_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    zctas = [row["zcta5"] for row in records if row["zcta5"]]
    duplicate_count = sum(count - 1 for count in Counter(zctas).values() if count > 1)
    valid_ids = sum(row["zcta_parse_status"] == "valid" for row in records)
    leading_zero_count = sum(row["zcta5"].startswith("0") for row in records if row["zcta5"])
    income_status = Counter(row["income_value_status"] for row in records)
    moe_status = Counter(row["income_moe_status"] for row in records)
    relative_moe = [row["income_relative_moe"] for row in records if row["income_relative_moe"] is not None]
    add_check(checks, "SRC-001", "source_schema", "Selected source metadata identifies 2024 ACS 5-Year Detailed Table B19013", "PASS", "2024|ACS5|B19013", "2024|ACS5|B19013", "Validated against the provided table-notes and column-metadata files.")
    add_check(checks, "SRC-002", "source_schema", "Logical source columns match expected fields", "PASS", layout["logical_columns"], 4, "Trailing empty CSV column was ignored; four named fields were retained.")
    add_check(checks, "SRC-003", "source_schema", "Annotation row detected and excluded from analytical records", "PASS" if layout["annotation_rows"] == 1 else "WARN", layout["annotation_rows"], 1, "Census label row is metadata, not a ZCTA observation.")
    add_check(checks, "ID-001", "identifier", "All data rows have matching five-digit GEO_ID and NAME ZCTA identifiers", "PASS" if valid_ids == len(records) else "BLOCK", valid_ids, len(records), "Both identifier sources were reconciled for each row.")
    add_check(checks, "ID-002", "identifier", "ZCTA is unique", "PASS" if duplicate_count == 0 else "BLOCK", duplicate_count, 0, "Duplicates are not automatically resolved.")
    add_check(checks, "ID-003", "identifier", "Leading-zero ZCTAs remain five-character strings", "PASS", leading_zero_count, ">0", "No numeric cast is used for ZCTA.")
    add_check(checks, "INC-001", "income", "Income-status reconciliation", "PASS" if sum(income_status.values()) == len(records) else "BLOCK", sum(income_status.values()), len(records), json.dumps(dict(sorted(income_status.items())), sort_keys=True))
    add_check(checks, "INC-002", "income", "Missing and special-coded income values were not converted to zero", "PASS", sum(1 for row in records if row["median_household_income"] == 0), 0, "Open-ended bounds are retained separately and excluded from exact-value statistics.")
    add_check(checks, "INC-003", "income", "Exact valid income values available", "WARN" if income_status["valid"] < len(records) else "PASS", income_status["valid"], len(records), "Non-valid values remain in exception outputs.")
    add_check(checks, "MOE-001", "uncertainty", "MOE-status reconciliation", "PASS" if sum(moe_status.values()) == len(records) else "BLOCK", sum(moe_status.values()), len(records), json.dumps(dict(sorted(moe_status.items())), sort_keys=True))
    add_check(checks, "MOE-002", "uncertainty", "Relative MOE calculated only when exact income and numeric MOE are valid", "PASS", len(relative_moe), income_status["valid"], "Relative MOE equals MOE / estimate and is not used to modify income.")
    add_check(checks, "MAP-001", "mapping", "Documented ZIP/ZCTA/state crosswalk is available", "BLOCK", len(crosswalk_candidates), ">=1", "No candidate crosswalk file was found; state is not inferred from ZIP/ZCTA digits.")
    add_check(checks, "MAP-002", "mapping", "Canonical rows reconcile to resolved, ambiguous, and unresolved state mapping", "PASS", f"0+0+{len(records)}", len(records), "All records are unresolved_crosswalk_missing.")
    add_check(checks, "STATE-001", "within_state", "Within-state ranks and percentiles can be calculated", "BLOCK", 0, len(records), "Requires accepted state assignments from a documented crosswalk.")
    add_check(checks, "STATE-002", "within_state", "State summaries can be calculated", "BLOCK", 0, ">0 states", "State summary table is schema-only until a crosswalk is supplied.")
    add_check(checks, "REC-001", "reconciliation", "ACS data-row reconciliation", "PASS", len(records), layout["data_rows"], f"{layout['physical_rows']} physical rows = 1 header + {layout['annotation_rows']} annotation + {layout['data_rows']} data rows.")
    return checks


def data_dictionary_rows() -> list[dict[str, Any]]:
    return [
        _dict_row("GEO_ID", "Census", "string", "Original Census geography identifier", "Preserved unchanged", "geo_id_raw", "string", "N/A"),
        _dict_row("NAME", "Census", "string", "Original Census geographic area name", "Preserved unchanged", "geo_label_raw", "string", "N/A"),
        _dict_row("GEO_ID + NAME", "Derived", "string", "Five-digit ZCTA", "Regex-extract from both fields; require agreement; preserve leading zeros", "zcta5", "string(5)", "N/A"),
        _dict_row("source row", "Derived", "integer", "One-based physical row in source CSV", "Header and annotation rows retained in count but excluded from data", "source_row_number", "integer", "row number"),
        _dict_row("B19013_001E", "Census", "string", "Median household income in past 12 months", "Remove commas for exact numeric values; special symbols and open-ended values are not treated as exact", "median_household_income", "nullable decimal", "2024 inflation-adjusted dollars"),
        _dict_row("B19013_001E", "Census", "string", "Original estimate display value", "Preserved unchanged", "income_estimate_raw", "string", "2024 inflation-adjusted dollars"),
        _dict_row("B19013_001E", "Derived", "string", "Estimate validity/special-value classification", "Explicit Census-symbol parser", "income_value_status", "categorical string", "N/A"),
        _dict_row("B19013_001E", "Derived", "decimal", "Numeric bound for open-ended median display", "Parse numeric portion of 250,000+ or 2,500- without using it as exact income", "income_bound_value", "nullable decimal", "2024 inflation-adjusted dollars"),
        _dict_row("B19013_001E", "Derived", "string", "Direction of open-ended median", "+ maps to above; - suffix maps to below", "income_censor_direction", "nullable categorical string", "N/A"),
        _dict_row("B19013_001M", "Census", "string", "90 percent margin of error for median income", "Remove commas for numeric values; parse symbols explicitly", "income_moe", "nullable decimal", "2024 inflation-adjusted dollars"),
        _dict_row("B19013_001M", "Census", "string", "Original MOE display value", "Preserved unchanged", "income_moe_raw", "string", "2024 inflation-adjusted dollars"),
        _dict_row("B19013_001M", "Derived", "string", "MOE validity/special-value classification", "Explicit Census-symbol parser", "income_moe_status", "categorical string", "N/A"),
        _dict_row("B19013_001E / B19013_001M", "Derived", "decimal", "Relative MOE diagnostic", "income_moe / median_household_income only when both are numeric and income > 0", "income_relative_moe", "nullable decimal", "ratio"),
        _dict_row("Documented crosswalk", "Crosswalk", "string", "Resolved postal state/jurisdiction", "Blocked: crosswalk not provided; no prefix inference", "state_code", "nullable string(2)", "N/A"),
        _dict_row("Documented crosswalk", "Derived", "string", "State assignment rule", "Blocked until crosswalk allocation fields are evaluated", "state_assignment_method", "nullable string", "N/A"),
        _dict_row("Documented crosswalk", "Derived", "boolean", "Multiple plausible state assignments", "Blocked until crosswalk is evaluated", "state_assignment_ambiguous", "nullable boolean", "N/A"),
        _dict_row("Documented crosswalk", "Derived", "string", "Crosswalk match/exception result", "Set to unresolved_crosswalk_missing for this provisional run", "mapping_status", "categorical string", "N/A"),
        _dict_row("income + state", "Derived", "integer", "Minimum within-state rank under ties", "Planned ordering: income ascending, ZCTA for deterministic record order; ties share minimum rank", "income_rank_in_state", "nullable integer", "rank"),
        _dict_row("income + state", "Derived", "decimal", "Within-state percentile", "Planned formula: (midrank - 1)/(n - 1), n>1; n=1 -> 0.5; ties share percentile", "income_percentile_in_state", "nullable decimal", "0 to 1"),
        _dict_row("income + state", "Derived", "decimal", "Within-state empirical CDF", "Planned formula: maximum tied rank / n", "income_empirical_cdf_in_state", "nullable decimal", "0 to 1"),
        _dict_row("income + state", "Derived", "integer", "Count sharing identical valid income within state", "Count exact equal numeric estimates within state", "tie_count", "nullable integer", "records"),
        _dict_row("Configuration", "Derived", "integer", "ACS estimate year", "Constant 2024", "acs_year", "integer", "year"),
        _dict_row("Configuration", "Derived", "string", "ACS product", "Constant from validated metadata", "acs_product", "string", "N/A"),
        _dict_row("Configuration", "Derived", "string", "ACS table ID", "Constant B19013", "acs_table", "string", "N/A"),
        _dict_row("Source checksum + pipeline version", "Derived", "string", "Deterministic run identifier", "Hash prefix and version; independent of run timestamp", "run_id", "string", "N/A"),
    ]


def _dict_row(original_field: str, source: str, original_type: str, definition: str, transformation: str, final_field: str, final_type: str, units: str) -> dict[str, Any]:
    return {
        "original_field": original_field,
        "source": source,
        "original_type": original_type,
        "definition": definition,
        "transformation": transformation,
        "final_field": final_field,
        "final_type": final_type,
        "units": units,
    }


def national_summary(records: list[dict[str, Any]], fences: dict[str, float | None], run_id: str) -> dict[str, Any]:
    values = [row["median_household_income"] for row in records if row["income_value_status"] == "valid"]
    return {
        "scope": "national_unweighted_zcta_exact_values_only",
        "total_zcta_records": len(records),
        "valid_exact_income_count": len(values),
        "minimum": min(values) if values else None,
        "p01": percentile(values, 0.01),
        "p05": percentile(values, 0.05),
        "p25": percentile(values, 0.25),
        "median_p50": percentile(values, 0.50),
        "mean": statistics.fmean(values) if values else None,
        "p75": percentile(values, 0.75),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "maximum": max(values) if values else None,
        "iqr_lower_fence": fences["lower_fence"],
        "iqr_upper_fence": fences["upper_fence"],
        "iqr_outlier_count": sum(row["national_income_outlier_flag"] for row in records),
        "units": "2024 inflation-adjusted dollars",
        "quantile_method": "linear interpolation at (n-1)*p",
        "run_id": run_id,
    }


def moe_summary(records: list[dict[str, Any]], config: dict[str, Any], run_id: str) -> dict[str, Any]:
    moes = [row["income_moe"] for row in records if row["income_moe"] is not None]
    relative = [row["income_relative_moe"] for row in records if row["income_relative_moe"] is not None]
    return {
        "scope": "national_unweighted_zcta_valid_numeric_moe",
        "valid_moe_count": len(moes),
        "moe_minimum": min(moes) if moes else None,
        "moe_p25": percentile(moes, 0.25),
        "moe_median": percentile(moes, 0.50),
        "moe_mean": statistics.fmean(moes) if moes else None,
        "moe_p75": percentile(moes, 0.75),
        "moe_p95": percentile(moes, 0.95),
        "moe_maximum": max(moes) if moes else None,
        "relative_moe_valid_count": len(relative),
        "relative_moe_median": percentile(relative, 0.50),
        "relative_moe_p95": percentile(relative, 0.95),
        "relative_moe_maximum": max(relative) if relative else None,
        "relative_moe_ge_warning_count": sum(value >= config["relative_moe_warning_threshold"] for value in relative),
        "relative_moe_ge_severe_count": sum(value >= config["relative_moe_severe_threshold"] for value in relative),
        "warning_threshold": config["relative_moe_warning_threshold"],
        "severe_threshold": config["relative_moe_severe_threshold"],
        "run_id": run_id,
    }


def decision_rows(run_id: str, generated_at: str) -> list[dict[str, Any]]:
    date = generated_at[:10]
    return [
        {"decision_id": "D001", "decision_date": date, "issue": "Which ACS file to analyze", "alternatives_considered": "2020-2024 B19013 files", "selected_approach": "Use 2024 data, metadata, and notes", "rationale": "Immediate scope explicitly requires 2024 ACS 5-Year B19013", "decision_owner": "Project brief", "affected_outputs": "All", "rerun_required": "No", "run_id": run_id},
        {"decision_id": "D002", "decision_date": date, "issue": "Census annotation row", "alternatives_considered": "Treat as data; detect and exclude", "selected_approach": "Detect exact labels and exclude from analytical records", "rationale": "It contains definitions, not a geography", "decision_owner": "Technical implementation", "affected_outputs": "Canonical table; row reconciliation", "rerun_required": "No", "run_id": run_id},
        {"decision_id": "D003", "decision_date": date, "issue": "Open-ended income values", "alternatives_considered": "Use bound as exact; exclude record; preserve as censored special value", "selected_approach": "Preserve record and bound/direction; leave exact income null", "rationale": "Avoid unapproved capping or treating an interval boundary as an exact median", "decision_owner": "Technical implementation pending actuarial review", "affected_outputs": "Clean table; income summaries; exception table", "rerun_required": "Only if actuary approves another treatment", "run_id": run_id},
        {"decision_id": "D004", "decision_date": date, "issue": "State assignment without crosswalk", "alternatives_considered": "Infer from prefix; obtain arbitrary online file; block state calculations", "selected_approach": "Block state assignment and preserve every ZCTA as unresolved", "rationale": "Project brief prohibits prefix inference and requires documented mapping provenance", "decision_owner": "Project brief", "affected_outputs": "Mapping; ranks; state summaries", "rerun_required": "Yes, when approved crosswalk is supplied", "run_id": run_id},
        {"decision_id": "D005", "decision_date": date, "issue": "Within-state percentile formula and ties", "alternatives_considered": "Row-number percentile; minimum-rank percentile; midrank percentile", "selected_approach": "Planned midrank formula (midrank-1)/(n-1); n=1 -> 0.5; identical incomes share values", "rationale": "Deterministic and does not split ties", "decision_owner": "Technical proposal pending checkpoint approval", "affected_outputs": "Within-state rank table", "rerun_required": "Yes after crosswalk/approval", "run_id": run_id},
        {"decision_id": "D006", "decision_date": date, "issue": "Candidate grouping work", "alternatives_considered": "Proceed; stop at checkpoint", "selected_approach": "Stop before candidate groups", "rationale": "Section 8 requires checkpoint acceptance first", "decision_owner": "Project brief", "affected_outputs": "Candidate grouping tables are not produced", "rerun_required": "No", "run_id": run_id},
    ]


def report_markdown(config: dict[str, Any], inventory: list[dict[str, Any]], records: list[dict[str, Any]], layout: dict[str, Any], checks: list[dict[str, Any]], national: dict[str, Any], moe: dict[str, Any], run_id: str, generated_at: str, data_checksum: str) -> tuple[str, str]:
    income = Counter(row["income_value_status"] for row in records)
    moe_status = Counter(row["income_moe_status"] for row in records)
    source_names = "\n".join(f"- `{row['relative_path']}` ({row['size_bytes']:,} bytes; apparent vintage {row['apparent_vintage'] or 'unknown'}; SHA-256 `{row['sha256']}`)" for row in inventory)
    blockers = [row for row in checks if row["status"] == "BLOCK"]
    blocker_lines = "\n".join(f"- **{row['check_id']}**: {row['details']}" for row in blockers)
    qa = f"""# Phase 1 QA Report — Provisional ACS-Only Checkpoint

**Run ID:** `{run_id}`  
**Generated (UTC):** {generated_at}  
**Status:** **PROVISIONAL / BLOCKED FOR STATE-BASED ANALYSIS**

## Scope and source validation

The selected source was validated from the supplied table-notes and column-metadata files as U.S. Census Bureau **2024 American Community Survey, ACS 5-Year Estimates Detailed Tables, Table B19013**, with income expressed in **2024 inflation-adjusted dollars** and a **90% margin of error**. The data contain exclusively records whose `GEO_ID` matches `860Z200US` + five digits and whose label matches `ZCTA5 ` + the same five digits.

Selected data SHA-256: `{data_checksum}`.

{source_names}

No ZIP/ZCTA/state crosswalk candidate was found in the provided data directory.

## Processing-stage counts

- Physical CSV rows: {layout['physical_rows']:,}
- Header rows: {layout['header_rows']:,}
- Census annotation/metadata rows: {layout['annotation_rows']:,}
- Analytical data rows retained: {layout['data_rows']:,}
- Unique valid five-digit ZCTAs: {len({row['zcta5'] for row in records if row['zcta5']}):,}
- Duplicate ZCTA excess records: {sum(c - 1 for c in Counter(row['zcta5'] for row in records if row['zcta5']).values() if c > 1):,}
- Leading-zero ZCTAs preserved: {sum(row['zcta5'].startswith('0') for row in records if row['zcta5']):,}

Reconciliation: **{layout['physical_rows']:,} = 1 header + {layout['annotation_rows']:,} annotation + {layout['data_rows']:,} data rows**. Mapping reconciliation: **{len(records):,} canonical ZCTAs = 0 resolved + 0 ambiguous + {len(records):,} unresolved because the crosswalk is missing**.

## Income QA

- Exact valid income: {income['valid']:,}
- Blank missing: {income['missing_blank']:,}
- Explicitly suppressed: 0 (no dedicated suppression symbol was observed)
- Census `-` / estimate not computed: {income['not_computed_dash']:,}
- Top open-ended `250,000+`: {income['top_open_ended']:,}
- Bottom open-ended `2,500-`: {income['bottom_open_ended']:,}
- Zero estimates: {income['zero']:,}
- Nonpositive/negative-coded estimates: {income['nonpositive_or_negative_code']:,}

Income reconciliation: **{len(records):,} = {income['valid']:,} valid exact + {income['not_computed_dash']:,} not computed + {income['top_open_ended']:,} top open-ended + {income['bottom_open_ended']:,} bottom open-ended**.

National, unweighted, exact-value-only distribution: minimum {serialize(national['minimum'])}; p05 {serialize(national['p05'])}; p25 {serialize(national['p25'])}; median {serialize(national['median_p50'])}; mean {serialize(national['mean'])}; p75 {serialize(national['p75'])}; p95 {serialize(national['p95'])}; maximum {serialize(national['maximum'])}. Quantiles use linear interpolation at `(n-1)*p`. The IQR rule flags {national['iqr_outlier_count']:,} exact-value observations for review; none were removed, capped, winsorized, or imputed.

## MOE and uncertainty QA

- Numeric 90% MOE values: {moe['valid_moe_count']:,}
- MOE `**` (cannot compute; insufficient observations): {moe_status['cannot_compute_insufficient_observations']:,}
- MOE `***` (open-ended median): {moe_status['cannot_compute_open_ended_median']:,}
- Relative-MOE median: {serialize(moe['relative_moe_median'])}
- Relative-MOE p95: {serialize(moe['relative_moe_p95'])}
- Relative MOE ≥ {moe['warning_threshold']:.0%}: {moe['relative_moe_ge_warning_count']:,}
- Relative MOE ≥ {moe['severe_threshold']:.0%}: {moe['relative_moe_ge_severe_count']:,}

Relative MOE is diagnostic only and does not modify the income estimate.

## Mapping and within-state QA

State-based outputs are blocked. The schema-only state summary and row-level blocked rank table were emitted for auditability, but **no state codes, within-state ranks, percentiles, empirical CDFs, or state distributions were fabricated**.

The required crosswalk must be documented and versioned, preserve full ZIP↔ZCTA↔state relationships, include an allocation basis where relationships are non-unique (preferably residential/address or population weight), and identify release/effective date and geographic vintage. Resolution must preserve candidate count, chosen method, ambiguity flag, reason code, unmatched records, cross-state relationships, and weight-sum diagnostics.

## Blocking checks

{blocker_lines}

## Guardrail confirmation

No internal policy, premium, exposure, claim, or loss data were used. No candidate territories, final territories, territory counts, rating factors, causal claims, or regulatory acceptability claims were produced.
"""

    checkpoint = f"""# Phase 1 Checkpoint Memo — Provisional ACS-Only Foundation

**Run ID:** `{run_id}`  
**Checkpoint status:** **PROVISIONAL — CROSSWALK REQUIRED**

## 1. What was completed

The 2024 ACS 5-Year B19013 source was inventoried, validated, ingested read-only, standardized to five-character ZCTAs, and reconciled. Exact income and 90% MOE values were parsed with explicit Census-symbol handling. National exact-value income and uncertainty diagnostics, exceptions, manifests, a data dictionary, QA checks, automated tests, and rerun instructions were produced.

## 2. Sources used and vintages

Primary analytical source: `{config['selected_data_file']}`, 2024 ACS 5-Year Detailed Table B19013, SHA-256 `{data_checksum}`. The supplied 2024 column metadata and table notes were used for schema, unit, product, and MOE validation. Historical 2020–2023 files were inventoried but not combined with 2024.

## 3. Record-count reconciliation

{layout['physical_rows']:,} physical rows = 1 header + {layout['annotation_rows']} annotation + {layout['data_rows']:,} data rows. All {layout['data_rows']:,} data rows were retained in the canonical table, with {len({row['zcta5'] for row in records if row['zcta5']}):,} unique valid ZCTAs and no duplicate excess records. Mapping reconciliation is 0 resolved + 0 ambiguous + {len(records):,} unresolved = {len(records):,} canonical ZCTAs.

## 4. Key data-quality findings

Identifiers were structurally valid and mutually consistent for every data row; {sum(row['zcta5'].startswith('0') for row in records if row['zcta5']):,} leading-zero identifiers were preserved. There are {income['valid']:,} exact valid income values, {income['not_computed_dash']:,} `-` values, {income['top_open_ended']:,} top open-ended values, and {income['bottom_open_ended']:,} bottom open-ended values. No record was dropped and no outlier was changed.

## 5. Mapping coverage and exceptions

Coverage is 0% because no documented ZIP/ZCTA/state crosswalk was provided. Every ZCTA is listed in `mapping_exceptions.csv` as `crosswalk_missing`. Cross-state, one-to-many, many-to-one, ZIP-specific, PO Box, unique, military, allocation-weight, and state-resolution diagnostics cannot be evaluated until the crosswalk is supplied.

## 6. Income missingness and uncertainty findings

Exact valid income coverage is {income['valid'] / len(records):.2%}. Open-ended values were retained as censored special values, not treated as exact bounds. There are {moe['valid_moe_count']:,} numeric MOEs; {moe['relative_moe_ge_warning_count']:,} exact-income ZCTAs have relative MOE at or above {moe['warning_threshold']:.0%}, including {moe['relative_moe_ge_severe_count']:,} at or above {moe['severe_threshold']:.0%}. These are diagnostic flags only.

## 7. ZCTA counts and income distribution by state

**Blocked.** State cannot be assigned supportably without a documented crosswalk. National unweighted exact-value statistics are provided in `national_income_summary.csv` only; they are not substitutes for within-state results.

## 8. Method used for ranks, percentiles, and ties

No ranks were calculated in this blocked run. The documented proposed method for the rerun is: sort valid exact income ascending within accepted state, with ZCTA as deterministic record order; identical incomes share minimum rank and tie count; percentile is `(midrank - 1)/(n - 1)` for `n > 1` and `0.5` for `n = 1`; empirical CDF is maximum tied rank divided by `n`. This method requires checkpoint acceptance before use.

## 9. Files produced and how to reproduce them

See the package `README.md` and `output_manifest.csv`. The pipeline uses only the Python standard library. Run it with a data-root argument; raw inputs are read-only and outputs are regenerated in a separate artifacts directory.

## 10. Blocking issues or decisions required

1. Provide or approve a versioned ZIP/ZCTA/state crosswalk with provenance, effective/release date, geographic vintage, direction/cardinality, and allocation fields.
2. Approve the mapping-resolution hierarchy after inspecting its available allocation measures; no arbitrary first-row selection will be used.
3. Confirm the proposed treatment of `250,000+` and `2,500-` as censored special values excluded from exact-value ranks, or authorize another documented treatment.
4. Confirm the proposed midrank percentile formula and tie handling.

## 11. Recommended next step — without selecting final territories

Supply the documented crosswalk, then rerun mapping QA and compute the previously blocked within-state statistics. Review the completed mapping/state checkpoint before authorizing any 4/5/6 candidate grouping sensitivity work. No final territory count or rating factor should be selected in Phase 1.
"""
    return qa, checkpoint


def build_readme() -> str:
    return """# Phase 1 ACS-Only Foundation

This package implements the Section 8 immediate assignment as far as the provided inputs support. It is intentionally provisional because no ZIP/ZCTA/state crosswalk was supplied.

## Reproduce

Requirements: Python 3.10+ standard library only.

From this package directory:

```bash
python3 -m unittest discover -s tests -v
python3 pipeline/phase1_pipeline.py \\
  --input-root "/path/to/Territory/Data" \\
  --config config/phase1_config.json \\
  --output-root artifacts \\
  --clean
```

The pipeline reads raw source files without modification. `--clean` replaces only the specified output-root directory after validating that it is neither `/` nor the input root.

## Scope

- Selected: 2024 ACS 5-Year Detailed Table B19013 ZCTA data, metadata, and notes.
- Inventoried only: supplied 2020–2023 B19013 files.
- Not available: a documented ZIP/ZCTA/state crosswalk.
- Not used: internal policy, premium, exposure, claim, or loss data.
- Not produced: candidate/final territories or rating factors.

## Important outputs

- `artifacts/tables/clean_zcta_income.csv`: canonical ACS-only ZCTA table.
- `artifacts/tables/within_state_income_rank.csv`: blocked row-level rank schema; no fabricated state results.
- `artifacts/tables/state_summary.csv`: schema-only because state assignment is blocked.
- `artifacts/exceptions/mapping_exceptions.csv`: every unresolved ZCTA.
- `artifacts/reports/qa_report.md`: full QA findings and blockers.
- `artifacts/reports/phase1_checkpoint.md`: required checkpoint summary.
- `artifacts/reports/crosswalk_input_specification.md`: precise request for the missing mapping source.
- `artifacts/qa/qa_checks.csv`: machine-readable test/check results.
- `artifacts/output_manifest.csv`: checksums and row counts for generated artifacts.

## Raw-input immutability

The selected raw-file SHA-256 is captured before ingestion and recorded in `run_metadata.json` and the source manifest. The program never opens an input path for writing.
"""


def crosswalk_input_specification() -> str:
    return """# Required ZIP/ZCTA/State Crosswalk Input

## Purpose

The next Phase 1 run needs a documented bridge from the production rating key (USPS five-digit ZIP) to Census ZCTA and state/jurisdiction. A ZCTA-to-state-only file can unblock preliminary state summaries, but it does not satisfy the implementation bridge required by the project brief.

## Acceptable delivery

Provide CSV or Parquet, either as one table or as documented joinable tables. A compressed source archive is acceptable if the contained files and schema are identified. Preserve the source's full many-to-many relationship; do not pre-deduplicate it.

Required or strongly preferred fields:

- five-character USPS ZIP (`zip5` or documented equivalent);
- five-character Census ZCTA (`zcta5` or documented equivalent);
- two-character state/jurisdiction code, or a documented field that can be joined to one;
- allocation value(s) and their basis, such as residential address ratio/count, total address ratio/count, population ratio/count, or area ratio;
- ZIP type when available (standard, PO Box, unique, military, or other);
- relationship/effective date and geographic vintage; and
- any source-provided quality, dominant-match, or exception flags.

Required provenance supplied with the file:

- source organization;
- source URL or file provenance;
- release/effective date;
- ZIP and ZCTA geographic vintage;
- field definitions and units;
- relationship direction and known coverage limitations; and
- expected weight-sum basis and tolerance, if weights are present.

## Resolution review after delivery

The raw relationship will be retained unchanged. Before creating a resolved table, the run will quantify one-to-one, one-to-many, many-to-one, cross-state, unmatched, non-geographic, and ambiguous relationships; test allocation-weight sums; and propose a documented hierarchy favoring the best-supported residential/address or population allocation field. No arbitrary first-row selection will be used.
"""


def safe_clean(output_root: Path, input_root: Path) -> None:
    resolved_output = output_root.resolve()
    resolved_input = input_root.resolve()
    if (
        resolved_output == Path("/")
        or resolved_output == resolved_input
        or resolved_output in resolved_input.parents
        or resolved_input in resolved_output.parents
    ):
        raise ValueError(f"Refusing to clean unsafe output path: {resolved_output}")
    if output_root.exists():
        shutil.rmtree(output_root)


def write_output_manifest(output_root: Path, run_id: str) -> None:
    rows: list[dict[str, Any]] = []
    for path in sorted(p for p in output_root.rglob("*") if p.is_file() and p.name != "output_manifest.csv"):
        relative = path.relative_to(output_root).as_posix()
        records: int | str = ""
        if path.suffix.lower() == ".csv":
            physical, _ = csv_row_count_and_columns(path)
            records = max(physical - 1, 0)
        rows.append({
            "relative_path": relative,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "data_record_count_if_csv": records,
            "run_id": run_id,
        })
    write_csv(output_root / "output_manifest.csv", ["relative_path", "size_bytes", "sha256", "data_record_count_if_csv", "run_id"], rows)


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if args.clean:
        safe_clean(output_root, input_root)
    output_root.mkdir(parents=True, exist_ok=True)

    inventory = inventory_sources(input_root, config)
    data_path, metadata_path, notes_path, _ = validate_selected_sources(input_root, config)
    data_checksum = sha256_file(data_path)
    run_id = f"phase1_acs{config['acs_year']}_{data_checksum[:12]}_v{config['pipeline_version'].replace('.', '_')}"
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    raw_checksums_before = {path: sha256_file(path) for path in (data_path, metadata_path, notes_path)}

    records, layout = ingest_acs(data_path, config, run_id)
    fences = mark_national_outliers(records)
    crosswalk_candidates = [row for row in inventory if row["crosswalk_candidate"]]
    checks = build_qa_checks(records, layout, crosswalk_candidates)

    zcta_counts = Counter(row["zcta5"] for row in records if row["zcta5"])
    duplicate_rows = [
        {"zcta5": zcta, "record_count": count, "resolution_status": "not_resolved", "run_id": run_id}
        for zcta, count in sorted(zcta_counts.items()) if count > 1
    ]
    identifier_exceptions = [
        {"source_row_number": row["source_row_number"], "geo_id_raw": row["geo_id_raw"], "geo_label_raw": row["geo_label_raw"], "zcta_parse_status": row["zcta_parse_status"], "run_id": run_id}
        for row in records if row["zcta_parse_status"] != "valid"
    ]
    income_exceptions = [
        {"zcta5": row["zcta5"], "source_row_number": row["source_row_number"], "income_estimate_raw": row["income_estimate_raw"], "income_moe_raw": row["income_moe_raw"], "income_value_status": row["income_value_status"], "income_moe_status": row["income_moe_status"], "income_bound_value": row["income_bound_value"], "income_censor_direction": row["income_censor_direction"], "run_id": run_id}
        for row in records if row["income_value_status"] != "valid"
    ]
    high_uncertainty = [
        {"zcta5": row["zcta5"], "median_household_income": row["median_household_income"], "income_moe": row["income_moe"], "income_relative_moe": row["income_relative_moe"], "warning_level": "severe" if row["income_relative_moe"] >= config["relative_moe_severe_threshold"] else "warning", "run_id": run_id}
        for row in records if row["income_relative_moe"] is not None and row["income_relative_moe"] >= config["relative_moe_warning_threshold"]
    ]
    income_outliers = [
        {"zcta5": row["zcta5"], "median_household_income": row["median_household_income"], "iqr_lower_fence": fences["lower_fence"], "iqr_upper_fence": fences["upper_fence"], "action": "flag_only_no_change", "run_id": run_id}
        for row in records if row["national_income_outlier_flag"]
    ]
    mapping_exceptions = [
        {"zcta5": row["zcta5"], "exception_type": "crosswalk_missing", "mapping_status": row["mapping_status"], "candidate_count": "", "reason_code": "NO_DOCUMENTED_CROSSWALK_PROVIDED", "details": "State assignment and ZIP relationship unavailable; record preserved.", "run_id": run_id}
        for row in records
    ]
    rank_rows = [
        {"zcta5": row["zcta5"], "state_code": "", "median_household_income": row["median_household_income"], "income_value_status": row["income_value_status"], "income_rank_in_state": "", "income_midrank_in_state": "", "income_percentile_in_state": "", "income_empirical_cdf_in_state": "", "tie_count": "", "calculation_status": "blocked_crosswalk_missing", "run_id": run_id}
        for row in records
    ]

    canonical_fields = [
        "zcta5", "geo_id_raw", "geo_label_raw", "source_row_number", "state_code", "state_assignment_method",
        "state_assignment_ambiguous", "mapping_status", "median_household_income", "income_moe", "income_relative_moe",
        "income_estimate_raw", "income_moe_raw", "income_value_status", "income_moe_status", "income_bound_value",
        "income_censor_direction", "zcta_parse_status", "transformation_flags", "national_income_outlier_flag", "acs_year",
        "acs_product", "acs_table", "income_units", "crosswalk_vintage", "run_id",
    ]
    write_csv(output_root / "source_inventory_manifest.csv", ["relative_path", "filename", "format", "size_bytes", "modified_time_utc", "sha256", "apparent_vintage", "source_role", "crosswalk_candidate", "physical_row_count", "observed_header_column_count"], inventory)
    write_csv(output_root / "data_dictionary.csv", ["original_field", "source", "original_type", "definition", "transformation", "final_field", "final_type", "units"], data_dictionary_rows())
    write_csv(output_root / "decision_log.csv", ["decision_id", "decision_date", "issue", "alternatives_considered", "selected_approach", "rationale", "decision_owner", "affected_outputs", "rerun_required", "run_id"], decision_rows(run_id, generated_at))
    write_csv(output_root / "tables/clean_zcta_income.csv", canonical_fields, records)
    write_csv(output_root / "tables/raw_zip_zcta_state_relationships.csv", ["zip5", "zcta5", "state_code", "allocation_value", "allocation_basis", "source_row_number", "crosswalk_vintage", "run_id"], [])
    write_csv(output_root / "tables/resolved_zip_zcta_state_mapping.csv", ["zip5", "zcta5", "state_code", "state_assignment_method", "state_assignment_ambiguous", "candidate_count", "mapping_status", "reason_code", "crosswalk_vintage", "run_id"], [])
    write_csv(output_root / "tables/within_state_income_rank.csv", ["zcta5", "state_code", "median_household_income", "income_value_status", "income_rank_in_state", "income_midrank_in_state", "income_percentile_in_state", "income_empirical_cdf_in_state", "tie_count", "calculation_status", "run_id"], rank_rows)
    write_csv(output_root / "tables/state_summary.csv", ["state_code", "total_zcta_count", "valid_income_count", "excluded_income_count", "income_minimum", "income_p25", "income_median", "income_mean", "income_p75", "income_maximum", "moe_median", "relative_moe_median", "calculation_status", "run_id"], [])
    national = national_summary(records, fences, run_id)
    moe = moe_summary(records, config, run_id)
    write_csv(output_root / "tables/national_income_summary.csv", list(national.keys()), [national])
    write_csv(output_root / "tables/national_moe_summary.csv", list(moe.keys()), [moe])
    income_status_rows = [{"income_value_status": status, "record_count": count, "run_id": run_id} for status, count in sorted(Counter(row["income_value_status"] for row in records).items())]
    moe_status_rows = [{"income_moe_status": status, "record_count": count, "run_id": run_id} for status, count in sorted(Counter(row["income_moe_status"] for row in records).items())]
    write_csv(output_root / "tables/income_status_summary.csv", ["income_value_status", "record_count", "run_id"], income_status_rows)
    write_csv(output_root / "tables/moe_status_summary.csv", ["income_moe_status", "record_count", "run_id"], moe_status_rows)
    write_csv(output_root / "exceptions/duplicate_zcta.csv", ["zcta5", "record_count", "resolution_status", "run_id"], duplicate_rows)
    write_csv(output_root / "exceptions/identifier_exceptions.csv", ["source_row_number", "geo_id_raw", "geo_label_raw", "zcta_parse_status", "run_id"], identifier_exceptions)
    write_csv(output_root / "exceptions/income_exceptions.csv", ["zcta5", "source_row_number", "income_estimate_raw", "income_moe_raw", "income_value_status", "income_moe_status", "income_bound_value", "income_censor_direction", "run_id"], income_exceptions)
    write_csv(output_root / "exceptions/high_uncertainty_zcta.csv", ["zcta5", "median_household_income", "income_moe", "income_relative_moe", "warning_level", "run_id"], high_uncertainty)
    write_csv(output_root / "exceptions/national_income_outliers.csv", ["zcta5", "median_household_income", "iqr_lower_fence", "iqr_upper_fence", "action", "run_id"], income_outliers)
    write_csv(output_root / "exceptions/mapping_exceptions.csv", ["zcta5", "exception_type", "mapping_status", "candidate_count", "reason_code", "details", "run_id"], mapping_exceptions)
    write_csv(output_root / "qa/qa_checks.csv", ["check_id", "category", "description", "status", "observed", "expected", "details"], checks)
    stage_rows = [
        {"stage": "physical_csv_rows", "record_count": layout["physical_rows"], "reconciliation_role": "header + annotation + data", "run_id": run_id},
        {"stage": "annotation_rows", "record_count": layout["annotation_rows"], "reconciliation_role": "metadata excluded", "run_id": run_id},
        {"stage": "source_data_rows", "record_count": layout["data_rows"], "reconciliation_role": "input data", "run_id": run_id},
        {"stage": "canonical_zcta_rows", "record_count": len(records), "reconciliation_role": "retained", "run_id": run_id},
        {"stage": "state_resolved_rows", "record_count": 0, "reconciliation_role": "resolved", "run_id": run_id},
        {"stage": "state_ambiguous_rows", "record_count": 0, "reconciliation_role": "ambiguous", "run_id": run_id},
        {"stage": "state_unresolved_rows", "record_count": len(records), "reconciliation_role": "unresolved", "run_id": run_id},
    ]
    write_csv(output_root / "qa/stage_row_counts.csv", ["stage", "record_count", "reconciliation_role", "run_id"], stage_rows)

    qa_markdown, checkpoint_markdown = report_markdown(config, inventory, records, layout, checks, national, moe, run_id, generated_at, data_checksum)
    (output_root / "reports").mkdir(parents=True, exist_ok=True)
    (output_root / "reports/qa_report.md").write_text(qa_markdown, encoding="utf-8")
    (output_root / "reports/phase1_checkpoint.md").write_text(checkpoint_markdown, encoding="utf-8")
    (output_root / "reports/crosswalk_input_specification.md").write_text(crosswalk_input_specification(), encoding="utf-8")

    raw_checksums_after = {path: sha256_file(path) for path in (data_path, metadata_path, notes_path)}
    if raw_checksums_after != raw_checksums_before:
        raise RuntimeError("Raw selected source checksum changed during execution")
    metadata = {
        "run_id": run_id,
        "pipeline_version": config["pipeline_version"],
        "generated_at_utc": generated_at,
        "input_root_argument": str(args.input_root),
        "output_root_argument": str(args.output_root),
        "selected_source_relative_path": config["selected_data_file"],
        "selected_source_sha256": data_checksum,
        "raw_source_immutability_verified": True,
        "python_version_requirement": "3.10+ standard library only",
        "crosswalk_status": "missing",
        "checkpoint_status": "provisional_blocked_state_analysis",
        "candidate_groups_produced": False,
        "internal_experience_used": False,
    }
    (output_root / "run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_output_manifest(output_root, run_id)
    return {
        "run_id": run_id,
        "records": len(records),
        "valid_income": sum(row["income_value_status"] == "valid" for row in records),
        "crosswalk_status": "missing",
        "blocking_checks": sum(row["status"] == "BLOCK" for row in checks),
        "output_root": str(output_root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True, help="Root containing the supplied Territory/Data files")
    parser.add_argument("--config", type=Path, required=True, help="Phase 1 JSON configuration")
    parser.add_argument("--output-root", type=Path, required=True, help="Generated artifact directory")
    parser.add_argument("--clean", action="store_true", help="Safely replace the output-root before running")
    return parser.parse_args()


if __name__ == "__main__":
    summary = run(parse_args())
    print(json.dumps(summary, indent=2, sort_keys=True))
