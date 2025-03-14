import pandas as pd

from syllable_match.utils import compute_window_indicator


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
            df.at[idx, "low-error-corrected"] = row["correction-syll"]
            # If prior syllable was a high error or a comparison or had an allowable disfluency...
            if (idx > 0) and (
                (df.iloc[idx - 1]["high-error"] == 1)
                or (df.iloc[idx - 1]["any-deviation"] == 0)
                or (df.iloc[idx - 1]["allowable-disfluency"] == 1)
            ):
                df.at[idx, "low-error-start"] = 1
                low_error_idx += 1
                df.at[idx, "low-error-idx"] = low_error_idx
            # If prior syllable was a low error...
            if (idx > 0) and (df.iloc[idx - 1]["low-error"] == 1):
                # Copy the prior syllable's low error index
                df.at[idx, "low-error-idx"] = df.iloc[idx - 1]["low-error-idx"]
            # If syllable is marked as an allowable disfluency, or if next syllable is a comparison...
            if (idx < len(df) - 1) and (
                (row["allowable-disfluency"] == 1)
                or (df.iloc[idx + 1]["any-deviation"] == 0)
            ):
                df.at[idx, "low-error-end"] = 1

        if row["high-error"] == 1:
            # If any attempt was made to correct the error...
            if row["correction-syll"] == 1:
                df.at[idx, "high-error-corrected"] = 1
            # If prior syllable was a low error or a comparison or had an allowable disfluency...
            if (idx > 0) and (
                (df.iloc[idx - 1]["low-error"] == 1)
                or (df.iloc[idx - 1]["any-deviation"] == 0)
                or (df.iloc[idx - 1]["allowable-disfluency"] == 1)
            ):
                df.at[idx, "high-error-start"] = 1
                high_error_idx += 1
                df.at[idx, "high-error-idx"] = high_error_idx
            # If prior syllable was a high error...
            if (idx > 0) and (df.iloc[idx - 1]["high-error"] == 1):
                df.at[idx, "high-error-idx"] = df.iloc[idx - 1]["high-error-idx"]
            # If syllable is marked as an allowable disfluency, or if next syllable is a comparison...
            if (idx < len(df) - 1) and (
                (row["allowable-disfluency"] == 1)
                or (df.iloc[idx + 1]["any-deviation"] == 0)
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
