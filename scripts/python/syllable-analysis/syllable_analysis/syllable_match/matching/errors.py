import pandas as pd

from ..resources import get_word_freq
from .utils import extract_marker_type

import logging


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
    logging.info(f"Matching {marker_type} errors...")

    for idx, row in df.iterrows():
        if row[marker_type] != 1:
            continue
        # Start by finding all syllables where any-deviation = 0
        #   AND any-deviation-before = 0 AND any-deviation-after = 0
        candidate_df = df[
            (df["any-deviation"] == 0)
            & (df["any-deviation-before"] == 0)
            & (df["any-deviation-after"] == 0)
            # Remove any syllables where the N+1 syllable does not also meet these criteria
            & (df["any-deviation-after"].shift(-1) == 0)
            # Remove syllables matched on the previous iteration
            & (df[f"comparison-{marker_type}"] != 1)
        ]
        logging.info(f"Size of candidate_df: {len(candidate_df)}")

        # Build a list of tuples of adjacent syllables
        potential_syllables = [
            (candidate_df.iloc[i], candidate_df.iloc[i + 1])
            for i in range(len(candidate_df) - 1)
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1
        ]
        logging.info(f"Size of potential_syllables: {len(potential_syllables)}")
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
        logging.info(
            f"Size of potential_syllables after first filter: {len(potential_syllables)}"
        )
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
        logging.info(
            f"Size of potential_syllables after second filter: {len(potential_syllables)}"
        )
        if not potential_syllables:
            row[f"{marker_type}-matched"] = 0
            if idx > 0:
                logging.info(
                    "Previous syllable info:\t"
                    + ", ".join([f"{col}: {row[col]}" for col in row.index])
                )
            logging.info(
                "Syllable info:\t"
                + ", ".join([f"{col}: {row[col]}" for col in row.index])
            )
            if idx < len(df) - 1:
                logging.info(
                    "Next syllable info:\t"
                    + ", ".join(
                        [
                            f"{col}: {df.iloc[idx + 1][col]}"
                            for col in df.iloc[idx + 1].index
                        ]
                    )
                )
            continue

        # Compute the average word-freq for the target syllable
        #   and its subsequent (N+1) syllable
        target_syll_word_freq = get_word_freq(row["CleanedWord"], row["word-pos"])
        next_syll_word_freq = get_word_freq(
            df.iloc[idx + 1]["CleanedWord"], df.iloc[idx + 1]["word-pos"]
        )
        mean_actual_freq = 0.5 * (target_syll_word_freq + next_syll_word_freq)
        logging.info(f"Mean actual freq: {mean_actual_freq}")

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

        logging.info(f"Best freq diff: {best_freq_diff}")

        # Mark the target syllable as matched
        df.at[idx, f"{marker_type}-matched"] = 1

        # Mark the best-fit as matching
        df.at[best_freq_diff_idx, f"comparison-{marker_type}"] = 1

        # Indicate which error we've matched to
        df.at[
            best_freq_diff_idx, f"comparison-{extract_marker_type(marker_type)}-idx"
        ] = row[f"{extract_marker_type(marker_type)}-idx"]
        logging.info(
            f"Matched {row['syllable_id']} to {df.at[best_freq_diff_idx, 'syllable_id']}"
        )


def match_errors_alt(df: pd.DataFrame) -> None:
    """
    Matches errors in the DataFrame.
    """
    for error_type in [
        "low-error-start",
        "low-error-end",
        "high-error-start",
        "high-error-end",
    ]:
        match_error_type_alt(df, error_type)


def match_error_type_alt(df: pd.DataFrame, marker_type: str) -> None:
    """
    Matches error types in the DataFrame (alternate version; matching constraints are more lax).

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        marker_type (str): The type of error marker to match. It may be one of the following:
                          'low-error-start', 'low-error-end', 'high-error-start', or 'high-error-end'.
    """
    logging.info(f"Matching {marker_type} errors...")

    for idx, row in df.iterrows():
        if row[marker_type] != 1:
            continue
        # Start by finding all syllables where any-deviation = 0
        #   AND any-deviation-before = 0 AND any-deviation-after = 0
        candidate_df = df[
            (df["any-deviation"] == 0)
            & (df["any-deviation-before"] == 0)
            & (df["any-deviation-after"] == 0)
            # Remove any syllables where the N+1 syllable does not also meet these criteria
            & (df["any-deviation-after"].shift(-1) == 0)
            # Remove syllables matched on the previous iteration
            & (df[f"comparison-{marker_type}"] != 1)
        ]
        logging.info(f"Size of candidate_df: {len(candidate_df)}")

        # Build a list of tuples of adjacent syllables
        potential_syllables = [
            (candidate_df.iloc[i], candidate_df.iloc[i + 1])
            for i in range(len(candidate_df) - 1)
            if candidate_df.iloc[i + 1].name == candidate_df.iloc[i].name + 1
        ]
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
            if (syll_a["word-before-period"] == row["word-before-period"])
            and (syll_a["word-after-period"] == row["word-after-period"])
            and (syll_a["word-before-comma"] == row["word-before-comma"])
            and (syll_a["word-after-comma"] == row["word-after-comma"])
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
                or (syll_a["last-syll-word"] == row["last-syll-word"])
            )
            and (
                not syll_a["word-after-period"]
                or (syll_a["first-syll-word"] == row["first-syll-word"])
            )
            and (
                not syll_a["word-before-comma"]
                or (syll_a["last-syll-word"] == row["last-syll-word"])
            )
            and (
                not syll_a["word-after-comma"]
                or (syll_a["first-syll-word"] == row["first-syll-word"])
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
        if idx >= len(df) - 1:
            potential_syllables = []
        else:
            # Save our next row data
            next_row: pd.Series = df.iloc[idx + 1]

            # Initial matches
            potential_syllables = [
                (syll_a, syll_b)
                for syll_a, syll_b in potential_syllables
                if (
                    (syll_b["word-before-period"] == next_row["word-before-period"])
                    and (syll_b["word-after-period"] == next_row["word-after-period"])
                    and (syll_b["word-before-comma"] == next_row["word-before-comma"])
                    and (syll_b["word-after-comma"] == next_row["word-after-comma"])
                )
            ]
            # Conditional matches
            potential_syllables = [
                (syll_a, syll_b)
                for syll_a, syll_b in potential_syllables
                if (
                    not syll_b["word-before-period"]
                    or (syll_b["last-syll-word"] == next_row["last-syll-word"])
                )
                and (
                    not syll_b["word-after-period"]
                    or (syll_b["first-syll-word"] == next_row["first-syll-word"])
                )
                and (
                    not syll_b["word-before-comma"]
                    or (syll_b["last-syll-word"] == next_row["last-syll-word"])
                )
                and (
                    not syll_b["word-after-comma"]
                    or (syll_b["first-syll-word"] == next_row["first-syll-word"])
                )
            ]
        logging.info(
            f"Size of potential_syllables after second filter: {len(potential_syllables)}"
        )
        if not potential_syllables:
            row[f"{marker_type}-matched"] = 0
            if idx > 0:
                logging.info(
                    "Previous syllable info:\t"
                    + ", ".join([f"{col}: {row[col]}" for col in row.index])
                )
            logging.info(
                "Syllable info:\t"
                + ", ".join([f"{col}: {row[col]}" for col in row.index])
            )
            if idx < len(df) - 1:
                logging.info(
                    "Next syllable info:\t"
                    + ", ".join(
                        [
                            f"{col}: {df.iloc[idx + 1][col]}"
                            for col in df.iloc[idx + 1].index
                        ]
                    )
                )
            continue

        # Compute the average word-freq for the target syllable
        #   and its subsequent (N+1) syllable
        target_syll_word_freq = get_word_freq(row["CleanedWord"], row["word-pos"])
        next_syll_word_freq = get_word_freq(
            df.iloc[idx + 1]["CleanedWord"], df.iloc[idx + 1]["word-pos"]
        )
        mean_actual_freq = 0.5 * (target_syll_word_freq + next_syll_word_freq)
        logging.info(f"Mean actual freq: {mean_actual_freq}")

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

        logging.info(f"Best freq diff: {best_freq_diff}")

        # Mark the target syllable as matched
        df.at[idx, f"{marker_type}-matched"] = 1

        # Mark the best-fit as matching
        df.at[best_freq_diff_idx, f"comparison-{marker_type}"] = 1

        # Indicate which error we've matched to
        df.at[
            best_freq_diff_idx, f"comparison-{extract_marker_type(marker_type)}-idx"
        ] = row[f"{extract_marker_type(marker_type)}-idx"]
        logging.info(
            f"Matched {row['syllable_id']} to {df.at[best_freq_diff_idx, 'syllable_id']}"
        )
