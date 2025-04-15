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
        # Preprocess parsed .xlsx columns -> "tp" (target passage), "tp2", and "os" (original speech)
        rp_1_df = preprocess_rp1_df(rp_1_df)
        print(rp_1_df)

        # print(f"Recalled passage: [passage_name]")
        # print(f"Errors/disfluencies/total: X/Y/Z")
        # print(f"Errors/disfluencies/total per syllable: A/B/C")
        # print(f"Errors/disfluencies/total per word: D/E/F")

        # Processing for recall period 2


# Run as python __file__ /home/nwelch/Documents/error-coding/data/processed_passages /home/nwelch/Documents/prelims-read
if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        exit(1)

    processed_dir = sys.argv[1]
    recall_dir = sys.argv[2]
    main(processed_dir, recall_dir)
