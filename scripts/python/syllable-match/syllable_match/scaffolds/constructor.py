import string
from dataclasses import dataclass, field

import pandas as pd

from syllable_match.models import FeatureExtractor, Syllable, SyllableEntry, Word


@dataclass
class ScaffoldConstructor:
    """
    A class responsible for constructing scaffolds from given words and syllables.

    The ScaffoldConstructor takes a passage name, a list of words, and a list of syllables
    to build a structured representation of syllables and their corresponding words. It allows
    for the registration of feature extractors to enrich the scaffold with additional features.

    Attributes:
        passage_name (str): The name of the passage being processed.
        words (list[str]): A list of words in the passage.
        syllables (list[str]): A list of syllables corresponding to the words.
        extractors (list[FeatureExtractor]): A list of feature extractors to apply to the scaffold.

    Methods:
        register_extractor(extractor: FeatureExtractor):
            Registers a single feature extractor.

        register_extractors(extractors: list[FeatureExtractor]):
            Registers multiple feature extractors.

        build() -> pd.DataFrame:
            Constructs the scaffold DataFrame with extracted features.

        build_syllable_directory() -> list[SyllableEntry]:
            Builds a directory of syllables and their corresponding words.
    """

    passage_name: str
    words: list[str]
    syllables: list[str]
    extractors: list[FeatureExtractor] = field(default_factory=list)

    def register_extractor(self, extractor: FeatureExtractor):
        self.extractors.append(extractor)

    def register_extractors(self, extractors: list[FeatureExtractor]):
        self.extractors.extend(extractors)

    def build(self) -> pd.DataFrame:
        syllable_directory = self.build_syllable_directory()

        # Create a list of all syllables and their corresponding words
        syllables = []
        cleaned_syllables = []
        words = []
        cleaned_words = []
        word_ids = []
        syllable_ids = []
        word_index = 1
        syllable_index = 1
        for entry in syllable_directory:
            for syllable in entry.syllables:
                syllables.append(syllable.text)
                cleaned_syllables.append(syllable.clean_text)
                words.append(entry.word.text)
                cleaned_words.append(entry.word.clean_text)
                # Indices (useful for unique identification)
                word_ids.append(f"{self.passage_name}_word{word_index}")
                syllable_ids.append(f"{self.passage_name}_syll{syllable_index}")
                syllable_index += 1
            word_index += 1

        # Extract features
        features = {
            extractor.feature_name: extractor.extract(syllable_directory)
            for extractor in self.extractors
        }

        features["syllable"] = syllables
        features["cleaned_syllable"] = cleaned_syllables
        features["word"] = words
        features["cleaned_word"] = cleaned_words
        features["word_id"] = word_ids
        features["syllable_id"] = syllable_ids

        # Sanity check: assert that the lengths of feature lists are identical
        feature_lengths = [len(value) for value in features.values()]
        assert len(set(feature_lengths)) == 1

        return pd.DataFrame(features)

    def build_syllable_directory(self) -> list[SyllableEntry]:
        syllable_directory = []
        syllable_queue = self.syllables.copy()

        for word in self.words:
            current_length = 0
            cleaned_word = word.replace("-", "").lower().strip(string.punctuation)
            word_length = len(cleaned_word)

            syllable_list = []
            while syllable_queue and current_length < word_length:
                current_syllable = syllable_queue.pop(0).lower()
                cleaned_syll = current_syllable.strip(string.punctuation)
                # Check if the syllable matches the start of the remaining word
                if cleaned_word.startswith(cleaned_syll, current_length):
                    syllable_list.append(
                        Syllable(
                            current_syllable,
                            cleaned_syll,
                            current_syllable[-1] in string.punctuation,
                            current_syllable[-1] in {".", "!", "?"},
                        )
                    )
                    current_length += len(cleaned_syll)

            if not syllable_list:
                raise Exception(self.passage_name, word, syllable_directory)

            syllable_directory.append(
                SyllableEntry(Word(word, cleaned_word), syllable_list)
            )

        return syllable_directory
