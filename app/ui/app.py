"""
Flask UI for the Fashion Garment Classification app.

Run:
    python ui/app.py
"""

import sys
import os
import json
import uuid
from pathlib import Path
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, send_file, jsonify, flash
)

# Ensure app/ is on the path
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from fashion_agent.graph import classify_image
from fashion_agent.storage import copy_image_to_db, store_result, _load_existing_records, _save_records

# ── Paths ────────────────────────────────────────────────────────────
DB_DIR = APP_DIR / "db"
STAGING_DIR = DB_DIR / "staging"
IMAGES_INFO_FILE = DB_DIR / "images_info.json"

# Ensure directories exist
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# ── Flask app ────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)
app.secret_key = "fashion-agent-dev-key"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def load_records() -> list[dict]:
    return _load_existing_records()


def save_records(records: list[dict]) -> None:
    _save_records(records)


MASTER_ATTRIBUTES_FILE = DB_DIR / "master_attributes.json"

def load_filters() -> dict:
    """Load global filter options from master_attributes.json."""
    if MASTER_ATTRIBUTES_FILE.exists():
        with open(MASTER_ATTRIBUTES_FILE, "r") as f:
            return json.load(f)
    return {}


# ── Routes ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Gallery page with search and filters."""
    records = load_records()
    filters = load_filters()
    return render_template("index.html", records=records, filters=filters)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """Upload and classify a garment image."""
    if request.method == "POST":
        if "image" not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)

        file = request.files["image"]
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file type. Use JPG, PNG, WEBP, or GIF.", "error")
            return redirect(request.url)

        # 1. Save to staging
        safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        staging_path = STAGING_DIR / safe_name
        file.save(str(staging_path))

        try:
            # 2. Classify with the fashion agent
            classification = classify_image(str(staging_path))

            # 3. Copy to db/images/<date>/
            stored_path = copy_image_to_db(str(staging_path))

            # 4. Persist to images_info.json
            record = store_result(
                original_image_path=file.filename,
                stored_image_path=stored_path,
                classification=classification,
            )

            # 5. Clean up staging
            staging_path.unlink(missing_ok=True)

            flash(f"Image classified successfully!", "success")
            return redirect(url_for("detail", record_id=record.id))

        except Exception as e:
            staging_path.unlink(missing_ok=True)
            flash(f"Classification failed: {str(e)}", "error")
            return redirect(request.url)

    return render_template("upload.html")


@app.route("/image/<record_id>")
def detail(record_id):
    """Detail view for a single classified image."""
    records = load_records()
    record = next((r for r in records if r["id"] == record_id), None)
    if not record:
        flash("Image not found", "error")
        return redirect(url_for("index"))
    return render_template("detail.html", record=record)


@app.route("/serve-image/<record_id>")
def serve_image(record_id):
    """Serve the stored image file."""
    records = load_records()
    record = next((r for r in records if r["id"] == record_id), None)
    if not record:
        return "Not found", 404

    image_path_str = record["stored_image_path"]
    
    # Intelligently resolve relative paths without breaking legacy absolute paths
    image_path = Path(image_path_str)
    if not image_path.is_absolute():
        image_path = APP_DIR / image_path

    if not image_path.exists():
        return "Image file not found", 404

    return send_file(str(image_path))


@app.route("/api/annotate/<record_id>", methods=["POST"])
def annotate(record_id):
    """Add/update designer annotations for an image."""
    data = request.json
    records = load_records()

    for r in records:
        if r["id"] == record_id:
            r["annotations"] = {
                "user_tags": data.get("user_tags", []),
                "notes": data.get("notes", ""),
            }
            save_records(records)
            return jsonify({"status": "ok", "annotations": r["annotations"]})

    return jsonify({"status": "error", "message": "Record not found"}), 404


@app.route("/api/delete/<record_id>", methods=["DELETE"])
def delete_record(record_id):
    """Delete an image record."""
    records = load_records()
    records = [r for r in records if r["id"] != record_id]
    save_records(records)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print(f"Starting Fashion UI at http://localhost:5001")
    print(f"Images DB: {DB_DIR / 'images'}")
    print(f"Records: {IMAGES_INFO_FILE}")
    app.run(debug=True, port=5001)
