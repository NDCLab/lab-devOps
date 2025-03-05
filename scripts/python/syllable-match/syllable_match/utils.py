import csv
import os

import pandas as pd


def compute_window_indicator(series: pd.Series, window: int = 7):
    """
    For a binary pandas Series, compute two lists: one indicating if any value in the previous 'window' rows is 1,
    and one for the next 'window' rows.
    """
    n = len(series)
    before = [0] * n
    after = [0] * n
    for i in range(n):
        # Check previous window rows (i-window to i-1)
        if i > 0:
            before[i] = 1 if series[max(0, i - window) : i].max() > 0 else 0
        else:
            before[i] = 0
        # Check next window rows (i+1 to i+window)
        if i < n - 1:
            after[i] = 1 if series[i + 1 : min(n, i + window + 1)].max() > 0 else 0
        else:
            after[i] = 0
    return before, after


def get_participants(base_dir: str, accepted_subjects: list[str] = []) -> list[str]:
    """
    Returns a list of paths to subject directories within the base directory that are in the accepted_subjects list.

    Parameters:
        base_dir (str): The base directory to search for subject directories.
        accepted_subjects (list[str], optional): A list of subject directories to filter by. Defaults to an empty list.

    Returns:
        list[str]: A list of paths to subject directories that are in the accepted_subjects list, rooted at base_dir.
    """
    return [
        os.path.join(base_dir, s)
        for s in os.listdir(base_dir)
        if s in accepted_subjects
    ]


def get_passages(subject_dir: str) -> list[str]:
    """
    Returns a list of paths to all CSV files under the first subdirectory of subject_dir that ends with `_reconciled`.
    """
    for p in os.listdir(subject_dir):
        if p.endswith("_reconciled"):
            reconciled_dir = os.path.join(subject_dir, p)
            return [
                os.path.join(reconciled_dir, f)
                for f in os.listdir(reconciled_dir)
                if f.endswith(".xlsx")
            ]
    return []


def extract_passage_name(passage_path: str) -> str:
    """
    Extracts the passage name from the path.
    """
    import re

    base_name = os.path.basename(passage_path)
    match = re.fullmatch(r"sub-\d+_(.*?)_reconciled\.xlsx", base_name)
    return match.group(1) if match else ""


def load_scaffold(scaffold_dir: str, passage_name: str) -> pd.DataFrame:
    """
    Loads the scaffold for a given passage name.
    """
    return pd.read_csv(os.path.join(scaffold_dir, f"{passage_name}-scaffold.csv"))


def get_templates(template_dir: str) -> list[str]:
    """
    Returns a list of paths to all CSV files under the template directory.
    """
    return [
        os.path.join(template_dir, f)
        for f in os.listdir(template_dir)
        if f.endswith(".xlsx")
    ]


def read_csv_files(dirname: str, exclude: list[str] = []) -> list[pd.DataFrame]:
    """Read all CSV files in a directory, excluding specified files."""
    return [
        pd.read_csv(os.path.join(dirname, file))
        for file in os.listdir(dirname)
        if file.endswith("csv") and file not in exclude
    ]


def extract_words_and_syllables(
    file_path: str, sep: str = "\t"
) -> tuple[list[str], list[str]]:
    """Extract words and syllables from a template file."""
    words = []
    syllables = []

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=sep)

        # Read the first row for "target text"
        first_row = next(reader, [])
        if "target text" in first_row:
            target_text_index = first_row.index("target text")
            words = [
                cell.strip()
                for cell in first_row[target_text_index + 1 :]
                if cell.strip()
            ]

        # Read the second row for "target syllables"
        second_row = next(reader, [])
        if "target syllables" in second_row:
            target_syllables_index = second_row.index("target syllables")
            syllables = [
                cell.strip()
                for cell in second_row[target_syllables_index + 1 :]
                if cell.strip()
            ]

    return words, syllables


def create_output_directory(base_dir: str, sub_dir: str) -> str:
    """Create an output directory if it doesn't exist."""
    out_dir = os.path.join(base_dir, sub_dir)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir
