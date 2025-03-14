import pandas as pd

from syllable_match.resources import get_word_freq


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
        # Remove syllables previously used as a match
        candidate_df = candidate_df[candidate_df["comparison-hesitation-start"] != 1]

        # Extract the next syllable (the end of the hesitation)
        hesitation_end = df.iloc[index + 1]
        # Get potential syllables (unmatched), ensuring they're adjacent
        potential_syllables = []
        for i in range(len(candidate_df) - 1):
            # Compare the syllable indices to make sure they're adjacent
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1:
                new_syllable_pair = (candidate_df.iloc[i], candidate_df.iloc[i + 1])
                potential_syllables.append(new_syllable_pair)
                i += 1  # Skip the next syllable

        # Find candidate syllables that match perfectly on:
        #   first-syll-word, last-syll-word, word-before-period,
        #   word-after-period, word-before-comma, and word-after-comma
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_a["first-syll-word"] == hesitation_start["first-syll-word"])
            & (syll_a["last-syll-word"] == hesitation_start["last-syll-word"])
            & (syll_a["word-before-period"] == hesitation_start["word-before-period"])
            & (syll_a["word-after-period"] == hesitation_start["word-after-period"])
            & (syll_a["word-before-comma"] == hesitation_start["word-before-comma"])
            & (syll_a["word-after-comma"] == hesitation_start["word-after-comma"])
        ]
        # Of these potential matches, identify which potential-syllables-to-match have an N+1
        #   syllable that matches the corresponding hesitation-end syllable on the following fields:
        #   first-syll-word, last-syll-word, word-before-period,
        #   word-after-period, word-before-comma, and word-after-comma
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_b["first-syll-word"] == hesitation_end["first-syll-word"])
            & (syll_b["last-syll-word"] == hesitation_end["last-syll-word"])
            & (syll_b["word-before-period"] == hesitation_end["word-before-period"])
            & (syll_b["word-after-period"] == hesitation_end["word-after-period"])
        ]

        # If no syllable pairs at all match the target hesitation start/end pair,
        #   then mark the target hesitation start/end as matched = 0
        if not potential_syllables:
            df.at[index, "hesitation-start-matched"] = 0
            df.at[index + 1, "hesitation-end-matched"] = 0
            return

        # Compute the average word-freq for the current
        #   hesitation-start and hesitation-end words
        hesitation_start_word_freq = get_word_freq(hesitation_start["CleanedWord"])
        hesitation_end_word_freq = get_word_freq(hesitation_end["CleanedWord"])
        mean_actual_freq = 0.5 * (hesitation_start_word_freq + hesitation_end_word_freq)

        # We find the potential pair of N, N+1 syllables
        #   that have the closest average word frequency
        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for syll_a, syll_b in potential_syllables:
            # Compute the average word-freq for the current
            #   potential-syllable-to-match and hesitation-end words
            potential_start_word_freq = get_word_freq(syll_a["CleanedWord"])
            potential_end_word_freq = get_word_freq(syll_b["CleanedWord"])

            # Handle the case where one or both word frequencies are 0
            if potential_start_word_freq == 0 and potential_end_word_freq != 0:
                potential_start_word_freq = potential_end_word_freq
            elif potential_start_word_freq != 0 and potential_end_word_freq == 0:
                potential_end_word_freq = potential_start_word_freq
            elif potential_start_word_freq == 0 and potential_end_word_freq == 0:
                potential_start_word_freq = -1
                potential_end_word_freq = -1

            mean_candidate_freq = 0.5 * (
                potential_start_word_freq + potential_end_word_freq
            )

            # Compute the difference between the mean word-freq and the average word-freq
            freq_diff = abs(mean_candidate_freq - mean_actual_freq)
            if freq_diff < best_freq_diff:
                best_freq_diff = freq_diff
                best_freq_diff_idx = syll_a.name  # gets index value

        # Mark the target hesitation start/end as matched = 1
        df.at[index, "hesitation-start-matched"] = 1
        df.at[index + 1, "hesitation-end-matched"] = 1

        # Mark the potential pair of N, N+1 syllables as matching
        df.at[best_freq_diff_idx, "comparison-hesitation-start"] = 1
        df.at[best_freq_diff_idx + 1, "comparison-hesitation-end"] = 1

        # Indicate which hesitations we've matched to
        df.loc[
            [best_freq_diff_idx, best_freq_diff_idx + 1], "comparison-hesitation-idx"
        ] = hesitation_start["hesitation-idx"]

    return
