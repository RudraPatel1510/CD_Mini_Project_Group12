"""
Web front-end for the Mini Compiler.

Run:   python app.py
Open:  http://localhost:5000
"""

import os

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from compiler import PHASES, compile_source

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
MAX_SOURCE_LENGTH = 100_000  # characters

app = Flask(__name__)


def sample_title(filename):
    """'03_else_if_ladder.txt' -> 'Else If Ladder'."""
    stem = os.path.splitext(filename)[0]
    words = stem.split("_")
    if words and words[0].isdigit():
        words = words[1:]
    return " ".join(word.capitalize() for word in words)


def load_samples(folder):
    samples = []
    if not os.path.isdir(folder):
        return samples
    for filename in sorted(os.listdir(folder)):
        if filename.endswith(".txt"):
            with open(os.path.join(folder, filename), encoding="utf-8") as handle:
                samples.append({"file": filename, "title": sample_title(filename), "code": handle.read()})
    return samples


def error_response(message, status=400):
    """A compile-style result describing a request problem (never a traceback)."""
    return jsonify({
        "success": False,
        "failed_phase": None,
        "phases": [{"name": phase, "status": "skipped"} for phase in PHASES],
        "errors": [{"phase": "Server", "message": message, "line": None, "column": None, "text": message}],
        "warnings": [],
    }), status


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/samples")
def samples():
    return jsonify({"groups": [
        {"name": "Valid Programs", "samples": load_samples(SAMPLES_DIR)},
        {"name": "Error Programs", "samples": load_samples(os.path.join(SAMPLES_DIR, "errors"))},
    ]})


@app.route("/api/compile", methods=["POST"])
def compile_endpoint():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("code"), str):
        return error_response("request body must be JSON like {\"code\": \"...\"}")
    code = data["code"]
    if len(code) > MAX_SOURCE_LENGTH:
        return error_response(f"program is too long (limit is {MAX_SOURCE_LENGTH} characters)")
    return jsonify(compile_source(code))


@app.errorhandler(Exception)
def handle_error(error):
    """Turn every unexpected error into clean JSON instead of a traceback page."""
    if isinstance(error, HTTPException):
        return error_response(f"{error.code} {error.name}", error.code)
    app.logger.exception("Unhandled error")
    return error_response("internal server error", 500)


if __name__ == "__main__":
    print("Mini Compiler running at http://localhost:5000  (press Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False)
