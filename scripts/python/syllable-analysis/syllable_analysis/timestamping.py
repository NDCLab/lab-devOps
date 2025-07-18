import logging
import os

import pandas as pd


def extract_word_context(df: pd.DataFrame, word_id: int, n: int) -> list[str]:
    """Extracts the context words surrounding a target word in a DataFrame.
    Given a DataFrame containing words and their unique IDs, this function retrieves the words
    within a window of size `n` before and after the specified `word_id`, including the target word itself.

    Args:
        df (pd.DataFrame): DataFrame containing at least 'WordID' and 'word' columns.
        word_id (int): The unique identifier of the target word.
        n (int): The number of words to include before and after the target word.

    Raises:
        ValueError: If `n` is not greater than 0.
        ValueError: If `word_id` does not exist.

    Returns:
        list[str]: A list of words in the context window, including the target word.

    """
    if n <= 0:
        raise ValueError("n must be greater than 0")

    if word_id not in set(df["WordID"]):
        raise ValueError(f"Invalid word_id: {word_id}")

    # Generate a list of legal words surrounding (and including) the target word
    context = [
        str(df[df["WordID"] == wid]["word"].iloc[0])
        for wid in range(word_id - n, word_id + n + 1)
        if wid in set(df["WordID"])
    ]

    return context


def create_timestamping_sheets(processed_passages_dir: str, output_dir: str):
    timestamp_dir = os.path.join(output_dir, "timestamp")
    os.makedirs(timestamp_dir, exist_ok=True)

    for participant_id in os.listdir(processed_passages_dir):
        logging.info(f"Creating timestamp templates for {participant_id}")
        # Prepare output location
        sub_timestamp_dir = os.path.join(timestamp_dir, participant_id)
        os.makedirs(sub_timestamp_dir, exist_ok=True)

        sub_dir = os.path.join(processed_passages_dir, participant_id)
        for passage in os.listdir(sub_dir):
            if "all-cols" not in passage or "lock" in passage:
                continue
            logging.debug(f"Processing passage {passage}")
            passage_df = pd.read_csv(os.path.join(sub_dir, passage))

            timestamp_rows = []
            for _, row in passage_df.iterrows():
                row_data = {
                    "SyllableID": row["SyllableID"],
                    "Syllable": row["Syllable"],
                }

                # Figure out what kind of deviation (if any) this row has,
                # or if it has been matched as a comparison syllable.
                row_types = []
                # Deviation types
                if row["hesitation-disfluency"] == 1:
                    row_types.append("hesitation")
                elif row["high-error"] == 1 or row["low-error"] == 1:
                    row_types.append("error")
                # Comparison types
                elif row["comparison-hesitation-idx"] == 1:
                    row_types.append("comparison (hesitation)")
                elif (
                    row["comparison-high-error-idx"] == 1
                    or row["comparison-low-error-idx"] == 1
                ):
                    row_types.append("comparison (error)")
                else:
                    timestamp_rows.append(row_data)
                    logging.debug(
                        f"Syllable {row_data["SyllableID"]} is not deviation or comparison"
                    )
                    continue

                row_data["RowTypes"] = ", ".join(row_types)
                logging.debug(
                    f"Syllable {row_data["SyllableID"]} has types {row_data["RowTypes"]}"
                )
                # We will add one row per "type" (deviation/comparison),
                # so we mark duplicated rows as such.
                row_data["Duplicate"] = "X" if len(row_types) > 1 else ""

                # Mark for timestamping according to deviation type
                for row_type in row_types:
                    if "hesitation" in row_type:
                        # NB: For hesitations, we mark the coda (offset) of the "start" syllable and
                        # the attack (onset) of the "end" syllable (capturing the hesitation itself).
                        if row["hesitation-start"]:
                            row_data["MarkLocation"] = "offset"
                            timestamp_rows.append(row_data)
                        if row["hesitation-end"]:
                            row_data["MarkLocation"] = "onset"
                            timestamp_rows.append(row_data)

                    elif "error" in row_type:
                        # NB: For errors, we mark the attack of the "start" syllable
                        # and the coda of the "end" syllable. This may be the same syllable.
                        if row["high-error-start"] or row["low-error-start"]:
                            row_data["MarkLocation"] = "onset"
                            timestamp_rows.append(row_data)
                        if row["high-error-end"] or row["low-error-end"]:
                            row_data["MarkLocation"] = "offset"
                            timestamp_rows.append(row_data)

            timestamp_df = pd.DataFrame(timestamp_rows)
            timestamp_df["Timestamp"] = pd.Series()

            timestamp_df.to_csv(
                os.path.join(sub_timestamp_dir, passage.replace("_all-cols", "")),
                index=False,
            )
