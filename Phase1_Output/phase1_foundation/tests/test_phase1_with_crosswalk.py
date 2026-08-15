import sys
import unittest
from pathlib import Path


PIPELINE_DIR = Path(__file__).resolve().parents[1] / "pipeline"
sys.path.insert(0, str(PIPELINE_DIR))
import phase1_with_crosswalk as pipeline  # noqa: E402


def acs_record(zcta, income=50000.0, status="valid"):
    return {
        "zcta5": zcta,
        "run_id": "test",
        "state_code": "",
        "state_assignment_method": "",
        "state_assignment_ambiguous": "",
        "mapping_status": "",
        "transformation_flags": "",
        "source_row_number": 1,
        "median_household_income": income if status == "valid" else None,
        "income_value_status": status,
        "income_moe": 1000.0 if status == "valid" else None,
        "income_relative_moe": 0.02 if status == "valid" else None,
    }


def relationship(zip5, zcta5, state, join_type):
    return {
        "zip5": zip5,
        "zcta5": zcta5,
        "state_code_source": state,
        "zip_join_type": join_type,
        "source_row_number": 2,
        "po_name": "",
        "zip_type": "Zip Code Area",
        "crosswalk_vintage": "test",
        "run_id": "test",
    }


class CrosswalkTests(unittest.TestCase):
    def test_identifier_normalization(self):
        self.assertEqual(pipeline.normalize_five_digit(601), "00601")
        self.assertEqual(pipeline.normalize_five_digit("00601"), "00601")
        self.assertEqual(pipeline.normalize_five_digit(None), "")

    def test_direct_match_priority_preserves_cross_state_flag(self):
        records = [acs_record("45202")]
        relationships = [
            relationship("45202", "45202", "OH", "Zip matches ZCTA"),
            relationship("41073", "45202", "KY", "Spatial join to ZCTA"),
        ]
        rows = pipeline.resolve_zcta_states(records, relationships, {"crosswalk_vintage": "test"})
        self.assertEqual(records[0]["state_code"], "OH")
        self.assertTrue(records[0]["state_assignment_ambiguous"])
        self.assertEqual(records[0]["state_candidate_codes"], "KY|OH")
        self.assertEqual(rows[0]["mapping_status"], "matched_ambiguous_cross_state")

    def test_exact_code_special_record_is_supported(self):
        records = [acs_record("32072")]
        relationships = [relationship("32072", "32072", "FL", "populated ZCTA, missing zip")]
        pipeline.resolve_zcta_states(records, relationships, {"crosswalk_vintage": "test"})
        self.assertEqual(records[0]["state_code"], "FL")
        self.assertEqual(records[0]["state_assignment_method"], "hrsa_exact_code_special_source_record")

    def test_unmatched_is_not_inferred(self):
        records = [acs_record("97258", status="not_computed_dash")]
        pipeline.resolve_zcta_states(records, [], {"crosswalk_vintage": "test"})
        self.assertEqual(records[0]["state_code"], "")
        self.assertEqual(records[0]["mapping_status"], "unmatched")

    def test_state_ties_share_rank_metrics(self):
        records = [acs_record("10001", 10.0), acs_record("10002", 20.0), acs_record("10003", 20.0)]
        for record in records:
            record["state_code"] = "NY"
        summaries, _ = pipeline.calculate_state_statistics(records, {"relative_moe_warning_threshold": 0.5, "relative_moe_severe_threshold": 1.0})
        self.assertEqual(len(summaries), 1)
        self.assertEqual(records[1]["income_rank_in_state"], 2)
        self.assertEqual(records[2]["income_rank_in_state"], 2)
        self.assertEqual(records[1]["tie_count"], 2)
        self.assertEqual(records[1]["income_percentile_in_state"], records[2]["income_percentile_in_state"])


if __name__ == "__main__":
    unittest.main()
