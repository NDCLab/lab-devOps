import os
from functools import lru_cache

import nltk
import pandas as pd

nltk.download("wordnet")
from nltk.stem import WordNetLemmatizer as wnl
from nltk.stem import LancasterStemmer as ls



@lru_cache(maxsize=1)
def load_word_frequencies():
    # Determine the path to the compressed CSV file
    tsv_path = os.path.join(os.path.dirname(__file__), "word_frequency.tsv.zip")

    # Load the compressed CSV into a DataFrame
    try:
        df = pd.read_csv(tsv_path, sep="\t", compression="zip")
        df.dropna(inplace=True)
        return df
    except FileNotFoundError:
        print(f"Error: The file {tsv_path} was not found.")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: The file {tsv_path} is empty.")
        return None
    except pd.errors.ParserError:
        print(f"Error: The file {tsv_path} could not be parsed.")
        return None


@lru_cache(maxsize=512)
def get_word_freq(word: str) -> int:
    """
    Get the frequency count for a word from the word frequency database.

    The word is first lemmatized (e.g. 'running' -> 'run') before looking up its frequency.
    If the word is not found in the database, returns 0.

    Args:
        word: The word to look up the frequency for

    Returns:
        int: The frequency count for the word, or 0 if not found

    Raises:
        ValueError: If the word frequency database failed to load
    """
    word_freqs = load_word_frequencies()
    if word_freqs is None:
        raise ValueError("Word frequencies not loaded")

    lemmatized_word = wnl.lemmatize(word)
    matching_entries = word_freqs[word_freqs["Word"] == lemmatized_word]
    if matching_entries.empty:
        return 0

    return int(matching_entries["FREQcount"].iloc[0])
