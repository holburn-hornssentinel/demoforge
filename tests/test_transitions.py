"""Tests for video transition builder."""

import pytest

from demoforge.assembler.transitions import TransitionBuilder, TransitionType


def test_transition_builder_initialization():
    """Should initialize with default settings."""
    builder = TransitionBuilder(
        default_transition=TransitionType.FADE,
        default_duration=1.0,
    )

    assert builder.default_transition == TransitionType.FADE
    assert builder.default_duration == 1.0


def test_build_xfade_filter_with_defaults():
    """Should build xfade filter with default transition and duration."""
    builder = TransitionBuilder(
        default_transition=TransitionType.FADE,
        default_duration=1.0,
    )

    filter_str = builder.build_xfade_filter(offset=5.0)

    assert filter_str == "xfade=transition=fade:duration=1.0:offset=5.0"


def test_build_xfade_filter_custom():
    """Should build xfade filter with custom transition and duration."""
    builder = TransitionBuilder()

    filter_str = builder.build_xfade_filter(
        offset=10.0,
        duration=2.0,
        transition=TransitionType.WIPELEFT,
    )

    assert filter_str == "xfade=transition=wipeleft:duration=2.0:offset=10.0"


def test_build_xfade_filter_all_transitions():
    """Should support all transition types."""
    builder = TransitionBuilder()

    transitions = [
        TransitionType.FADE,
        TransitionType.FADEBLACK,
        TransitionType.FADEWHITE,
        TransitionType.WIPELEFT,
        TransitionType.WIPERIGHT,
        TransitionType.SLIDELEFT,
        TransitionType.SLIDERIGHT,
        TransitionType.DISSOLVE,
        TransitionType.CIRCLECROP,
    ]

    for transition in transitions:
        filter_str = builder.build_xfade_filter(
            offset=1.0,
            duration=1.0,
            transition=transition,
        )
        assert f"transition={transition.value}" in filter_str


def test_build_transition_chain_two_scenes():
    """Should build transition chain for two scenes."""
    builder = TransitionBuilder(default_duration=1.0)

    scene_durations = [5.0, 7.0]
    filters = builder.build_transition_chain(scene_durations)

    # Two scenes = one transition
    assert len(filters) == 1

    # Transition should occur at first scene duration minus overlap
    assert "offset=4.0" in filters[0]


def test_build_transition_chain_multiple_scenes():
    """Should build transition chain for multiple scenes."""
    builder = TransitionBuilder(default_duration=1.0)

    scene_durations = [5.0, 7.0, 6.0, 4.0]
    filters = builder.build_transition_chain(scene_durations)

    # Four scenes = three transitions
    assert len(filters) == 3


def test_build_transition_chain_custom_duration():
    """Should use custom transition duration."""
    builder = TransitionBuilder()

    scene_durations = [5.0, 7.0, 6.0]
    filters = builder.build_transition_chain(
        scene_durations,
        transition_duration=2.0,
    )

    # All filters should have duration=2.0
    for filter_str in filters:
        assert "duration=2.0" in filter_str


def test_build_transition_chain_custom_type():
    """Should use custom transition type."""
    builder = TransitionBuilder()

    scene_durations = [5.0, 7.0]
    filters = builder.build_transition_chain(
        scene_durations,
        transition_type=TransitionType.SLIDELEFT,
    )

    # Filter should use slideleft transition
    assert "transition=slideleft" in filters[0]


def test_build_transition_chain_offsets():
    """Should calculate correct transition offsets."""
    builder = TransitionBuilder(default_duration=1.0)

    scene_durations = [5.0, 7.0, 6.0]
    filters = builder.build_transition_chain(scene_durations)

    # First transition: at end of first scene minus overlap
    assert "offset=4.0" in filters[0]

    # Second transition: cumulative time minus overlap
    # 5.0 + 7.0 - 1.0 = 11.0
    assert "offset=11.0" in filters[1]


def test_build_transition_chain_single_scene():
    """Should return empty list for single scene."""
    builder = TransitionBuilder()

    scene_durations = [5.0]
    filters = builder.build_transition_chain(scene_durations)

    # No transitions needed for single scene
    assert len(filters) == 0


def test_build_transition_chain_empty():
    """Should return empty list for no scenes."""
    builder = TransitionBuilder()

    scene_durations = []
    filters = builder.build_transition_chain(scene_durations)

    assert len(filters) == 0


def test_transition_type_enum_values():
    """Should have correct enum values for all transitions."""
    assert TransitionType.FADE.value == "fade"
    assert TransitionType.FADEBLACK.value == "fadeblack"
    assert TransitionType.FADEWHITE.value == "fadewhite"
    assert TransitionType.WIPELEFT.value == "wipeleft"
    assert TransitionType.DISSOLVE.value == "dissolve"
    assert TransitionType.CIRCLECROP.value == "circlecrop"


def test_transition_duration_precision():
    """Should handle decimal transition durations."""
    builder = TransitionBuilder()

    filter_str = builder.build_xfade_filter(
        offset=5.5,
        duration=0.75,
        transition=TransitionType.FADE,
    )

    assert "duration=0.75" in filter_str
    assert "offset=5.5" in filter_str


def test_transition_chain_with_varied_durations():
    """Should handle scenes with varied durations."""
    builder = TransitionBuilder(default_duration=1.5)

    # Mix of short and long scenes
    scene_durations = [3.0, 10.0, 2.5, 8.0, 4.0]
    filters = builder.build_transition_chain(scene_durations)

    # Should create transitions for all scene pairs
    assert len(filters) == len(scene_durations) - 1

    # All filters should be valid FFmpeg strings
    for filter_str in filters:
        assert filter_str.startswith("xfade=")
        assert "transition=" in filter_str
        assert "duration=" in filter_str
        assert "offset=" in filter_str


def test_transition_offset_calculation():
    """Should calculate transition offsets correctly in chain."""
    builder = TransitionBuilder(default_duration=1.0)

    scene_durations = [5.0, 7.0, 6.0]
    filters = builder.build_transition_chain(scene_durations)

    # First transition should be at end of first scene minus overlap
    assert "offset=4.0" in filters[0]

    # Second transition offset calculation
    # First scene: 5.0s, transition: 1.0s overlap, second scene: 7.0s
    # Total before second transition: 5.0 + 7.0 - 1.0 = 11.0
    assert "offset=11.0" in filters[1]


def test_build_complex_filter_chain():
    """Should build valid complex filter chain."""
    builder = TransitionBuilder(
        default_transition=TransitionType.FADE,
        default_duration=1.0,
    )

    scene_durations = [5.0, 7.0, 6.0, 4.0, 8.0]

    filters = builder.build_transition_chain(
        scene_durations,
        transition_duration=1.5,
        transition_type=TransitionType.DISSOLVE,
    )

    # Should have correct number of transitions
    assert len(filters) == 4

    # All filters should use dissolve
    for filter_str in filters:
        assert "transition=dissolve" in filter_str
        assert "duration=1.5" in filter_str
