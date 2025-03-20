import pandas as pd

from syllable_match.resources import get_word_freq

from .utils import extract_marker_type


def match_errors(df: pd.DataFrame) -> None:
    """
    Matches errors in the DataFrame.
    """
    for error_type in [
        "low-error-start",
        "low-error-end",
        "high-error-start",
        "high-error-end",
    ]:
        match_error_type(df, error_type)


def match_error_type(df: pd.DataFrame, marker_type: str) -> None:
    """
    Matches error types in the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        marker_type (str): The type of error marker to match. It may be one of the following:
                          'low-error-start', 'low-error-end', 'high-error-start', or 'high-error-end'.
    """
    # Start by finding all syllables where any-deviation = 0
    #   AND any-deviation-before = 0 AND any-deviation-after = 0
    candidate_df = df[
        (df["any-deviation"] == 0)
        & (df["any-deviation-before"] == 0)
        & (df["any-deviation-after"] == 0)
    ]
    # Remove any syllables where the N+1 syllable does not also meet these criteria
    candidate_df = candidate_df[candidate_df["any-deviation-after"].shift(-1) == 0]

    for idx, row in df.iterrows():
        if row[marker_type] != 1:
            continue
        # Remove syllables matched on the previous iteration
        candidate_df = candidate_df[
            candidate_df[f"{extract_marker_type(marker_type)}-start"] != 1
        ]

        # Build a list of tuples of adjacent syllables
        potential_syllables = [
            (candidate_df.iloc[i], candidate_df.iloc[i + 1])
            for i in range(len(candidate_df) - 1)
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1
        ]
        # Find candidate syllables that match perfectly on: first-syll-word,
        #   last-syll-word, word-before-period, word-after-period,
        #   word-before-comma, word-after-comma
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_a["first-syll-word"] == row["first-syll-word"])
            & (syll_a["last-syll-word"] == row["last-syll-word"])
            & (syll_a["word-before-period"] == row["word-before-period"])
            & (syll_a["word-after-period"] == row["word-after-period"])
            & (syll_a["word-before-comma"] == row["word-before-comma"])
            & (syll_a["word-after-comma"] == row["word-after-comma"])
        ]
        # Of these potential matches, identify the candidates with an N+1 syllable
        #   that matches the target syllable's N+1 syllable on: first-syll-word,
        #   last-syll-word, word-before-period, word-after-period,
        #   word-before-comma, word-after-comma
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (idx < len(df) - 1)
            and (
                (syll_b["first-syll-word"] == df.iloc[idx + 1]["first-syll-word"])
                & (syll_b["last-syll-word"] == df.iloc[idx + 1]["last-syll-word"])
                & (
                    syll_b["word-before-period"]
                    == df.iloc[idx + 1]["word-before-period"]
                )
                & (syll_b["word-after-period"] == df.iloc[idx + 1]["word-after-period"])
                & (syll_b["word-before-comma"] == df.iloc[idx + 1]["word-before-comma"])
                & (syll_b["word-after-comma"] == df.iloc[idx + 1]["word-after-comma"])
            )
        ]
        if not potential_syllables:
            row[f"{marker_type}-matched"] = 0
            continue

        # Compute the average word-freq for the target syllable
        #   and its subsequent (N+1) syllable
        target_syll_word_freq = get_word_freq(row["CleanedWord"], row["word-pos"])
        next_syll_word_freq = get_word_freq(
            df.iloc[idx + 1]["CleanedWord"], df.iloc[idx + 1]["word-pos"]
        )
        mean_actual_freq = 0.5 * (target_syll_word_freq + next_syll_word_freq)

        # We find the potential pair of N, N+1 syllables
        #   that have the closest average word frequency
        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for syll_a, syll_b in potential_syllables:
            # Compute the average word-freq for the current
            #   potential-syllable-to-match and hesitation-end words
            potential_syll_word_freq = get_word_freq(
                syll_a["CleanedWord"], syll_a["word-pos"]
            )
            potential_next_word_freq = get_word_freq(
                syll_b["CleanedWord"], syll_b["word-pos"]
            )

            # Handle the case where one or both word frequencies are 0
            if potential_syll_word_freq == 0 and potential_next_word_freq != 0:
                potential_syll_word_freq = potential_next_word_freq
            elif potential_syll_word_freq != 0 and potential_next_word_freq == 0:
                potential_next_word_freq = potential_syll_word_freq
            elif potential_syll_word_freq == 0 and potential_next_word_freq == 0:
                potential_syll_word_freq = -1
                potential_next_word_freq = -1

            mean_candidate_freq = 0.5 * (
                potential_syll_word_freq + potential_next_word_freq
            )

            # Compute the difference between the mean word-freq and the average word-freq
            freq_diff = abs(mean_candidate_freq - mean_actual_freq)
            if freq_diff < best_freq_diff:
                best_freq_diff = freq_diff
                best_freq_diff_idx = syll_a.name

        # Mark the target syllable as matched
        df.at[idx, f"{marker_type}-matched"] = 1

        # Mark the best-fit as matching
        df.at[best_freq_diff_idx, f"comparison-{marker_type}"] = 1

        # Indicate which error we've matched to
        df.at[
            best_freq_diff_idx, f"comparison-{extract_marker_type(marker_type)}-idx"
        ] = row[f"{extract_marker_type(marker_type)}-idx"]
