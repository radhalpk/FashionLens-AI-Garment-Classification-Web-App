"""Pydantic models for garment classification output."""

from datetime import datetime
from pydantic import BaseModel, Field


class LocationContext(BaseModel):
    continent: str = Field(description="Best guess of origin/inspiration continent")
    country: str = Field(default="unknown", description="Best guess of country")
    city: str = Field(default="unknown", description="Best guess of city")
    setting: str = Field(description="e.g. street market, boutique, runway, outdoor, studio")


class GarmentClassification(BaseModel):
    """Structured output from the fashion classification model."""
    description: str = Field(description="Rich natural-language description of the garment (2-4 sentences)")
    garment_type: str = Field(description="e.g. dress, jacket, trousers, skirt, blouse, coat")
    style: str = Field(description="e.g. streetwear, bohemian, minimalist, classic, formal")
    material: str = Field(description="e.g. cotton, silk, denim, leather, wool, polyester")
    color_palette: list[str] = Field(description="List of dominant colors")
    pattern: str = Field(description="e.g. solid, striped, floral, plaid, geometric, abstract")
    season: str = Field(description="e.g. spring/summer, fall/winter, transitional, all-season")
    occasion: str = Field(description="e.g. everyday, office, evening, festival, resort, bridal")
    consumer_profile: str = Field(description="Target consumer profile")
    trend_notes: str = Field(description="Notable trend observations")
    designer: str = Field(default="unknown", description="Best guess of the designer or brand")
    location_context: LocationContext = Field(description="Location and setting context")
    tags: list[str] = Field(description="Searchable tags summarizing key attributes")


class ImageRecord(BaseModel):
    """Full record stored in images_info.json for each processed image."""
    id: str = Field(description="Unique identifier for this record")
    original_image_path: str = Field(description="Original source image path")
    stored_image_path: str = Field(description="Path where the image is stored in db/images/")
    timestamp: str = Field(description="ISO timestamp of when the image was processed")
    classification: GarmentClassification = Field(description="Model classification output")
