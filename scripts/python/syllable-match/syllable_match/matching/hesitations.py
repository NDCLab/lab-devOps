import pandas as pd

from syllable_match.resources import load_word_frequencies


def match_hesitations(df: pd.DataFrame) -> None:
    """
    Matches hesitations in the DataFrame.
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

    # Loop over hesitations
    for index, hesitation_start in df[df["hesitation-start"] == 1].iterrows():
        # Extract the next syllable (the end of the hesitation)
        hesitation_end = df.iloc[index + 1]
        # Get potential syllables (unmatched)
        potential_syllables = candidate_df[
            candidate_df["comparison-hesitation-start"] != 1
        ]
        # Find candidate syllables that match perfectly on:
        #   first-syll-word, last-syll-word, word-before-period,
        #   word-after-period, word-before-comma, and word-after-comma
        potential_syllables = potential_syllables[
            (
                potential_syllables["first-syll-word"]
                == hesitation_start["first-syll-word"]
            )
            & (
                potential_syllables["last-syll-word"]
                == hesitation_start["last-syll-word"]
            )
            & (
                potential_syllables["word-before-period"]
                == hesitation_start["word-before-period"]
            )
            & (
                potential_syllables["word-after-period"]
                == hesitation_start["word-after-period"]
            )
            & (
                potential_syllables["word-before-comma"]
                == hesitation_start["word-before-comma"]
            )
            & (
                potential_syllables["word-after-comma"]
                == hesitation_start["word-after-comma"]
            )
        ]
        # Of these potential matches, identify which potential-syllables-to-match have an N+1
        #   syllable that matches the corresponding hesitation-end syllable on the following fields:
        #   first-syll-word, last-syll-word, word-before-period,
        #   word-after-period, word-before-comma, and word-after-comma
        potential_syllables = potential_syllables[
            (
                potential_syllables.shift(-1)["first-syll-word"]
                == hesitation_end["first-syll-word"]
            )
            & (
                potential_syllables.shift(-1)["last-syll-word"]
                == hesitation_end["last-syll-word"]
            )
            & (
                potential_syllables.shift(-1)["word-before-period"]
                == hesitation_end["word-before-period"]
            )
            & (
                potential_syllables.shift(-1)["word-after-period"]
                == hesitation_end["word-after-period"]
            )
        ]

        # If no syllable pairs at all match the target hesitation start/end pair,
        #   then mark the target hesitation start/end as matched = 0
        if potential_syllables.empty:
            df.at[index, "hesitation-start-matched"] = 0
            df.at[index + 1, "hesitation-end-matched"] = 0
            return

        # Compute the average word-freq for the current
        #   hesitation-start and hesitation-end words
        word_freqs = load_word_frequencies()
        hesitation_start_word_freq = word_freqs[
            word_freqs["Word"] == hesitation_start["CleanedWord"]
        ]["FREQcount"]
        hesitation_end_word_freq = word_freqs[
            word_freqs["word"] == hesitation_end["word-before-period"]
        ]["word-freq"]
        mean_actual_freq = 0.5 * (hesitation_start_word_freq + hesitation_end_word_freq)

        # We find the potential pair of N, N+1 syllables
        #   that have the closest average word frequency
        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for idx, p in potential_syllables.iterrows():
            # Compute the average word-freq for the current
            #   potential-syllable-to-match and hesitation-end words
            potential_start_word_freq = word_freqs[
                word_freqs["Word"] == p["CleanedWord"]
            ]["FREQcount"]
            potential_end_word_freq = word_freqs[
                word_freqs["Word"] == potential_syllables[idx + 1]["CleanedWord"]
            ]["FREQcount"]
            mean_candidate_freq = 0.5 * (
                potential_start_word_freq + potential_end_word_freq
            )

            # Compute the difference between the mean word-freq and the average word-freq
            freq_diff = abs(mean_candidate_freq - mean_actual_freq)
            if freq_diff < best_freq_diff:
                best_freq_diff = freq_diff
                best_freq_diff_idx = idx

        # Mark the target hesitation start/end as matched = 1
        df.at[index, "hesitation-start-matched"] = 1
        df.at[index + 1, "hesitation-end-matched"] = 1

        # Mark the potential pair of N, N+1 syllables as matching
        df.at[best_freq_diff_idx, "comparison-hesitation-start"] = 1
        df.at[best_freq_diff_idx + 1, "comparison-hesitation-end"] = 1

        # Indicate which hesitations we've matched to
        df.at[best_freq_diff_idx, "comparison-hesitation-start-idx"] = index
        df.at[best_freq_diff_idx + 1, "comparison-hesitation-end-idx"] = index + 1

    return
