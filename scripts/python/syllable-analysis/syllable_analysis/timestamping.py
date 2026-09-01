import logging
import os
import pandas as pd

# Subtype labels
ERROR_TYPE_COLUMNS = {
    "Error_Misproduction": "Misproduction",
    "Error_InsertedSyllable": "Inserted Syllable",
    "Error_OmittedSyllable": "Omitted Syllable",
    "Error_InsertedWord": "Inserted Word",
    "Error_OmittedWord": "Omitted Word",
    "Error_WordStressError": "Word Stress Error",
}

def get_error_subtype(row, error_type_columns=ERROR_TYPE_COLUMNS):
    """Build the SubType string for a syllable from its Error_* flags.

    When both the syllable-level and word-level flags are set for the same
    category (insertion or omission), only the word-level label is kept
    """
    subtypes = []
    for column, label in error_type_columns.items():
        if row.get(column, 0) != 0:
            # Suppress syllable-level when word-level is also present
            if column == "Error_InsertedSyllable" and row.get("Error_InsertedWord", 0) != 0:
                continue
            if column == "Error_OmittedSyllable" and row.get("Error_OmittedWord", 0) != 0:
                continue
            subtypes.append(label)
    return ", ".join(subtypes)


def get_matched_error_subtype(
    passage_df, idx, level, pair, error_type_columns=ERROR_TYPE_COLUMNS
):
    """Look up the SubType of the error a comparison syllable is matched to.

    For a comparison syllable matched to error *idx* at the given *level*
    ("high-error" or "low-error") and boundary *pair* ("start" or "end"),
    find the actual error syllable in *passage_df* and compute its SubType
    from the Error_* columns — exactly the same logic used for deviation
    rows.
    """
    if pd.isna(idx):
        return ""

    idx_col = f"{level}-idx"
    flag_col = f"{level}-{pair}"  # e.g. "low-error-start"

    error_rows = passage_df[
        (passage_df[idx_col] == int(idx)) & (passage_df[flag_col] == 1)
    ]

    if len(error_rows) >= 1:
        return get_error_subtype(error_rows.iloc[0], error_type_columns)

    return ""


def extract_word_context(df: pd.DataFrame, word_id: int, n: int) -> list[str]:
    """Extracts the context words surrounding a target word in a DataFrame.

    Given a DataFrame containing words and their unique IDs, this function
    retrieves the words within a window of size *n* before and after the
    specified *word_id*, including the target word itself.

    Args:
        df: DataFrame containing at least 'WordID' and 'word' columns.
        word_id: The unique identifier of the target word.
        n: The number of words to include before and after the target word.

    Raises:
        ValueError: If *n* is not greater than 0.
        ValueError: If *word_id* does not exist in *df*.

    Returns:
        A list of words in the context window, including the target word.
    """
    if n <= 0:
        raise ValueError("n must be greater than 0")

    if word_id not in set(df["WordID"]):
        raise ValueError(f"Invalid word_id: {word_id}")

    context = [
        str(df[df["WordID"] == wid]["word"].iloc[0])
        for wid in range(word_id - n, word_id + n + 1)
        if wid in set(df["WordID"])
    ]

    return context

# order
COLUMN_ORDER = [
    "SyllableID",
    "Syllable",
    "Type",
    "SubType",
    "Index",
    "StartEnd",
    "Deviation",
    "Duplicate",
    "Timestamp",
]


def create_timestamping_sheets(processed_passages_dir: str, output_dir: str):
    timestamp_dir = os.path.join(output_dir, "timestamp")
    os.makedirs(timestamp_dir, exist_ok=True)

    comparison_types = {"hesitation", "high-error", "low-error"}
    start_end = ["start", "end"]

    for participant_id in os.listdir(processed_passages_dir):
        logging.debug(f"Creating timestamp templates for {participant_id} for timestamping")
        sub_timestamp_dir = os.path.join(timestamp_dir, participant_id)
        os.makedirs(sub_timestamp_dir, exist_ok=True)

        sub_dir = os.path.join(processed_passages_dir, participant_id)
        for passage in os.listdir(sub_dir):
            if "all-cols" not in passage or "lock" in passage:
                continue
            logging.debug(f"Processing passage {passage} for {participant_id} for timestamping")
            passage_df = pd.read_csv(os.path.join(sub_dir, passage))

            # Need to identify which sylls are matched.
            # hesitations if matched by definition have the start and end matched
            # but errors may be partially matched (e.g. only start or end)
            matched_idxs = {}
            for level in ("high-error", "low-error"):
                matched = set()
                for boundary in ("start", "end"):
                    col = f"{level}-{boundary}-matched"
                    idx_col = f"{level}-idx"
                    if col in passage_df.columns:
                        matched |= set(
                            passage_df.loc[passage_df[col] == 1, idx_col]
                            .dropna()
                            .astype(int)
                        )
                matched_idxs[level] = matched

            hes_col = "hesitation-start-matched"
            hes_idx_col = "hesitation-idx"
            if hes_col in passage_df.columns:
                matched_idxs["hesitation"] = set(
                    passage_df.loc[passage_df[hes_col] == 1, hes_idx_col]
                    .dropna()
                    .astype(int)
                )
            else:
                matched_idxs["hesitation"] = set()

            # Build rows
            timestamp_rows = []
            for _, row in passage_df.iterrows():
                row_data = {
                    "SyllableID": row["SyllableID"],
                    "Syllable": row["Syllable"],
                }

                row_types = []

                if row.get("hesitation-start") == 1 or row.get("hesitation-end") == 1:
                    row_types.append("hesitation")
                if row.get("any-error") == 1:
                    if row.get("high-error") == 1:
                        row_types.append("high-error")
                    elif row.get("low-error") == 1:
                        row_types.append("low-error")

                if pd.notna(row.get("comparison-hesitation-idx")):
                    row_types.append("comparison (hesitation)")
                if pd.notna(row.get("comparison-high-error-idx")):
                    row_types.append("comparison (high-error)")
                if pd.notna(row.get("comparison-low-error-idx")):
                    row_types.append("comparison (low-error)")

                # no deviation, no comparison
                if not row_types:
                    timestamp_rows.append(row_data.copy())
                    continue

                # rows for each type on this syllable
                rows_before = len(timestamp_rows)
                for row_type in row_types:
                    # Reset per-type fields
                    row_data["Type"] = ""
                    row_data["SubType"] = ""
                    row_data["Index"] = pd.NA
                    row_data["StartEnd"] = pd.NA
                    row_data["Deviation"] = 0

                    # Deviation rows (Error Hes / Deviation = 1)
                    if "comparison" not in row_type:
                        row_data["Deviation"] = 1

                        if row_type == "hesitation":
                            hes_idx = row.get("hesitation-idx", pd.NA)

                            if pd.isna(hes_idx) or int(hes_idx) not in matched_idxs.get("hesitation", set()):
                                continue

                            row_data["Type"] = "hesitation"
                            row_data["Index"] = hes_idx
                            if row.get("hesitation-start") == 1:
                                row_data["StartEnd"] = 1
                                timestamp_rows.append(row_data.copy())
                            if row.get("hesitation-end") == 1:
                                row_data["StartEnd"] = 2
                                timestamp_rows.append(row_data.copy())

                        elif row_type in ("high-error", "low-error"):
                            error_idx = row.get(f"{row_type}-idx")

                            if pd.isna(error_idx) or int(error_idx) not in matched_idxs.get(row_type, set()):
                                continue

                            row_data["Type"] = row_type
                            row_data["Index"] = error_idx
                            row_data["SubType"] = get_error_subtype(
                                row, ERROR_TYPE_COLUMNS
                            )

                            if row.get(f"{row_type}-start") == 1:
                                row_data["StartEnd"] = 1
                                timestamp_rows.append(row_data.copy())
                            if row.get(f"{row_type}-end") == 1:
                                row_data["StartEnd"] = 2
                                timestamp_rows.append(row_data.copy())

                    # Comaprsion rows (Deviation = 0)
                    else:
                        row_data["Deviation"] = 0

                        for match_type in comparison_types:
                            if match_type not in row_type:
                                continue

                            idx = row.get(f"comparison-{match_type}-idx")

                            if pd.isna(idx) or int(idx) not in matched_idxs.get(match_type, set()):
                                continue

                            row_data["Type"] = match_type
                            row_data["Index"] = idx

                            for pair in start_end:
                                if row.get(f"comparison-{match_type}-{pair}") != 1:
                                    continue

                                row_data["StartEnd"] = 1 if pair == "start" else 2

                                if match_type in ("high-error", "low-error"):
                                    row_data["SubType"] = get_matched_error_subtype(
                                        passage_df,
                                        idx,
                                        match_type,
                                        pair,
                                        ERROR_TYPE_COLUMNS,
                                    )
                                else:
                                    row_data["SubType"] = ""

                                timestamp_rows.append(row_data.copy())
                if len(timestamp_rows) == rows_before:
                    timestamp_rows.append({
                        "SyllableID": row["SyllableID"],
                        "Syllable": row["Syllable"],
                })
            timestamp_df = pd.DataFrame(timestamp_rows)

            timestamp_df["Duplicate"] = timestamp_df.apply(
                lambda r: (
                    "X"
                    if timestamp_df["SyllableID"].value_counts()[r["SyllableID"]] > 1
                    else ""
                ),
                axis=1,
            )

            timestamp_df["Timestamp"] = pd.Series()
            final_cols = [c for c in COLUMN_ORDER if c in timestamp_df.columns]
            timestamp_df = timestamp_df[final_cols]
            timestamp_df.to_csv(
                os.path.join(
                    sub_timestamp_dir, passage.replace("_all-cols", "")
                ),
                index=False,
            )
