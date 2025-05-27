import argparse
import datetime
import logging
import os

from syllable_analysis.error_analysis import summarize
from syllable_analysis.error_analysis.analyze import analyze_recall_periods
from syllable_analysis.scaffolds import build_scaffolds
from syllable_analysis.syllable_match import process_subject_data


def get_args():
    parser = argparse.ArgumentParser(
        description="Process subject data for READ analysis."
    )

    parser.add_argument(
        "input_dir", type=str, help="The input directory containing data."
    )
    parser.add_argument(
        "coding_template_dir",
        type=str,
        help="The directory that contains blank error coding templates "
        + "(e.g., elephant_11g.xlsx, pencils_9g.xlsx).",
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="The parent directory to contain results. "
        + "This script's data will be placed in a timestamped subdirectory.",
    )

    # Add accepted_subjects as an optional argument
    parser.add_argument(
        "--accepted_subjects",
        nargs="*",  # Allows multiple values
        default=None,  # Default to None if not provided
        help=(
            "List of accepted subjects in 'sub-ID' format, e.g., 'sub-003 sub-004 ...'. "
            "If not provided, all subjects are accepted."
        ),
    )

    return parser.parse_args()


def main(
    input_dir: str,
    coding_template_dir: str,
    output_parentdir: str,
    accepted_subjects: list[str],
):
    logging.info("Starting processing")

    # 0. Set up directories
    if not os.path.isdir(output_parentdir):
        raise FileNotFoundError(output_parentdir + " is not a directory.")

    dt_now = datetime.datetime.now().strftime("%Y%m%d_%H%M-data")
    output_subdir = os.path.join(output_parentdir, dt_now)
    os.makedirs(output_subdir)

    # 1. Build scaffolds
    scaffold_dir = os.path.join(output_subdir, "scaffolds")
    build_scaffolds(coding_template_dir, scaffold_dir)

    # 2. Process subject data
    process_subject_data(
        input_dir, scaffold_dir, output_subdir, accepted_subjects or None
    )

    # 3. Extract summary statistics from subject data
    summarize(os.path.join(output_subdir, "processed_passages"), output_subdir)

    # 4. Process recall data
    analyze_recall_periods(input_dir, output_subdir)


if __name__ == "__main__":
    args = get_args()
    main(
        args.input_dir,
        args.coding_template_dir,
        args.output_dir,
        args.accepted_subjects,
    )
