import pandas as pd

from syllable_match.resources import load_word_frequencies


def match_errors(df: pd.DataFrame) -> pd.DataFrame:
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
    potential_syllables = df[
        (df["any-deviation"] == 0)
        & (df["any-deviation-before"] == 0)
        & (df["any-deviation-after"] == 0)
    ]
    # Remove any syllables where the N+1 syllable does not also meet these criteria
    potential_syllables = potential_syllables[
        potential_syllables["any-deviation-after"].shift(-1) == 0
    ]

    for idx, row in df.iterrows():
        if row[marker_type] != 1:
            continue
        # Remove syllables matched on the previous iteration
        potential_syllables = potential_syllables[
            potential_syllables[f"{marker_type}-start"] != 1
        ]
        # Find candidate syllables that match perfectly on: first-syll-word,
        #   last-syll-word, word-before-period, word-after-period,
        #   word-before-comma, word-after-comma
        potential_syllables = potential_syllables[
            (potential_syllables["first-syll-word"] == row["first-syll-word"])
            & (potential_syllables["last-syll-word"] == row["last-syll-word"])
            & (potential_syllables["word-before-period"] == row["word-before-period"])
            & (potential_syllables["word-after-period"] == row["word-after-period"])
            & (potential_syllables["word-before-comma"] == row["word-before-comma"])
            & (potential_syllables["word-after-comma"] == row["word-after-comma"])
        ]
        # Of these potential matches, identify the candidates with an N+1 syllable
        #   that matches the target syllable's N+1 syllable on: first-syll-word,
        #   last-syll-word, word-before-period, word-after-period,
        #   word-before-comma, word-after-comma
        potential_syllables = potential_syllables[
            (
                potential_syllables["first-syll-word"].shift(-1)
                == df[idx + 1]["first-syll-word"]
            )
            & (
                potential_syllables["last-syll-word"].shift(-1)
                == df[idx + 1]["last-syll-word"]
            )
            & (
                potential_syllables["word-before-period"].shift(-1)
                == df[idx + 1]["word-before-period"]
            )
            & (
                potential_syllables["word-after-period"].shift(-1)
                == df[idx + 1]["word-after-period"]
            )
            & (
                potential_syllables["word-before-comma"].shift(-1)
                == df[idx + 1]["word-before-comma"]
            )
            & (
                potential_syllables["word-after-comma"].shift(-1)
                == df[idx + 1]["word-after-comma"]
            )
        ]
        if potential_syllables.empty:
            row[f"{marker_type}-matched"] = 0
            continue

        # Compute the average word-freq for the target syllable
        #   and its subsequent (N+1) syllable
        word_freqs = load_word_frequencies()
        target_syll_word_freq = word_freqs[word_freqs["Word"] == row["CleanedWord"]][
            "FREQcount"
        ]
        next_syll_word_freq = word_freqs[
            word_freqs["word"] == df[idx + 1]["CleanedWord"]
        ]["word-freq"]
        mean_actual_freq = 0.5 * (target_syll_word_freq + next_syll_word_freq)

        # We find the potential pair of N, N+1 syllables
        #   that have the closest average word frequency
        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for potential_idx, p in potential_syllables.iterrows():
            # Compute the average word-freq for the current
            #   potential-syllable-to-match and hesitation-end words
            potential_syll_word_freq = word_freqs[
                word_freqs["Word"] == p["CleanedWord"]
            ]["FREQcount"]
            potential_next_word_freq = word_freqs[
                word_freqs["Word"]
                == potential_syllables[potential_idx + 1]["CleanedWord"]
            ]["FREQcount"]
            mean_candidate_freq = 0.5 * (
                potential_syll_word_freq + potential_next_word_freq
            )

            # Compute the difference between the mean word-freq and the average word-freq
            freq_diff = abs(mean_candidate_freq - mean_actual_freq)
            if freq_diff < best_freq_diff:
                best_freq_diff = freq_diff
                best_freq_diff_idx = potential_idx

        # Mark the target syllable as matched
        df.at[idx, f"{marker_type}-matched"] = 1

        # Mark the best-fit syllable as matching
        df.at[best_freq_diff_idx, f"comparison-{marker_type}"] = 1

        # Indicate which error we've matched to
        df.at[best_freq_diff_idx, f"comparison-{marker_type}-idx"] = idx
