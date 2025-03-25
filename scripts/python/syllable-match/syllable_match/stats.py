import os
import string

import pandas as pd
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from nltk.stem.lancaster import LancasterStemmer

from syllable_match.resources import load_word_frequencies


def make_master_sheet(sub_dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Create a master DataFrame by combining multiple DataFrames and appending overall statistics.

    Parameters:
    sub_dfs (list[pd.DataFrame]): A list of DataFrames with identical columns.

    Returns:
        pd.DataFrame: A master DataFrame with combined data and overall statistics.
    """
    check_identical_columns(sub_dfs)
    master_df = create_master_df(sub_dfs)
    all_stats = compute_overall_stats(sub_dfs)
    master_df = append_overall_stats(master_df, all_stats)
    return master_df


def create_master_df(sub_dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Concatenate DataFrames and compute the mean for each group by 'PassageName'.

    Parameters:
        sub_dfs (list[pd.DataFrame]): A list of DataFrames with identical columns.

    Returns:
        pd.DataFrame: A DataFrame with the mean values for each 'PassageName'.
    """
    master_df = pd.concat(sub_dfs, ignore_index=True)
    master_df = master_df.groupby("PassageName", as_index=False).mean(numeric_only=True)
    master_df.insert(0, "Statistic", "Mean")
    return master_df


def compute_overall_stats(sub_dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Compute overall statistics (mean and standard deviation) for numeric columns.

    Parameters:
        sub_dfs (list[pd.DataFrame]): A list of DataFrames with identical columns.

    Returns:
        pd.DataFrame: A DataFrame with overall mean and standard deviation for each numeric column.
    """
    df_combined = pd.concat(sub_dfs, ignore_index=True)
    return df_combined.select_dtypes(include="number").agg(["mean", "std"])


def append_overall_stats(
    master_df: pd.DataFrame, all_stats: pd.DataFrame
) -> pd.DataFrame:
    """
    Append overall statistics to the master DataFrame.

    Parameters:
        master_df (pd.DataFrame): The master DataFrame with combined data.
        all_stats (pd.DataFrame): A DataFrame with overall statistics.

    Returns:
        pd.DataFrame: The master DataFrame with appended overall statistics.
    """
    row_mean = {"PassageName": "All", "Statistic": "Mean"}
    row_std = {"PassageName": "All", "Statistic": "Standard Deviation"}

    for col in all_stats.columns:
        row_mean[col] = all_stats.loc["mean", col]
        row_std[col] = all_stats.loc["std", col]

    return pd.concat([master_df, pd.DataFrame([row_mean, row_std])], ignore_index=True)


def check_identical_columns(sub_dfs: list[pd.DataFrame]) -> None:
    """
    Check if all DataFrames in the list have identical columns.

    Parameters:
        sub_dfs (list[pd.DataFrame]): A list of DataFrames to check.

    Raises:
        ValueError: If the list is empty or if any DataFrame has different columns.
    """
    if not sub_dfs:
        raise ValueError("The list of DataFrames is empty.")

    first_df_columns = sub_dfs[0].columns
    for df in sub_dfs[1:]:
        if not first_df_columns.equals(df.columns):
            raise ValueError("All DataFrames must have identical columns.")


def generate_summary_statistics(
    sub_dfs: dict[str, pd.DataFrame], output_dir: str
) -> None:
    """
    Generate summary statistics for each participant and save them to a CSV file.

    Parameters:
        sub_dfs (dict[str, pd.DataFrame]): A dictionary of DataFrames with participant names as keys.
        output_dir (str): The directory to save the summary statistics.
    """
    for participant_name, df in sub_dfs.items():
        df.to_csv(
            os.path.join(output_dir, f"{participant_name}_summary_statistics.csv"),
            index=False,
        )


def get_wordnet_pos(pos_str: str) -> str:
    if pd.isna(pos_str):
        return wordnet.NOUN  # Default
    pos_str = pos_str.upper()
    if pos_str.startswith("V"):
        return wordnet.VERB
    elif pos_str.startswith("J"):
        return wordnet.ADJ
    elif pos_str.startswith("R"):
        return wordnet.ADV
    elif pos_str.startswith("N"):
        return wordnet.NOUN
    return wordnet.NOUN  # Fallback default


def get_sheet_stats(df: pd.DataFrame, passage_name: str) -> pd.DataFrame:
    sheet_data = {}
    sheet_data["PassageName"] = passage_name
    sheet_data["SyllableCount"] = df["SyllableID"].nunique()
    sheet_data["WordCount"] = df["WordID"].nunique()

    # Convenience column for word errors
    df["WordError"] = (
        (df["Error_InsertedWord"] == 1)
        | (df["Error_OmittedWord"] == 1)
        | (df["Error_WordStressError"] == 1)
    )

    # Calculate counts of inserted and omitted syllables without word errors
    sheet_data["InsertedSyllableWithoutWordErrorCount"] = len(
        df[(df["Error_InsertedSyllable"] == 1) & (df["WordError"] == 0)].index
    )
    sheet_data["OmittedSyllableWithoutWordErrorCount"] = len(
        df[(df["Error_OmittedSyllable"] == 1) & (df["WordError"] == 0)].index
    )

    sheet_data["WordSubstitutionCount"] = len(
        df[df["Outcome_WordSubstitution"] != 0].index
    )
    sheet_data["WordApproximationCount"] = len(
        df[df["Outcome_WordApproximation"] != 0].index
    )

    for mistake_type in ["Error", "Disfluency"]:
        mistake_cols = df.columns[df.columns.str.startswith(f"{mistake_type}_")]
        for col in mistake_cols:
            has_error = df[df[col] != 0]
            raw_count = len(has_error.index)
            # multiple errors in the same word are counted as the same error
            word_error_count = has_error.groupby("WordID").size().count()
            assert raw_count >= word_error_count

            sheet_data[f"{col}_RawCount"] = raw_count
            sheet_data[f"{col}_WordErrorCount"] = word_error_count

            # count unattempted, successful, and unsuccessful corrections
            no_correction_attempt_count = len(has_error[has_error[col] == 1].index)
            unsuccessful_correction_count = len(has_error[has_error[col] == 2].index)
            successful_correction_count = len(has_error[has_error[col] == 3].index)
            sheet_data[f"{col}_NoCorrectionAttemptCount"] = no_correction_attempt_count
            sheet_data[f"{col}_UnsuccessfulCorrectionCount"] = (
                unsuccessful_correction_count
            )
            sheet_data[f"{col}_SuccessfulCorrectionCount"] = successful_correction_count

    # Calculate counts of matched high / low errors and hesitations
    for error_type in ["high-error", "low-error", "hesitation"]:
        start_col = f"{error_type}-start-matched"
        end_col = f"{error_type}-end-matched"
        # Get the counts of matched high / low errors and hesitation start/endpoints
        sheet_data[f"{start_col}_Count"] = len(df[df[start_col] == 1].index)
        sheet_data[f"{end_col}_Count"] = len(df[df[end_col] == 1].index)
        # Get counts of full matches
        sheet_data[f"{error_type}-full-match_Count"] = len(
            df[(df[start_col] == 1) & (df[end_col] == 1)].index
        )
        # Get counts of partial matches
        sheet_data[f"{error_type}-start-match_Count"] = len(
            df[(df[start_col] == 1) & (df[end_col] == 0)].index
        )
        sheet_data[f"{error_type}-end-match_Count"] = len(
            df[(df[start_col] == 0) & (df[end_col] == 1)].index
        )
        # Get counts of no matches
        sheet_data[f"{error_type}-no-match_Count"] = len(
            df[(df[start_col] == 0) & (df[end_col] == 0)].index
        )

    # Calculate percentage of fully matched high / low errors and hesitations
    sheet_data["high-error-full-match_Percentage"] = 100 * (
        sheet_data["high-error-full-match_Count"]
        / max(len(df[~df["high-error-start"].isna()].index), 1)
    )
    sheet_data["low-error-full-match_Percentage"] = 100 * (
        sheet_data["low-error-full-match_Count"]
        / max(len(df[~df["low-error-start"].isna()].index), 1)
    )
    sheet_data["hesitation-full-match_Percentage"] = 100 * (
        sheet_data["hesitation-full-match_Count"]
        / max(len(df[~df["hesitation-start"].isna()].index), 1)
    )

    # Calculate percentage of partial matches

    # High error partial matches
    sheet_data["high-error-start-match_Percentage"] = 100 * (
        sheet_data["high-error-start-match_Count"]
        / max(len(df[~df["high-error-start"].isna()].index), 1)
    )
    sheet_data["high-error-end-match_Percentage"] = 100 * (
        sheet_data["high-error-end-match_Count"]
        / max(len(df[~df["high-error-end"].isna()].index), 1)
    )
    sheet_data["high-error-partial-match_Percentage"] = (
        sheet_data["high-error-start-match_Percentage"]
        + sheet_data["high-error-end-match_Percentage"]
    )
    # Low error partial matches
    sheet_data["low-error-start-match_Percentage"] = 100 * (
        sheet_data["low-error-start-match_Count"]
        / max(len(df[~df["low-error-start"].isna()].index), 1)
    )
    sheet_data["low-error-end-match_Percentage"] = 100 * (
        sheet_data["low-error-end-match_Count"]
        / max(len(df[~df["low-error-end"].isna()].index), 1)
    )
    sheet_data["low-error-partial-match_Percentage"] = (
        sheet_data["low-error-start-match_Percentage"]
        + sheet_data["low-error-end-match_Percentage"]
    )
    # Hesitation partial matches
    sheet_data["hesitation-start-match_Percentage"] = 100 * (
        sheet_data["hesitation-start-match_Count"]
        / max(len(df[~df["hesitation-start"].isna()].index), 1)
    )
    sheet_data["hesitation-end-match_Percentage"] = 100 * (
        sheet_data["hesitation-end-match_Count"]
        / max(len(df[~df["hesitation-end"].isna()].index), 1)
    )
    sheet_data["hesitation-partial-match_Percentage"] = (
        sheet_data["hesitation-start-match_Percentage"]
        + sheet_data["hesitation-end-match_Percentage"]
    )

    # Calculate percentage of no matches
    sheet_data["high-error-no-match_Percentage"] = 100 * (
        sheet_data["high-error-no-match_Count"]
        / max(len(df[~df["high-error-start"].isna()].index), 1)
    )
    sheet_data["low-error-no-match_Percentage"] = 100 * (
        sheet_data["low-error-no-match_Count"]
        / max(len(df[~df["low-error-start"].isna()].index), 1)
    )
    sheet_data["hesitation-no-match_Percentage"] = 100 * (
        sheet_data["hesitation-no-match_Count"]
        / max(len(df[~df["hesitation-start"].isna()].index), 1)
    )

    return pd.DataFrame([sheet_data])


def summarize_word_matches(scaffold_dir: str, output_file: str) -> None:
    wnl = WordNetLemmatizer()
    stemmer = LancasterStemmer()

    if os.path.exists(output_file):
        os.remove(output_file)

    # Summary statistics for number of direct matches, lemmatized matches, stemmed matches, and no matches
    word_freqs = load_word_frequencies()
    for scaffold in os.listdir(scaffold_dir):
        scaffold_path = os.path.join(scaffold_dir, scaffold)
        scaffold_df = pd.read_csv(scaffold_path)

        # Basic text normalization
        scaffold_df["cleaned_word"] = (
            scaffold_df["word"].str.lower().str.strip(string.punctuation)
        )
        # Standardize apostrophes
        scaffold_df["cleaned_word"] = scaffold_df["cleaned_word"].str.replace(
            "\u2018", "'"
        )
        scaffold_df["cleaned_word"] = scaffold_df["cleaned_word"].str.replace(
            "\u2019", "'"
        )

        # Identify hyphenated and apostrophe-containing words
        hyphenated_mask = scaffold_df["cleaned_word"].str.contains("-")
        apostrophe_mask = scaffold_df["cleaned_word"].str.contains("'")

        # Split and expand hyphenated words while preserving other columns
        hyphenated_rows = scaffold_df[hyphenated_mask].copy()
        if not hyphenated_rows.empty:
            hyphenated_split = hyphenated_rows["cleaned_word"].str.split("-")
            hyphenated_df = hyphenated_rows.loc[
                hyphenated_rows.index.repeat(hyphenated_split.str.len())
            ]
            hyphenated_df["word"] = [
                word for words in hyphenated_split for word in words
            ]

        # Split and expand apostrophe words while preserving other columns
        apostrophe_rows = scaffold_df[apostrophe_mask].copy()
        if not apostrophe_rows.empty:
            apostrophe_split = apostrophe_rows["cleaned_word"].str.split("'")
            apostrophe_df = apostrophe_rows.loc[
                apostrophe_rows.index.repeat(apostrophe_split.str.len())
            ]
            apostrophe_df["word"] = [
                word for words in apostrophe_split for word in words
            ]

        # Keep words that had neither hyphens nor apostrophes
        clean_df = scaffold_df[~(hyphenated_mask | apostrophe_mask)].copy()
        clean_df["word"] = clean_df["cleaned_word"]

        # Combine everything
        final_df = pd.concat(
            [clean_df, hyphenated_df, apostrophe_df], ignore_index=True
        )
        # Strip punctuation again, just in case
        final_df["word"] = final_df["word"].str.strip(string.punctuation)

        # Get direct matches
        direct_match = final_df[final_df["word"].isin(word_freqs["word"])]
        final_df = final_df[~final_df["word"].isin(word_freqs["word"])]

        # Get lemmatized matches
        lemmatized_words = final_df.apply(
            lambda row: wnl.lemmatize(row["word"], get_wordnet_pos(row["word-pos"])),
            axis=1,
        )
        lemmatized_mask = lemmatized_words.isin(word_freqs["word"])
        lemmatized_match = final_df[lemmatized_mask]
        final_df = final_df[~lemmatized_mask]

        # Get stemmed matches
        stemmed_words = final_df["word"].apply(stemmer.stem)
        stemmed_mask = stemmed_words.isin(word_freqs["word"])
        stemmed_match = final_df[stemmed_mask]
        final_df = final_df[~stemmed_mask]

        # Output summary statistics for number of direct/lemmatized/stemmed/no matches to a file
        with open(output_file, "a") as f:
            f.write(f"Scaffold: {scaffold}\n")
            f.write(f"Direct matches: {len(direct_match)}\n")
            f.write(f"Lemmatized matches: {len(lemmatized_match)}\n")
            f.write(f"Stemmed matches: {len(stemmed_match)}\n")

            # Build no-matches string
            no_match_entries = []
            for _, row in final_df.iterrows():
                entry = f"{row['word']} ({row['word-pos']})"
                no_match_entries.append(entry)

            f.write(f"No matches: {len(final_df)} ({', '.join(no_match_entries)})\n")
            f.write("\n")
