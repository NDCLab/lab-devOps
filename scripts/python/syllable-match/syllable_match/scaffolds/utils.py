import os
import re

import pandas as pd

from syllable_match.utils import extract_words_and_syllables

from .constructor import ScaffoldConstructor


def set_nan_fields(df: pd.DataFrame, fields: list[str]):
    """
    Adds new fields to a DataFrame with NaN values.

    This function iterates over a list of field names and adds each field to the DataFrame with NaN values.

    Parameters:
    - df (pd.DataFrame): The DataFrame to which new fields will be added.
    - fields (list[str]): A list of field names to be added to the DataFrame.

    Returns:
    - None: This function modifies the DataFrame in place and does not return a value.
    """
    for field in fields:
        df[field] = None


def convert_xlsx_to_csv_string(filepath: str, sep: str = "\t"):
    """
    Converts a single .xlsx file to .csv format as a string.

    This function checks if the file is an .xlsx file and if a corresponding .csv file does not already exist in the data directory.
    If these conditions are met, it reads the .xlsx file, replaces line breaks with spaces, removes unnecessary column names, and standardizes text data to lower-case.
    The converted data is then returned as a string.

    Parameters:
    - filepath (str): The path to the .xlsx file to be converted.
    - sep (str): The separator to use in the .csv file. Default is tab.

    Returns:
    - str: The converted data as a CSV string.
    """

    # Make sure we're dealing with an .xlsx file
    if not os.path.splitext(os.path.basename(filepath))[1] == ".xlsx":
        return

    # Construct new CSV
    df_xlsx = pd.read_excel(filepath)

    # Replace all fields containing line breaks with space
    df = df_xlsx.replace("\n", " ", regex=True)
    df_str = df.to_csv(index=False, sep=sep, encoding="utf-8")

    # Adjust for quirks in reading non-relational data into Pandas
    # Remove empty column names
    df_str = re.sub(r"Unnamed:\s\d+", sep, df_str)
    # Fix deduplicated column names
    df_str = re.sub(r"(.+?)\.\d+", r"\1", df_str)
    df_str = df_str.lower()

    return df_str


def main(data_dir: str):
    extractors = []

    out_dir = os.path.join(data_dir, "scaffolds")

    os.makedirs(out_dir, exist_ok=True)

    # second pass, build the scaffolds

    for basename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, basename)

        if os.path.isdir(filepath):
            continue

        ext = os.path.splitext(basename)[1]
        if ext == ".tsv":
            sep = "\t"
        elif ext == ".csv":
            sep = ","
        elif ext == ".xlsx":
            continue

        else:
            print(f"Skipping {filepath}, unknown extension {ext}")
            continue

        passage_name = os.path.splitext(basename)[0]

        sep = "\t" if basename.endswith(".tsv") else ","

        words, syllables = extract_words_and_syllables(filepath, sep=sep)

        constructor = ScaffoldConstructor(passage_name, words, syllables)

        constructor.register_extractors(extractors)

        df = constructor.build()

        df.to_csv(os.path.join(out_dir, f"{passage_name}-scaffold.csv"), index=False)
