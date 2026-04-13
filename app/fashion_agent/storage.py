"""
Storage utilities — copy images to db/images/<date>/ and persist
classification records to output/images_info.json.
"""

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from .models import GarmentClassification, ImageRecord


# Directories relative to the app/ folder
APP_DIR = Path(__file__).resolve().parent.parent
DB_DIR = APP_DIR / "db"
DB_IMAGES_DIR = DB_DIR / "images"
MASTER_ATTRIBUTES_FILE = DB_DIR / "master_attributes.json"
IMAGES_INFO_FILE = DB_DIR / "images_info.json"


def _get_today_folder() -> Path:
    """Return db/images/YYYY-MM-DD/ folder, creating it if needed."""
    today = datetime.now().strftime("%Y-%m-%d")
    folder = DB_IMAGES_DIR / today
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def copy_image_to_db(source_path: str) -> str:
    """Copy the source image into db/images/<date>/ and return the stored path."""
    source = Path(source_path)
    dest_folder = _get_today_folder()
    dest = dest_folder / source.name

    # If a file with the same name already exists, add a suffix
    if dest.exists():
        stem = source.stem
        suffix = source.suffix
        dest = dest_folder / f"{stem}_{uuid.uuid4().hex[:8]}{suffix}"

    shutil.copy2(str(source), str(dest))
    return str(dest.relative_to(APP_DIR))


def _load_existing_records() -> list[dict]:
    """Load existing records from images_info.json."""
    if IMAGES_INFO_FILE.exists():
        with open(IMAGES_INFO_FILE, "r") as f:
            return json.load(f)
    return []


def _update_master_attributes(records: list[dict]) -> None:
    """Extract distinct attributes from all records and save to db/master_attributes.json."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    master = {
        "garment_type": set(),
        "style": set(),
        "material": set(),
        "pattern": set(),
        "season": set(),
        "occasion": set(),
        "consumer_profile": set(),
        "trend_notes": set(),
        "color_palette": set(),
        "continent": set(),
        "country": set(),
        "city": set(),
        "year": set(),
        "month": set(),
        "tags": set(),
        "user_tags": set()
    }

    for r in records:
        c = r.get("classification", {})
        for field in ["garment_type", "style", "material", "pattern", "season", "occasion", "consumer_profile", "trend_notes"]:
            val = c.get(field, "")
            # Split comma-separated values to distinct elements
            for v in str(val).split(","):
                v = v.strip()
                if v and v.lower() != 'unknown':
                    master[field].add(v.lower())

        for color in c.get("color_palette", []):
            master["color_palette"].add(color.strip().lower())
            
        for tag in c.get("tags", []):
            master["tags"].add(tag.strip().lower())

        loc = c.get("location_context", {})
        if loc.get("continent") and loc.get("continent").lower() != "unknown":
            master["continent"].add(loc["continent"].strip().lower())
        if loc.get("country") and loc.get("country").lower() != "unknown":
            master["country"].add(loc["country"].strip().lower())
        if loc.get("city") and loc.get("city").lower() != "unknown":
            master["city"].add(loc["city"].strip().lower())
            
        timestamp = r.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                master["year"].add(str(dt.year))
                master["month"].add(dt.strftime("%B")) # "January", "February", etc.
            except ValueError:
                pass
            
        annot = r.get("annotations", {})
        if annot:
            for utag in annot.get("user_tags", []):
                master["user_tags"].add(utag.strip().lower())

    # Convert sets to sorted lists
    sorted_master = {k: sorted(list(v)) for k, v in master.items()}
    
    with open(MASTER_ATTRIBUTES_FILE, "w") as f:
        json.dump(sorted_master, f, indent=2)


def _save_records(records: list[dict]) -> None:
    """Save records to images_info.json and update master attributes."""
    with open(IMAGES_INFO_FILE, "w") as f:
        json.dump(records, f, indent=2)
        
    _update_master_attributes(records)


def store_result(
    original_image_path: str,
    stored_image_path: str,
    classification: GarmentClassification,
) -> ImageRecord:
    """
    Create an ImageRecord, append it to images_info.json, and return it.
    """
    record = ImageRecord(
        id=uuid.uuid4().hex,
        original_image_path=original_image_path,
        stored_image_path=stored_image_path,
        timestamp=datetime.now().isoformat(),
        classification=classification,
    )

    records = _load_existing_records()
    records.append(record.model_dump())
    _save_records(records)

    return record
