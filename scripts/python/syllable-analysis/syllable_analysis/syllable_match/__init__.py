import logging
import os
from collections import defaultdict

import pandas as pd

from syllable_analysis.utils import (
    create_output_directory,
    extract_passage_name,
    get_participants,
    get_passages,
    load_scaffold,
)

from .fields import DEFAULT_FIELDS
from .labels import label_duplications, label_errors, label_hesitations
from .matching import (
    match_duplications,
    match_errors_alt,
    match_hesitations_alt,
)
from .parsing import get_raw_df, preprocess_fields


def process_subject_data(
    input_dir: str,
    scaffold_dir: str,
    output_dir: str,
    accepted_subjects: list[str] = None,
):
    # Dictionary to store scaffold dataframes for each participant
    # Format: {participant_id: {passage_name: dataframe}}
    sub_dfs = defaultdict(dict)

    # Loop over each participant
    logging.info("Step 2: Processing participants...")
    all_participants = get_participants(input_dir, accepted_subjects)
    for participant_idx, participant_dir in enumerate(all_participants):
        logging.info(
            f"Processing participant {os.path.basename(participant_dir)} ({participant_idx+1}/{len(all_participants)})"
        )
        # Loop over each passage for the participant
        participant_passages = get_passages(participant_dir)
        for passage_idx, passage_path in enumerate(participant_passages):
            logging.info(
                f"Processing passage {os.path.basename(passage_path)} ({passage_idx+1}/{len(participant_passages)})"
            )
            # Load the corresponding scaffold
            passage_name = extract_passage_name(passage_path)
            if not passage_name:
                raise ValueError(f"Improperly named file {passage_path}")
            scaffold_df = load_scaffold(scaffold_dir, passage_name)

            # Load the passage data
            passage_df = get_raw_df(passage_path)
            # Preprocess the passage data
            preprocess_fields(passage_df)
            # Combine the scaffold and passage data
            passage_df = pd.concat([scaffold_df, passage_df], axis=1)

            # Add new fields with NaN values
            for field in DEFAULT_FIELDS:
                if field not in passage_df.columns:
                    passage_df[field] = None

            # Hesitation labeling loop
            label_hesitations(passage_df)

            # Hesitation matching loop
            match_hesitations_alt(passage_df)

            # Error labeling loop
            label_errors(passage_df)

            # Error matching loop
            match_errors_alt(passage_df)

            # Duplication labeling loop
            label_duplications(passage_df)

            # Duplication matching loop
            match_duplications(passage_df)

            sub_dfs[os.path.basename(participant_dir)][passage_name] = passage_df

    # Save the sub_dfs to CSV files, calculate summary statistics for each participant
    sub_dfs_dir = create_output_directory(output_dir, "processed_passages")
    for participant_id in sub_dfs:
        participant_dir = os.path.join(sub_dfs_dir, participant_id)
        os.makedirs(participant_dir)
        for passage_name, df in sub_dfs[participant_id].items():
            df.to_csv(
                os.path.join(participant_dir, f"{passage_name}_all-cols.csv"),
                index=False,
            )
            df_limited = df[DEFAULT_FIELDS]
            df_limited.to_csv(
                os.path.join(participant_dir, f"{passage_name}.csv"), index=False
            )
