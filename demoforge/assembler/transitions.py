"""FFmpeg transition filter chain builder for smooth scene transitions.

Supports various xfade transition types for professional video assembly.
"""

from enum import Enum


class TransitionType(str, Enum):
    """Available FFmpeg xfade transition types."""

    FADE = "fade"  # Simple crossfade (default)
    FADEBLACK = "fadeblack"  # Fade through black
    FADEWHITE = "fadewhite"  # Fade through white
    DISTANCE = "distance"  # Distance-based transition
    WIPELEFT = "wipeleft"  # Wipe from left to right
    WIPERIGHT = "wiperight"  # Wipe from right to left
    WIPEUP = "wipeup"  # Wipe from bottom to top
    WIPEDOWN = "wipedown"  # Wipe from top to bottom
    SLIDELEFT = "slideleft"  # Slide left
    SLIDERIGHT = "slideright"  # Slide right
    SLIDEUP = "slideup"  # Slide up
    SLIDEDOWN = "slidedown"  # Slide down
    CIRCLECROP = "circlecrop"  # Circular crop transition
    RECTCROP = "rectcrop"  # Rectangular crop transition
    DISSOLVE = "dissolve"  # Dissolve effect
    PIXELIZE = "pixelize"  # Pixelization transition


class TransitionBuilder:
    """Builds FFmpeg xfade filter chains for video transitions."""

    def __init__(
        self,
        default_transition: TransitionType = TransitionType.FADE,
        default_duration: float = 1.0,
    ) -> None:
        """Initialize transition builder.

        Args:
            default_transition: Default transition type
            default_duration: Default transition duration in seconds
        """
        self.default_transition = default_transition
        self.default_duration = default_duration

    def build_xfade_filter(
        self,
        offset: float,
        duration: float | None = None,
        transition: TransitionType | None = None,
    ) -> str:
        """Build a single xfade filter string.

        Args:
            offset: Time offset when transition starts (seconds)
            duration: Transition duration (uses default if None)
            transition: Transition type (uses default if None)

        Returns:
            FFmpeg xfade filter string

        Example:
            >>> builder.build_xfade_filter(5.0, 1.0, TransitionType.FADE)
            'xfade=transition=fade:duration=1.0:offset=5.0'
        """
        dur = duration if duration is not None else self.default_duration
        trans = transition if transition is not None else self.default_transition

        return f"xfade=transition={trans.value}:duration={dur}:offset={offset}"

    def build_transition_chain(
        self,
        scene_durations: list[float],
        transition_duration: float | None = None,
        transition_type: TransitionType | None = None,
    ) -> list[str]:
        """Build complete transition filter chain for multiple scenes.

        Args:
            scene_durations: List of scene durations in seconds
            transition_duration: Duration of each transition
            transition_type: Type of transition to use

        Returns:
            List of xfade filter strings

        Example:
            >>> builder.build_transition_chain([5.0, 3.0, 4.0], 1.0)
            ['xfade=transition=fade:duration=1.0:offset=4.0',
             'xfade=transition=fade:duration=1.0:offset=7.0']
        """
        if len(scene_durations) < 2:
            # No transitions needed for single scene
            return []

        dur = transition_duration if transition_duration is not None else self.default_duration
        trans = transition_type if transition_type is not None else self.default_transition

        transitions = []
        current_offset = 0.0

        for i in range(len(scene_durations) - 1):
            # Calculate offset: start transition before current scene ends
            current_offset += scene_durations[i] - dur

            transitions.append(
                f"xfade=transition={trans.value}:duration={dur}:offset={current_offset}"
            )

            # Add transition duration to offset for next scene
            current_offset += dur

        return transitions

    def build_complex_filter(
        self,
        num_inputs: int,
        scene_durations: list[float],
        transition_duration: float | None = None,
        transition_type: TransitionType | None = None,
    ) -> str:
        """Build complete FFmpeg complex filter for scene transitions.

        Args:
            num_inputs: Number of input video streams
            scene_durations: List of scene durations in seconds
            transition_duration: Duration of each transition
            transition_type: Type of transition to use

        Returns:
            Complete FFmpeg -filter_complex argument

        Example:
            >>> builder.build_complex_filter(3, [5.0, 3.0, 4.0], 1.0)
            '[0:v][1:v]xfade=transition=fade:duration=1.0:offset=4.0[v01];
             [v01][2:v]xfade=transition=fade:duration=1.0:offset=7.0[v12]'
        """
        if num_inputs < 2:
            # No transitions needed
            return "[0:v]copy[outv]"

        if len(scene_durations) != num_inputs:
            raise ValueError(
                f"Scene durations ({len(scene_durations)}) must match "
                f"number of inputs ({num_inputs})"
            )

        transitions = self.build_transition_chain(
            scene_durations, transition_duration, transition_type
        )

        # Build filter chain: [0:v][1:v]xfade[v01];[v01][2:v]xfade[v12];...
        filter_parts = []

        for i, transition in enumerate(transitions):
            if i == 0:
                # First transition: combine input 0 and 1
                input_a = "[0:v]"
                input_b = "[1:v]"
            else:
                # Subsequent transitions: use previous output
                input_a = f"[v{i-1}{i}]"
                input_b = f"[{i+1}:v]"

            output = f"[v{i}{i+1}]"
            filter_parts.append(f"{input_a}{input_b}{transition}{output}")

        # Join all filter parts with semicolons
        complex_filter = ";".join(filter_parts)

        # Add final output label
        final_output = f"[v{num_inputs-2}{num_inputs-1}]"
        complex_filter = complex_filter.replace(
            final_output, "[outv]", 1
        )  # Replace last output with [outv]

        return complex_filter

    @staticmethod
    def estimate_output_duration(
        scene_durations: list[float],
        transition_duration: float,
    ) -> float:
        """Estimate total output video duration with transitions.

        Transitions overlap scenes, reducing total duration.

        Args:
            scene_durations: List of scene durations in seconds
            transition_duration: Duration of each transition

        Returns:
            Total estimated duration in seconds

        Example:
            >>> TransitionBuilder.estimate_output_duration([5.0, 3.0, 4.0], 1.0)
            10.0  # 5 + 3 + 4 - 2 (two transitions of 1s each)
        """
        total_scenes = sum(scene_durations)
        num_transitions = max(0, len(scene_durations) - 1)
        total_transition_overlap = num_transitions * transition_duration

        return total_scenes - total_transition_overlap


def create_transition_builder(
    transition_type: TransitionType = TransitionType.FADE,
    transition_duration: float = 1.0,
) -> TransitionBuilder:
    """Factory function to create a TransitionBuilder.

    Args:
        transition_type: Default transition type
        transition_duration: Default transition duration

    Returns:
        Configured TransitionBuilder instance
    """
    return TransitionBuilder(
        default_transition=transition_type,
        default_duration=transition_duration,
    )
