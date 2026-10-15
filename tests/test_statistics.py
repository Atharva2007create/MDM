import math
import unittest
from unittest.mock import patch

import pandas as pd

from statistics_engine import (
    AnalysisValidationError,
    analyze_dataframe,
    calculate_descriptive_statistics,
    calculate_regression,
    calculate_spearman,
    perform_hypothesis_test,
    prepare_numeric_series,
    unavailable_regression,
)


class DescriptiveStatisticsTests(unittest.TestCase):
    def test_mean_and_odd_median(self):
        result = calculate_descriptive_statistics(pd.Series([1, 3, 5]))
        self.assertAlmostEqual(result["mean"], 3.0)
        self.assertAlmostEqual(result["median"], 3.0)

    def test_even_median(self):
        result = calculate_descriptive_statistics(pd.Series([1, 2, 7, 10]))
        self.assertAlmostEqual(result["median"], 4.5)

    def test_sample_standard_deviation(self):
        result = calculate_descriptive_statistics(pd.Series([2, 4, 4, 4, 5, 5, 7, 9]))
        self.assertAlmostEqual(result["sample_standard_deviation"], math.sqrt(32 / 7))


class AssociationTests(unittest.TestCase):
    def test_known_positive_spearman_relationship(self):
        result = calculate_spearman(pd.Series([1, 2, 3, 4, 5]), pd.Series([10, 20, 30, 40, 50]))
        self.assertAlmostEqual(result["coefficient"], 1.0)
        self.assertEqual(result["direction"], "strong positive")

    def test_known_negative_spearman_relationship(self):
        result = calculate_spearman(pd.Series([1, 2, 3, 4, 5]), pd.Series([50, 40, 30, 20, 10]))
        self.assertAlmostEqual(result["coefficient"], -1.0)
        self.assertEqual(result["direction"], "strong negative")

    def test_known_linear_regression(self):
        result = calculate_regression(pd.Series([1, 2, 3, 4]), pd.Series([3, 5, 7, 9]))
        self.assertAlmostEqual(result["slope"], 2.0)
        self.assertAlmostEqual(result["intercept"], 1.0)
        self.assertAlmostEqual(result["r_squared"], 1.0)

    def test_unavailable_regression_has_stable_null_contract(self):
        result = unavailable_regression("Regression is not defensible for this selection.")
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["slope"])
        self.assertIsNone(result["intercept"])
        self.assertIsNone(result["r_squared"])
        self.assertEqual(result["line_coordinates"], [])
        self.assertIn("not defensible", result["reason"])

    def test_analysis_preserves_other_results_when_regression_is_unavailable(self):
        dataframe = pd.DataFrame(
            {"internet": [1, 2, 3, 4], "learning": [2, 3, 5, 8]}
        )
        with patch(
            "statistics_engine.calculate_regression",
            side_effect=AnalysisValidationError("Regression is not defensible."),
        ):
            result = analyze_dataframe(
                dataframe, "internet", "learning", source_name="synthetic-test.csv"
            )
        self.assertEqual(result["correlation"]["status"], "available")
        self.assertEqual(result["regression"]["status"], "unavailable")
        self.assertIsNone(result["regression"]["slope"])
        self.assertEqual(result["visualization_data"]["regression_line"], [])

    def test_hypothesis_test_decisions(self):
        reject = perform_hypothesis_test({"coefficient": 0.9, "p_value": 0.01})
        retain = perform_hypothesis_test({"coefficient": 0.1, "p_value": 0.20})
        self.assertEqual(reject["decision"], "Reject H0")
        self.assertEqual(retain["decision"], "Fail to reject H0")

    def test_constant_variable_is_rejected(self):
        with self.assertRaisesRegex(AnalysisValidationError, "constant"):
            calculate_spearman(pd.Series([1, 1, 1]), pd.Series([1, 2, 3]))


class ValidationAndCleaningTests(unittest.TestCase):
    def test_documented_ordinal_scale_is_encoded(self):
        encoded, metadata = prepare_numeric_series(
            pd.Series(["Very Bad", "Average", "Very Good"]), "rating"
        )
        self.assertEqual(encoded.tolist(), [1.0, 3.0, 5.0])
        self.assertEqual(metadata["kind"], "ordered_rating")

    def test_three_level_satisfaction_scale_is_encoded(self):
        encoded, metadata = prepare_numeric_series(
            pd.Series(["Bad", "Average", "Good"]), "satisfaction"
        )
        self.assertEqual(encoded.tolist(), [1.0, 2.0, 3.0])
        self.assertIn("three-level", metadata["transformation"]["description"])

    def test_ambiguous_partial_ordinal_scale_is_rejected(self):
        with self.assertRaisesRegex(AnalysisValidationError, "ambiguous partial"):
            prepare_numeric_series(pd.Series(["Bad", "Good"]), "partial rating")

    def test_unordered_categories_are_rejected(self):
        with self.assertRaisesRegex(AnalysisValidationError, "not numeric"):
            prepare_numeric_series(pd.Series(["Laptop", "Mobile", "Desktop"]), "device")

    def test_missing_pairs_are_removed_and_reported(self):
        dataframe = pd.DataFrame(
            {
                "internet": [1, 2, None, 4, 5],
                "learning": [2, 4, 6, None, 10],
            }
        )
        result = analyze_dataframe(
            dataframe, "internet", "learning", source_name="synthetic-test.csv"
        )
        self.assertEqual(result["sample_size"], 3)
        self.assertEqual(result["missing_data"]["excluded_from_paired_analysis"], 2)

    def test_infinite_values_are_excluded_and_reported(self):
        dataframe = pd.DataFrame(
            {
                "internet": [1, 2, float("inf"), 4, 5],
                "learning": [2, 4, 6, 8, 10],
            }
        )
        result = analyze_dataframe(
            dataframe, "internet", "learning", source_name="synthetic-test.csv"
        )
        self.assertEqual(result["sample_size"], 4)
        self.assertEqual(result["missing_data"]["connectivity_missing_or_invalid"], 1)
        self.assertEqual(
            result["selected_variables"]["connectivity"]["processing"]["invalid_value_count"],
            1,
        )

    def test_duplicate_rows_are_retained_and_reported(self):
        dataframe = pd.DataFrame(
            {
                "internet": [1, 2, 3, 3],
                "learning": [2, 4, 6, 6],
            }
        )
        result = analyze_dataframe(
            dataframe, "internet", "learning", source_name="synthetic-test.csv"
        )
        self.assertEqual(result["dataset"]["duplicate_row_count"], 1)
        self.assertEqual(result["sample_size"], 4)
        self.assertTrue(any("retained" in warning for warning in result["warnings"]))

    def test_visualization_points_are_limited_without_changing_statistics(self):
        dataframe = pd.DataFrame(
            {
                "internet": range(1, 502),
                "learning": range(2, 503),
            }
        )
        result = analyze_dataframe(
            dataframe, "internet", "learning", source_name="synthetic-test.csv"
        )
        self.assertEqual(result["sample_size"], 501)
        self.assertEqual(len(result["visualization_data"]["scatter_points"]), 500)
        self.assertTrue(result["visualization_data"]["scatter_points_sampled"])


if __name__ == "__main__":
    unittest.main()
