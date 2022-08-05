import pandas as pd
import sys
import math
import os

# TODO: Change to path agnostic implement
data_tracker_file = "/home/data/NDClab/datasets/test-readAloud-v4/data-monitoring/central-tracker_readAloud-valence.csv"

# rhs: data, lhs: tracker
redcheck_columns = {
    "demo_b_s1_r1_e1_timestamp" : "demo_b_s1_r1_e1", 
    "bfne_b_s1_r1_e1_timestamp" : "bfne_b_s1_r1_e1", 
    "aq10_s1_r1_e1_timestamp" : "aq10_s1_r1_e1", 
    "bmis_s1_r1_e1_timestamp" : "bmis_s1_r1_e1", 
    "phq8_s1_r1_e1_timestamp" : "phq8_s1_r1_e1",
    "panasnow_s1_r1_e1_timestamp": "panasnow_s1_r1_e1",
    "scaared_b_s1_r1_e1_timestamp" : "scaared_b_s1_r1_e1", 
    "erq_s1_r1_e1_timestamp" : "erq_s1_r1_e1", 
    "sias6sps6_b_s1_r1_e1_timestamp" : "sias6sps6_b_s1_r1_e1", 
    "ari_s1_r1_e1_timestamp" : "ari_s1_r1_e1",
    "stai5_s1_r1_e1_timestamp": "stai5_s1_r1_e1"}

preprocess_cols = ["readAloudChallenge_s1_r1_e1", "ldt_s1_r1_e1", "dccs_s1_r1_e1"]

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
            tracker_df.loc[id, "redcapData_s1_r1_e1"] = "1"
            # check for part. consent
            tracker_df.loc[id, "consent_s1_r1_e1"] = "1" if file_df.loc[id, "consent_yn"]==1 else "0"
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
                sys.exit()
            ids = [int(id) for id in tracker_df.index]
            # refactor to accept only subject ids, and not dirnames
            for id in ids:
                tracker_df.loc[id, "pavloviaData_s1_r1_e1"] = "1"
                # update preprocess pav data
                for col in preprocess_cols:
                    tracker_df.loc[id, col] = "10"
            # make remaining empty values equal to 0
            tracker_df["pavloviaData_s1_r1_e1"] = tracker_df["pavloviaData_s1_r1_e1"].fillna("0")
            for col in preprocess_cols:
                    tracker_df[col] = tracker_df[col].fillna("0")
            tracker_df.to_csv(data_tracker_file)
            print("Success: pavlovia data tracker updated.")
    if data_type == "zoom":
        for (_, dirnames, _) in os.walk(file_path):
            if len(dirnames) == 0:
                sys.exit()
            ids = [int(id) for id in tracker_df.index]
            for id in ids:
                tracker_df.loc[id, "zoomData_s1_r1_e1"] = "1"
            tracker_df["zoomData_s1_r1_e1"] = tracker_df["zoomData_s1_r1_e1"].fillna("0")
            tracker_df.to_csv(data_tracker_file)
            print("Success: zoom data tracker updated.")

     
                            