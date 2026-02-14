"""Fallback title card and code snippet generation using Pillow."""

from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from demoforge.models import Screenshot


class TitleCardGenerator:
    """Generates title cards and code snippets as fallback visuals."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        output_dir: Path = Path("/app/output/screenshots"),
    ) -> None:
        """Initialize title card generator.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            output_dir: Directory to save generated images
        """
        self.width = width
        self.height = height
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_font(self, size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
        """Get font for rendering text.

        Args:
            size: Font size in points

        Returns:
            Font object
        """
        try:
            # Try to use a nice font if available
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except OSError:
            # Fallback to default font
            return ImageFont.load_default()

    def generate_title_card(
        self,
        text: str,
        scene_id: str,
        background_color: tuple[int, int, int] = (30, 41, 59),  # Slate 800
        text_color: tuple[int, int, int] = (248, 250, 252),  # Slate 50
    ) -> Screenshot:
        """Generate a title card with text.

        Args:
            text: Text to display
            scene_id: Scene identifier
            background_color: RGB background color
            text_color: RGB text color

        Returns:
            Screenshot metadata for generated title card
        """
        # Create image
        image = Image.new("RGB", (self.width, self.height), background_color)
        draw = ImageDraw.Draw(image)

        # Calculate font size based on text length
        if len(text) < 50:
            font_size = 120
        elif len(text) < 100:
            font_size = 80
        else:
            font_size = 60

        font = self._get_font(font_size)

        # Wrap text to fit width
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            # Simple width estimation (not perfect but works)
            if len(test_line) * (font_size * 0.6) < self.width * 0.8:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        # Calculate total text height
        line_height = font_size + 20
        total_height = len(lines) * line_height

        # Start y position (center vertically)
        y = (self.height - total_height) // 2

        # Draw each line centered
        for line in lines:
            # Get text bounding box for centering
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2

            draw.text((x, y), line, fill=text_color, font=font)
            y += line_height

        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{scene_id}_title_{timestamp}.png"
        image_path = self.output_dir / filename

        image.save(str(image_path), "PNG")

        return Screenshot(
            scene_id=scene_id,
            url=None,
            image_path=image_path,
            width=self.width,
            height=self.height,
            captured_at=datetime.now(),
        )

    def generate_code_snippet(
        self,
        code: str,
        scene_id: str,
        language: str = "python",
        background_color: tuple[int, int, int] = (15, 23, 42),  # Slate 900
        text_color: tuple[int, int, int] = (226, 232, 240),  # Slate 200
    ) -> Screenshot:
        """Generate a code snippet image.

        Args:
            code: Code to display
            scene_id: Scene identifier
            language: Programming language (for future syntax highlighting)
            background_color: RGB background color
            text_color: RGB text color

        Returns:
            Screenshot metadata for generated code image
        """
        # Create image
        image = Image.new("RGB", (self.width, self.height), background_color)
        draw = ImageDraw.Draw(image)

        # Use monospace-like sizing
        font_size = 36
        font = self._get_font(font_size)

        # Split code into lines
        lines = code.split("\n")

        # Calculate line height
        line_height = font_size + 10

        # Start y position (with padding)
        y = 60
        x = 60

        # Draw code lines
        for line in lines[:25]:  # Limit to 25 lines
            if y > self.height - 60:
                break
            draw.text((x, y), line, fill=text_color, font=font)
            y += line_height

        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{scene_id}_code_{timestamp}.png"
        image_path = self.output_dir / filename

        image.save(str(image_path), "PNG")

        return Screenshot(
            scene_id=scene_id,
            url=None,
            image_path=image_path,
            width=self.width,
            height=self.height,
            captured_at=datetime.now(),
        )
