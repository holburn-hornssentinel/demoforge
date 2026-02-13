"""Google Vision API integration for screenshot intelligence."""

import os
from pathlib import Path
from typing import Any

from google.cloud import vision


class VisionAnalyzer:
    """Analyzes screenshots using Google Vision API."""

    def __init__(self, credentials_path: str | None = None) -> None:
        """Initialize Vision analyzer.

        Args:
            credentials_path: Optional path to service account JSON.
                             If not provided, uses GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        self.client = vision.ImageAnnotatorClient()

    def detect_labels(self, image_path: Path, max_results: int = 10) -> list[dict[str, Any]]:
        """Detect labels in an image.

        Args:
            image_path: Path to image file
            max_results: Maximum number of labels to return

        Returns:
            List of labels with descriptions and scores
        """
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.label_detection(image=image, max_results=max_results)

        return [
            {
                "description": label.description,
                "score": label.score,
                "topicality": label.topicality,
            }
            for label in response.label_annotations
        ]

    def detect_text(self, image_path: Path) -> dict[str, Any]:
        """Detect and extract text from an image (OCR).

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with full_text and individual text annotations
        """
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)

        if not response.text_annotations:
            return {"full_text": "", "annotations": []}

        # First annotation is the full text
        full_text = response.text_annotations[0].description

        # Rest are individual words/phrases
        annotations = [
            {
                "text": annotation.description,
                "bounds": [
                    {"x": vertex.x, "y": vertex.y}
                    for vertex in annotation.bounding_poly.vertices
                ],
            }
            for annotation in response.text_annotations[1:]
        ]

        return {"full_text": full_text, "annotations": annotations}

    def detect_objects(
        self, image_path: Path, min_confidence: float = 0.5
    ) -> list[dict[str, Any]]:
        """Detect objects in an image.

        Args:
            image_path: Path to image file
            min_confidence: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            List of detected objects with names, confidence, and bounding boxes
        """
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.object_localization(image=image)

        return [
            {
                "name": obj.name,
                "confidence": obj.score,
                "bounds": [
                    {"x": vertex.x, "y": vertex.y}
                    for vertex in obj.bounding_poly.normalized_vertices
                ],
            }
            for obj in response.localized_object_annotations
            if obj.score >= min_confidence
        ]

    def detect_logos(self, image_path: Path) -> list[dict[str, Any]]:
        """Detect logos in an image.

        Args:
            image_path: Path to image file

        Returns:
            List of detected logos with descriptions and confidence
        """
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.logo_detection(image=image)

        return [
            {
                "description": logo.description,
                "score": logo.score,
                "bounds": [
                    {"x": vertex.x, "y": vertex.y}
                    for vertex in logo.bounding_poly.vertices
                ],
            }
            for logo in response.logo_annotations
        ]

    def get_image_properties(self, image_path: Path) -> dict[str, Any]:
        """Get image properties including dominant colors.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with dominant colors and other properties
        """
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.image_properties(image=image)

        dominant_colors = response.image_properties_annotation.dominant_colors

        return {
            "dominant_colors": [
                {
                    "color": {
                        "red": color.color.red,
                        "green": color.color.green,
                        "blue": color.color.blue,
                    },
                    "score": color.score,
                    "pixel_fraction": color.pixel_fraction,
                }
                for color in dominant_colors.colors[:5]  # Top 5 colors
            ]
        }

    def analyze_screenshot(
        self, image_path: Path, detect_all: bool = True
    ) -> dict[str, Any]:
        """Comprehensive screenshot analysis.

        Args:
            image_path: Path to screenshot file
            detect_all: Run all detection methods (labels, text, objects, logos)

        Returns:
            Dictionary with all analysis results
        """
        results: dict[str, Any] = {}

        if detect_all:
            results["labels"] = self.detect_labels(image_path)
            results["text"] = self.detect_text(image_path)
            results["objects"] = self.detect_objects(image_path)
            results["logos"] = self.detect_logos(image_path)
            results["properties"] = self.get_image_properties(image_path)
        else:
            # Just labels and text for faster analysis
            results["labels"] = self.detect_labels(image_path, max_results=5)
            results["text"] = self.detect_text(image_path)

        return results

    def suggest_highlights(self, image_path: Path) -> list[dict[str, Any]]:
        """Suggest areas to highlight based on detected UI elements.

        Args:
            image_path: Path to screenshot file

        Returns:
            List of suggested highlights with coordinates and reasons
        """
        # Detect objects (buttons, forms, etc.)
        objects = self.detect_objects(image_path, min_confidence=0.6)

        # Detect text areas
        text_result = self.detect_text(image_path)

        highlights = []

        # Suggest highlighting interactive elements
        for obj in objects:
            if obj["name"].lower() in ["button", "text box", "menu", "icon"]:
                highlights.append(
                    {
                        "type": "object",
                        "element": obj["name"],
                        "confidence": obj["confidence"],
                        "bounds": obj["bounds"],
                        "reason": f"Interactive {obj['name']} detected",
                    }
                )

        # Suggest highlighting important text (headers, CTAs)
        for annotation in text_result.get("annotations", [])[:10]:
            text = annotation["text"].lower()
            if any(
                keyword in text
                for keyword in ["get started", "sign up", "learn more", "demo", "free"]
            ):
                highlights.append(
                    {
                        "type": "text",
                        "text": annotation["text"],
                        "bounds": annotation["bounds"],
                        "reason": "Call-to-action text detected",
                    }
                )

        return highlights
