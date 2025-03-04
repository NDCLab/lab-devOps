import string

import pandas as pd

from .models import FeatureExtractor, SyllableEntry


class SyllableAtPassageBeginningExtractor(FeatureExtractor):
    """
    Marks whether the syllable is one of the first 7 syllables in the passage.
    """

    feature_name = "beg-passage"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        beg_passage = []
        for entry in syllable_directory:
            count = len(entry.syllables)
            for i in range(count):
                # Check if the syllable index is within the first 7 syllables
                if i < 7:
                    beg_passage.append(1)
                else:
                    beg_passage.append(0)
        return beg_passage


class SyllableAtPassageEndExtractor(FeatureExtractor):
    """
    Marks whether the syllable is one of the last 7 syllables in the passage.
    """

    feature_name = "end-passage"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        end_passage = []
        for entry in syllable_directory:
            count = len(entry.syllables)
            for i in range(count):
                # Check if the syllable index is within the last 7 syllables
                if i >= count - 7:
                    end_passage.append(1)
                else:
                    end_passage.append(0)
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

    def __init__(self, frequency_df: pd.DataFrame):
        self.word_frequencies = self.load_frequencies(frequency_df)

    def load_frequencies(self, frequency_df: pd.DataFrame) -> dict[str, int]:
        frequencies = {}
        for _, row in frequency_df.iterrows():
            word = row["Word"].lower().strip(string.punctuation)
            freq_count = int(row["FREQcount"])
            frequencies[word] = freq_count
        return frequencies

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        frequencies = []
        for entry in syllable_directory:
            frequency = self.word_frequencies.get(entry.word.clean_text, 0)
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
        return [1 if syll.word.text.endswith(".") else 0 for syll in syllable_directory]


class WordAfterPeriodExtractor(FeatureExtractor):
    """
    Marks whether the previous word ends with a period.
    """

    feature_name = "word-after-period"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        result = []
        for i in range(len(syllable_directory)):
            if i > 0 and syllable_directory[i - 1].word.text.endswith("."):
                result.append(1)
            else:
                result.append(0)
        return result


class WordBeforeCommaExtractor(FeatureExtractor):
    """
    Marks whether the word ends with a comma.
    """

    feature_name = "word-before-comma"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        return [1 if syll.word.text.endswith(",") else 0 for syll in syllable_directory]


class WordAfterCommaExtractor(FeatureExtractor):
    """
    Marks whether the previous word starts with a comma.
    """

    feature_name = "word-after-comma"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        result = []
        for i in range(len(syllable_directory)):
            if i > 0 and syllable_directory[i - 1].word.text.endswith(","):
                result.append(1)
            else:
                result.append(0)
        return result


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
