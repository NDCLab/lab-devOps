import logging
import os
import pandas as pd

def set_error_syllable(row_data, passage_df, idx, idx_col, matched_col):
    """
    Sets the target syllable information in the row_data dictionary based on the provided index and columns.
    If the index is NaN, a warning is logged and the function returns without modifying row_data.

    """
    if pd.isna(idx):
        logging.warning(f"Index is NaN for row {row_data['SyllableID']}, cannot set error syllable for idx_col {row_data['SyllableID']} and matched_col {matched_col}.")
        row_data["TargetSyllableID"] = pd.NA
        row_data["TargetSyllable"] = pd.NA
        return row_data

    error_row = passage_df[
        (passage_df[idx_col] == int(idx)) &
        (passage_df[matched_col] == 1)
    ]

    if len(error_row) == 1:
        row_data["TargetSyllableID"] = error_row["SyllableID"].iloc[0]
        row_data["TargetSyllable"] = error_row["Syllable"].iloc[0]
    else:
        logging.warning(f"For index {idx}, found {len(error_row)} for matched syllable {row_data['SyllableID']} ({row_data['Syllable']}) and matched_col {matched_col}. Cannot set TargetSyllableID. ")
    return row_data

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
    ERROR_TYPE_COLUMNS = {
    "Error_Misproduction": "Misproduction",
    "Error_InsertedSyllable": "Insertion",
    "Error_OmittedSyllable": "Omission",
    "Error_InsertedWord": "Inserted Word",
    "Error_OmittedWord": "Omitted Word",
    "Error_WordStressError": "Word Stress Error",
    }

    comparison_types = {
        "hesitation": {"start": "offset", "end": "onset"},
        "high-error": {"start": "onset", "end": "offset"},
        "low-error": {"start": "onset", "end": "offset"},
    }

    for participant_id in os.listdir(processed_passages_dir):
        logging.info(f"Creating timestamp templates for {participant_id} for timestamping")
        # Prepare output location
        sub_timestamp_dir = os.path.join(timestamp_dir, participant_id)
        os.makedirs(sub_timestamp_dir, exist_ok=True)

        sub_dir = os.path.join(processed_passages_dir, participant_id)
        for passage in os.listdir(sub_dir):
            if "all-cols" not in passage or "lock" in passage:
                continue
            logging.debug(f"Processing passage {passage} for {participant_id} for timestamping")
            passage_df = pd.read_csv(os.path.join(sub_dir, passage))

            timestamp_rows = []
            for _, row in passage_df.iterrows():
                #print(f"Processing row: {row['SyllableID']}, {row['Syllable']}")
                row_data = {
                    "SyllableID": row["SyllableID"],
                    "Syllable": row["Syllable"],
                }

                # Figure out what kind of deviation (if any) this row has,
                # or if it has been matched as a comparison syllable.
                row_types = []
                row_data["ErrorType"] = ""
                # Deviation types
                if row["hesitation-start"] == 1 or row["hesitation-end"] == 1:
                    row_types.append("hesitation")
                # generate whether it is high error or low-error
                if row["any-error"] == 1:
                    if row["high-error"] == 1:
                        row_types.append("high-error")
                    elif row["low-error"] == 1:
                        row_types.append("low-error")
                # Comparison types
                if not pd.isna(row["comparison-hesitation-idx"]):
                    row_types.append("comparison (hesitation)")
                if pd.notna(row["comparison-high-error-idx"]):
                    row_types.append("comparison (high-error)")
                if pd.notna(row["comparison-low-error-idx"]):
                    row_types.append("comparison (low-error)")
                # No deviation or comparison; just a correctly produced syllable
                if not row_types:
                    timestamp_rows.append(row_data.copy())
                    #logging.debug( f"Syllable {row_data['SyllableID']} is not deviation or comparison")
                    continue

                #row_data["RowTypes"] = ", ".join(row_types)
                #logging.debug(f"Syllable {row_data['SyllableID']} has types {row_data['RowTypes']}")
                # Mark for timestamping according to deviation type
                for row_type in row_types:
                    #logging.debug(f"Processing syllable {row_data['SyllableID']} with types {row_type} and has {row_types}")
                    row_data["RowTypes"] = row_type
                    row_data["TargetSyllableID"] = pd.NA
                    row_data["TargetSyllable"] = pd.NA
                    row_data["ErrorType"] = ""

                    if "hesitation" in row_type:
                        # NB: For hesitations, we mark the coda (offset) of the "start" syllable and
                        # the attack (onset) of the "end" syllable (capturing the hesitation itself).
                        if row["hesitation-start"] == 1:
                            row_data["MarkLocation"] = "offset"
                            timestamp_rows.append(row_data.copy())
                        if row["hesitation-end"] == 1:
                            row_data["MarkLocation"] = "onset"
                            timestamp_rows.append(row_data.copy())

                    elif "error" in row_type:
                        # NB: For errors, we mark the attack of the "start" syllable
                        # and the coda of the "end" syllable. This may be the same syllable.
                        error_types = [
                            label
                            for column, label in ERROR_TYPE_COLUMNS.items()
                            if row[column] != 0
                        ]

                        row_data["ErrorType"] = ", ".join(error_types)


                        if row["high-error-start"] == 1 or row["low-error-start"] == 1:
                            row_data["MarkLocation"] = "onset"
                            timestamp_rows.append(row_data.copy())
                        if row["high-error-end"] == 1 or row["low-error-end"] == 1:
                            row_data["MarkLocation"] = "offset"
                            timestamp_rows.append(row_data.copy())

                    if "comparison" in row_type:
                        for match_type, mark_locations in comparison_types.items():
                            if match_type not in row_type:
                                continue
                            idx = row[f"comparison-{match_type}-idx"]
                            for pair, mark_location in mark_locations.items():
                                if row[f"comparison-{match_type}-{pair}"] != 1:
                                    continue

                                row_data = set_error_syllable(row_data,passage_df,idx,f"{match_type}-idx",f"{match_type}-{pair}-matched",)
                                row_data["MarkLocation"] = mark_location
                                timestamp_rows.append(row_data.copy())




            timestamp_df = pd.DataFrame(timestamp_rows)
            # We will add one row per "type" (deviation/comparison),
            # so we mark duplicated rows as such.
            timestamp_df["Duplicate"] = timestamp_df.apply(
                lambda row: "X"
                if timestamp_df["SyllableID"].value_counts()[row["SyllableID"]] > 1
                else "",
                axis=1,
            )
            timestamp_df["Timestamp"] = pd.Series()

            timestamp_df.to_csv(
                os.path.join(sub_timestamp_dir, passage.replace("_all-cols", "")),
                index=False,
            )
