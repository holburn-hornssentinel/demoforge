"""Brand template loader and configuration for DemoForge.

Loads brand configuration from YAML files to customize video appearance.
"""

import yaml
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class BrandConfig(BaseModel):
    """Brand configuration for customizing video appearance."""

    # Brand identity
    name: str = Field(default="DemoForge", description="Brand name")
    logo_path: Path | None = Field(None, description="Path to brand logo (PNG/SVG)")

    # Colors (hex format)
    primary_color: str = Field(default="#3B82F6", description="Primary brand color")
    secondary_color: str = Field(default="#8B5CF6", description="Secondary brand color")
    accent_color: str = Field(default="#10B981", description="Accent color")
    background_color: str = Field(default="#0F172A", description="Background color")
    text_color: str = Field(default="#F8FAFC", description="Text color")

    # Typography
    font_family: str = Field(default="Arial", description="Font family for text")
    title_font_size: int = Field(default=72, description="Title font size (px)")
    subtitle_font_size: int = Field(default=36, description="Subtitle font size (px)")
    body_font_size: int = Field(default=24, description="Body font size (px)")

    # Watermark settings
    watermark_enabled: bool = Field(default=True, description="Show brand watermark")
    watermark_text: str | None = Field(None, description="Watermark text override")
    watermark_position: str = Field(
        default="bottom-right",
        description="Watermark position (top-left, top-right, bottom-left, bottom-right)"
    )
    watermark_opacity: int = Field(default=128, description="Watermark opacity (0-255)")

    # Lower third overlay settings
    lower_third_enabled: bool = Field(default=True, description="Show lower third overlays")
    lower_third_background: str | None = Field(
        None, description="Lower third background color (hex)"
    )

    def get_rgb_color(self, color_hex: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple.

        Args:
            color_hex: Hex color string (e.g., "#3B82F6")

        Returns:
            RGB tuple (r, g, b)
        """
        color_hex = color_hex.lstrip("#")
        return tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))

    def get_rgba_color(self, color_hex: str, alpha: int = 255) -> tuple[int, int, int, int]:
        """Convert hex color to RGBA tuple.

        Args:
            color_hex: Hex color string
            alpha: Alpha channel (0-255)

        Returns:
            RGBA tuple (r, g, b, a)
        """
        rgb = self.get_rgb_color(color_hex)
        return (*rgb, alpha)


def load_brand_config(brand_file: Path) -> BrandConfig:
    """Load brand configuration from YAML file.

    Args:
        brand_file: Path to brand.yml file

    Returns:
        Loaded brand configuration

    Raises:
        FileNotFoundError: If brand file doesn't exist
        ValueError: If brand file is invalid
    """
    if not brand_file.exists():
        raise FileNotFoundError(f"Brand file not found: {brand_file}")

    try:
        with open(brand_file, "r") as f:
            data = yaml.safe_load(f)

        return BrandConfig(**data)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid brand YAML file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load brand config: {e}")


def get_default_brand_config() -> BrandConfig:
    """Get the default DemoForge brand configuration.

    Returns:
        Default brand config
    """
    return BrandConfig(
        name="DemoForge",
        primary_color="#3B82F6",  # Blue
        secondary_color="#8B5CF6",  # Purple
        accent_color="#10B981",  # Green
        background_color="#0F172A",  # Slate 900
        text_color="#F8FAFC",  # Slate 50
        font_family="Arial",
        watermark_enabled=True,
        watermark_text="Generated with DemoForge",
        watermark_position="bottom-right",
        watermark_opacity=128,
        lower_third_enabled=True,
    )


def create_brand_template(output_path: Path, **overrides: Any) -> None:
    """Create a brand template YAML file.

    Args:
        output_path: Path to write brand.yml
        **overrides: Brand config overrides
    """
    default_config = get_default_brand_config()

    # Apply overrides
    config_dict = default_config.model_dump()
    config_dict.update(overrides)

    # Convert Path objects to strings for YAML serialization
    for key, value in config_dict.items():
        if isinstance(value, Path):
            config_dict[key] = str(value)

    # Write YAML
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
