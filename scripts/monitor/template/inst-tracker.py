import pandas as pd
import sys
import math
from os.path import basename, normpath

check_columns = []

if __name__ == "__main__":
    file = sys.argv[1]
    dataset = sys.argv[2]

    proj_name = basename(normpath(dataset))

    data_tracker_file = "{}/data-monitoring/central-tracker_{}.csv".format(dataset, proj_name)
    tracker_df = pd.read_csv(data_tracker_file, index_col="id")
    
    file_df = pd.read_csv(file, index_col="record_id")
    tracker_df = pd.read_csv(data_tracker_file, index_col="id")

    for index, row in file_df.iterrows():
        id = row.name
        # check if id exists in tracker
        if id not in tracker_df.index:
            print(id, "missing in tracker file, skipping")
            continue
        for key in check_columns:
            try:
                val = file_df.loc[id, key]
                if tracker_df.loc[id, key] ==  1 or tracker_df.loc[id, key] == 0:
                    continue
                tracker_df.loc[id, key] = 0 if math.isnan(val) else 1
            except Exception as e_msg:
                tracker_df.loc[id, key] = 0

    tracker_df.to_csv(data_tracker_file)
    print("Success: data tracker updated.")
