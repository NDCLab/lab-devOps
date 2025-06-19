import os
import re

import pandas as pd


def extract_word_context(df: pd.DataFrame, word_id: str, n: int) -> list[str]:
    """Extracts the context words surrounding a target word in a DataFrame.
    Given a DataFrame containing words and their unique IDs, this function retrieves the words
    within a window of size `n` before and after the specified `word_id`, including the target word
    itself. The function assumes that `word_id` follows the pattern 'prefix_number', and constructs
    the context window accordingly.

    Args:
        df (pd.DataFrame): DataFrame containing at least 'word_id' and 'word' columns.
        word_id (str): The unique identifier of the target word (e.g., 'cars_11g_word1').
        n (int): The number of words to include before and after the target word.

    Raises:
        ValueError: If `n` is not greater than 0.
        ValueError: If `word_id` does not match the expected pattern.

    Returns:
        list[str]: A list of words in the context window, including the target word.
        Only words present in the DataFrame are included.

    """
    if n <= 0:
        raise ValueError("n must be greater than 0")

    id_match = re.match(r"(\w+_\d+\w_word)(\d+)", word_id)
    if id_match is None:
        raise ValueError(f"Invalid word_id: {word_id}")

    id_prefix = str(id_match.group(1))
    word_idx = int(id_match.group(2))
    # Generate a list of word indices surrounding (and including) the target word
    local_words = [f"{id_prefix}{idx}" for idx in range(word_idx - n, word_idx + n + 1)]
    # Grab legal words
    context = [
        str(df.loc[lambda df: df["word_id"] == wid]["word"][0])
        for wid in local_words
        if wid in set(df["word_id"])
    ]

    return context


def create_timestamping_sheets(processed_passages_dir: str, output_dir: str):
    timestamp_dir = os.path.join(output_dir, "timestamp")
    os.makedirs(timestamp_dir)

    for participant_id in os.listdir(processed_passages_dir):
        # Prepare output location
        sub_timestamp_dir = os.path.join(timestamp_dir, participant_id)
        os.makedirs(sub_timestamp_dir)

        sub_dir = os.path.join(processed_passages_dir, participant_id)
        for passage in os.listdir(sub_dir):
            if "all-cols" not in passage:
                continue
            passage_df = pd.read_csv(os.path.join(sub_dir, passage))
            error_idxs = passage_df[passage_df["any_deviation"] == 1]["syllable_id"]

            timestamp_data = []
            for idx in error_idxs:
                syll_row = passage_df.loc[lambda df: df["syllable_id" == idx]][0]
                word_id = syll_row["word_id"]
                # Gather the base data for this syllable
                target_data = {
                    "syllable_id": idx,
                    "syllable": syll_row["cleaned_syllable"],
                    # Take two words before and after the target word
                    "context": " ".join(extract_word_context(passage_df, word_id, 2)),
                }

                # If we matched this syllable, record match data
                for err_type in ["hesitation", "high-error", "low-error"]:
                    match_col = f"comparison-{err_type}-idx"
                    match_idx = syll_row[match_col]
                    if pd.isna(match_idx):
                        continue
                    match_row = passage_df.loc[
                        lambda df: df["syllable_id" == match_idx]
                    ][0]
                    match_word_id = match_row["word_id"]
                    # Record the match data + the target syllable data
                    match_data = target_data.copy()
                    match_data.update(
                        {
                            "match_syllable_id": match_idx,
                            "match_syllable": match_row["cleaned_syllable"],
                            "match_context": " ".join(
                                extract_word_context(passage_df, match_word_id, 2)
                            ),
                        }
                    )
                    timestamp_data.append(match_data)

            timestamp_df = pd.DataFrame(timestamp_data)
            # Add new timestamp columns
            timestamp_df["timestamp_target"] = pd.Series()
            timestamp_df["timestamp_matched"] = pd.Series()

            timestamp_df.to_csv(
                os.path.join(sub_timestamp_dir, passage.replace("_all-cols", ""))
            )
