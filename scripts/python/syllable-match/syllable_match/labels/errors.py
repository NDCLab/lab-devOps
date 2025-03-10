import pandas as pd


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
    )

    # Label high errors
    df["high-error"] = (
        (df["Error_Misproduction"] > 0) & (df["Outcome_WordSubstitution"] > 0)
        | ((df["Error_WordStressError"] > 0) & (df["Outcome_WordSubstitution"] > 0))
        | ((df["Error_InsertedSyllable"] > 0) & (df["Outcome_WordSubstitution"] > 0))
        | ((df["Error_OmittedSyllable"] > 0) & (df["Outcome_WordSubstitution"] > 0))
        | (df["Error_InsertedWord"] > 0)
        | (df["Error_OmittedWord"] > 0)
    )

    # Label allowable disfluencies
    df["allowable-disfluency"] = (
        (df["Disfluency_InsertedProsodicBreak"] > 0)
        | (df["Disfluency_FilledPause"] > 0)
        | (df["Disfluency_Hesitation"] > 0)
        | (df["Disfluency_Elongation"] > 0)
        | (
            # Current syllable is a duplication, but next syllable is not
            (df["Disfluency_DuplicationElongationSyllable"] > 0)
            & (df["Disfluency_DuplicationElongationSyllable"].shift(-1) == 0)
        )
        | (
            # Current syllable is part of a correction, but next syllable is not
            (df["correction-syll"] == 1) & (df["correction-syll"].shift(-1) == 0)
        )
    )
