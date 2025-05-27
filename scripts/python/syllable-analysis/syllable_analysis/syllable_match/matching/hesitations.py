import logging

import pandas as pd

from ..resources import get_word_freq


def match_hesitations(df: pd.DataFrame) -> None:
    """
    Matches hesitations in the DataFrame.
    """
    logging.info("Matching hesitations...")

    # Loop over hesitations
    for index, hesitation_start in df[df["hesitation-start"] == 1].iterrows():
        # Start by finding all syllables where any-deviation = 0
        #   AND any-deviation-before = 0 AND any-deviation-after = 0
        candidate_df = df[
            (df["any-deviation"] == 0)
            & (df["any-deviation-before"] == 0)
            & (df["any-deviation-after"] == 0)
            # Remove any syllables where the N+1 syllable does not also meet these criteria
            & (df["any-deviation-after"].shift(-1) == 0)
            # Remove syllables matched on the previous iteration
            & (df["comparison-hesitation-start"] != 1)
        ]
        logging.info(f"Size of candidate_df: {len(candidate_df)}")

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
        logging.info(f"Size of potential_syllables: {len(potential_syllables)}")
        # Find candidate syllables that match perfectly on:
        #   first-syll-word, last-syll-word, word-before-period,
        #   word-after-period, word-before-comma, and word-after-comma
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_a["first-syll-word"] == hesitation_start["first-syll-word"])
            and (syll_a["last-syll-word"] == hesitation_start["last-syll-word"])
            and (syll_a["word-before-period"] == hesitation_start["word-before-period"])
            and (syll_a["word-after-period"] == hesitation_start["word-after-period"])
            and (syll_a["word-before-comma"] == hesitation_start["word-before-comma"])
            and (syll_a["word-after-comma"] == hesitation_start["word-after-comma"])
        ]
        logging.info(
            f"Size of potential_syllables after first filter: {len(potential_syllables)}"
        )
        # Of these potential matches, identify which potential-syllables-to-match have an N+1
        #   syllable that matches the corresponding hesitation-end syllable on the following fields:
        #   first-syll-word, last-syll-word, word-before-period,
        #   word-after-period, word-before-comma, and word-after-comma
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_b["first-syll-word"] == hesitation_end["first-syll-word"])
            and (syll_b["last-syll-word"] == hesitation_end["last-syll-word"])
            and (syll_b["word-before-period"] == hesitation_end["word-before-period"])
            and (syll_b["word-after-period"] == hesitation_end["word-after-period"])
        ]
        logging.info(
            f"Size of potential_syllables after second filter: {len(potential_syllables)}"
        )
        # If no syllable pairs at all match the target hesitation start/end pair,
        #   then mark the target hesitation start/end as matched = 0
        if not potential_syllables:
            df.at[index, "hesitation-start-matched"] = 0
            df.at[index + 1, "hesitation-end-matched"] = 0
            if index > 1:
                logging.info(
                    "Previous syllable info:\t"
                    + ", ".join(
                        [
                            f"{col}: {df.iloc[index - 1][col]}"
                            for col in df.iloc[index - 1].index
                        ]
                    )
                )
            logging.info(
                "Syllable info:\t"
                + ", ".join(
                    [
                        f"{col}: {hesitation_start[col]}"
                        for col in hesitation_start.index
                    ]
                )
            )
            if index < len(df) - 2:
                logging.info(
                    "Next syllable info:\t"
                    + ", ".join(
                        [
                            f"{col}: {df.iloc[index + 1][col]}"
                            for col in df.iloc[index + 1].index
                        ]
                    )
                )

            return

        # Compute the average word-freq for the current
        #   hesitation-start and hesitation-end words
        hesitation_start_word_freq = get_word_freq(
            hesitation_start["CleanedWord"], hesitation_start["word-pos"]
        )
        hesitation_end_word_freq = get_word_freq(
            hesitation_end["CleanedWord"], hesitation_end["word-pos"]
        )
        mean_actual_freq = 0.5 * (hesitation_start_word_freq + hesitation_end_word_freq)

        # We find the potential pair of N, N+1 syllables
        #   that have the closest average word frequency
        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for syll_a, syll_b in potential_syllables:
            # Compute the average word-freq for the current
            #   potential-syllable-to-match and hesitation-end words
            potential_start_word_freq = get_word_freq(
                syll_a["CleanedWord"], syll_a["word-pos"]
            )
            potential_end_word_freq = get_word_freq(
                syll_b["CleanedWord"], syll_b["word-pos"]
            )

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
        logging.info(
            f"Matched {hesitation_start['syllable_id']} to {df.at[best_freq_diff_idx, 'syllable_id']}"
        )

    return


def match_hesitations_alt(df: pd.DataFrame) -> None:
    """
    Matches hesitations in the DataFrame (alternate version; matching constraints are more lax).
    """
    logging.info("Matching hesitations...")

    # Loop over hesitations
    for index, hesitation_start in df[df["hesitation-start"] == 1].iterrows():
        # Start by finding all syllables where any-deviation = 0
        #   AND any-deviation-before = 0 AND any-deviation-after = 0
        candidate_df = df[
            (df["any-deviation"] == 0)
            & (df["any-deviation-before"] == 0)
            & (df["any-deviation-after"] == 0)
            # Remove any syllables where the N+1 syllable does not also meet these criteria
            & (df["any-deviation-after"].shift(-1) == 0)
            # Remove syllables matched on the previous iteration
            & (df["comparison-hesitation-start"] != 1)
        ]
        logging.info(f"Size of candidate_df: {len(candidate_df)}")

        # Extract the next syllable (the end of the hesitation)
        hesitation_end = df.iloc[index + 1]

        # Get values for whether hesitation syllables are from one or two words
        # We check the property first-syll-word for the end syllable.
        # Possible values for (start.isFirstSyllable, end.isFirstSyllable) are:
        #   0,0 = syllables within one word;
        #   1,0 = syllables within one word;
        #   0,1 = syllables in two words;
        #   1,1 = syllables in two words.
        # Output is only dependent on end syllable, so that's all we need to check!
        hesitation_spans_multiple_words = bool(hesitation_end["first-syll-word"])

        # Get potential syllables (unmatched), ensuring they're adjacent
        potential_syllables = []
        for i in range(len(candidate_df) - 1):
            # Compare the syllable indices to make sure they're adjacent
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1:
                new_syllable_pair = (candidate_df.iloc[i], candidate_df.iloc[i + 1])
                potential_syllables.append(new_syllable_pair)
                i += 1  # Skip the next syllable
        logging.info(f"Size of potential_syllables: {len(potential_syllables)}")

        # Find candidate syllables that match perfectly on:
        #
        # number of words spanned (see above; may be 1 or 2)
        # word-before-period
        #   and if true, also match perfectly on: last-syll-word
        # word-after-period
        #   and if true, also match perfectly on: first-syll-word
        # word-before-comma
        #   and if true, also match perfectly on: last-syll-word
        # word-after-comma
        #   and if true, also match perfectly on: first-syll-word
        #
        # Check initial matches
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (bool(syll_b["first-syll-word"]) == hesitation_spans_multiple_words)
            and (syll_a["word-before-period"] == hesitation_start["word-before-period"])
            and (syll_a["word-after-period"] == hesitation_start["word-after-period"])
            and (syll_a["word-before-comma"] == hesitation_start["word-before-comma"])
            and (syll_a["word-after-comma"] == hesitation_start["word-after-comma"])
        ]
        # Check conditional matches
        #
        # We reframe our conditional matches above from
        #   "Keep rows where match(A). If A is true, only keep rows where match(B)"
        #   to "Keep rows where match(A). Then keep rows where A implies match(B)."
        #
        # We can rewrite p -> q = not(p) or q, so our "keep" condition is:
        #   not(A) or match(B)
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (
                not syll_a["word-before-period"]
                or (syll_a["last-syll-word"] == hesitation_start["last-syll-word"])
            )
            and (
                not syll_a["word-after-period"]
                or (syll_a["first-syll-word"] == hesitation_start["first-syll-word"])
            )
            and (
                not syll_a["word-before-comma"]
                or (syll_a["last-syll-word"] == hesitation_start["last-syll-word"])
            )
            and (
                not syll_a["word-after-comma"]
                or (syll_a["first-syll-word"] == hesitation_start["first-syll-word"])
            )
        ]
        logging.info(
            f"Size of potential_syllables after first filter: {len(potential_syllables)}"
        )

        # Of these potential matches, identify which potential-syllables-to-match have an N+1
        #   syllable that matches the corresponding hesitation-end syllable on the following fields:
        #
        # word-before-period
        #   and if true, also match perfectly on: last-syll-word
        # word-after-period
        #   and if true, also match perfectly on: first-syll-word
        # word-before-comma
        #   and if true, also match perfectly on: last-syll-word
        # word-after-comma
        #   and if true, also match perfectly on: first-syll-word
        #
        # We apply a similar two-part match from above using implication.
        #
        # Initial matches
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (syll_b["word-before-period"] == hesitation_end["word-before-period"])
            and (syll_b["word-after-period"] == hesitation_end["word-after-period"])
            and (syll_b["word-before-comma"] == hesitation_end["word-before-comma"])
            and (syll_b["word-after-comma"] == hesitation_end["word-after-comma"])
        ]
        # Conditional matches
        potential_syllables = [
            (syll_a, syll_b)
            for syll_a, syll_b in potential_syllables
            if (
                not syll_b["word-before-period"]
                or (syll_b["last-syll-word"] == hesitation_end["last-syll-word"])
            )
            and (
                not syll_b["word-after-period"]
                or (syll_b["first-syll-word"] == hesitation_end["first-syll-word"])
            )
            and (
                not syll_b["word-before-comma"]
                or (syll_b["last-syll-word"] == hesitation_end["last-syll-word"])
            )
            and (
                not syll_b["word-after-comma"]
                or (syll_b["first-syll-word"] == hesitation_end["first-syll-word"])
            )
        ]
        logging.info(
            f"Size of potential_syllables after second filter: {len(potential_syllables)}"
        )
        # If no syllable pairs at all match the target hesitation start/end pair,
        #   then mark the target hesitation start/end as matched = 0
        if not potential_syllables:
            df.at[index, "hesitation-start-matched"] = 0
            df.at[index + 1, "hesitation-end-matched"] = 0
            if index > 1:
                logging.info(
                    "Previous syllable info:\t"
                    + ", ".join(
                        [
                            f"{col}: {df.iloc[index - 1][col]}"
                            for col in df.iloc[index - 1].index
                        ]
                    )
                )
            logging.info(
                "Syllable info:\t"
                + ", ".join(
                    [
                        f"{col}: {hesitation_start[col]}"
                        for col in hesitation_start.index
                    ]
                )
            )
            if index < len(df) - 2:
                logging.info(
                    "Next syllable info:\t"
                    + ", ".join(
                        [
                            f"{col}: {df.iloc[index + 1][col]}"
                            for col in df.iloc[index + 1].index
                        ]
                    )
                )

            return

        # Compute the average word-freq for the current
        #   hesitation-start and hesitation-end words
        hesitation_start_word_freq = get_word_freq(
            hesitation_start["CleanedWord"], hesitation_start["word-pos"]
        )
        hesitation_end_word_freq = get_word_freq(
            hesitation_end["CleanedWord"], hesitation_end["word-pos"]
        )
        mean_actual_freq = 0.5 * (hesitation_start_word_freq + hesitation_end_word_freq)

        # We find the potential pair of N, N+1 syllables
        #   that have the closest average word frequency
        best_freq_diff = float("inf")
        best_freq_diff_idx = None
        for syll_a, syll_b in potential_syllables:
            # Compute the average word-freq for the current
            #   potential-syllable-to-match and hesitation-end words
            potential_start_word_freq = get_word_freq(
                syll_a["CleanedWord"], syll_a["word-pos"]
            )
            potential_end_word_freq = get_word_freq(
                syll_b["CleanedWord"], syll_b["word-pos"]
            )

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
        logging.info(
            f"Matched {hesitation_start['syllable_id']} to {df.at[best_freq_diff_idx, 'syllable_id']}"
        )

    return
