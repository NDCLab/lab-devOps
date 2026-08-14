import logging
import os
import re

import pandas as pd

from syllable_analysis.utils import extract_words_and_syllables

from .constructor import ScaffoldConstructor


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

def get_carriage_returns(file_path,total_length):
    # check if result matches with syllables_list
    # 1. Get the integer index position of the matching row
    df = pd.read_excel(file_path, header=None)
    row_pos = df.index.get_loc(
        df[df.iloc[:, 1].str.contains("Carriage Return", na=False)].index[0]
    )
    if row_pos is None:
        raise ValueError("No row containing 'Carriage Return' found in the second column.")

    # 2. Get columns after the 2nd column (index 2 onwards) for that row
    result = df.iloc[row_pos, 2:total_length+2]
    

    # make sure they're all integers
    result = result.astype(int)
    before_carriage_list = result.tolist()
    after_carriage_list = result.shift(1, fill_value=0).tolist()

    return before_carriage_list, after_carriage_list


def main(data_dir: str):
    extractors = []

    out_dir = os.path.join(data_dir, "scaffolds")

    os.makedirs(out_dir, exist_ok=True)

    # second pass, build the scaffolds
    print(f"Building scaffolds in {out_dir}...")

    for basename in os.listdir(data_dir):
        print(f"Processing {basename}...")
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
            logging.warning(f"Skipping {filepath}, unknown extension {ext}")
            continue

        passage_name = os.path.splitext(basename)[0]

        sep = "\t" if basename.endswith(".tsv") else ","

        words, syllables = extract_words_and_syllables(filepath, sep=sep)

        constructor = ScaffoldConstructor(passage_name, words, syllables)

        constructor.register_extractors(extractors)

        df = constructor.build()
        total_length = len(df["syllable_id"])
        before_carriage, after_carriage = get_carriage_returns(filepath, total_length)
        df["word-before-carriage"] = before_carriage
        df["word-after-carriage"] = after_carriage
        df["word-before-carriage"] = df.groupby("word_id")["word-before-carriage"].transform("max")
        df["word-after-carriage"] = df.groupby("word_id")["word-after-carriage"].transform("max")
        print(f"Written carriage return information for {passage_name} to {out_dir}")
        # check if columns are present in the dataframe
        if "word-before-carriage" not in df.columns or "word-after-carriage" not in df.columns:
            raise ValueError("Required columns are missing from the DataFrame.")


        df.to_csv(os.path.join(out_dir, f"{passage_name}-scaffold.csv"), index=False)