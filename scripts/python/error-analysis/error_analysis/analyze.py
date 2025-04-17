import os
import re
import sys

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


def main(processed_dir: str, recall_dir: str):
    recall_subs = os.listdir(recall_dir)

    rp1_data = []

    for sub in recall_subs:
        recall_sub_dir = os.path.join(recall_dir, sub)
        sub_files = os.listdir(recall_sub_dir)
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

        # Get the subject's data dir
        sub_data_dir = os.path.join(processed_dir, sub)
        if not os.path.isdir(sub_data_dir):
            print(f"Could not find processed data for {sub}, skipping")
            continue

        print(f"Participant: {sub}")
        hline = "-" * 50
        # Get all subject files
        all_sub_passages = [f for f in os.listdir(sub_data_dir) if "all-cols" not in f]
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

    all_rp1_df = pd.DataFrame(rp1_data)
    all_rp1_df.to_csv("rp1_data.csv", index=False)
    print("Saved tabular data for RP 1!")


# Run as python __file__ /home/nwelch/Documents/error-coding/data/processed_passages /home/nwelch/Documents/prelims-read
if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        exit(1)

    processed_dir = sys.argv[1]
    recall_dir = sys.argv[2]
    main(processed_dir, recall_dir)
