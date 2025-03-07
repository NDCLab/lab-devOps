import pandas as pd
from dataclasses import dataclass


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
                return (
                    str(previous_candidates["syllable_id"].iloc[0]),
                    previous_feature,
                )
            else:
                previous_candidates = candidates
                previous_feature = feature
                candidates = filtered

        if not candidates.empty:
            return (str(candidates["syllable_id"].iloc[0]), str())
        else:
            return None
