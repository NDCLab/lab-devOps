import os

import pandas as pd

from syllable_analysis.syllable_match.stats import get_sheet_stats


def summarize(processed_passages_dir: str, output_dir: str):
    # Calculate summary statistics for each participant
    all_stats = []
    for participant_id in os.listdir(processed_passages_dir):
        print(f"Processing participant {participant_id}")
        participant_stats = []
        for passage_name in os.listdir(os.path.join(processed_passages_dir, participant_id)):
            if not passage_name.endswith("_all-cols.csv"):
                continue

            df = pd.read_csv(os.path.join(processed_passages_dir, participant_id, passage_name))
            passage_stats = get_sheet_stats(
                df, os.path.splitext(passage_name)[0].removesuffix("_all-cols")
            )
            # Add passage counts / statistics as a dict in the participant stats list
            participant_stats.append(passage_stats)

        # Add participant stats to the master stats dataframe
        all_stats.extend(participant_stats)

        participant_dir = os.path.join(output_dir, "processed_passages", participant_id)
        os.makedirs(participant_dir)

        participant_stats_df = pd.DataFrame(participant_stats)
        participant_stats_df.to_csv(
            os.path.join(participant_dir, f"{participant_id}-passage-counts.csv"),
            index=False,
        )

    # Step 4: After processing all participants and passages, generate summary statistics
    per_passage_df = pd.DataFrame(all_stats)
    # Explicitly specify which columns to average
    numeric_cols = per_passage_df.select_dtypes(include=["int64", "float64"]).columns
    # Remove the PassageName column if it's in numeric_cols
    numeric_cols = numeric_cols[numeric_cols != "PassageName"]

    # Group by PassageName and calculate mean only for numeric columns, skipping NaN values
    per_passage_df = (
        per_passage_df.groupby("PassageName")[numeric_cols]
        .agg(lambda x: x.mean(skipna=True) if x.notna().any() else pd.NA)
        .reset_index()
    )
    per_passage_df.insert(0, "Statistic", "Mean")

    # Compute overall mean and standard deviation across ALL passages and subjects
    overall_df = pd.DataFrame(all_stats)

    # Calculate stats while handling NaN values
    overall_df = overall_df[numeric_cols].agg(
        {
            col: ["mean", "std"] if overall_df[col].notna().any() else [pd.NA, pd.NA]
            for col in numeric_cols
        }
    )

    # Create two new rows for overall mean and std
    row_mean = {"PassageName": "All", "Statistic": "Mean"}
    row_std = {"PassageName": "All", "Statistic": "Standard Deviation"}

    for col in overall_df.columns:
        row_mean[col] = overall_df.loc["mean", col]
        row_std[col] = overall_df.loc["std", col]

    # Append new rows to per-passage statistics to get master DataFrame
    master_df = pd.concat(
        [per_passage_df, pd.DataFrame([row_mean, row_std])], ignore_index=True
    )

    # Save master DataFrame
    master_df.to_csv(os.path.join(output_dir, "master-statistics.csv"), index=False)
