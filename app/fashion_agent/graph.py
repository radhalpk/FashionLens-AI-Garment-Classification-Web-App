"""
LangGraph-based fashion classification agent.

Single-node graph that takes an image, sends it to Gemini,
and returns a validated GarmentClassification.
"""

import json
import re
import base64
from pathlib import Path
from typing import TypedDict, Optional

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.llm_client import make_vision_llm

from .models import GarmentClassification
from .prompt import CLASSIFICATION_PROMPT


# ── State ────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    image_path: str
    image_data: str
    mime_type: str
    classification: Optional[dict]
    raw_response: str


# ── Nodes ────────────────────────────────────────────────────────────
def encode_image_node(state: AgentState) -> dict:
    """Read and base64-encode the image."""
    path = Path(state["image_path"])
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
    return {"image_data": data, "mime_type": mime_type}


def classify_node(state: AgentState) -> dict:
    """Send the image to Gemini and parse structured output."""
    llm = make_vision_llm()

    message = HumanMessage(
        content=[
            {"type": "text", "text": CLASSIFICATION_PROMPT},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{state['mime_type']};base64,{state['image_data']}"},
            },
        ]
    )

    response = llm.invoke([message])
    raw = response.content

    # Strip markdown fences if present (```json ... ``` or ``` ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned.strip())

    # Parse and validate through Pydantic
    parsed = json.loads(cleaned)
    validated = GarmentClassification(**parsed)

    return {
        "classification": validated.model_dump(),
        "raw_response": raw,
    }


# ── Graph ────────────────────────────────────────────────────────────
def build_graph():
    """Build the fashion classification LangGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("encode_image", encode_image_node)
    graph.add_node("classify", classify_node)

    graph.add_edge(START, "encode_image")
    graph.add_edge("encode_image", "classify")
    graph.add_edge("classify", END)

    return graph.compile()


# ── Public API ───────────────────────────────────────────────────────
def classify_image(image_path: str) -> GarmentClassification:
    """Run the classification agent on an image and return validated output."""
    agent = build_graph()
    result = agent.invoke({
        "image_path": image_path,
        "image_data": "",
        "mime_type": "",
        "classification": None,
        "raw_response": "",
    })
    return GarmentClassification(**result["classification"])
