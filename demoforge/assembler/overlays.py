"""Overlay generation for lower thirds, branding, and visual enhancements.

Uses Pillow to generate overlay images that can be composited onto videos.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from demoforge.models import Screenshot


class OverlayGenerator:
    """Generates overlay images for video composition."""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        output_dir: Path = Path("/app/output/overlays"),
    ) -> None:
        """Initialize overlay generator.

        Args:
            width: Video width in pixels
            height: Video height in pixels
            output_dir: Directory to save overlay images
        """
        self.width = width
        self.height = height
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_font(self, size: int, bold: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
        """Get font for rendering text.

        Args:
            size: Font size in points
            bold: Use bold variant if available

        Returns:
            Font object
        """
        try:
            if bold:
                return ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size
                )
            else:
                return ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size
                )
        except OSError:
            return ImageFont.load_default()

    def create_lower_third(
        self,
        title: str,
        subtitle: str = "",
        output_path: Path | None = None,
        background_color: tuple[int, int, int, int] = (0, 0, 0, 180),
        text_color: tuple[int, int, int] = (255, 255, 255),
    ) -> Path:
        """Create a lower third overlay.

        Args:
            title: Main text (e.g., product name)
            subtitle: Secondary text (e.g., tagline)
            output_path: Output file path (auto-generated if None)
            background_color: RGBA background color
            text_color: RGB text color

        Returns:
            Path to generated overlay image
        """
        # Create transparent image
        image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Lower third dimensions (bottom 20% of screen)
        bar_height = int(self.height * 0.15)
        bar_y = self.height - bar_height - 50  # 50px from bottom

        # Draw semi-transparent bar
        draw.rectangle(
            [(0, bar_y), (self.width, bar_y + bar_height)],
            fill=background_color,
        )

        # Draw title text
        title_font = self._get_font(48, bold=True)
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = 80  # Left padding
        title_y = bar_y + 20

        draw.text((title_x, title_y), title, fill=text_color, font=title_font)

        # Draw subtitle if provided
        if subtitle:
            subtitle_font = self._get_font(32)
            subtitle_y = title_y + 55

            draw.text(
                (title_x, subtitle_y), subtitle, fill=text_color, font=subtitle_font
            )

        # Save
        if output_path is None:
            output_path = self.output_dir / "lower_third.png"

        image.save(str(output_path), "PNG")
        return output_path

    def create_intro_card(
        self,
        title: str,
        subtitle: str = "",
        output_path: Path | None = None,
        background_color: tuple[int, int, int] = (15, 23, 42),  # Slate 900
        text_color: tuple[int, int, int] = (248, 250, 252),  # Slate 50
    ) -> Screenshot:
        """Create an intro/title card.

        Args:
            title: Main title text
            subtitle: Subtitle text
            output_path: Output file path (auto-generated if None)
            background_color: RGB background color
            text_color: RGB text color

        Returns:
            Screenshot model with card metadata
        """
        # Create image
        image = Image.new("RGB", (self.width, self.height), background_color)
        draw = ImageDraw.Draw(image)

        # Calculate vertical centering
        y_center = self.height // 2

        # Draw title
        title_font = self._get_font(96, bold=True)
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_x = (self.width - title_width) // 2
        title_y = y_center - 60 if subtitle else y_center - (title_height // 2)

        draw.text((title_x, title_y), title, fill=text_color, font=title_font)

        # Draw subtitle if provided
        if subtitle:
            subtitle_font = self._get_font(48)
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            subtitle_y = title_y + 120

            # Slightly dimmed color for subtitle
            subtitle_color = tuple(int(c * 0.7) for c in text_color)
            draw.text(
                (subtitle_x, subtitle_y),
                subtitle,
                fill=subtitle_color,
                font=subtitle_font,
            )

        # Save
        if output_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"intro_card_{timestamp}.png"

        image.save(str(output_path), "PNG")

        from datetime import datetime
        from demoforge.models import Screenshot

        return Screenshot(
            scene_id="intro_card",
            url=None,
            image_path=output_path,
            width=self.width,
            height=self.height,
            captured_at=datetime.now(),
        )

    def create_outro_card(
        self,
        main_text: str,
        call_to_action: str = "",
        output_path: Path | None = None,
        background_color: tuple[int, int, int] = (15, 23, 42),  # Slate 900
        text_color: tuple[int, int, int] = (248, 250, 252),  # Slate 50
        accent_color: tuple[int, int, int] = (59, 130, 246),  # Blue 500
    ) -> Screenshot:
        """Create an outro/end card with call-to-action.

        Args:
            main_text: Main closing message
            call_to_action: CTA text (e.g., "Visit github.com/org/repo")
            output_path: Output file path
            background_color: RGB background color
            text_color: RGB text color
            accent_color: RGB accent color for CTA

        Returns:
            Screenshot model with card metadata
        """
        # Create image
        image = Image.new("RGB", (self.width, self.height), background_color)
        draw = ImageDraw.Draw(image)

        y_center = self.height // 2

        # Draw main text
        main_font = self._get_font(72, bold=True)
        main_bbox = draw.textbbox((0, 0), main_text, font=main_font)
        main_width = main_bbox[2] - main_bbox[0]
        main_x = (self.width - main_width) // 2
        main_y = y_center - 100 if call_to_action else y_center - 36

        draw.text((main_x, main_y), main_text, fill=text_color, font=main_font)

        # Draw call-to-action if provided
        if call_to_action:
            cta_font = self._get_font(48)
            cta_bbox = draw.textbbox((0, 0), call_to_action, font=cta_font)
            cta_width = cta_bbox[2] - cta_bbox[0]
            cta_x = (self.width - cta_width) // 2
            cta_y = main_y + 140

            draw.text((cta_x, cta_y), call_to_action, fill=accent_color, font=cta_font)

        # Save
        if output_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"outro_card_{timestamp}.png"

        image.save(str(output_path), "PNG")

        from datetime import datetime
        from demoforge.models import Screenshot

        return Screenshot(
            scene_id="outro_card",
            url=None,
            image_path=output_path,
            width=self.width,
            height=self.height,
            captured_at=datetime.now(),
        )

    def add_branding_watermark(
        self,
        text: str = "DemoForge",
        output_path: Path | None = None,
        position: str = "bottom-right",
        opacity: int = 128,
    ) -> Path:
        """Create a subtle branding watermark overlay.

        Args:
            text: Branding text
            output_path: Output file path
            position: Position ("top-left", "top-right", "bottom-left", "bottom-right")
            opacity: Opacity (0-255)

        Returns:
            Path to watermark overlay
        """
        # Create transparent image
        image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Get font and text size
        font = self._get_font(24)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Calculate position
        padding = 30
        if position == "top-left":
            x, y = padding, padding
        elif position == "top-right":
            x, y = self.width - text_width - padding, padding
        elif position == "bottom-left":
            x, y = padding, self.height - text_height - padding
        else:  # bottom-right
            x, y = self.width - text_width - padding, self.height - text_height - padding

        # Draw text with opacity
        text_color = (255, 255, 255, opacity)
        draw.text((x, y), text, fill=text_color, font=font)

        # Save
        if output_path is None:
            output_path = self.output_dir / "watermark.png"

        image.save(str(output_path), "PNG")
        return output_path
