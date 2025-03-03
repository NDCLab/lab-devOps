import os

import pandas as pd


def load_word_frequencies():
    # Determine the path to the compressed CSV file
    csv_path = os.path.join(os.path.dirname(__file__), "word_frequency.csv.zip")

    # Load the compressed CSV into a DataFrame
    try:
        df = pd.read_csv(csv_path, compression="zip")
        return df
    except FileNotFoundError:
        print(f"Error: The file {csv_path} was not found.")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: The file {csv_path} is empty.")
        return None
    except pd.errors.ParserError:
        print(f"Error: The file {csv_path} could not be parsed.")
        return None
