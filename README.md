# FashionLens: AI Garment Classification Web App

FashionLens is a lightweight, AI-powered web application that helps fashion designers organize, search, and reuse inspiration imagery captured in the field. Built as a proof-of-concept, it leverages multimodal large language models (LLMs) via LangGraph to automatically extract highly structured metadata from raw images.

## Features
- **Intelligent Classification**: Upload any fashion image, and Gemini 2.0 Vision automatically identifies the Garment Type, Style, Material, Context, Setting, and Color Palette.
- **Dynamic Filtering**: A real-time, purely native HTML5 accordion filter system automatically parses the unified dataset of your wardrobe without bloated JS logic.
- **Searchable Index**: Perform lightning-fast, client-side, multi-field fuzzy text searches across descriptions and deep metadata.
- **Designer Annotations**: Supplement the AI's output with your own context, adding custom searchable tags and observations.

---

## Setup & Installation

### Requirements
- Python 3.10+
- Google API Key (for Gemini 2.0 Flash)
- [uv](https://docs.astral.sh/uv/) (Recommended for lightning-fast setup)

### Configuration
1. Clone this repository and navigate to the project directory.
2. Configure your environment variables via a `.env` file at the project root:
   ```env
   GOOGLE_API_KEY2=your_gemini_api_key_here
   ```
3. Install dependencies and bootstrap the project natively using `uv`:
   ```bash
   # Sync dependencies and create a dedicated virtual environment
   uv sync
   ```
   *(Alternatively, use standard pip: `pip install .[dev]`)*

### Running the Application
Using `uv run` handles the virtual environment context for you automatically:
```bash
uv run python app/ui/app.py
```
Open **http://localhost:5001** in your browser. *(Note: Port 5001 is used intentionally to avoid conflicts with MacOS built-in AirPlay listeners on 5000).*

---

## Architectural Choices
1. **LangGraph over raw LLM calls:** We wrapped Gemini Vision through LangGraph. While slightly heavier, it enforces strict step-based agent flows. In the future, this makes it incredibly simple to add a "reflection" node if the LLM hallucinated, or a routing node (e.g. passing shoes to a different specialized LLM compared to dresses).
2. **Pydantic Validation:** The LLM's classification logic explicitly requires a JSON output mapped tightly to a Pydantic `GarmentClassification` schema. This strictly casts fields like `color_palette` to lists rather than CSV strings, ensuring frontend logic doesn't crash during rendering.
3. **Flat File Data Store (`db/`):** To keep the proof-of-concept completely lightweight without Dockerized database dependencies (PostgreSQL/MongoDB), we used atomic file copies for image blob storage (`db/images/YYYY-MM-DD/`) and maintained an append-only JSON master file (`images_info.json`). 
4. **Master Attributes Cache:** `storage.py` actively intercepts writes and parses the full index down into a deduplicated JSON file (`master_attributes.json`). This ensures the UI's dropdown menus generate instantly without looping records mid-render.

---

## Trade-offs & Limitations
1. **Client-Side Search:** Currently, searching and filtering logic lives entirely in `main.js`. This is snappy for < 10,000 images but will bottleneck client memory at scale. A full production implementation would offload this to Elasticsearch or Postgres full-text indices.
2. **Synchronous Uploads:** The Flask app currently waits synchronously for the LLM to process an image. If the API lags, the UI hangs. A production-ready release would rely on a background celery worker and a polling loading screen.
3. **Basic File System Locking:** The JSON Flat File store is perfectly fine for single-user dev testing, but is susceptible to race conditions if multiple designers concurrently bulk-upload imagery.

---

## Evaluation Summary

Included in the `/eval` folder is a benchmarking suite. 

**Methodology**: We mapped a subset of local testing images against an expected `ground_truth.json` file. The test harness loops over these images, pings the model in isolation, and scores the resulting parsed objects against the expected tags using a fuzzy string-presence algorithm.

**Report Output**:
```
Images Processed: 2
Time Elapsed:     87.63 seconds

Per-Attribute Accuracy:
 - Garment_type   : 100.0% (2/2)
 - Material       : 100.0% (2/2)
 - Continent      : 100.0% (2/2)
 - Occasion       : 100.0% (2/2)

Summary & Improvement Opportunities:
 - Model successfully correlates regional aesthetics to location context.
 - Material prediction can be occasionally vague without macro-lens texture shots.
 - Future improvement: pass explicit style taxonomies (e.g. fashion dictionary) directly into the system prompt to enforce standard terminology.
```

---

## Testing Pipeline
Execute the automated testing suite from the project root using `pytest`. The test framework utilizes `tempfile` storage overrides so it does not irreparably touch the primary testing DB.
```bash
python3 -m pytest tests/test_backend.py 
```
Includes:
- **Unit Testing:** Validates regex markdown-fencing strippers.
- **Integration Testing:** Assesses the `_update_master_attributes` algorithm's ability to recursively extract correct datasets.
- **E2E Testing:** Simulates Flask HTTP traffic against active routes natively.
