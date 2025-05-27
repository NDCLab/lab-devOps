import os

from .syllable_match.feature_extractors import (
    FeatureExtractor,
    SyllableAtPassageBeginningExtractor,
    SyllableAtPassageEndExtractor,
    SyllableEndsWordExtractor,
    SyllableStartsWordExtractor,
    WordAfterCommaExtractor,
    WordAfterPeriodExtractor,
    WordBeforeCommaExtractor,
    WordBeforePeriodExtractor,
    WordFrequencyExtractor,
    WordPOSExtractor,
)
from .syllable_match.scaffolds import create_scaffolds
from .syllable_match.stats import summarize_word_matches
from .utils import get_templates


def get_scaffold_extractors() -> list[FeatureExtractor]:
    """
    Returns a list of FeatureExtractor instances to be used for scaffold creation.

    These extractors are responsible for analyzing various aspects of syllables
    and words, such as their positions, punctuation, and frequency, to facilitate
    the construction of detailed scaffolds.

    Note:
        This is meant to be configured according to desired default values in the scaffold
        that are independent of a participant's reading of a given passage.

    Returns:
        list[FeatureExtractor]: A list of initialized FeatureExtractor instances.
    """
    return [
        SyllableAtPassageBeginningExtractor(),
        SyllableAtPassageEndExtractor(),
        SyllableStartsWordExtractor(),
        SyllableEndsWordExtractor(),
        WordBeforePeriodExtractor(),
        WordAfterPeriodExtractor(),
        WordBeforeCommaExtractor(),
        WordAfterCommaExtractor(),
        WordFrequencyExtractor(),
        WordPOSExtractor(),
    ]


def build_scaffolds(template_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    create_scaffolds(get_templates(template_dir), output_dir, get_scaffold_extractors())
    summarize_word_matches(
        output_dir, os.path.join(output_dir, "word_matching_statistics.txt")
    )
