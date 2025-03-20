from syllable_match.models import FeatureExtractor, SyllableEntry
from syllable_match.resources import get_word_freq


class SyllableAtPassageBeginningExtractor(FeatureExtractor):
    """
    Marks whether the syllable is one of the first 7 syllables in the passage.
    """

    feature_name = "beg-passage"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        beg_passage = []
        total_syllables = 0
        for entry in syllable_directory:
            count = len(entry.syllables)
            for i in range(count):
                # Check if the syllable index is within the first 7 syllables in the passage
                if total_syllables + i < 7:
                    beg_passage.append(1)
                else:
                    beg_passage.append(0)
            total_syllables += count
        return beg_passage


class SyllableAtPassageEndExtractor(FeatureExtractor):
    """
    Marks whether the syllable is one of the last 7 syllables in the passage.
    """

    feature_name = "end-passage"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        end_passage = []
        remaining_syllables = sum(len(entry.syllables) for entry in syllable_directory)
        for entry in syllable_directory:
            count = len(entry.syllables)
            for i in range(count):
                # Check if the syllable index is within the last 7 syllables in the passage
                if remaining_syllables - i <= 7:
                    end_passage.append(1)
                else:
                    end_passage.append(0)
            remaining_syllables -= count
        return end_passage


class SyllableStartsWordExtractor(FeatureExtractor):
    """
    Marks whether the syllable is the first in the word.
    """

    feature_name = "first-syll-word"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        syll_is_onset = []
        for entry in syllable_directory:
            count = len(entry.syllables)
            # First syllable is marked as 1, all others are 0
            syll_is_onset += [1] + [0] * (count - 1)
        return syll_is_onset


class SyllableEndsWordExtractor(FeatureExtractor):
    """
    Marks whether the syllable is the last in the word.
    """

    feature_name = "last-syll-word"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        syll_is_last = []
        for entry in syllable_directory:
            count = len(entry.syllables)
            # Last syllable is marked as 1, all others are 0
            syll_is_last += [0] * (count - 1) + [1]
        return syll_is_last


class WordFrequencyExtractor(FeatureExtractor):
    """
    Marks the frequency of the word in the corpus.
    """

    feature_name = "word-freq"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        frequencies = []
        for entry in syllable_directory:
            frequency = get_word_freq(entry.word.text)
            frequencies.extend([frequency] * len(entry.syllables))
        return frequencies


class SyllablePositionExtractor(FeatureExtractor):
    """
    Marks the position of the syllable in the word.
    """

    feature_name = "syllable-position"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        positions = []
        for entry in syllable_directory:
            positions += range(1, len(entry.syllables) + 1)
        return positions


class WordBeforePeriodExtractor(FeatureExtractor):
    """
    Marks whether the word ends with a period.
    """

    feature_name = "word-before-period"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        features = []
        for entry in syllable_directory:
            if entry.word.text.endswith("."):
                features += [1] * len(entry.syllables)
            else:
                features += [0] * len(entry.syllables)
        return features


class WordAfterPeriodExtractor(FeatureExtractor):
    """
    Marks whether the previous word ends with a period.
    """

    feature_name = "word-after-period"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        features = []
        for i, entry in enumerate(syllable_directory):
            if i > 0 and syllable_directory[i - 1].word.text.endswith("."):
                features += [1] * len(entry.syllables)
            else:
                features += [0] * len(entry.syllables)
        return features


class WordBeforeCommaExtractor(FeatureExtractor):
    """
    Marks whether the word ends with a comma.
    """

    feature_name = "word-before-comma"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        features = []
        for entry in syllable_directory:
            if entry.word.text.endswith(","):
                features += [1] * len(entry.syllables)
            else:
                features += [0] * len(entry.syllables)
        return features


class WordAfterCommaExtractor(FeatureExtractor):
    """
    Marks whether the previous word starts with a comma.
    """

    feature_name = "word-after-comma"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        features = []
        for i, entry in enumerate(syllable_directory):
            if i > 0 and syllable_directory[i - 1].word.text.endswith(","):
                features += [1] * len(entry.syllables)
            else:
                features += [0] * len(entry.syllables)
        return features


class SyllableCountExtractor(FeatureExtractor):
    """
    Marks the number of syllables in the word.
    """

    feature_name = "word-syllable-count"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        syllable_counts = []
        for entry in syllable_directory:
            count = len(entry.syllables)
            syllable_counts.extend([count] * count)
        return syllable_counts
