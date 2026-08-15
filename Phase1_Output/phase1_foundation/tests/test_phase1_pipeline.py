import importlib.util
import unittest
from pathlib import Path


PIPELINE_PATH = Path(__file__).resolve().parents[1] / "pipeline" / "phase1_pipeline.py"
SPEC = importlib.util.spec_from_file_location("phase1_pipeline", PIPELINE_PATH)
PIPELINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PIPELINE)


class ParsingTests(unittest.TestCase):
    def test_zcta_preserves_leading_zero(self):
        zcta, status, flags = PIPELINE.extract_zcta("860Z200US00601", "ZCTA5 00601")
        self.assertEqual(zcta, "00601")
        self.assertEqual(status, "valid")
        self.assertIn("leading_zero_preserved", flags)

    def test_zcta_mismatch_is_not_silently_resolved(self):
        zcta, status, _ = PIPELINE.extract_zcta("860Z200US00601", "ZCTA5 00602")
        self.assertEqual(zcta, "")
        self.assertEqual(status, "geo_id_label_mismatch")

    def test_exact_income(self):
        parsed = PIPELINE.parse_estimate("19454")
        self.assertEqual(parsed["value"], 19454.0)
        self.assertEqual(parsed["status"], "valid")

    def test_open_ended_income_not_used_as_exact(self):
        parsed = PIPELINE.parse_estimate("250,000+")
        self.assertIsNone(parsed["value"])
        self.assertEqual(parsed["bound"], 250000.0)
        self.assertEqual(parsed["direction"], "above")
        self.assertEqual(parsed["status"], "top_open_ended")

    def test_dash_is_not_zero(self):
        parsed = PIPELINE.parse_estimate("-")
        self.assertIsNone(parsed["value"])
        self.assertEqual(parsed["status"], "not_computed_dash")

    def test_moe_symbol(self):
        parsed = PIPELINE.parse_moe("***")
        self.assertIsNone(parsed["value"])
        self.assertEqual(parsed["status"], "cannot_compute_open_ended_median")


class StatisticsTests(unittest.TestCase):
    def test_linear_percentile(self):
        self.assertEqual(PIPELINE.percentile([1.0, 3.0], 0.5), 2.0)

    def test_midrank_ties_are_deterministic(self):
        result = PIPELINE.midrank_percentiles([("002", 20.0), ("001", 10.0), ("003", 20.0)])
        self.assertEqual(result["001"]["rank"], 1)
        self.assertEqual(result["002"]["rank"], 2)
        self.assertEqual(result["003"]["rank"], 2)
        self.assertEqual(result["002"]["tie_count"], 2)
        self.assertEqual(result["002"]["percentile"], result["003"]["percentile"])
        self.assertEqual(result["002"]["empirical_cdf"], 1.0)

    def test_single_observation_percentile(self):
        result = PIPELINE.midrank_percentiles([("only", 10.0)])
        self.assertEqual(result["only"]["percentile"], 0.5)


if __name__ == "__main__":
    unittest.main()
