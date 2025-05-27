import os
import re
import string

import pandas as pd
from tqdm import tqdm


def get_sheet_data(filepath: str):
    raw_df = get_raw_df(filepath)

    sheet_data = {}
    sheet_data["PassageName"] = re.match(
        r"sub-\d+_(.+?)_reconciled.+", os.path.basename(filepath)
    ).group(1)
    sheet_data["SyllableCount"] = raw_df["SyllableID"].nunique()
    sheet_data["WordCount"] = raw_df["WordID"].nunique()
    sheet_data["InsertedSyllableWithoutWordErrorCount"] = len(
        raw_df[raw_df["InsertedSyllableWithoutWordError"] != 0].index
    )
    sheet_data["OmittedSyllableWithoutWordErrorCount"] = len(
        raw_df[raw_df["OmittedSyllableWithoutWordError"] != 0].index
    )
    sheet_data["WordSubstitutionCount"] = len(
        raw_df[raw_df["Outcome_WordSubstitution"] != 0].index
    )
    sheet_data["WordApproximationCount"] = len(
        raw_df[raw_df["Outcome_WordApproximation"] != 0].index
    )

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

            # count unattempted, successful, and unsuccessful corrections
            no_correction_attempt_count = len(has_error[has_error[col] == 1].index)
            unsuccessful_correction_count = len(has_error[has_error[col] == 2].index)
            successful_correction_count = len(has_error[has_error[col] == 3].index)
            sheet_data[f"{col}_NoCorrectionAttemptCount"] = no_correction_attempt_count
            sheet_data[f"{col}_UnsuccessfulCorrectionCount"] = (
                unsuccessful_correction_count
            )
            sheet_data[f"{col}_SuccessfulCorrectionCount"] = successful_correction_count

    return sheet_data


def process_subject_sheets(subject_dir: str):
    data_dirs = os.listdir(subject_dir)
    for sheet_dir in data_dirs:
        if not (
            os.path.isdir(os.path.join(subject_dir, sheet_dir))
            and sheet_dir.endswith("_reconciled")
        ):
            continue

        subject_data = []
        reconciled_dir = os.path.join(subject_dir, sheet_dir)
        sheets = [
            file
            for file in os.listdir(reconciled_dir)
            if os.path.splitext(file)[1] == ".xlsx"
        ]
        for sheet in tqdm(sheets, leave=False):
            sheet_path = os.path.join(reconciled_dir, sheet)
            sheet_data = get_sheet_data(sheet_path)
            subject_data.append(sheet_data)

        subject_df = pd.DataFrame(subject_data)
        return subject_df

    return None


def main():
    # output each DataFrame separately
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    for subject, df in sub_dfs.items():
        df.to_csv(os.path.join(data_dir, f"{subject}-passage-data.csv"), index=False)

    # make a "master sheet" with averages
    master_df = pd.concat(sub_dfs.values(), ignore_index=True)
    master_df = master_df.groupby("PassageName", as_index=False).mean(numeric_only=True)
    master_df.insert(0, "Statistic", "Mean")

    # compute overall mean and std across ALL passages and subjects
    df_combined = pd.concat(sub_dfs.values(), ignore_index=True)
    all_stats = df_combined.select_dtypes(include="number").agg(["mean", "std"])

    # create two new rows for overall mean and std
    row_mean = {"PassageName": "All", "Statistic": "Mean"}
    row_std = {"PassageName": "All", "Statistic": "Standard Deviation"}

    for col in all_stats.columns:
        row_mean[col] = all_stats.loc["mean", col]
        row_std[col] = all_stats.loc["std", col]

    # append new rows to the master DataFrame
    master_df = pd.concat(
        [master_df, pd.DataFrame([row_mean, row_std])], ignore_index=True
    )

    # save master DataFrame
    master_df.to_csv(os.path.join(data_dir, "master-statistics.csv"), index=False)


if __name__ == "__main__":
    main()
