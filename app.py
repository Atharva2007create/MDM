"""Phase 1 Flask foundation for the MDM mini-project."""

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)


@app.get("/")
def index():
    """Render the application's landing page."""
    return render_template("index.html")


@app.get("/api/health")
def health_check():
    """Report whether the backend is available."""
    return jsonify(status="ok", message="MDM backend is running")


@app.errorhandler(404)
def not_found(error):
    """Return JSON for unknown API routes and Flask's default page elsewhere."""
    if request.path.startswith("/api/"):
        return jsonify(status="error", message="API route not found"), 404
    return error


@app.errorhandler(500)
def internal_server_error(error):
    """Keep unexpected API errors machine-readable."""
    if request.path.startswith("/api/"):
        return jsonify(status="error", message="Internal server error"), 500
    return error


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
