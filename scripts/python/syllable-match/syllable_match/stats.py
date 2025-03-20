import os

import pandas as pd


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
