import os
import re
import sys

import numpy as np
import pandas as pd


def usage():
    print(f"Usage: python {__file__} processed-data-dir recall-data-dir")


def preprocess_rp1_df(df: pd.DataFrame):
    df = df.copy()
    new_cols = {}
    # Lowercase, strip, and normalize spaces for all columns
    for col in df.columns:
        cleaned_col = re.sub(r"\s+", " ", col.lower()).strip()
        if "target passage 2" in cleaned_col:
            new_cols[col] = "tp2"
        elif "target passage" in cleaned_col:
            new_cols[col] = "tp"
        elif "original speech" in cleaned_col:
            new_cols[col] = "os"
        else:
            raise ValueError("Unexpected column name", col)
    df.rename(columns=new_cols, inplace=True)
    return df


def find_all(main_str: str, sub_str: str):
    """
    Returns the indices of the "start points" of all occurrences
    of the substring in the main string.
    """
    start_idx = 0
    while True:
        start_idx = main_str.find(sub_str, start_idx)
        if start_idx == -1:  # no match found
            return
        yield start_idx
        start_idx += len(sub_str)


def extract_passage_name(passage_path: str) -> str:
    """
    Extracts the passage name from the path.
    """
    import re

    base_name = os.path.basename(passage_path)
    match = re.fullmatch(
        r"sub-\d+_([a-zA-Z]+_\d+[a-zA-Z]+).*reconciled.*\.xlsx", base_name
    )
    return match.group(1) if match else ""


def main(processed_dir: str, recall_dir: str):
    recall_subs = os.listdir(recall_dir)

    rp1_data = []
    rp2_data = []

    for sub in recall_subs:
        print(f"Participant: {sub}")
        # Save some useful variables
        hline = "-" * 50
        recall_sub_dir = os.path.join(recall_dir, sub)
        sub_files = os.listdir(recall_sub_dir)
        # Get the subject's data dir
        sub_data_dir = os.path.join(processed_dir, sub)
        if not os.path.isdir(sub_data_dir):
            print(f"Could not find processed data for {sub}, skipping")
            continue
        # Get all subject files
        all_sub_passages = [f for f in os.listdir(sub_data_dir) if "all-cols" in f]

        # Processing for recall period 1
        try:
            pat = re.compile(re.escape(sub) + r"_recallperiod1excel.*\.xlsx")
            rp_1_file = [f for f in sub_files if pat.fullmatch(f)][0]
        except IndexError:
            print(f"Could not find recall period 1 Excel file for {sub}, skipping")
            continue
        rp_1_df = pd.read_excel(os.path.join(recall_sub_dir, rp_1_file))
        # Preprocess parsed .xlsx columns
        # -> "tp" (target passage), "tp2" (may be NaN), and "os" (original speech)
        rp_1_df = preprocess_rp1_df(rp_1_df)
        rp_1_df.map(lambda x: x.strip() if pd.notnull(x) else "")
        # Drop rows where TP is NaN (repeats)
        rp_1_df = rp_1_df[~rp_1_df["tp"].isna()]

        all_recalled = tuple()
        for _, row in rp_1_df.iterrows():
            if "hammer" in row["tp"]:  # sample passage
                continue
            print(hline)
            print(f"Original speech: {row["os"]}")
            recalled_passages = tuple(
                str(passage).lower().replace("gen_", "")
                for passage in [row["tp"], row["tp2"]]
                if pd.notnull(passage)  # if tp2=NaN, skip it
            )
            # Get the relevant processed file(s) for the matched passage(s)
            if any(f.startswith(recalled_passages) for f in all_sub_passages):
                all_recalled += recalled_passages
            else:
                print(
                    f"Could not find any passages matching {", ".join(recalled_passages)} "
                    + f"for {sub} "
                    + f"(OS {row['os']}, TP {row['tp']}, TP2 {row['tp2']})"
                    + ", skipping"
                )
                continue

        # For each of the participant's passages, get:
        # - Total number of errors
        # - Total number of disfluencies
        # - Total number of syllables
        # - Total number of words
        # Report this information next to participant info and note
        #   whether they recalled the passage.
        for filename in all_sub_passages:
            path = os.path.join(sub_data_dir, filename)
            match_df = pd.read_csv(path)
            passage_name = os.path.splitext(os.path.basename(path))[0]
            print(
                f"Passage: {passage_name}" + " (recalled)"
                if passage_name.startswith(all_recalled)
                else ""
            )
            # Get general stats
            err_count = match_df["any-error"].sum()
            dis_count = match_df["any-disfluency"].sum()
            syll_count = len(match_df.index)
            word_count = match_df["first-syll-word"].sum()
            print(f"Errors/disfluencies: {err_count}/{dis_count}")
            # Calculate per-syllable error/disfluency rates
            err_per_syll = err_count / max(syll_count, 1)
            dis_per_syll = dis_count / max(syll_count, 1)
            print(
                f"Errors/disfluencies per syllable: {err_per_syll:.3f}/{dis_per_syll:.3f}"
            )
            # Calculate per-word error/disfluency rates
            err_per_word = err_count / max(word_count, 1)
            dis_per_word = dis_count / max(word_count, 1)
            print(
                f"Errors/disfluencies per word: {err_per_word:.3f}/{dis_per_word:.3f}"
            )
            rp1_data.append(
                {
                    "participant": sub,
                    "passageName": passage_name,
                    "recalled": 1 if passage_name.startswith(all_recalled) else 0,
                    "errorCount": int(err_count),
                    "disfluencyCount": int(dis_count),
                    "errorsPerSyllable": err_per_syll,
                    "disfluenciesPerSyllable": dis_per_syll,
                    "errorsPerWord": err_per_word,
                    "disfluenciesPerWord": dis_per_word,
                }
            )

        # Processing for recall period 2
        try:
            pat = re.compile(re.escape(sub) + r"_recallperiod2.*\.txt")
            rp_1_file = [f for f in sub_files if pat.fullmatch(f)][0]
        except IndexError:
            print(f"Could not find recall period 2 text file for {sub}, skipping")
            continue
        with open(os.path.join(recall_sub_dir, rp_1_file), "r") as f:
            recalled_phrases = f.readlines()

        # Clean up recalled phrases a bit
        recalled_phrases = [
            re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z ']", "", r.lower())).strip()
            for r in recalled_phrases
        ]
        # Save only unique and non-empty phrases
        recalled_phrases = list(set(rp for rp in recalled_phrases if rp))

        # Figure out which passage(s), if any, contain each phrase
        phrase_recall_info = []
        for phrase in recalled_phrases:
            phrase_dict = {"phrase": phrase, "occurrences": {}}
            for filename in all_sub_passages:
                path = os.path.join(sub_data_dir, filename)
                passage_df = pd.read_csv(path)
                # Order by syllable ID, keep only unique word IDs, extract words
                passage_df = passage_df.sort_values(by=["SyllableID"]).drop_duplicates(
                    subset="WordID", keep="first"
                )
                # Pull out some summary stats from the coded passage (will help later)
                passage_summary_stats = {}
                for dev_col in ["any-disfluency", "correction-syll", "any-error"]:
                    passage_summary_stats[f"passage_raw_{dev_col}_count"] = len(
                        passage_df[passage_df[dev_col] != 0].index
                    )
                    passage_summary_stats[f"passage_perWord_{dev_col}_count"] = (
                        len(passage_df[passage_df[dev_col] != 0].index)
                        / passage_df["WordID"].nunique()
                    )
                    passage_summary_stats[f"passage_perSyllable_{dev_col}_count"] = (
                        len(passage_df[passage_df[dev_col] != 0].index)
                        / passage_df["SyllableID"].nunique()
                    )
                # Also pull out the highest syllable ID possible
                max_syll_id = passage_df["SyllableID"].astype(int).max()
                # Apply the same cleaning to the passage text
                cleaned_words = (
                    passage_df["CleanedWord"]
                    .dropna()
                    .str.lower()
                    .str.replace(r"[^a-zA-Z ']", "", regex=True)
                    .str.replace(r"\s+", " ", regex=True)
                    .str.strip()
                    .replace("", np.nan)
                    .dropna()
                )
                passage_text = " ".join(cleaned_words)
                # Find all matches of the phrase in the text and save them
                start_indices = list(find_all(passage_text, phrase))
                # Use the start index to reverse-engineer the start & end points
                # (word index) of each occurrence, then extract data.
                # For our purposes, this is:
                #   - Number of disfluencies/corrections/errors (deviations) within the phrase (raw, per-word, and per-syllable)
                #   - Num. of deviations within 5 syllables of the phrase (before & after) (raw, per-word, and per-syllable)
                #   - Num. of deviations in the passage that the phrase appears in
                #   - Num. of times the phrase appears in this passage & all passages
                n_occurrences = len(start_indices)
                for start_idx in start_indices:
                    # Pull in passage-wide stats that we calculated earlier
                    occurrence_info = passage_summary_stats
                    occurrence_info = {
                        "phrase": phrase,
                        "file": filename,
                        "phrase_passage_count": n_occurrences,
                    }
                    # Calculate start word index by counting the number of spaces
                    # in the substring up to (but not including) the start index
                    # TODO: Fix this, currently prone to off-by-one errors (not acceptable in our case)
                    start_word_idx = passage_text.count(" ", 0, start_idx)
                    # Calculate end word index by adding the number of spaces in
                    # the phrase to be found to the start word index
                    end_word_idx = start_word_idx + phrase.count(" ")

                    # Get the index of the first and last sylllables in our phrase
                    first_syll_idx = passage_df[
                        passage_df["WordID"] == start_word_idx
                    ].iloc[0]["SyllableID"]
                    last_syll_idx = passage_df[
                        passage_df["WordID"] == end_word_idx
                    ].iloc[-1]["SyllableID"]

                    # Get number of deviations in the phrase
                    phrase_entries = passage_df[
                        passage_df["SyllableID"].between(first_syll_idx, last_syll_idx)
                    ]
                    for dev_type in ["disfluency", "correction", "error"]:
                        # Raw
                        # Per-word
                        # Per-syllable
                        pass
                    # Get number of deviations within 5 syllables of phrase
                    five_syll_entries = passage_df[
                        passage_df["SyllableID"].between(
                            max(0, first_syll_idx - 5),
                            min(last_syll_idx + 5, max_syll_id),
                        )
                    ]
                    for dev_type in ["disfluency", "correction", "error"]:
                        # Raw
                        # Per-word
                        # Per-syllable
                        pass
                    # Save occurrence_info to our running list
                    rp2_data.append(occurrence_info)

            phrase_recall_info.append(phrase_dict)

    all_rp1_df = pd.DataFrame(rp1_data)
    all_rp1_df.to_csv("rp1_data.csv", index=False)
    print("Saved tabular data for RP 1!")

    all_rp2_df = pd.DataFrame(rp2_data)
    all_rp2_df.to_csv("rp2_data.csv", index=False)
    print("Saved tabular data for RP 2!")


# Run as python __file__ /home/nwelch/Documents/error-coding/data/processed_passages /home/nwelch/Documents/prelims-read
if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        exit(1)

    processed_dir = sys.argv[1]
    recall_dir = sys.argv[2]
    main(processed_dir, recall_dir)
