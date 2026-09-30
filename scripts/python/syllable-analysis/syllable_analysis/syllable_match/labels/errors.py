import pandas as pd

from syllable_analysis.utils import compute_window_indicator

import pandas as pd
import logging

def validate_error_boundaries(df: pd.DataFrame, name: str = "", strict: bool = False) -> list[str]:
    """Check that every labeled error has exactly one start and one end.

    For each level ("high-error", "low-error") this verifies:
      1. No orphans: every error syllable has an idx (i.e. its run got a start).
      2. Each idx has exactly one *-start and exactly one *-end.
      3. The start is the first syllable of the run and the end is the last.

    Problems are logged as warnings. Returns the list of problem strings, and
    raises ValueError instead if strict=True.
    """
    problems = []
    tag = f"[{name}] " if name else ""
    sid = df["SyllableID"] if "SyllableID" in df.columns else pd.Series(df.index, index=df.index)

    for level in ("high-error", "low-error"):
        err = df[level].fillna(0) == 1
        start = df[f"{level}-start"].fillna(0) == 1
        end = df[f"{level}-end"].fillna(0) == 1
        idx = df[f"{level}-idx"]

        # 1. Orphaned error syllables (no idx means no start was ever assigned)
        orphans = df.index[err & idx.isna()].tolist()
        if orphans:
            problems.append(f"{tag}{level}: error syllable(s) with no idx/start at rows {orphans}")

        # 2 & 3. Per-idx checks
        for i, run in df[err & idx.notna()].groupby(idx[err & idx.notna()].astype(int)):
            rows = run.index
            n_start, n_end = int(start[rows].sum()), int(end[rows].sum())
            span = f"{level} idx {i} (rows {rows.min()}-{rows.max()}, SyllableID {sid[rows.min()]}-{sid[rows.max()]})"
            if n_start != 1:
                problems.append(f"{tag}{span}: expected 1 start, found {n_start}")
            if n_end != 1:
                problems.append(f"{tag}{span}: expected 1 end, found {n_end}")
            if n_start == 1 and not start[rows.min()]:
                problems.append(f"{tag}{span}: start is not on the first syllable of the run")
            if n_end == 1 and not end[rows.max()]:
                problems.append(f"{tag}{span}: end is not on the last syllable of the run")

        # Stray flags on syllables that aren't errors of this level
        stray = df.index[(start | end) & ~err].tolist()
        if stray:
            problems.append(f"{tag}{level}: start/end flag on non-error syllable(s) at rows {stray}")

    for p in problems:
        logging.warning(p)
    if not problems:
        logging.debug(f"{tag}error boundaries OK")
    if problems and strict:
        raise ValueError("Error boundary validation failed:\n" + "\n".join(problems))
    return problems


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

    if "high-error-idx" in df.columns and df["high-error-idx"].notna().any():
        high_flags = bool_errors.groupby(df["high-error-idx"]).transform("max")
    else:
        high_flags = pd.DataFrame(False, index=df.index, columns=orig_cols)

    if "low-error-idx" in df.columns and df["low-error-idx"].notna().any():
        low_flags  = bool_errors.groupby(df["low-error-idx"]).transform("max")
    else:
        low_flags = pd.DataFrame(False, index=df.index, columns=orig_cols)

    high_start = df["high-error-start"] == 1 if "high-error-start" in df.columns else pd.Series(False, index=df.index)
    high_end   = df["high-error-end"] == 1 if "high-error-end" in df.columns else pd.Series(False, index=df.index)
    low_start  = df["low-error-start"] == 1 if "low-error-start" in df.columns else pd.Series(False, index=df.index)
    low_end    = df["low-error-end"] == 1 if "low-error-end" in df.columns else pd.Series(False, index=df.index)

    high_valid = high_start | high_end
    low_valid  = low_start | low_end

    high_masked = high_flags.where(high_valid.fillna(False), False)
    low_masked  = low_flags.where(low_valid.fillna(False), False)

    result = (high_masked | low_masked).astype(int)
    result.columns = new_cols

    df[new_cols] = result


def label_errors(df: pd.DataFrame, name: str = "") -> None:
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
            # If this is the last syllable in the passage, or the syllable is marked as an
            # allowable disfluency, or the next syllable is not part of this same low error...
            if (
                (idx == len(df) - 1)
                or (row["allowable-disfluency"] == 1)
                or (df.iloc[idx + 1]["low-error"] == 0)
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

            # If this is the last syllable in the passage, or the syllable is marked as an
            # allowable disfluency, or the next syllable is not part of this same high error...
            if (
                (idx == len(df) - 1)
                or (row["allowable-disfluency"] == 1)
                or (df.iloc[idx + 1]["high-error"] == 0)
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
    validate_error_boundaries(df, name=name)