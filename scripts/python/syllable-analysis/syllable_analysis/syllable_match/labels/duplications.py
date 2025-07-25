import pandas as pd

from syllable_analysis.utils import compute_window_indicator


def label_duplications(df: pd.DataFrame) -> None:
    """
    Identifies and labels duplications within a given DataFrame following the specified approach.
    Assumes columns exist: Disfluency_DuplicationRepetitionSyllable (row 20),
    duplication-word (row 21), duplication-phrase (row 22),
    and SyllInfo_LastPreCorrectionSyllable (row 25).
    """
    # Initialize duplication columns
    df["duplication"] = 0
    df["duplication-start"] = 0
    df["duplication-end"] = 0
    df["duplication-idx"] = 0
    df["duplication-word"] = 0
    df["duplication-phrase"] = 0

    duplication_idx = 0

    # First loop: identify duplication sequences
    for idx, row in df.iterrows():
        if row["Disfluency_DuplicationRepetitionSyllable"] > 0:
            df.at[idx, "duplication"] = 1

            # Check if this is the start of a new duplication
            is_new_duplication = (
                (idx == 0)
                or (df.iloc[idx - 1]["Disfluency_DuplicationRepetitionSyllable"] == 0)
                or (df.iloc[idx - 1]["SyllInfo_LastPreCorrectionSyllable"] > 0)
            )

            if is_new_duplication:
                df.at[idx, "duplication-start"] = 1
                duplication_idx += 1
                df.at[idx, "duplication-idx"] = duplication_idx
            else:
                # Copy duplication index from prior syllable
                df.at[idx, "duplication-idx"] = df.iloc[idx - 1]["duplication-idx"]

            # Check if this is the end of a duplication
            is_duplication_end = (
                (row["SyllInfo_LastPreCorrectionSyllable"] > 0)
                or (idx == len(df) - 1)
                or (df.iloc[idx + 1]["Disfluency_DuplicationRepetitionSyllable"] == 0)
            )

            if is_duplication_end:
                df.at[idx, "duplication-end"] = 1

            # Label word vs phrase duplications
            if row["duplication-word"] > 0 and row["duplication-phrase"] == 0:
                df.at[idx, "duplication-word"] = 1
            elif row["duplication-phrase"] > 0 and row["duplication-word"] == 0:
                df.at[idx, "duplication-phrase"] = 1

        # Mark duplication-start-before and duplication-start-after
        dupe_start_before, dupe_start_after = compute_window_indicator(
            df["duplication-start"], 7
        )
        df["duplication-start-before"] = dupe_start_before
        df["duplication-start-after"] = dupe_start_after
