import pandas as pd
import argparse as argparse
def only_white_res(df, white_col):
    df[white_col] = df[white_col].fillna(0)
    only_white_df = df[df[white_col] == 1]
    only_white_count  = 0
    for i,row in only_white_df.iterrows():
        # make sure the sum of the row is 1
        if row.sum() > 1:
            #print(f"Row {i} has more than one response: ")
            # print the columns that have a response of 1
            for col in only_white_df.columns:
                if row[col] == 1:
                    #print(col)
                    pass
        else:
            only_white_count += 1
    #print(f"Non-white response count: {len(only_white_df) - only_white_count}")
    return only_white_count


def get_race_count(df, col):
    df[col] = df[col].fillna(0)
    # get the total count of responses for this column
    # print(f"Total responses for column {col}: {total_responses}")
    # get value counts for each response
    value_counts = df[col].value_counts()
    #print(value_counts)
    if 1 in value_counts:
        total_responses = value_counts[1]
    else:
        total_responses = 0
    return total_responses

    
    
def compute_rmr(df_path):
    old_df = pd.read_csv(df_path)

    child_race_col = "demo_d_race_s1_r1_e1"
    child_race_col_es = "demoes_d_race_s1_r1_e1"
    hispanic_col = "demo_d_latinx_s1_r1_e1"
    hispanic_col_es = "demoes_d_latinx_s1_r1_e1"
    complete_col = "demo_d_s1_r1_e1_complete"
    complete_col_es = "demoes_d_s1_r1_e1_complete"
    df = old_df.copy()[(old_df[complete_col] == 2) | (old_df[complete_col_es ] == 2)]
    race_df = df.copy()[[col for col in df.columns if col.startswith(child_race_col) or col.startswith(child_race_col_es)]]
    white_col = "demo_d_race_s1_r1_e1___10"
    white_col_es = "demoes_d_race_s1_r1_e1___10"
    only_white_count1 = only_white_res(race_df, white_col)
    only_white_count2 = only_white_res(race_df, white_col_es)
    only_white_count = only_white_count1 + only_white_count2
    total_count = len(df)
    if hispanic_col  in df.columns:
        hispanic_count = get_race_count(df, hispanic_col)
        hispanic_count2 = get_race_count(df, hispanic_col_es)
        hispanic_count = hispanic_count + hispanic_count2
        total_count = len(df)
        summary = "RMR Report Summary"
    summary += "\n-------------------\n"
    # print total Count
    summary += f"Total responses: {total_count}"
    minority_count = total_count - only_white_count
    summary += f"\n Minority Response: {minority_count}"
    summary += f"\n Hispanic Response: {hispanic_count}"

    print(summary)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("df_path", help="Path to the CSV file containing the data for IQS parent")
    args = parser.parse_args()
    if args.df_path is None:
        print("Please provide a path to the CSV file containing the data")
            

    compute_rmr(args.df_path)