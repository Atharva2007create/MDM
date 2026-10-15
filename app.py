"""Flask application for the MDM mini-project."""

from io import BytesIO
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import MethodNotAllowed, RequestEntityTooLarge

from statistics_engine import (
    AnalysisValidationError,
    analyze_dataframe,
    preview_dataframe,
)


app = Flask(__name__)
MAX_CSV_SIZE = 5 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_CSV_SIZE + (64 * 1024)
DEFAULT_DATASET = Path(app.root_path) / "data" / "ONLINE EDUCATION SYSTEM REVIEW.csv"


@app.get("/")
def index():
    """Render the application's landing page."""
    return render_template("index.html")


@app.get("/api/health")
def health_check():
    """Report whether the backend is available."""
    return jsonify(status="ok", message="MDM backend is running")


def _error(message, status_code):
    return jsonify(status="error", message=message), status_code


def _read_uploaded_csv(upload):
    filename = (upload.filename or "").strip()
    if not filename:
        raise AnalysisValidationError("No CSV file was selected.")
    if Path(filename).suffix.casefold() != ".csv":
        raise AnalysisValidationError("Unsupported file format. Upload a .csv file.")

    content = upload.stream.read(MAX_CSV_SIZE + 1)
    if len(content) > MAX_CSV_SIZE:
        raise RequestEntityTooLarge()
    if not content:
        raise AnalysisValidationError("The uploaded CSV file is empty.")
    return _parse_csv(content), filename


def _parse_csv(content):
    if b"\x00" in content:
        raise AnalysisValidationError(
            "The uploaded file contains null bytes and is not a valid text CSV."
        )
    try:
        dataframe = pd.read_csv(BytesIO(content))
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
        raise AnalysisValidationError(
            "The uploaded file is not a readable CSV."
        ) from error
    if dataframe.empty or len(dataframe.columns) == 0:
        raise AnalysisValidationError("The CSV contains no data rows or columns.")
    return dataframe


def _load_request_dataframe():
    source = request.form.get("source", "").strip().casefold()
    upload = request.files.get("file")
    has_upload = upload is not None and bool((upload.filename or "").strip())

    if source and source != "default":
        raise AnalysisValidationError("source must be 'default' when provided.")
    if source == "default" and has_upload:
        raise AnalysisValidationError("Provide either a CSV upload or source=default, not both.")
    if source == "default":
        if not DEFAULT_DATASET.is_file():
            raise AnalysisValidationError("The verified default dataset is not available.")
        try:
            return pd.read_csv(DEFAULT_DATASET), DEFAULT_DATASET.name
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as error:
            raise AnalysisValidationError("The default dataset could not be read.") from error
    if not has_upload:
        raise AnalysisValidationError("Provide a CSV file or set source=default.")
    return _read_uploaded_csv(upload)


@app.post("/api/preview")
def preview_dataset():
    """Validate and summarize an uploaded or verified local CSV."""
    try:
        dataframe, source_name = _load_request_dataframe()
        return jsonify(dataset={"source": source_name, **preview_dataframe(dataframe)})
    except AnalysisValidationError as error:
        return _error(str(error), 400)


@app.post("/api/analyze")
def analyze_dataset():
    """Calculate descriptive and inferential statistics for selected columns."""
    try:
        dataframe, source_name = _load_request_dataframe()
        result = analyze_dataframe(
            dataframe,
            request.form.get("connectivity_column", "").strip(),
            request.form.get("learning_column", "").strip(),
            source_name=source_name,
        )
        return jsonify(result)
    except AnalysisValidationError as error:
        return _error(str(error), 400)


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(error):
    """Return a clear response when a request exceeds the CSV size limit."""
    return _error("CSV file exceeds the 5 MB upload limit.", 413)


@app.errorhandler(404)
def not_found(error):
    """Return JSON for unknown API routes and Flask's default page elsewhere."""
    if request.path.startswith("/api/"):
        return jsonify(status="error", message="API route not found"), 404
    return error


@app.errorhandler(MethodNotAllowed)
def method_not_allowed(error):
    """Return JSON when an API route is called with the wrong HTTP method."""
    if request.path.startswith("/api/"):
        return _error("HTTP method not allowed for this API route.", 405)
    return error


@app.errorhandler(500)
def internal_server_error(error):
    """Keep unexpected API errors machine-readable."""
    if request.path.startswith("/api/"):
        return jsonify(status="error", message="Internal server error"), 500
    return error


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
