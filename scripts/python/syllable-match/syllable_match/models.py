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
    @property
    @abstractmethod
    def feature_name(self) -> str:
        pass

    @abstractmethod
    def extract(self, syllable_directory: list[SyllableEntry]) -> list:
        pass
