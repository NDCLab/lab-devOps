import logging

import pandas as pd

from ..resources import get_word_freq


def match_duplications(df: pd.DataFrame) -> None:
    """
    Matches duplications in the DataFrame (strict version).
    """
    logging.info("Matching duplications...")

    # Match duplication starts
    for index, duplication_start in df[df["duplication-start"] == 1].iterrows():
        # Get candidate syllables
        candidate_df = df[
            (df["any-deviation"] == 0)
            & (df["any-deviation-before"] == 0)
            & (df["any-deviation-after"] == 0)
            & (df["any-deviation-after"].shift(-1) == 0)
            & (df["comparison-duplication-start"] != 1)
        ]

        if index + 1 >= len(df):
            continue

        duplication_following = df.iloc[index + 1]

        # Get potential syllable pairs
        potential_syllables = []
        for i in range(len(candidate_df) - 1):
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1:
                potential_syllables.append(
                    (candidate_df.iloc[i], candidate_df.iloc[i + 1])
                )

        # Filter for perfect matches on specified fields
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_a["first-syll-word"] == duplication_start["first-syll-word"])
            and (syll_a["last-syll-word"] == duplication_start["last-syll-word"])
            and (
                syll_a["word-before-period"] == duplication_start["word-before-period"]
            )
            and (syll_a["word-after-period"] == duplication_start["word-after-period"])
            and (syll_a["word-before-comma"] == duplication_start["word-before-comma"])
            and (syll_a["word-after-comma"] == duplication_start["word-after-comma"])
        ]

        # Filter for N+1 syllable matches
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_b["first-syll-word"] == duplication_following["first-syll-word"])
            and (syll_b["last-syll-word"] == duplication_following["last-syll-word"])
            and (
                syll_b["word-before-period"]
                == duplication_following["word-before-period"]
            )
            and (
                syll_b["word-after-period"]
                == duplication_following["word-after-period"]
            )
            and (
                syll_b["word-before-comma"]
                == duplication_following["word-before-comma"]
            )
            and (
                syll_b["word-after-comma"] == duplication_following["word-after-comma"]
            )
        ]

        if not potential_syllables:
            df.at[index, "duplication-start-matched"] = 0
            continue

        # Find best frequency match
        duplication_start_freq = get_word_freq(
            duplication_start["CleanedWord"], duplication_start["word-pos"]
        )
        duplication_following_freq = get_word_freq(
            duplication_following["CleanedWord"], duplication_following["word-pos"]
        )
        mean_actual_freq = 0.5 * (duplication_start_freq + duplication_following_freq)

        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for syll_a, syll_b in potential_syllables:
            potential_start_freq = get_word_freq(
                syll_a["CleanedWord"], syll_a["word-pos"]
            )
            potential_following_freq = get_word_freq(
                syll_b["CleanedWord"], syll_b["word-pos"]
            )

            # Handle zero frequencies
            if potential_start_freq == 0 and potential_following_freq != 0:
                potential_start_freq = potential_following_freq
            elif potential_start_freq != 0 and potential_following_freq == 0:
                potential_following_freq = potential_start_freq
            elif potential_start_freq == 0 and potential_following_freq == 0:
                potential_start_freq = -1
                potential_following_freq = -1

            mean_candidate_freq = 0.5 * (
                potential_start_freq + potential_following_freq
            )
            freq_diff = abs(mean_candidate_freq - mean_actual_freq)

            if freq_diff < best_freq_diff:
                best_freq_diff = freq_diff
                best_freq_diff_idx = syll_a.name

        # Mark matches
        df.at[index, "duplication-start-matched"] = 1
        df.at[best_freq_diff_idx, "comparison-duplication-start"] = 1
        df.at[best_freq_diff_idx, "comparison-duplication-start-idx"] = (
            duplication_start["duplication-idx"]
        )

    # Match duplication ends
    for index, duplication_end in df[df["duplication-end"] == 1].iterrows():
        # Get candidate syllables (reset for duplication ends)
        candidate_df = df[
            (df["any-deviation"] == 0)
            & (df["any-deviation-before"] == 0)
            & (df["any-deviation-after"] == 0)
            & (df["any-deviation-after"].shift(-1) == 0)
            & (df["comparison-duplication-end"] != 1)
        ]

        if index + 1 >= len(df):
            continue

        duplication_following = df.iloc[index + 1]

        # Get potential syllable pairs
        potential_syllables = []
        for i in range(len(candidate_df) - 1):
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1:
                potential_syllables.append(
                    (candidate_df.iloc[i], candidate_df.iloc[i + 1])
                )

        # Filter for perfect matches on specified fields
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_a["first-syll-word"] == duplication_end["first-syll-word"])
            and (syll_a["last-syll-word"] == duplication_end["last-syll-word"])
            and (syll_a["word-before-period"] == duplication_end["word-before-period"])
            and (syll_a["word-after-period"] == duplication_end["word-after-period"])
            and (syll_a["word-before-comma"] == duplication_end["word-before-comma"])
            and (syll_a["word-after-comma"] == duplication_end["word-after-comma"])
        ]

        # Filter for N+1 syllable matches
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_b["first-syll-word"] == duplication_following["first-syll-word"])
            and (syll_b["last-syll-word"] == duplication_following["last-syll-word"])
            and (
                syll_b["word-before-period"]
                == duplication_following["word-before-period"]
            )
            and (
                syll_b["word-after-period"]
                == duplication_following["word-after-period"]
            )
            and (
                syll_b["word-before-comma"]
                == duplication_following["word-before-comma"]
            )
            and (
                syll_b["word-after-comma"] == duplication_following["word-after-comma"]
            )
        ]

        if not potential_syllables:
            df.at[index, "duplication-end-matched"] = 0
            continue

        # Find best frequency match
        duplication_end_freq = get_word_freq(
            duplication_end["CleanedWord"], duplication_end["word-pos"]
        )
        duplication_following_freq = get_word_freq(
            duplication_following["CleanedWord"], duplication_following["word-pos"]
        )
        mean_actual_freq = 0.5 * (duplication_end_freq + duplication_following_freq)

        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for syll_a, syll_b in potential_syllables:
            potential_end_freq = get_word_freq(
                syll_a["CleanedWord"], syll_a["word-pos"]
            )
            potential_following_freq = get_word_freq(
                syll_b["CleanedWord"], syll_b["word-pos"]
            )

            # Handle zero frequencies
            if potential_end_freq == 0 and potential_following_freq != 0:
                potential_end_freq = potential_following_freq
            elif potential_end_freq != 0 and potential_following_freq == 0:
                potential_following_freq = potential_end_freq
            elif potential_end_freq == 0 and potential_following_freq == 0:
                potential_end_freq = -1
                potential_following_freq = -1

            mean_candidate_freq = 0.5 * (potential_end_freq + potential_following_freq)
            freq_diff = abs(mean_candidate_freq - mean_actual_freq)

            if freq_diff < best_freq_diff:
                best_freq_diff = freq_diff
                best_freq_diff_idx = syll_a.name

        # Mark matches
        df.at[index, "duplication-end-matched"] = 1
        df.at[best_freq_diff_idx, "comparison-duplication-end"] = 1
        df.at[best_freq_diff_idx, "comparison-duplication-end-idx"] = duplication_end[
            "duplication-idx"
        ]


def match_duplications_alt(df: pd.DataFrame) -> None:
    """
    Matches duplications in the DataFrame (relaxed version).
    """
    logging.info("Matching duplications (relaxed)...")

    # Match duplication starts
    for index, duplication_start in df[df["duplication-start"] == 1].iterrows():
        candidate_df = df[
            (df["any-deviation"] == 0)
            & (df["any-deviation-before"] == 0)
            & (df["any-deviation-after"] == 0)
            & (df["any-deviation-after"].shift(-1) == 0)
            & (df["comparison-duplication-start"] != 1)
        ]

        if index + 1 >= len(df):
            continue

        duplication_following = df.iloc[index + 1]
        duplication_spans_multiple_words = bool(
            duplication_following["first-syll-word"]
        )

        # Get potential syllable pairs
        potential_syllables = []
        for i in range(len(candidate_df) - 1):
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1:
                potential_syllables.append(
                    (candidate_df.iloc[i], candidate_df.iloc[i + 1])
                )

        # Initial matches with relaxed criteria
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (bool(syll_b["first-syll-word"]) == duplication_spans_multiple_words)
            and (
                syll_a["word-before-period"] == duplication_start["word-before-period"]
            )
            and (syll_a["word-after-period"] == duplication_start["word-after-period"])
            and (syll_a["word-before-comma"] == duplication_start["word-before-comma"])
            and (syll_a["word-after-comma"] == duplication_start["word-after-comma"])
        ]

        # Conditional matches using implication logic
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (
                not syll_a["word-before-period"]
                or (syll_a["last-syll-word"] == duplication_start["last-syll-word"])
            )
            and (
                not syll_a["word-after-period"]
                or (syll_a["first-syll-word"] == duplication_start["first-syll-word"])
            )
            and (
                not syll_a["word-before-comma"]
                or (syll_a["last-syll-word"] == duplication_start["last-syll-word"])
            )
            and (
                not syll_a["word-after-comma"]
                or (syll_a["first-syll-word"] == duplication_start["first-syll-word"])
            )
        ]

        # Filter for N+1 syllable matches
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (
                syll_b["word-before-period"]
                == duplication_following["word-before-period"]
            )
            and (
                syll_b["word-after-period"]
                == duplication_following["word-after-period"]
            )
            and (
                syll_b["word-before-comma"]
                == duplication_following["word-before-comma"]
            )
            and (
                syll_b["word-after-comma"] == duplication_following["word-after-comma"]
            )
        ]

        # Conditional matches for N+1 syllable
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (
                not syll_b["word-before-period"]
                or (syll_b["last-syll-word"] == duplication_following["last-syll-word"])
            )
            and (
                not syll_b["word-after-period"]
                or (
                    syll_b["first-syll-word"]
                    == duplication_following["first-syll-word"]
                )
            )
            and (
                not syll_b["word-before-comma"]
                or (syll_b["last-syll-word"] == duplication_following["last-syll-word"])
            )
            and (
                not syll_b["word-after-comma"]
                or (
                    syll_b["first-syll-word"]
                    == duplication_following["first-syll-word"]
                )
            )
        ]

        if not potential_syllables:
            df.at[index, "duplication-start-matched"] = 0
            continue

        # Find best frequency match (same as strict version)
        duplication_start_freq = get_word_freq(
            duplication_start["CleanedWord"], duplication_start["word-pos"]
        )
        duplication_following_freq = get_word_freq(
            duplication_following["CleanedWord"], duplication_following["word-pos"]
        )
        mean_actual_freq = 0.5 * (duplication_start_freq + duplication_following_freq)

        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for syll_a, syll_b in potential_syllables:
            potential_start_freq = get_word_freq(
                syll_a["CleanedWord"], syll_a["word-pos"]
            )
            potential_following_freq = get_word_freq(
                syll_b["CleanedWord"], syll_b["word-pos"]
            )

            if potential_start_freq == 0 and potential_following_freq != 0:
                potential_start_freq = potential_following_freq
            elif potential_start_freq != 0 and potential_following_freq == 0:
                potential_following_freq = potential_start_freq
            elif potential_start_freq == 0 and potential_following_freq == 0:
                potential_start_freq = -1
                potential_following_freq = -1

            mean_candidate_freq = 0.5 * (
                potential_start_freq + potential_following_freq
            )
            freq_diff = abs(mean_candidate_freq - mean_actual_freq)

            if freq_diff < best_freq_diff:
                best_freq_diff = freq_diff
                best_freq_diff_idx = syll_a.name

        # Mark matches
        df.at[index, "duplication-start-matched"] = 1
        df.at[best_freq_diff_idx, "comparison-duplication-start"] = 1
        df.at[best_freq_diff_idx, "comparison-duplication-start-idx"] = (
            duplication_start["duplication-idx"]
        )

    # Match duplication ends (similar relaxed logic)
    for index, duplication_end in df[df["duplication-end"] == 1].iterrows():
        candidate_df = df[
            (df["any-deviation"] == 0)
            & (df["any-deviation-before"] == 0)
            & (df["any-deviation-after"] == 0)
            & (df["any-deviation-after"].shift(-1) == 0)
            & (df["comparison-duplication-end"] != 1)
        ]

        if index + 1 >= len(df):
            continue

        duplication_following = df.iloc[index + 1]
        duplication_spans_multiple_words = bool(
            duplication_following["first-syll-word"]
        )

        # Get potential syllable pairs
        potential_syllables = []
        for i in range(len(candidate_df) - 1):
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1:
                potential_syllables.append(
                    (candidate_df.iloc[i], candidate_df.iloc[i + 1])
                )

        # Apply same relaxed filtering logic as for starts
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (bool(syll_b["first-syll-word"]) == duplication_spans_multiple_words)
            and (syll_a["word-before-period"] == duplication_end["word-before-period"])
            and (syll_a["word-after-period"] == duplication_end["word-after-period"])
            and (syll_a["word-before-comma"] == duplication_end["word-before-comma"])
            and (syll_a["word-after-comma"] == duplication_end["word-after-comma"])
        ]

        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (
                not syll_a["word-before-period"]
                or (syll_a["last-syll-word"] == duplication_end["last-syll-word"])
            )
            and (
                not syll_a["word-after-period"]
                or (syll_a["first-syll-word"] == duplication_end["first-syll-word"])
            )
            and (
                not syll_a["word-before-comma"]
                or (syll_a["last-syll-word"] == duplication_end["last-syll-word"])
            )
            and (
                not syll_a["word-after-comma"]
                or (syll_a["first-syll-word"] == duplication_end["first-syll-word"])
            )
        ]

        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (
                syll_b["word-before-period"]
                == duplication_following["word-before-period"]
            )
            and (
                syll_b["word-after-period"]
                == duplication_following["word-after-period"]
            )
            and (
                syll_b["word-before-comma"]
                == duplication_following["word-before-comma"]
            )
            and (
                syll_b["word-after-comma"] == duplication_following["word-after-comma"]
            )
        ]

        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (
                not syll_b["word-before-period"]
                or (syll_b["last-syll-word"] == duplication_following["last-syll-word"])
            )
            and (
                not syll_b["word-after-period"]
                or (
                    syll_b["first-syll-word"]
                    == duplication_following["first-syll-word"]
                )
            )
            and (
                not syll_b["word-before-comma"]
                or (syll_b["last-syll-word"] == duplication_following["last-syll-word"])
            )
            and (
                not syll_b["word-after-comma"]
                or (
                    syll_b["first-syll-word"]
                    == duplication_following["first-syll-word"]
                )
            )
        ]

        if not potential_syllables:
            df.at[index, "duplication-end-matched"] = 0
            continue

        # Find best frequency match (same logic as strict version)
        duplication_end_freq = get_word_freq(
            duplication_end["CleanedWord"], duplication_end["word-pos"]
        )
        duplication_following_freq = get_word_freq(
            duplication_following["CleanedWord"], duplication_following["word-pos"]
        )
        mean_actual_freq = 0.5 * (duplication_end_freq + duplication_following_freq)

        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for syll_a, syll_b in potential_syllables:
            potential_end_freq = get_word_freq(
                syll_a["CleanedWord"], syll_a["word-pos"]
            )
            potential_following_freq = get_word_freq(
                syll_b["CleanedWord"], syll_b["word-pos"]
            )

            if potential_end_freq == 0 and potential_following_freq != 0:
                potential_end_freq = potential_following_freq
            elif potential_end_freq != 0 and potential_following_freq == 0:
                potential_following_freq = potential_end_freq
            elif potential_end_freq == 0 and potential_following_freq == 0:
                potential_end_freq = -1
                potential_following_freq = -1

            mean_candidate_freq = 0.5 * (potential_end_freq + potential_following_freq)
            freq_diff = abs(mean_candidate_freq - mean_actual_freq)

            if freq_diff < best_freq_diff:
                best_freq_diff = freq_diff
                best_freq_diff_idx = syll_a.name

        # Mark matches
        df.at[index, "duplication-end-matched"] = 1
        df.at[best_freq_diff_idx, "comparison-duplication-end"] = 1
        df.at[best_freq_diff_idx, "comparison-duplication-end-idx"] = duplication_end[
            "duplication-idx"
        ]
