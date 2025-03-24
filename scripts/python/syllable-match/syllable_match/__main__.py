import argparse
import os
from collections import defaultdict

import pandas as pd
from pydantic_settings import BaseSettings
from tqdm import tqdm

from syllable_match.feature_extractors import (
    SyllableAtPassageBeginningExtractor,
    SyllableAtPassageEndExtractor,
    SyllableEndsWordExtractor,
    SyllableStartsWordExtractor,
    WordAfterCommaExtractor,
    WordAfterPeriodExtractor,
    WordBeforeCommaExtractor,
    WordBeforePeriodExtractor,
    WordFrequencyExtractor,
    WordPOSExtractor,
)
from syllable_match.labels import label_duplications, label_errors, label_hesitations
from syllable_match.matching import match_duplications, match_errors, match_hesitations
from syllable_match.models import FeatureExtractor
from syllable_match.parsing import get_raw_df, preprocess_fields
from syllable_match.scaffolds import create_scaffolds
from syllable_match.stats import get_sheet_stats, summarize_word_matches
from syllable_match.utils import (
    create_output_directory,
    extract_passage_name,
    get_participants,
    get_passages,
    get_templates,
    load_scaffold,
)


def get_args():
    parser = argparse.ArgumentParser(
        description="Process subject data with various operations."
    )

    parser.add_argument(
        "input_dir", type=str, help="The input directory containing data."
    )
    parser.add_argument("output_dir", type=str, help="The directory to output results.")

    # Add accepted_subjects as an optional argument
    parser.add_argument(
        "--accepted_subjects",
        nargs="*",  # Allows multiple values
        default=[],  # Default to an empty list if not provided
        help=(
            "List of accepted subjects in 'sub-ID' format. If not provided as a "
            "command line option, the script will look in the config file. If absent "
            "there, all subjects are accepted."
        ),
    )

    # Add --force flag
    parser.add_argument(
        "--force",
        action="store_true",
        help="If set, empties the output directory if it already exists.",
    )

    return parser.parse_args()


class Config(BaseSettings):
    default_fields: list[str]
    accepted_subjects: list[str] = []


def load_config(config_path: str) -> Config:
    config = Config.model_validate_json(open(config_path).read())
    return config


def get_scaffold_extractors() -> list[FeatureExtractor]:
    """
    Returns a list of FeatureExtractor instances to be used for scaffold creation.

    These extractors are responsible for analyzing various aspects of syllables
    and words, such as their positions, punctuation, and frequency, to facilitate
    the construction of detailed scaffolds.

    Note:
        This is meant to be configured according to desired default values in the scaffold
        that are independent of a participant's reading of a given passage.

    Returns:
        list[FeatureExtractor]: A list of initialized FeatureExtractor instances.
    """
    return [
        SyllableAtPassageBeginningExtractor(),
        SyllableAtPassageEndExtractor(),
        SyllableStartsWordExtractor(),
        SyllableEndsWordExtractor(),
        WordBeforePeriodExtractor(),
        WordAfterPeriodExtractor(),
        WordBeforeCommaExtractor(),
        WordAfterCommaExtractor(),
        WordFrequencyExtractor(),
        WordPOSExtractor(),
    ]


def main():
    args = get_args()
    config = load_config(os.path.join(args.input_dir, "config.json"))

    # Step 0: Start with an empty output_dir
    print("Step 0: Checking output directory...")
    if os.path.exists(args.output_dir):
        if args.force:
            print("Output directory exists. Emptying the directory...")
            # Empty the output directory
            for root, dirs, files in os.walk(args.output_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        else:
            raise FileExistsError(
                f"The output directory '{args.output_dir}' already exists."
            )
    else:
        print("Output directory does not exist. Creating directory...")
        os.makedirs(args.output_dir)

    # Step 1: Construct basic scaffolds for each passage template
    print("Step 1: Constructing basic scaffolds...")
    template_dir = os.path.join(args.input_dir, "templates")
    if not os.path.exists(template_dir):
        raise FileNotFoundError(
            f"The templates directory '{template_dir}' does not exist."
        )
    scaffold_dir = create_output_directory(args.output_dir, "scaffolds")
    create_scaffolds(
        get_templates(template_dir), scaffold_dir, get_scaffold_extractors()
    )

    summarize_word_matches(
        scaffold_dir, os.path.join(args.output_dir, "word_matching_statistics.txt")
    )

    # Dictionary to store scaffold dataframes for each participant
    # Format: {participant_id: {passage_name: dataframe}}
    sub_dfs = defaultdict(dict)

    # Step 2: Loop over each participant
    print("Step 2: Processing participants...")
    for participant_dir in tqdm(
        get_participants(
            args.input_dir, args.accepted_subjects or config.accepted_subjects
        ),
    ):
        # Step 3: Loop over each passage for the participant
        for passage_path in tqdm(
            get_passages(participant_dir), desc="Processing passages", leave=False
        ):
            # Load the corresponding scaffold
            passage_name = extract_passage_name(passage_path)
            scaffold_df = load_scaffold(scaffold_dir, passage_name)

            # Load the passage data
            passage_df = get_raw_df(passage_path)
            # Preprocess the passage data
            preprocess_fields(passage_df)
            # Combine the scaffold and passage data
            passage_df = pd.concat([scaffold_df, passage_df], axis=1)

            # Add new fields with NaN values
            for field in config.default_fields:
                if field not in passage_df.columns:
                    passage_df[field] = None

            # Hesitation labeling loop
            label_hesitations(passage_df)

            # Hesitation matching loop
            match_hesitations(passage_df)

            # Error labeling loop
            label_errors(passage_df)

            # Error matching loop
            match_errors(passage_df)

            # Duplication labeling loop
            label_duplications(passage_df)

            # Duplication matching loop
            match_duplications(passage_df)

            # # Save the output file for the passage
            # print(f"Saving output file for passage: {os.path.basename(passage_path)}")
            # passage_df = passage_df[config["default_fields"]]
            # save_output_file(passage_df, args.output_dir)

            sub_dfs[os.path.basename(participant_dir)][passage_name] = passage_df

    # Save the sub_dfs to CSV files, calculate summary statistics for each participant
    sub_dfs_dir = create_output_directory(args.output_dir, "processed_passages")
    summary_dfs = []
    for participant_id in sub_dfs:
        participant_dir = create_output_directory(sub_dfs_dir, participant_id)
        counts = []
        for passage_name, df in sub_dfs[participant_id].items():
            counts.append(get_sheet_stats(df, passage_name))
            df_limited = df[config.default_fields]
            df_limited.to_csv(
                os.path.join(participant_dir, f"{passage_name}.csv"), index=False
            )
        counts = pd.concat(counts, ignore_index=True)
        counts.to_csv(
            os.path.join(participant_dir, f"{participant_id}-passage-data.csv"),
            index=False,
        )
        summary_dfs.append(counts)

    # Step 4: After processing all participants and passages, generate summary statistics
    master_df = pd.concat(summary_dfs, ignore_index=True)
    master_df = master_df.groupby("PassageName", as_index=False).mean(numeric_only=True)
    master_df.insert(0, "Statistic", "Mean")

    # Compute overall mean and standard deviation across ALL passages and subjects
    df_combined = pd.concat(summary_dfs, ignore_index=True)
    all_stats = df_combined.select_dtypes(include="number").agg(["mean", "std"])

    # Create two new rows for overall mean and std
    row_mean = {"PassageName": "All", "Statistic": "Mean"}
    row_std = {"PassageName": "All", "Statistic": "Standard Deviation"}

    for col in all_stats.columns:
        row_mean[col] = all_stats.loc["mean", col]
        row_std[col] = all_stats.loc["std", col]

    # Append new rows to the master DataFrame
    master_df = pd.concat(
        [master_df, pd.DataFrame([row_mean, row_std])], ignore_index=True
    )

    # Save master DataFrame
    master_df.to_csv(
        os.path.join(args.output_dir, "master-statistics.csv"), index=False
    )


if __name__ == "__main__":
    main()
