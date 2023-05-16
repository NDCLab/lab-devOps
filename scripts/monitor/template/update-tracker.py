import pandas as pd
import sys
from os.path import basename, normpath, join, isdir
from os import listdir, walk
import pathlib
import re

# list audio-vid data
audivid = ["zoom", "audio", "video"]
# list pav-psy data
pavpsy = ["pavlovia", "psychopy"]
# list eeg systems
eeg = ["eeg", "digi"]
# list hallMonitor key
provenance = "code-hallMonitor"

# TODO: Make this occur once during construction
def get_redcap_columns(datadict):
    completed = "_complete"
    df_dd = pd.read_csv(datadict)

    # filter for prov
    df_dd = df_dd.loc[df_dd['provenance'] == provenance]

    cols = {}
    for _, row in df_dd.iterrows():
        # skip redcap static
        if "consent" in row["variable"] or "redcap" in row["variable"]:
            continue
        # skip other data checks
        if "audio" in row["variable"] or "bv" in row["variable"]:
            continue
        cols[row["variable"] + completed] = row["variable"]

    return cols
        

if __name__ == "__main__":
    checked_path = sys.argv[1]
    data_types = sys.argv[2]
    dataset = sys.argv[3]
    redcap_path = sys.argv[4]

    data_types = data_types.split(',')
    DATA_DICT = dataset + "/data-monitoring/data-dictionary/central-tracker_datadict.csv"
    redcheck_columns = get_redcap_columns(DATA_DICT)
    
    # extract project path from dataset
    proj_name = basename(normpath(dataset))

    data_tracker_file = "{}/data-monitoring/central-tracker_{}.csv".format(dataset, proj_name)
    tracker_df = pd.read_csv(data_tracker_file, index_col="id")
    ids = [id for id in tracker_df.index]
    subjects = []
    
    if "redcap" in data_types:  
        file_df = pd.read_csv(redcap_path, index_col="record_id")
        # If hallMonitor passes "redcap" arg, data exists and passed checks 
        for index, row in file_df.iterrows():
            id = int(row.name)
            if id not in tracker_df.index:
                print(id, "missing in tracker file, skipping")
                continue 
            # check for part. consent
            if file_df.loc[id, "consent_yn"]==1:
                tracker_df.loc[id, "consent_s1_r1_e1"] = "1"
                subjects.append(id)
            for key, value in redcheck_columns.items():
                try:
                    val = file_df.loc[id, key]
                    tracker_df.loc[id, value] = "1" if val == 2 else "0"	 
                except Exception as e_msg:
                    continue
        # make remaining empty values equal to 0
        # tracker_df["redcapData_s1_r1_e1"] = tracker_df["redcapData_s1_r1_e1"].fillna("0")
        # for measures as well
        # for key in redcheck_columns.keys():
        #    tracker_df[redcheck_columns[key]] = tracker_df[redcheck_columns[key]].fillna("NA") 
        tracker_df.to_csv(data_tracker_file)
    else:
        sys.exit('Can\'t find redcap in ' + dataset +'/sourcedata/raw, exiting ')

    if bool(set(data_types) & set(pavpsy)):
        tasks = sys.argv[5]
        tasks = tasks.split(",")
        # TODO: Pipeline checks data already processed. 
        for dir in (set(data_types) & set(pavpsy)):
            for (dirpath, dirnames, filenames) in walk(checked_path + dir):
                path = pathlib.PurePath(dirpath)
    
                # TODO: need better implementation.
                # Need to apply better engineering principles here
                if "sub" in path.name:
                    dir_id = int(path.name[4:])
                    if dir_id not in ids:
                        continue
                else:
                    continue
            
                for task in tasks:
                    if task in ''.join(filenames):
                        tracker_df.loc[dir_id, task] = "1"
                    else: 
                        tracker_df.loc[dir_id, task] = "0"

            tracker_df.to_csv(data_tracker_file)
    
    if bool(set(data_types) & set(audivid)):
        for data_type in list(set(data_types) & set(audivid)):
            for sub in subjects:
                dir_id = sub
            
                collabel = data_type + "Data_s1_r1_e1"
                tracker_df.loc[dir_id, collabel] = "1" if dir_id in ids else "0"
    
                # make remaining empty values equal to 0
                # tracker_df[collabel] = tracker_df[collabel].fillna("0")
        tracker_df.to_csv(data_tracker_file)
    
    if bool(set(data_types) & set(eeg)):
        # check initial csv for either Brainvision or EGI column (shouldn't have both)
        df_dd = pd.read_csv(DATA_DICT)
        bv_present = False; egi_present = False
        for _, row in df_dd.iterrows():
            if "bvData" in row["variable"]:
                bv_present = True
            if "egiData" in row["variable"]:
                egi_present = True
        for sub in subjects:
            dir_id = sub
            # TODO: Need better implementation here
            if "eeg" in data_types:
                if bv_present:
                    tracker_df.loc[dir_id, "bvData_s1_r1_e1"] = "0"
                    if isdir(join(checked_path+'bidsish','sub-'+str(dir_id),'eeg')):
                        for f in listdir(join(checked_path+'bidsish','sub-'+str(dir_id),'eeg')):
                            if re.match('^.*eeg$',f):
                                tracker_df.loc[dir_id, "bvData_s1_r1_e1"] = "1"
                if egi_present:
                    tracker_df.loc[dir_id, "egiData_s1_r1_e1"] = "0"
                    if isdir(join(checked_path+'bidsish','sub-'+str(dir_id),'eeg')):
                        for f in listdir(join(checked_path+'bidsish','sub-'+str(dir_id),'eeg')):
                            if re.match('^.*mff$',f):
                                tracker_df.loc[dir_id, "egiData_s1_r1_e1"] = "1"
            if "digi" in data_types:
                tracker_df.loc[dir_id, "digiData_s1_r1_e1"] = "0"
                if isdir(join(checked_path+'bidsish','sub-'+str(dir_id),'digi')):
                    for f in listdir(join(checked_path+'bidsish','sub-'+str(dir_id),'digi')):
                        if re.match('^.*gpg$',f):
                            tracker_df.loc[dir_id, "digiData_s1_r1_e1"] = "1"


            # make remaining empty values equal to 0
            # tracker_df[collabel] = tracker_df[collabel].fillna("0")
        tracker_df.to_csv(data_tracker_file)
    print("Success: {} data tracker updated.".format(', '.join(data_types)))
