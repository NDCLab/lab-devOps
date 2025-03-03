from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class Scaffold:
    df: pd.DataFrame
    passage_name: str


@dataclass
class Word:
    text: str
    clean_text: str


@dataclass
class Syllable:
    text: str
    clean_text: str
    has_punctuation: bool
    ends_sentence: bool


@dataclass
class SyllableEntry:
    word: Word
    syllables: list[Syllable]


class FeatureExtractor(ABC):
    """
    Abstract base class for feature extractors that analyze syllable entries.

    This class defines the interface for feature extractors, which are responsible
    for extracting specific features from a list of SyllableEntry objects. Each
    feature extractor must implement the `feature_name` property and the `extract`
    method.

    To implement a feature extractor, inherit from this class and provide concrete
    implementations for the `feature_name` property and the `extract` method.

    Example:
    ```
        class MyFeatureExtractor(FeatureExtractor):
            feature_name = "my_feature"

            def extract(self, syllable_directory: list[SyllableEntry]) -> list:
                # Implement feature extraction logic here
                return [len(syll.text) for syll in syllable_directory]
    ```

    Properties:
        feature_name (str): The name of the feature being extracted.

    Methods:
        extract(syllable_directory: list[SyllableEntry]) -> list:
            Extracts the feature from the given syllable directory.
    """

    @property
    @abstractmethod
    def feature_name(self) -> str:
        pass

    @abstractmethod
    def extract(self, syllable_directory: list[SyllableEntry]) -> list:
        """
        Extracts a specific feature from a list of SyllableEntry objects.

        This method should be implemented by subclasses to define the logic for
        extracting a particular feature from the provided syllable directory.

        Parameters:
            syllable_directory (list[SyllableEntry]): A list of SyllableEntry objects
            from which the feature will be extracted.

        Returns:
            list: A list containing the extracted feature values.
        """
        pass
