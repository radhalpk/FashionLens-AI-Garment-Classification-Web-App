"""
Fashion Agent — Direct test runner.

Run this file directly to test the classification pipeline:
    python -m fashion_agent.main
    OR
    python fashion_agent/main.py
"""

import sys
import json
from pathlib import Path

# Ensure app/ is on the path so imports work when running this file directly
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from fashion_agent.graph import classify_image
from fashion_agent.storage import copy_image_to_db, store_result


def run(image_path: str) -> None:
    """Full pipeline: classify → copy to db → persist record."""
    source = Path(image_path)

    if not source.exists():
        print(f"Error: Image not found: {image_path}")
        return

    print(f"Processing: {image_path}")

    # 1. Run the classification agent
    print("Running classification agent...")
    classification = classify_image(str(source.resolve()))
    print("Classification complete.\n")

    # 2. Copy the image to db/images/<date>/
    stored_path = copy_image_to_db(str(source.resolve()))
    print(f"Image stored at: {stored_path}")

    # 3. Persist the result to output/images_info.json
    record = store_result(
        original_image_path=str(source.resolve()),
        stored_image_path=stored_path,
        classification=classification,
    )

    print(f"Record saved with ID: {record.id}\n")
    print("Classification Output:")
    print(json.dumps(classification.model_dump(), indent=2))


if __name__ == "__main__":
    # ── Test run with a sample image ──
    # test_image = APP_DIR / "images" / "Models of Indian Dresses.jpeg"

    test_image = APP_DIR / "images" / "Trending Ankara ShortGowns StylesFashionGalleryFlipmemes_com.jpeg"
    run(str(test_image))
