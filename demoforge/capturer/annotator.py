"""Screenshot annotation tools for highlighting key UI elements."""

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


class ScreenshotAnnotator:
    """Annotates screenshots with highlights, boxes, arrows, and callouts."""

    def __init__(
        self,
        box_color: str = "#FF6B6B",
        box_width: int = 4,
        circle_color: str = "#4ECDC4",
        circle_width: int = 5,
        arrow_color: str = "#FFE66D",
        arrow_width: int = 4,
    ) -> None:
        """Initialize the annotator.

        Args:
            box_color: Hex color for highlight boxes
            box_width: Line width for boxes
            circle_color: Hex color for callout circles
            circle_width: Line width for circles
            arrow_color: Hex color for arrows
            arrow_width: Line width for arrows
        """
        self.box_color = box_color
        self.box_width = box_width
        self.circle_color = circle_color
        self.circle_width = circle_width
        self.arrow_color = arrow_color
        self.arrow_width = arrow_width

    def _normalize_bounds(
        self, bounds: list[dict[str, float]], image_width: int, image_height: int
    ) -> tuple[int, int, int, int]:
        """Convert normalized or absolute bounds to pixel coordinates.

        Args:
            bounds: List of {x, y} vertices (normalized 0-1 or absolute pixels)
            image_width: Image width in pixels
            image_height: Image height in pixels

        Returns:
            Tuple of (x1, y1, x2, y2) in pixels
        """
        # Check if bounds are normalized (all values between 0 and 1)
        is_normalized = all(
            0 <= point.get("x", 0) <= 1 and 0 <= point.get("y", 0) <= 1
            for point in bounds
        )

        if is_normalized:
            # Convert normalized to pixels
            x_coords = [int(point["x"] * image_width) for point in bounds]
            y_coords = [int(point["y"] * image_height) for point in bounds]
        else:
            # Already in pixels
            x_coords = [int(point["x"]) for point in bounds]
            y_coords = [int(point["y"]) for point in bounds]

        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def draw_box(
        self,
        image: Image.Image,
        bounds: list[dict[str, float]],
        color: str | None = None,
        width: int | None = None,
    ) -> Image.Image:
        """Draw a rectangular box around a region.

        Args:
            image: PIL Image to annotate
            bounds: List of {x, y} vertices defining the box
            color: Optional override for box color
            width: Optional override for line width

        Returns:
            Annotated image
        """
        draw = ImageDraw.Draw(image)
        x1, y1, x2, y2 = self._normalize_bounds(bounds, image.width, image.height)

        draw.rectangle(
            [(x1, y1), (x2, y2)],
            outline=color or self.box_color,
            width=width or self.box_width,
        )

        return image

    def draw_circle(
        self,
        image: Image.Image,
        bounds: list[dict[str, float]],
        color: str | None = None,
        width: int | None = None,
    ) -> Image.Image:
        """Draw a circle callout around a region.

        Args:
            image: PIL Image to annotate
            bounds: List of {x, y} vertices defining the region
            color: Optional override for circle color
            width: Optional override for line width

        Returns:
            Annotated image
        """
        draw = ImageDraw.Draw(image)
        x1, y1, x2, y2 = self._normalize_bounds(bounds, image.width, image.height)

        # Calculate center and radius for bounding circle
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        radius = max((x2 - x1) // 2, (y2 - y1) // 2) + 10  # Add padding

        draw.ellipse(
            [
                (center_x - radius, center_y - radius),
                (center_x + radius, center_y + radius),
            ],
            outline=color or self.circle_color,
            width=width or self.circle_width,
        )

        return image

    def draw_arrow(
        self,
        image: Image.Image,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        color: str | None = None,
        width: int | None = None,
    ) -> Image.Image:
        """Draw an arrow from start to end point.

        Args:
            image: PIL Image to annotate
            start_x: Arrow start X coordinate
            start_y: Arrow start Y coordinate
            end_x: Arrow end X coordinate
            end_y: Arrow end Y coordinate
            color: Optional override for arrow color
            width: Optional override for line width

        Returns:
            Annotated image
        """
        draw = ImageDraw.Draw(image)
        arrow_color = color or self.arrow_color
        arrow_width = width or self.arrow_width

        # Draw main line
        draw.line(
            [(start_x, start_y), (end_x, end_y)], fill=arrow_color, width=arrow_width
        )

        # Draw arrowhead (simple triangle)
        # Calculate angle and arrowhead points
        import math

        angle = math.atan2(end_y - start_y, end_x - start_x)
        arrow_length = 15
        arrow_angle = math.pi / 6  # 30 degrees

        # Left point of arrowhead
        left_x = end_x - arrow_length * math.cos(angle - arrow_angle)
        left_y = end_y - arrow_length * math.sin(angle - arrow_angle)

        # Right point of arrowhead
        right_x = end_x - arrow_length * math.cos(angle + arrow_angle)
        right_y = end_y - arrow_length * math.sin(angle + arrow_angle)

        draw.polygon(
            [(end_x, end_y), (left_x, left_y), (right_x, right_y)],
            fill=arrow_color,
        )

        return image

    def annotate_highlights(
        self, image_path: Path, highlights: list[dict[str, Any]], output_path: Path
    ) -> Path:
        """Annotate a screenshot with suggested highlights.

        Args:
            image_path: Path to input image
            highlights: List of highlight suggestions from VisionAnalyzer
            output_path: Path to save annotated image

        Returns:
            Path to annotated image
        """
        image = Image.open(image_path)

        for highlight in highlights:
            highlight_type = highlight.get("type")
            bounds = highlight.get("bounds", [])

            if not bounds:
                continue

            if highlight_type == "object":
                # Draw box around interactive elements (buttons, forms, etc.)
                image = self.draw_box(image, bounds)
            elif highlight_type == "text":
                # Draw circle around important text (CTAs, headers)
                image = self.draw_circle(image, bounds)

        # Save annotated image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

        return output_path

    def annotate_custom(
        self,
        image_path: Path,
        annotations: list[dict[str, Any]],
        output_path: Path,
    ) -> Path:
        """Annotate a screenshot with custom annotations.

        Args:
            image_path: Path to input image
            annotations: List of annotation specs with type, bounds, color, etc.
            output_path: Path to save annotated image

        Returns:
            Path to annotated image

        Example annotations:
            [
                {"type": "box", "bounds": [...], "color": "#FF0000"},
                {"type": "circle", "bounds": [...], "width": 3},
                {"type": "arrow", "start": [100, 100], "end": [200, 200]}
            ]
        """
        image = Image.open(image_path)

        for annotation in annotations:
            ann_type = annotation.get("type")

            if ann_type == "box":
                image = self.draw_box(
                    image,
                    annotation["bounds"],
                    color=annotation.get("color"),
                    width=annotation.get("width"),
                )
            elif ann_type == "circle":
                image = self.draw_circle(
                    image,
                    annotation["bounds"],
                    color=annotation.get("color"),
                    width=annotation.get("width"),
                )
            elif ann_type == "arrow":
                start = annotation["start"]
                end = annotation["end"]
                image = self.draw_arrow(
                    image,
                    start[0],
                    start[1],
                    end[0],
                    end[1],
                    color=annotation.get("color"),
                    width=annotation.get("width"),
                )

        # Save annotated image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

        return output_path
