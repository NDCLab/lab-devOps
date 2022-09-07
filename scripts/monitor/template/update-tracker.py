import pandas as pd
import sys
from os.path import basename, normpath
from os import walk

# list audio-vid data
audivid = ["zoom", "audio", "video", "digi"]
# list pav-psy data
pavpsy = ["pavlovia", "psychopy"]
# list eeg systems
eeg = ["bv", "egi"]

# rhs: data, lhs: tracker
# TODO: utilize data dictionary
redcheck_columns = {}

if __name__ == "__main__":
    file_path = sys.argv[1]
    data_type = sys.argv[2]
    dataset = sys.argv[3]
    # extract project path from dataset
    proj_name = basename(normpath(dataset))

    data_tracker_file = "{}data-monitoring/central-tracker_{}.csv".format(dataset, proj_name)
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

    if data_type in pavpsy or data_type in audivid or data_type in eeg:
        
        for (_, dirnames, _) in walk(file_path):
            if len(dirnames) == 0:
                continue
            
            try:
                dir_ids = [int(sub[4:]) for sub in dirnames]
            except:
                print(file_path)
            ids = [id for id in tracker_df.index]
            collabel = data_type + "Data_s1_r1_e1"
            for id in ids:
                tracker_df.loc[id, collabel] = "1" if id in dir_ids else "0"
    
            # make remaining empty values equal to 0
            tracker_df[collabel] = tracker_df[collabel].fillna("0")
            tracker_df.to_csv(data_tracker_file)
            print("Success: {} data tracker updated.".format(data_type))