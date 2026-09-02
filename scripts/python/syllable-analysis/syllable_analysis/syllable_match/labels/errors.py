import pandas as pd

from syllable_analysis.utils import compute_window_indicator

import pandas as pd


def label_subtype_errors(df: pd.DataFrame) -> None:
    col_map = {
        "Error_Misproduction": "any-misproduction",
        "Error_OmittedSyllable": "any-syll-omission",
        "Error_InsertedSyllable": "any-syll-insertion",
        "Error_WordStressError": "any-word-stress",
        "Error_InsertedWord": "any-word-insertion",
        "Error_OmittedWord": "any-word-omission",


    }

    orig_cols = list(col_map.keys())
    new_cols = list(col_map.values())

    # Vectorized boolean matrix (same as before)
    bool_errors = df[orig_cols] > 0

    # transform("max") broadcasts the per-group max back to every row, aligned to df's index.
    # No merge, no suffixes, no temp columns, no fillna needed.
    high_flags = bool_errors.groupby(df["high-error-idx"]).transform("max")
    low_flags  = bool_errors.groupby(df["low-error-idx"]).transform("max")

    high_valid = (df["high-error-start"] == 1) | (df["high-error-end"] == 1)
    low_valid  = (df["low-error-start"] == 1)  | (df["low-error-end"] == 1)


    high_masked = high_flags.where(high_valid.fillna(False), False)
    low_masked  = low_flags.where(low_valid.fillna(False), False)

    result = (high_masked | low_masked).astype(int)
    result.columns = new_cols

    df[new_cols] = result


def label_errors(df: pd.DataFrame) -> None:
    """
    Labels errors in the DataFrame.
    """
    # Label low errors
    df["low-error"] = (
        ((df["Error_Misproduction"] > 0) & (df["Outcome_WordSubstitution"] == 0))
        | ((df["Error_WordStressError"] > 0) & (df["Outcome_WordSubstitution"] == 0))
        | (
            (df["Error_InsertedSyllable"] > 0)
            & (df["Error_InsertedWord"] == 0)
            & (df["Outcome_WordSubstitution"] == 0)
        )
        | (
            (df["Error_OmittedSyllable"] > 0)
            & (df["Error_OmittedWord"] == 0)
            & (df["Outcome_WordSubstitution"] == 0)
        )
    ).astype(int)

    # Label high errors
    df["high-error"] = (
        (df["Error_Misproduction"] > 0) & (df["Outcome_WordSubstitution"] > 0)
        | ((df["Error_WordStressError"] > 0) & (df["Outcome_WordSubstitution"] > 0))
        | ((df["Error_InsertedSyllable"] > 0) & (df["Outcome_WordSubstitution"] > 0))
        | ((df["Error_OmittedSyllable"] > 0) & (df["Outcome_WordSubstitution"] > 0))
        | (df["Error_InsertedWord"] > 0)
        | (df["Error_OmittedWord"] > 0)
    ).astype(int)

    # Label allowable disfluencies
    df["allowable-disfluency"] = (
        (df["Disfluency_InsertedProsodicBreak"] > 0)
        | (df["Disfluency_FilledPause"] > 0)
        | (df["Disfluency_Hesitation"] > 0)
        | (df["Disfluency_Elongation"] > 0)
        | (
            # Current syllable is a duplication, but next syllable is not
            (df["Disfluency_DuplicationRepetitionSyllable"] > 0)
            & (df["Disfluency_DuplicationRepetitionSyllable"].shift(-1) == 0)
        )
        | (
            # Current syllable is part of a correction, but next syllable is not
            (df["correction-syll"] == 1) & (df["correction-syll"].shift(-1) == 0)
        )
    ).astype(int)

    # Make additional markings for high and low errors
    high_error_idx = 0
    low_error_idx = 0
    for idx, row in df.iterrows():

        if row["low-error"] == 1:
            # Mark whether an attempt was made to correct the error
            if row["correction-syll"] == 1:
                df.at[idx, "low-error-corrected"] = 1
            else:
                df.at[idx, "low-error-corrected"] = 0
            # First determine if this is a continuation of a prior low error span or the start of a new one
            if (idx > 0) and (df.iloc[idx - 1]["low-error"] == 1) and (df.iloc[idx - 1]["allowable-disfluency"] == 0):
                # Copy the prior syllable's low error index
                df.at[idx, "low-error-idx"] = df.iloc[idx - 1]["low-error-idx"]
            # If the previous syllable was a high error, or has no deviations, or had an allowable disfluency, or if this is the first syllable...
            # Then this syllable is the start of a new low error span
            elif ((idx > 0) and (
                (df.iloc[idx - 1]["high-error"] == 1)
                or (df.iloc[idx - 1]["any-deviation"] == 0)
                or (df.iloc[idx - 1]["allowable-disfluency"] == 1)
            )) or ((idx == 0)):
                df.at[idx, "low-error-start"] = 1
                low_error_idx += 1
                df.at[idx, "low-error-idx"] = low_error_idx
            # If syllable is marked as an allowable disfluency, or if next syllable has no deviations,
            # or if this is a low-error-start and the next syllable is an allowable disfluency...
            if (idx < len(df) - 1) and (
                (row["allowable-disfluency"] == 1)
                or (df.iloc[idx + 1]["any-deviation"] == 0)
                or (
                    (df.at[idx, "low-error-start"] == 1)
                    and (df.iloc[idx + 1]["allowable-disfluency"] == 1)
                    and (df.iloc[idx + 1]["low-error"] == 0)
                )
            ):
                df.at[idx, "low-error-end"] = 1

        if row["high-error"] == 1:
            # If any attempt was made to correct the error...
            if row["correction-syll"] == 1:
                df.at[idx, "high-error-corrected"] = 1
            else:
                df.at[idx, "high-error-corrected"] = 0

            # Determine if this is a continuation of a prior high error span or the start of a new one
            if (idx > 0) and (df.iloc[idx - 1]["high-error"] == 1) and (df.iloc[idx - 1]["allowable-disfluency"] == 0):
                df.at[idx, "high-error-idx"] = df.iloc[idx - 1]["high-error-idx"]
            # If the previous syllable was a low error, or has no deviations, or had an allowable disfluency, or if this is the first syllable...
            elif ((idx > 0) and (
                (df.iloc[idx - 1]["low-error"] == 1)
                or (df.iloc[idx - 1]["any-deviation"] == 0)
                or (df.iloc[idx - 1]["allowable-disfluency"] == 1)
            )) or ((idx == 0)):
                df.at[idx, "high-error-start"] = 1
                high_error_idx += 1
                df.at[idx, "high-error-idx"] = high_error_idx

            # If syllable is marked as an allowable disfluency, or if next syllable is a comparison...
            if (idx < len(df) - 1) and (
                (row["allowable-disfluency"] == 1)
                or (df.iloc[idx + 1]["any-deviation"] == 0)
                or (
                    (df.at[idx, "high-error-start"] == 1)
                    and (df.iloc[idx + 1]["allowable-disfluency"] == 1)
                    and (df.iloc[idx + 1]["high-error"] == 0)
                )
            ):
                df.at[idx, "high-error-end"] = 1

    for idx, row in df.iterrows():
        # After marking high and low errors, check for endpoints
        if (row["low-error"] == 1) and (
            (idx == len(df) - 1) or (df.iloc[idx + 1]["high-error"] == 1)
        ):
            df.at[idx, "low-error-end"] = 1
        if (row["high-error"] == 1) and (
            (idx == len(df) - 1) or (df.iloc[idx + 1]["low-error"] == 1)
        ):
            df.at[idx, "high-error-end"] = 1

    # Generate before/after indicators with a window size of 7
    df["high-error-before"], df["high-error-after"] = compute_window_indicator(
        df["high-error"], 7
    )
    df["low-error-before"], df["low-error-after"] = compute_window_indicator(
        df["low-error"], 7
    )

    df["high-error-start-before"], df["high-error-start-after"] = compute_window_indicator(
        df["high-error-start"], 7
    )
    df["low-error-start-before"], df["low-error-start-after"] = compute_window_indicator(
        df["low-error-start"], 7
    )

    label_subtype_errors(df)
