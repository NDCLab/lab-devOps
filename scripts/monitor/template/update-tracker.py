import pandas as pd
import sys
import math
import os

# TODO: Change to path agnostic implement
data_tracker_file = "/home/data/NDClab/datasets/test-readAloud-v4/data-monitoring/central-tracker_readAloud-valence.csv"

# rhs: data, lhs: tracker
redcheck_columns = {}

if __name__ == "__main__":
    file_path = sys.argv[1]
    data_type = sys.argv[2]
    tracker_df = pd.read_csv(data_tracker_file, index_col="id")
    
    if data_type == "redcap":  
        file_df = pd.read_csv(file_path, index_col="record_id")
        # If hallMonitor passes "redcap" arg, data exists and passed checks 
        for index, row in file_df.iterrows():
            id = row.name
            if id not in tracker_df.index:
                continue 
            # check for part. consent
            tracker_df.loc[id, "consent_s1_r1_e1"] = "1" if file_df.loc[id, "consent_yn"]==1 else "0"
            tracker_df.loc[id, "redcapData_s1_r1_e1"] = tracker_df.loc[id, "consent_s1_r1_e1"]
            if id not in tracker_df.index:
                print(id, "missing in tracker file, skipping")
                continue
            for key in redcheck_columns.keys():
                try:
                    val = file_df.loc[id, key]
                    tracker_df.loc[id, redcheck_columns[key]] = "1" if isinstance(val, str) else "0"	 
                except Exception as e_msg:
                    tracker_df.loc[id, redcheck_columns[key]] = "0"
        # make remaining empty values equal to 0
        tracker_df["redcapData_s1_r1_e1"] = tracker_df["redcapData_s1_r1_e1"].fillna("0")
        # for measures as well
        for key in redcheck_columns.keys():
            tracker_df[redcheck_columns[key]] = tracker_df[redcheck_columns[key]].fillna("NA") 
        tracker_df.to_csv(data_tracker_file)
        print("Success: redcap data tracker updated.")
    if data_type == "pavlovia":
        # If hallMonitor passes "pavlovia" arg, data exists and passed checks
        for (_, dirnames, _) in os.walk(file_path):
            if len(dirnames) == 0:
                continue
            dir_ids = [int(sub[4:]) for sub in dirnames]
            ids = [id for id in tracker_df.index]
            for id in ids:
                tracker_df.loc[id, "pavloviaData_s1_r1_e1"] = "1" if id in dir_ids else "0"
            # make remaining empty values equal to 0
            tracker_df["pavloviaData_s1_r1_e1"] = tracker_df["pavloviaData_s1_r1_e1"].fillna("0")
            tracker_df.to_csv(data_tracker_file)
            print("Success: pavlovia data tracker updated.")
    if data_type == "zoom":
        for (_, dirnames, _) in os.walk(file_path):
            if len(dirnames) == 0:
                sys.exit()
            dir_ids = [sub[4:] for sub in dirnames]
            ids = [id for id in tracker_df.index]
            for id in ids:
                tracker_df.loc[id, "zoomData_s1_r1_e1"] = "1" if id in dir_ids else "0"
            tracker_df["zoomData_s1_r1_e1"] = tracker_df["zoomData_s1_r1_e1"].fillna("0")
            tracker_df.to_csv(data_tracker_file)
            print("Success: zoom data tracker updated.")

     
                            