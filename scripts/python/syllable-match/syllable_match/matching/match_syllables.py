import os
import sys

import pandas as pd

from syllable_match.feature_extractors import (
    SyllableEndsWordExtractor,
    PunctuationEndExtractor,
    PunctuationStartExtractor,
    SyllableStartsWordExtractor,
    SyllableCountExtractor,
    SyllablePositionExtractor,
    WordEndsSentenceExtractor,
    WordFrequencyExtractor,
    WordStartsSentenceExtractor,
)
from syllable_match.matching.matcher import SyllableMatcher
from syllable_match.utils import read_csv_files


def usage():
    print(f"Usage:\tpython {os.path.basename(__file__)} directory syllable_id")


def read_scaffold(path: str):
    return pd.read_csv(path)


def read_scaffolds(dirname: str, exclude: list[str] = []):
    return read_csv_files(dirname, exclude)


def main(scaffold_dir: str, syllable_id: str):
    scaffolds = read_scaffolds(scaffold_dir)

    features = [
        "syllable",
        "cleaned_syllable",
        "word",
        "cleaned_word",
        WordFrequencyExtractor.feature_name,
        SyllableStartsWordExtractor.feature_name,
        SyllableEndsWordExtractor.feature_name,
        SyllablePositionExtractor.feature_name,
        SyllableCountExtractor.feature_name,
        PunctuationStartExtractor.feature_name,
        PunctuationEndExtractor.feature_name,
        WordStartsSentenceExtractor.feature_name,
        WordEndsSentenceExtractor.feature_name,
    ]
    matcher = SyllableMatcher(features, scaffolds)

    print(matcher.find_matching_syllable(syllable_id))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        exit(1)

    main(sys.argv[1], sys.argv[2])
