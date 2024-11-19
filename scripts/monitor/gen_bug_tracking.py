import argparse
import os


def create_test_case():
    pass


def create_base_subject():
    pass


def get_args():
    parser = argparse.ArgumentParser(
        description="The hallMonitor.py script ensures data integrity by validating files within raw and checked directories against a central tracker and data dictionary. It performs checks for expected files, naming conventions, and handles exceptions such as no-data.txt and deviation.txt files. It logs errors for missing, extra, or misnamed files, runs special checks for data types like EEG and Psychopy, and prepares valid files for QA. The script outputs errors and updates logs to assist the data monitor in verifying and resolving issues."
    )
    parser.add_argument(
        "basedir",
        type=validated_dir,
        help="the destination directory for generated data",
    )

    return parser.parse_args()


def validated_dir(input):
    basedir = os.path.realpath(input)
    if not os.path.exists(basedir):
        raise argparse.ArgumentTypeError(f"{basedir} does not exist")
    elif not os.path.isdir(basedir):
        raise argparse.ArgumentTypeError(f"{basedir} is not a directory")
    return basedir


if __name__ == "__main__":
    args = get_args()
