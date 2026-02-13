"""Duration calculation and enforcement utilities."""


class DurationEnforcer:
    """Enforces target duration constraints for demo scripts."""

    # Average speaking rates (words per minute)
    SPEAKING_RATE_SLOW = 130
    SPEAKING_RATE_NORMAL = 150
    SPEAKING_RATE_FAST = 170

    def __init__(
        self, target_seconds: int, speaking_rate: int = SPEAKING_RATE_NORMAL
    ) -> None:
        """Initialize duration enforcer.

        Args:
            target_seconds: Target video duration in seconds
            speaking_rate: Words per minute for narration
        """
        self.target_seconds = target_seconds
        self.speaking_rate = speaking_rate

    @property
    def target_words(self) -> int:
        """Calculate target word count for the duration.

        Returns:
            Target number of words
        """
        minutes = self.target_seconds / 60.0
        return int(minutes * self.speaking_rate)

    @property
    def min_words(self) -> int:
        """Minimum acceptable word count (-10%).

        Returns:
            Minimum number of words
        """
        return int(self.target_words * 0.9)

    @property
    def max_words(self) -> int:
        """Maximum acceptable word count (+10%).

        Returns:
            Maximum number of words
        """
        return int(self.target_words * 1.1)

    def calculate_duration(self, word_count: int) -> float:
        """Calculate duration in seconds for a given word count.

        Args:
            word_count: Number of words

        Returns:
            Estimated duration in seconds
        """
        minutes = word_count / self.speaking_rate
        return minutes * 60.0

    def is_within_bounds(self, word_count: int) -> bool:
        """Check if word count is within acceptable bounds.

        Args:
            word_count: Number of words

        Returns:
            True if within ±10% of target
        """
        return self.min_words <= word_count <= self.max_words

    def get_adjustment_message(self, word_count: int) -> str:
        """Get message for adjusting script to target duration.

        Args:
            word_count: Current word count

        Returns:
            Human-readable adjustment message
        """
        if word_count < self.min_words:
            words_needed = self.min_words - word_count
            return f"Script is too short. Add approximately {words_needed} more words."
        elif word_count > self.max_words:
            words_excess = word_count - self.max_words
            return f"Script is too long. Remove approximately {words_excess} words."
        else:
            return "Script duration is within target bounds."
