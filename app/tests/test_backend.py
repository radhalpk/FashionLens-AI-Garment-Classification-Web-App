import sys
import os
import json
import uuid
import tempfile
import pytest
from pathlib import Path

# Add app to path
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

# Mock paths for testing storage without corrupting real DB
with tempfile.TemporaryDirectory() as temp_dir:
    import fashion_agent.storage as storage
    storage.DB_DIR = Path(temp_dir) / "db"
    storage.DB_IMAGES_DIR = storage.DB_DIR / "images"
    storage.MASTER_ATTRIBUTES_FILE = storage.DB_DIR / "master_attributes.json"
    storage.OUTPUT_DIR = Path(temp_dir) / "output"
    storage.IMAGES_INFO_FILE = storage.OUTPUT_DIR / "images_info.json"

from fashion_agent.graph import classify_node, AgentState
from fashion_agent.models import GarmentClassification
from fashion_agent.storage import _update_master_attributes
from ui.app import app


# ── 1. UNIT TEST ──────────────────────────────────────────────────────────
def test_parse_llm_json_stripping():
    """Unit test for the regex parsing logic used in classify_node."""
    import re

    # Simulate Gemini's tendency to wrap json in markdown fences
    raw_response = "```json\n{\n  \"garment_type\": \"dress\",\n  \"style\": \"casual\",\n  \"material\": \"cotton\",\n  \"pattern\": \"solid\",\n  \"season\": \"summer\",\n  \"occasion\": \"everyday\",\n  \"consumer_profile\": \"young adult\",\n  \"trend_notes\": \"timeless\",\n  \"color_palette\": [\"blue\"],\n  \"location_context\": {\"continent\": \"North America\", \"country\": \"USA\", \"city\": \"NY\", \"setting\": \"street\"},\n  \"description\": \"A blue dress.\",\n  \"tags\": [\"blue dress\"]\n}\n```"

    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", raw_response.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned.strip())

    try:
        parsed = json.loads(cleaned)
        validated = GarmentClassification(**parsed)
        assert validated.garment_type == "dress"
        assert validated.color_palette == ["blue"]
    except Exception as e:
        pytest.fail(f"Failed to parse fenced JSON: {e}")


# ── 2. INTEGRATION TEST ───────────────────────────────────────────────────
def test_master_attributes_generation():
    """Integration test verifying storage engine generates correct filters."""
    # Create fake records mimicking db schema
    records = [
        {
            "id": "1",
            "classification": {
                "garment_type": "Sneakers",
                "consumer_profile": "Athletes",
                "location_context": {"continent": "Asia", "country": "Japan", "city": "Tokyo"}
            },
            "timestamp": "2026-03-15T12:00:00.000Z"
        },
        {
            "id": "2",
            "classification": {
                "garment_type": "sneakers", # Should deduplicate case-insensitively
                "consumer_profile": "Casual",
                "location_context": {"continent": "Europe", "country": "unknown", "city": "unknown"}
            },
            "timestamp": "2026-04-10T12:00:00.000Z"
        }
    ]

    _update_master_attributes(records)

    with open(storage.MASTER_ATTRIBUTES_FILE, "r") as f:
        master = json.load(f)

    assert "sneakers" in master["garment_type"]
    assert len(master["garment_type"]) == 1 # Deduplication check
    assert "athletes" in master["consumer_profile"]
    assert "japan" in master["country"]
    assert "unknown" not in master["country"] # 'unknown' should be filtered out
    assert "2026" in master["year"]
    assert "March" in master["month"]
    assert "April" in master["month"]


# ── 3. END-TO-END TEST ────────────────────────────────────────────────────
@pytest.fixture
def client():
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client

def test_flask_gallery_and_upload_routes(client):
    """End-to-end test hitting the primary routes of the Flask UI."""
    # Test index
    response = client.get('/')
    assert response.status_code == 200
    assert b"Inspiration Gallery" in response.data

    # Test upload page
    response = client.get('/upload')
    assert response.status_code == 200
    assert b"Upload Garment" in response.data

    # Note: We do not test actual POST /upload to avoid hitting the live Gemini API inside CI.
    # Instead, we test that the fallback works.
    response = client.post('/upload', data={})
    assert response.status_code == 302 # Redirect loop missing file flash
