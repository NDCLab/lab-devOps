import pandas as pd


def label_hesitations(df: pd.DataFrame) -> None:
    """
    Identifies and labels hesitations within a given DataFrame. This function marks the start and end of hesitations,
    and assigns a unique index to each hesitation sequence. The output DataFrame includes three new columns:
    'hesitation-start', 'hesitation-end', and 'hesitation-idx'.
    """

    # Initialize 'hesitation-start' column by copying 'hesitation-disfluency' values
    df["hesitation-start"] = df["hesitation-disfluency"]

    # Determine 'hesitation-end' by shifting 'hesitation-start' down
    #    by one row and filling NaNs with 0
    df["hesitation-end"] = df["hesitation-start"].shift(1, fill_value=0)

    # Assign a unique index to each hesitation sequence
    df["hesitation-idx"] = (
        df[df["hesitation-start"].astype(bool) | df["hesitation-end"].astype(bool)]
        .groupby("hesitation-start")
        .cumcount()
        + 1
    )
    # For rows without hesitation, set 'hesitation-idx' to NaN
    df.loc[
        ~(df["hesitation-start"].astype(bool) | df["hesitation-end"].astype(bool)),
        "hesitation-idx",
    ] = None
