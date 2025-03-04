import argparse
import json
import os

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
)
from syllable_match.models import FeatureExtractor
from syllable_match.resources import load_word_frequencies
from syllable_match.scaffolds import create_scaffolds
from syllable_match.stats import make_master_sheet
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
        help="List of accepted subjects. If not provided, all subjects are accepted.",
    )

    # Add --force flag
    parser.add_argument(
        "--force",
        action="store_true",
        help="If set, empties the output directory if it already exists.",
    )

    return parser.parse_args()


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return json.load(f)


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
        WordFrequencyExtractor(load_word_frequencies()),
    ]


def main():
    args = get_args()
    config = load_config(os.path.join(args.input_dir, "config.json"))

    # Step 0: Start with an empty output_dir
    if os.path.exists(args.output_dir):
        if args.force:
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
        os.makedirs(args.output_dir)

    # Step 1: Construct basic scaffolds for each passage template
    template_dir = os.path.join(args.input_dir, "templates")
    if not os.path.exists(template_dir):
        raise FileNotFoundError(
            f"The templates directory '{template_dir}' does not exist."
        )
    scaffold_dir = create_output_directory(args.output_dir, "scaffolds")
    create_scaffolds(
        get_templates(template_dir), scaffold_dir, get_scaffold_extractors()
    )

    # Step 2: Loop over each participant
    for participant_dir in get_participants(args.input_dir, args.accepted_subjects):
        # Step 3: Loop over each passage for the participant
        for passage_path in get_passages(participant_dir):
            # Load the corresponding scaffold
            passage_name = extract_passage_name(passage_path)
            scaffold = load_scaffold(scaffold_dir, passage_name)

            # Add new fields with NaN values
            output_file = initialize_output_file(scaffold)
            add_nan_fields(
                output_file,
                fields=config["calculated_fields"],
            )

            # Preprocessing loop to populate simple fields
            preprocess_fields(output_file)

            # Hesitation labeling loop
            label_hesitations(output_file)

            # Hesitation matching loop
            match_hesitations(output_file)

            # Error labeling loop
            label_errors(output_file)

            # Error matching loop
            match_errors(output_file)

            # Duplication labeling loop
            label_duplications(output_file)

            # Duplication matching loop
            match_duplications(output_file)

            # Save the output file for the passage
            save_output_file(output_file, args.output_dir)

    # Step 4: After processing all participants and passages, generate summary statistics
    generate_summary_statistics(args.output_dir)

    # Loop over all output files to count occurrences and output count files
    for participant_dir in get_participants(args.output_dir):
        count_occurrences(participant_dir, args.output_dir)

    # Generate a master file with all participants and summary stats
    make_master_sheet(args.output_dir)


if __name__ == "__main__":
    main()
