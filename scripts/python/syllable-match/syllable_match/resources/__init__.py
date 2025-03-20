import os
import string
from functools import lru_cache

import nltk
import pandas as pd

nltk.download("wordnet")
from nltk.stem import WordNetLemmatizer as wnl



@lru_cache(maxsize=1)
def load_word_frequencies():
    # Determine the path to the compressed CSV file
    tsv_path = os.path.join(os.path.dirname(__file__), "word_frequency.tsv.zip")

    # Load the compressed CSV into a DataFrame
    try:
        df = pd.read_csv(tsv_path, sep="\t", compression="zip")
        df.dropna(inplace=True)
        df.rename(
            columns={
                "Word": "word",
                "FREQcount": "frequency_count",
                "CDcount": "film_count",
                "FREQlow": "lowercase_start_frequency",
                "CDlow": "lowercase_start_film_count",
                "SUBTLWF": "frequency_per_million",
                "Lg10WF": "log10_frequency",
                "SUBTLCD": "film_appearance_percent",
                "Lg10CD": "log10_film_count",
            },
            inplace=True,
        )
        df["word"] = df["word"].str.lower()
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


@lru_cache(maxsize=1)
def get_corpus_median():
    word_freqs = load_word_frequencies()
    if word_freqs is None:
        raise ValueError("Word frequencies not loaded")
    return word_freqs["frequency_per_million"].median()


@lru_cache(maxsize=512)
def get_word_freq(word: str) -> float:
    """
    Get the frequency for a word from the word frequency database.

    The word is first lemmatized (e.g. 'running' -> 'run') before looking up its frequency.
    If the word is not found in the database, returns 0.

    Args:
        word: The (uncleaned) word to look up the frequency for

    Returns:
        int: The word's frequency per million words in the corpus, or the corpus median if not found

    Raises:
        ValueError: If the word frequency database failed to load
    """
    word_freqs = load_word_frequencies()
    if word_freqs is None:
        raise ValueError("Word frequencies not loaded")

    # Apply basic word normalization
    word = word.lower()
    word = word.strip(string.punctuation)

    # Special handling for words split by apostrophe or hyphen:
    #   average the frequencies of the n word parts
    if "'" in word or "-" in word:
        parts = word.split("'") if "'" in word else word.split("-")
        freqs = [get_word_freq(part) for part in parts]
        return sum(freqs) / len(freqs)

    # Look for exact matches first
    matching_entries = word_freqs[word_freqs["word"] == word]
    if not matching_entries.empty:
        return int(matching_entries["frequency_per_million"].iloc[0])

    # If no exact match, look for lemmatized matches
    lemmatized_word = wnl.lemmatize(word)
    matching_entries = word_freqs[word_freqs["word"] == lemmatized_word]
    if not matching_entries.empty:
        return int(matching_entries["frequency_per_million"].iloc[0])

    # If no matches, return corpus median
    return get_corpus_median()
