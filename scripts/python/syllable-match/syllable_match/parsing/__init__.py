import re
import string

import pandas as pd


def get_raw_df(filepath: str):
    """
    Reads an Excel file and processes its content to create a raw DataFrame for further analysis.

    This function reads an Excel file specified by the `filepath` parameter, renames its columns to "Category" and "Item",
        and then iterates over each row to categorize and collect data based on specific conditions. It identifies and
        separates data into lists for errors, disfluencies, outcomes, and syllables involved in correction.
        The function also parses out passage words and syllables, matches each syllable with the corresponding word, and
        assigns sequential syllable IDs. Finally, it converts the collected data into a DataFrame, adds custom feature
        columns, and truncates value lists for feature columns to match the number of syllables.

    Parameters:
        filepath (str): The path to the Excel file to be processed.

    Returns:
        pd.DataFrame: A raw DataFrame containing the processed data with custom feature columns.
    """
    df = pd.read_excel(filepath)
    cols = df.columns
    df.rename(columns={cols[0]: "Category", cols[1]: "Item"}, inplace=True)

    # Lists to hold each category's items
    errors = []
    disfluencies = []
    outcomes = []
    syllables_involved = []

    # Flags for tracking which category we're currently collecting
    collecting_errors = False
    collecting_disfluencies = False
    collecting_outcomes = False
    collecting_syllables_involved = False

    for _, row in df.iterrows():
        # Convert both Category and Item to strings, then strip
        category = str(row["Category"]).strip()
        item = str(row["Item"]).strip()

        if category == "Types of Errors":
            # Switch to collecting Errors
            collecting_errors = True
            collecting_disfluencies = False
            collecting_outcomes = False
            collecting_syllables_involved = False

            if item:
                errors.append(item)

        elif category == "Types of Disfluencies":
            # Switch to collecting Disfluencies
            collecting_errors = False
            collecting_disfluencies = True
            collecting_outcomes = False
            collecting_syllables_involved = False

            if item:
                disfluencies.append(item)

        elif category == "Outcomes":
            # Switch to collecting Outcomes
            collecting_errors = False
            collecting_disfluencies = False
            collecting_outcomes = True
            collecting_syllables_involved = False

            if item:
                outcomes.append(item)

        elif category == "Syllables Involved in Correction":
            # Switch to collecting Syllables Involved in Correction
            collecting_errors = False
            collecting_disfluencies = False
            collecting_outcomes = False
            collecting_syllables_involved = True

            if item:
                syllables_involved.append(item)

        else:
            # Blank category cell → continue collecting under the current heading
            if collecting_errors and item:
                errors.append(item)
            elif collecting_disfluencies and item:
                disfluencies.append(item)
            elif collecting_outcomes and item:
                outcomes.append(item)
            elif collecting_syllables_involved and item:
                syllables_involved.append(item)

    other_cols = df.columns[~df.columns.isin({"Category", "Item"})]
    raw_data = {}

    for error_type in errors:
        err_row = df[df["Item"] == error_type].iloc[0][other_cols]
        colname = "Error_" + re.sub(r"[^\w]", "", error_type.title())
        raw_data[colname] = err_row.dropna().tolist()

    for disfluency_type in disfluencies:
        dis_row = df[df["Item"] == disfluency_type].iloc[0][other_cols]
        colname = "Disfluency_" + re.sub(r"[^\w]", "", disfluency_type.title())
        raw_data[colname] = dis_row.dropna().tolist()

    for outcome_type in outcomes:
        out_row = df[df["Item"] == outcome_type].iloc[0][other_cols]
        colname = "Outcome_" + re.sub(r"[^\w]", "", outcome_type.title())
        raw_data[colname] = out_row.dropna().tolist()

    for syll_info in syllables_involved:
        if "syllable" not in syll_info.lower():
            continue
        syll_row = df[df["Item"] == syll_info].iloc[0][other_cols]
        colname = "SyllInfo_" + re.sub(r"[^\w]", "", syll_info.title())
        raw_data[colname] = syll_row.dropna().tolist()

    # parse out passage words and syllables
    passage = " ".join(
        c for c in other_cols.dropna().tolist() if "unnamed:" not in c.lower()
    )
    passage = re.sub(r"\s+", " ", passage)
    passage = re.sub(r"(.+?)\.\d+", r"\1", passage)
    passage_words = passage.split()
    cleaned_passage_words = [
        word.lower().replace("-", "").strip(string.punctuation)
        for word in passage_words
    ]

    syll_row = df[df["Item"].astype(str).str.lower() == "target syllables"].iloc[0]
    passage_sylls = syll_row[other_cols].dropna().astype(str).str.strip().tolist()
    cleaned_passage_sylls = [
        str(syll).lower().replace("-", "").strip(string.punctuation)
        for syll in passage_sylls
    ]

    # Match up each syllable with the corresponding word
    raw_data["Syllable"] = passage_sylls
    raw_data["CleanedWord"], raw_data["WordID"] = match_syllable_to_word(
        cleaned_passage_words, cleaned_passage_sylls
    )
    raw_data["CleanedSyllable"] = cleaned_passage_sylls
    # assign sequential syllable IDs
    raw_data["SyllableID"] = list(range(len(cleaned_passage_sylls)))

    for col in raw_data.keys():
        if col in {"CleanedWord", "CleanedSyllable"}:
            continue
        # truncate value lists for feature columns to number of syllables
        raw_data[col] = raw_data[col][: len(cleaned_passage_sylls)]

    # Convert dict of iterables to DataFrame for easier manipulation
    raw_df = pd.DataFrame(raw_data)

    # Add custom feature columns
    raw_df["WordHasError"] = (
        raw_df["Error_InsertedWord"].astype(bool)
        | raw_df["Error_OmittedWord"].astype(bool)
        | raw_df["Error_WordStressError"].astype(bool)
        | raw_df["Disfluency_DuplicationRepetitionWord"].astype(bool)
    ).astype(int)

    raw_df["InsertedSyllableWithoutWordError"] = (
        raw_df["Error_InsertedSyllable"].astype(bool)
        & ~(raw_df["WordHasError"].astype(bool))
    ).astype(int)
    raw_df["OmittedSyllableWithoutWordError"] = (
        raw_df["Error_OmittedSyllable"].astype(bool)
        & ~(raw_df["WordHasError"].astype(bool))
    ).astype(int)

    return raw_df


def match_syllable_to_word(word_list, syllable_list) -> tuple[list[str], list[int]]:
    """
    This function matches syllables to words in a given list.

    Args:
        word_list (list): A list of words.
        syllable_list (list): A list of syllables.

    Returns:
        tuple: A tuple containing two lists. The first list contains the words that each syllable belongs to,
               and the second list contains the indices of these words in the original word list.
    """
    matching_words = []
    indices = []
    syllable_queue = syllable_list.copy()

    for word_index, word in enumerate(word_list):
        # Track how many characters of this word we've covered
        current_length = 0
        word_length = len(word)

        # Keep taking syllables until we've matched the entire word
        while current_length < word_length:
            # Take the next syllable from the queue
            syllable = syllable_queue.pop(0)
            current_length += len(syllable)

            # Assign that syllable to this word
            matching_words.append(word)
            indices.append(word_index)

        # At this point, current_length == word_length

    return matching_words, indices
