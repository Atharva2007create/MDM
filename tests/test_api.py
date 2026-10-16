from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from app import app


VALID_CSV = b"internet,learning,note\n1,2,a\n2,4,b\n3,6,c\n4,8,d\n5,10,e\n"
NONSIGNIFICANT_NEGATIVE_CSV = b"internet,learning\n1,3\n2,5\n3,1\n4,4\n5,2\n"


class ApiTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_health_endpoint_remains_functional(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_homepage_remains_functional(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Internet Speed and Online Learning Experience", response.data)

    def test_phase_one_static_assets_and_health_status_wiring(self):
        homepage = self.client.get("/")
        stylesheet = self.client.get("/static/style.css")
        javascript = self.client.get("/static/app.js")
        try:
            self.assertEqual(stylesheet.status_code, 200)
            self.assertEqual(javascript.status_code, 200)
            self.assertIn(b'id="backend-status"', homepage.data)
            self.assertIn(b'fetch("/api/health"', javascript.data)
            self.assertIn(b"Backend connected", javascript.data)
            self.assertIn(b'replaceChildren(toast)', javascript.data)
            self.assertIn(b"[hidden]{display:none!important}", stylesheet.data)
            self.assertIn(b".data-tables>.panel{min-width:0}", stylesheet.data)
            self.assertIn(b'/static/favicon.svg', homepage.data)
        finally:
            homepage.close()
            stylesheet.close()
            javascript.close()

    def test_phase_three_dashboard_contract(self):
        homepage_response = self.client.get("/")
        javascript_response = self.client.get("/static/app.js")
        chart_response = self.client.get("/static/vendor/chartjs/chart.umd.min.js")
        try:
            homepage = homepage_response.get_data(as_text=True)
            javascript = javascript_response.get_data(as_text=True)
            for screen in (
                "overview",
                "dataset",
                "analysis",
                "visualizations",
                "findings",
                "report",
            ):
                self.assertIn(f'data-screen-panel="{screen}"', homepage)
            self.assertIn("/static/vendor/chartjs/chart.umd.min.js", homepage)
            self.assertNotIn("cdn.jsdelivr.net/npm/chart.js", homepage)
            self.assertEqual(chart_response.status_code, 200)
            self.assertIn(b"Chart.js v4.5.1", chart_response.data[:100])
            self.assertIn('jsonRequest("/api/preview"', javascript)
            self.assertIn('jsonRequest("/api/analyze"', javascript)
            self.assertIn('fetch("/api/report/pdf"', javascript)
            self.assertIn("chart?.destroy()", javascript)
            self.assertIn("does not establish causation", javascript)
            self.assertIn("invalidateAnalysis", javascript)
            self.assertIn('id="download-findings-pdf"', homepage)
            self.assertIn('id="download-report-pdf"', homepage)
            self.assertNotIn("PDF Export · Phase 4", homepage)
            self.assertNotIn("Mbps speed", homepage)
        finally:
            homepage_response.close()
            javascript_response.close()
            chart_response.close()

    def test_homepage_and_health_do_not_require_default_dataset(self):
        with patch("app.DEFAULT_DATASET", Path("missing-dataset.csv")):
            self.assertEqual(self.client.get("/").status_code, 200)
            self.assertEqual(self.client.get("/api/health").status_code, 200)

    def test_unknown_api_route_returns_json_error(self):
        response = self.client.get("/api/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["status"], "error")

    def test_wrong_api_method_returns_json_error(self):
        response = self.client.get("/api/preview")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.get_json()["status"], "error")

    def test_valid_dataset_preview(self):
        response = self.client.post(
            "/api/preview",
            data={"file": (BytesIO(VALID_CSV), "students.csv")},
            content_type="multipart/form-data",
        )
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["dataset"]["row_count"], 5)
        self.assertEqual(payload["dataset"]["columns"], ["internet", "learning", "note"])
        self.assertEqual(payload["dataset"]["duplicate_row_count"], 0)

    def test_valid_analysis_response(self):
        response = self.client.post(
            "/api/analyze",
            data={
                "file": (BytesIO(VALID_CSV), "students.csv"),
                "connectivity_column": "internet",
                "learning_column": "learning",
            },
            content_type="multipart/form-data",
        )
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["sample_size"], 5)
        self.assertAlmostEqual(payload["correlation"]["coefficient"], 1.0)
        self.assertAlmostEqual(payload["regression"]["slope"], 2.0)
        self.assertEqual(payload["hypothesis_test"]["decision"], "Reject H0")
        self.assertEqual(len(payload["visualization_data"]["scatter_points"]), 5)
        self.assertNotIn("NaN", response.get_data(as_text=True))

    def test_invalid_column_selection(self):
        response = self.client.post(
            "/api/analyze",
            data={
                "file": (BytesIO(VALID_CSV), "students.csv"),
                "connectivity_column": "missing",
                "learning_column": "learning",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("not found", response.get_json()["message"])

    def test_invalid_csv_is_rejected(self):
        response = self.client.post(
            "/api/preview",
            data={"file": (BytesIO(b'one,two\n"unterminated'), "broken.csv")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("not a readable CSV", response.get_json()["message"])

    def test_null_byte_csv_is_rejected(self):
        response = self.client.post(
            "/api/preview",
            data={"file": (BytesIO(b"\x00value\n\x001\n"), "binary.csv")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("null bytes", response.get_json()["message"])

    def test_non_csv_extension_is_rejected(self):
        response = self.client.post(
            "/api/preview",
            data={"file": (BytesIO(VALID_CSV), "students.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported file format", response.get_json()["message"])

    def test_missing_data_source_is_rejected(self):
        response = self.client.post("/api/preview")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Provide a CSV file", response.get_json()["message"])

    def test_empty_csv_is_rejected(self):
        response = self.client.post(
            "/api/preview",
            data={"file": (BytesIO(b""), "empty.csv")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("empty", response.get_json()["message"])

    def test_oversized_csv_is_rejected(self):
        with patch("app.MAX_CSV_SIZE", 10):
            response = self.client.post(
                "/api/preview",
                data={"file": (BytesIO(b"value\n1\n2\n3\n"), "large.csv")},
                content_type="multipart/form-data",
            )
        self.assertEqual(response.status_code, 413)
        self.assertIn("5 MB", response.get_json()["message"])

    def test_file_and_default_source_conflict_is_rejected(self):
        response = self.client.post(
            "/api/preview",
            data={
                "source": "default",
                "file": (BytesIO(VALID_CSV), "students.csv"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("either", response.get_json()["message"])

    def test_unordered_analysis_column_is_rejected(self):
        response = self.client.post(
            "/api/analyze",
            data={
                "file": (BytesIO(VALID_CSV), "students.csv"),
                "connectivity_column": "note",
                "learning_column": "learning",
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("not numeric", response.get_json()["message"])

    def test_default_dataset_preview(self):
        response = self.client.post("/api/preview", data={"source": "default"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["dataset"]["row_count"], 1033)

    def test_default_dataset_analysis(self):
        response = self.client.post(
            "/api/analyze",
            data={
                "source": "default",
                "connectivity_column": "Internet facility in your locality",
                "learning_column": "Your interaction in online mode",
            },
        )
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["sample_size"], 1033)
        self.assertEqual(payload["correlation"]["status"], "available")
        self.assertEqual(payload["regression"]["status"], "available")
        self.assertTrue(payload["visualization_data"]["scatter_points_sampled"])

    def test_default_dataset_pdf_report(self):
        response = self.client.post(
            "/api/report/pdf",
            data={
                "source": "default",
                "connectivity_column": "Internet facility in your locality",
                "learning_column": "Your interaction in online mode",
            },
        )
        content = response.get_data()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn(
            'attachment; filename=NetLearn_Analysis_Report.pdf',
            response.headers["Content-Disposition"],
        )
        self.assertTrue(content.startswith(b"%PDF-"))
        self.assertGreater(len(content), 10_000)
        self.assertIn(b"Research Objective", content)
        self.assertIn(b"Hypothesis Testing", content)
        self.assertIn(b"Internet facility in your locality", content)
        self.assertIn(b"Your interaction in online mode", content)

    def test_uploaded_csv_pdf_uses_current_variables_and_calculations(self):
        response = self.client.post(
            "/api/report/pdf",
            data={
                "file": (BytesIO(VALID_CSV), "students.csv"),
                "connectivity_column": "internet",
                "learning_column": "learning",
            },
            content_type="multipart/form-data",
        )
        content = response.get_data()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(content.startswith(b"%PDF-"))
        self.assertIn(b"students.csv", content)
        self.assertIn(b"y = 2x + 0", content)
        self.assertIn(b"Reject H0", content)

    def test_pdf_invalid_request_returns_json_error(self):
        response = self.client.post(
            "/api/report/pdf",
            data={
                "source": "default",
                "connectivity_column": "missing",
                "learning_column": "Your interaction in online mode",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.mimetype, "application/json")
        self.assertIn("not found", response.get_json()["message"])

    def test_pdf_preserves_negative_nonsignificant_interpretation(self):
        response = self.client.post(
            "/api/report/pdf",
            data={
                "file": (BytesIO(NONSIGNIFICANT_NEGATIVE_CSV), "negative.csv"),
                "connectivity_column": "internet",
                "learning_column": "learning",
            },
            content_type="multipart/form-data",
        )
        content = response.get_data()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"moderate negative", content)
        self.assertIn(b"Fail to reject H0", content)
        self.assertNotIn(b"Reject H0", content.replace(b"Fail to reject H0", b""))


if __name__ == "__main__":
    unittest.main()
