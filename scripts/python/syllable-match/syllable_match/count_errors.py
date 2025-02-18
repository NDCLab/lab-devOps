import os
import re
import string

import pandas as pd


RECONCILED_SUBS = {
    f"sub-{id}"
    for id in {
        3300001,
        3300002,
        3300003,
        3300004,
        3300006,
        3300008,
        3300009,
        3300014,
        3300015,
        3300016,
        3300017,
        3300018,
        3300019,
        3300024,
        3300026,
        3300027,
        3300030,
    }
}


def match_syllable_to_word(word_list, syllable_list) -> tuple[list[str], list[int]]:
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


def get_sheet_data(filepath: str):
    raw_df = get_raw_df(filepath)

    sheet_data = {}
    sheet_data["PassageName"] = re.fullmatch(
        r"sub-\d+_(.+?)_reconciled\.\w+", os.path.basename(filepath)
    ).group(1)
    sheet_data["SyllableCount"] = raw_df["SyllableID"].nunique()
    sheet_data["WordCount"] = raw_df["WordID"].nunique()

    for mistake_type in ["Error", "Disfluency"]:
        mistake_cols = raw_df.columns[raw_df.columns.str.startswith(f"{mistake_type}_")]
        for col in mistake_cols:
            has_error = raw_df[raw_df[col] != 0]
            raw_count = len(has_error.index)
            # multiple errors in the same word are counted as the same error
            word_error_count = has_error.groupby("WordID").size().count()
            assert raw_count >= word_error_count

            sheet_data[f"{col}_RawCount"] = raw_count
            sheet_data[f"{col}_WordErrorCount"] = word_error_count

    return sheet_data


def get_raw_df(filepath: str):
    df = pd.read_excel(filepath)
    cols = df.columns
    df.rename(columns={cols[0]: "Category", cols[1]: "Item"}, inplace=True)

    # Lists to hold each category’s items
    errors = []
    disfluencies = []
    outcomes = []
    syllables_involved = []

    # Flags for tracking which category we’re currently collecting
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

    raw_df = pd.DataFrame(raw_data)
    return raw_df


def process_subject_sheets(subject_dir: str):
    data_dirs = os.listdir(subject_dir)
    for sheet_dir in data_dirs:
        if not (
            os.path.isdir(os.path.join(subject_dir, sheet_dir))
            and sheet_dir.endswith("_reconciled")
        ):
            continue

        reconciled_dir = os.path.join(subject_dir, sheet_dir)
        for sheet in os.listdir(reconciled_dir):
            sheet_path = os.path.join(reconciled_dir, sheet)
            sheet_df = count_sheet_errors(sheet_path)

            if sheet_df is None:
                continue

            # saving logic here

        # collation logic here (return at this point)

    return None


def main():
    base_dir = "/home/nwelch/Documents/error-coding"
    print(base_dir)

    for subject in os.listdir(base_dir):
        if subject not in RECONCILED_SUBS:
            continue

        subject_dir = os.path.join(base_dir, subject)
        sub_df = process_subject_sheets(subject_dir)

        if sub_df is None:
            continue

        # saving logic here

    # collation logic here


if __name__ == "__main__":
    main()
