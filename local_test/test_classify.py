"""
Fashion Garment Classification Test
Send a garment image to Gemini via LangChain and get structured JSON classification output.
"""

import json
import base64
from pathlib import Path

from langchain_core.messages import HumanMessage
from llm_client import make_vision_llm


def encode_image(image_path: str) -> tuple[str, str]:
    """Read an image file and return (base64_data, mime_type)."""
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    mime_type = mime_map.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return data, mime_type


CLASSIFICATION_PROMPT = """
You are a fashion garment classification expert.

Analyze the provided garment image and return a JSON object with the following fields.
Be as detailed and accurate as possible.

Return ONLY valid JSON — no markdown fences, no commentary.

{
  "description": "A rich natural-language description of the garment and its styling context (2-4 sentences).",
  "garment_type": "e.g. dress, jacket, trousers, skirt, blouse, coat, etc.",
  "style": "e.g. streetwear, bohemian, minimalist, classic, avant-garde, casual, formal, etc.",
  "material": "e.g. cotton, silk, denim, leather, wool, polyester, linen, knit, etc.",
  "color_palette": ["list of dominant colors, e.g. 'navy blue', 'ivory', 'burnt orange'"],
  "pattern": "e.g. solid, striped, floral, plaid, geometric, abstract, animal print, etc.",
  "season": "e.g. spring/summer, fall/winter, transitional, all-season",
  "occasion": "e.g. everyday, office, evening, festival, resort, athleisure, bridal, etc.",
  "consumer_profile": "e.g. young professional, Gen-Z trend-forward, luxury mature, budget-conscious, etc.",
  "trend_notes": "Any notable trend observations — e.g. oversized silhouette, Y2K revival, quiet luxury, artisan craft, etc.",
  "location_context": {
    "continent": "best guess of origin/inspiration continent",
    "country": "best guess of country, or 'unknown'",
    "city": "best guess of city, or 'unknown'",
    "setting": "e.g. street market, boutique, runway, outdoor, studio, etc."
  },
  "tags": ["list of searchable tags summarizing key attributes"]
}
"""


def classify_image(image_path: str) -> dict:
    """Send an image to Gemini and get structured garment classification."""
    image_data, mime_type = encode_image(image_path)

    llm = make_vision_llm()

    message = HumanMessage(
        content=[
            {"type": "text", "text": CLASSIFICATION_PROMPT},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
            },
        ]
    )

    response = llm.invoke([message])
    result = json.loads(response.content)
    return result


if __name__ == "__main__":
    # Resolve image path relative to this script's directory
    script_dir = Path(__file__).parent
    # image_path = r"/Users/manikantamb/_MyFiles/Work_/MyWork_Local/Fashion Garmet Classification & Inspiration Web App/app/images/Trending Ankara ShortGowns StylesFashionGalleryFlipmemes_com.jpeg"
    image_path = r"/Users/manikantamb/_MyFiles/Work_/MyWork_Local/Fashion Garmet Classification & Inspiration Web App/app/images/Models of Indian Dresses.jpeg"

    print(f"Classifying: {image_path}\n")
    result = classify_image(str(image_path))
    print(json.dumps(result, indent=2))
