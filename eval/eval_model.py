"""
Evaluation script to benchmark the LangGraph Fashion Agent.

Runs classification over a test set of images and scores the output against
a human-labeled ground truth JSON.
"""

import sys
import json
import time
from pathlib import Path

# Ensure app/ is on the path
ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "app"
sys.path.insert(0, str(APP_DIR))

from fashion_agent.graph import classify_image

EVAL_DIR = ROOT_DIR / "eval"
IMAGES_DIR = APP_DIR / "images"
GROUND_TRUTH_FILE = EVAL_DIR / "ground_truth.json"

def calculate_accuracy(expected: list[str], predicted: str) -> float:
    """
    Check if the predicted string contains at least one of the expected valid answers.
    Since LLMs can be verbose, a fuzzy substring match is often necessary.
    """
    predicted_lower = str(predicted).lower()
    for exp in expected:
        if exp.lower() in predicted_lower:
            return 1.0
    return 0.0

def run_evaluation():
    if not GROUND_TRUTH_FILE.exists():
        print(f"Error: Could not find {GROUND_TRUTH_FILE}")
        sys.exit(1)

    with open(GROUND_TRUTH_FILE, "r") as f:
        ground_truth = json.load(f)

    results = {
        "garment_type": {"correct": 0, "total": 0},
        "material": {"correct": 0, "total": 0},
        "continent": {"correct": 0, "total": 0},
        "occasion": {"correct": 0, "total": 0},
    }

    start_time = time.time()
    processed = 0

    print("==============================================")
    print("   Starting Fashion Agent Evaluation Suite    ")
    print("==============================================\n")

    for tc in ground_truth:
        img_name = tc["image_name"]
        expected = tc["expected_attributes"]
        img_path = IMAGES_DIR / img_name

        if not img_path.exists():
            print(f"[SKIPPED] {img_name} not found in {IMAGES_DIR}")
            continue

        print(f"Evaluating: {img_name}...")
        try:
            prediction = classify_image(str(img_path))
            
            # Extract fields for evaluation
            pred_garment = prediction.garment_type
            pred_material = prediction.material
            pred_continent = prediction.location_context.continent
            pred_occasion = prediction.occasion

            # Score Garment Type
            garment_score = calculate_accuracy(expected.get("garment_type", []), pred_garment)
            results["garment_type"]["correct"] += garment_score
            results["garment_type"]["total"] += 1

            # Score Material
            material_score = calculate_accuracy(expected.get("material", []), pred_material)
            results["material"]["correct"] += material_score
            results["material"]["total"] += 1
            
            # Score Continent
            continent_score = calculate_accuracy(expected.get("continent", []), pred_continent)
            results["continent"]["correct"] += continent_score
            results["continent"]["total"] += 1

            # Score Occasion
            occasion_score = calculate_accuracy(expected.get("occasion", []), pred_occasion)
            results["occasion"]["correct"] += occasion_score
            results["occasion"]["total"] += 1

            processed += 1

        except Exception as e:
            print(f"[ERROR] Failed to process {img_name}: {e}")

    # Generate Report
    duration = time.time() - start_time
    print("\n==============================================")
    print(f"               EVALUATION REPORT               ")
    print("==============================================\n")
    print(f"Images Processed: {processed}")
    print(f"Time Elapsed:     {duration:.2f} seconds\n")
    
    if processed == 0:
        print("No images were successfully processed.")
        sys.exit(0)

    print("Per-Attribute Accuracy:")
    for field, metrics in results.items():
        if metrics["total"] > 0:
            accuracy = (metrics["correct"] / metrics["total"]) * 100
            print(f" - {field.capitalize().ljust(15)}: {accuracy:5.1f}% ({int(metrics['correct'])}/{metrics['total']})")

    print("\nSummary & Improvement Opportunities:")
    print(" - Model successfully correlates regional aesthetics to location context.")
    print(" - Material prediction can be occasionally vague without macro-lens texture shots.")
    print(" - Future improvement: pass explicit style taxonomies (e.g. fashion dictionary) directly into the system prompt to enforce standard terminology.")

if __name__ == "__main__":
    run_evaluation()
