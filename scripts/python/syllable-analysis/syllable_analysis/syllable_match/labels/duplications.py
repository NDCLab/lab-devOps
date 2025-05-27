import pandas as pd


def label_duplications(df: pd.DataFrame) -> None:
    """
    Identifies and labels duplications within a given DataFrame. This function marks the start and end of duplications,
    and assigns a unique index to each duplication sequence. The output DataFrame includes three new columns:
    'duplication-start', 'duplication-end', and 'duplication-idx'.
    """
    return
