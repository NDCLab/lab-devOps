import os
import sys
from dataclasses import dataclass

import pandas as pd

from .create_scaffolds import (
    EndSyllableExtractor,
    PunctuationEndExtractor,
    PunctuationStartExtractor,
    StartSyllableExtractor,
    SyllableCountExtractor,
    SyllablePositionExtractor,
    WordEndsSentenceExtractor,
    WordFrequencyExtractor,
    WordStartsSentenceExtractor,
)


def usage():
    print(f"Usage:\tpython {os.path.basename(__file__)} directory syllable_id")


def read_scaffold(path: str):
    return pd.read_csv(path)


def read_scaffolds(dirname: str, exclude: list[str] = []):
    scaffolds = [
        read_scaffold(os.path.join(dirname, file))
        for file in os.listdir(dirname)
        if file.endswith("csv") and file not in exclude
    ]
    return scaffolds


@dataclass
class SyllableMatcher:
    features: list[str]
    scaffolds: list[pd.DataFrame]

    def find_matching_syllable(self, syllable_id: str):
        src_df = self._get_source_scaffold(syllable_id)
        if src_df is None:
            raise ValueError(f"Could not find syllable with ID {syllable_id}")

        syll_match, feature = self._find_match_in_scaffold(syllable_id, src_df)
        if syll_match is not None:
            return (syll_match, feature)

        for scaffold in self.scaffolds:
            if scaffold == src_df:
                continue

            syll_match, feature = self._find_match_in_scaffold(syllable_id, scaffold)
            if syll_match is not None:
                return (syll_match, feature)

        raise ValueError(
            f"Could not find a match for syllable with ID {syllable_id}"
            + f" (checked {len(self.scaffolds)} scaffolds)"
        )

    def _get_source_scaffold(self, syllable_id: str):
        for scaffold in self.scaffolds:
            if (scaffold["syllable_id"] == syllable_id).any():
                return scaffold
        return None

    def _find_match_in_scaffold(self, syllable_id: str, scaffold: pd.DataFrame):
        target_rows = scaffold[scaffold["syllable_id"] == syllable_id]
        if target_rows.empty:
            return None
        target_row = target_rows.iloc[0]

        candidates = scaffold[scaffold["syllable_id"] != syllable_id]
        # Keep a backup of the previous candidate set in case we need to backtrack
        previous_candidates = candidates
        previous_feature = ""

        for feature in self.features:
            if feature not in scaffold.columns:
                continue

            ref_value = target_row[feature]
            filtered = candidates[candidates[feature] == ref_value]

            n_filtered = len(filtered.index)
            if n_filtered == 1:
                return (str(filtered["syllable_id"].iloc[0]), feature)
            elif n_filtered == 0:
                # No matches on this feature: backtrack and return the
                # first candidate from the previous candidate list.
                return (str(previous_candidates["syllable_id"].iloc[0]), previous_feature)
            else:
                # More than one candidate remains; save the current candidate set
                # in case the next feature yields zero matches.
                previous_candidates = candidates
                previous_feature = feature
                candidates = filtered

        # If we've gone through all features and we still have
        # multiple candidates, just return the first one.
        if not candidates.empty:
            return (str(candidates["syllable_id"].iloc[0]), str())
        else:
            return None


def main(scaffold_dir: str, syllable_id: str):
    scaffolds = read_scaffolds(scaffold_dir)

    features = [
        "syllable",
        "cleaned_syllable",
        "word",
        "cleaned_word",
        WordFrequencyExtractor.feature_name,
        StartSyllableExtractor.feature_name,
        EndSyllableExtractor.feature_name,
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
