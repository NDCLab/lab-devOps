import pandas as pd
import sys
from os.path import basename, normpath, join, isdir
from os import listdir, walk
import pathlib
import re

# list audio-vid data
audivid = ["zoom", "audio", "video", "audacity"]
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
        # also map Sp. surveys to same column name in central tracker if completed
        surv_match = re.search('^([a-zA-Z]+)_([a-zA-Z]_)?(s[0-9]+_r[0-9]+_e[0-9]+)$', row["variable"])
        if surv_match and "questionnaire" in row["description"]:
            surv_version = '' if not surv_match.group(2) else surv_match.group(2)
            surv_esp = surv_match.group(1) + 'es_' + surv_version + surv_match.group(3)
            cols[surv_esp + completed] = row["variable"]
    return cols
        

if __name__ == "__main__":
    checked_path = sys.argv[1]
    data_types = sys.argv[2]
    dataset = sys.argv[3]
    redcap_path = sys.argv[4]
    session = sys.argv[5]
    tasks = sys.argv[6]
    child = sys.argv[7]
    parental_reports = sys.argv[8]
    if session == "none":
      session = ""
      ses_tag = ""
    else:
      ses_tag = "_" + session
    if parental_reports == "none":
      parental_reports = []
    else:
      parental_reports = parental_reports.split(',')

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
        rc_df = pd.read_csv(redcap_path, index_col="record_id")
        # If hallMonitor passes "redcap" arg, data exists and passed checks 
        vals = pd.read_csv(redcap_path, header=None, nrows=1).iloc[0,:].value_counts()
        # Exit if duplicate column names in redcap
        if any(vals.values != 1):
            dupes = []
            for rc_col in vals.keys():
                if vals[rc_col] > 1:
                    dupes.append(rc_col)
            sys.exit('Duplicate columns found in redcap: ' + ', '.join(dupes) + '. Exiting')
        for index, row in rc_df.iterrows():
            id = int(row.name)
            if child == 'true':
                if re.search('30[089](\d{4})', str(id)):
                    child_id = '300' + re.search('30[089](\d{4})', str(id)).group(1)
                    child_id = int(child_id)
                else:
                    print(str(id), "doesn't match expected child or parent id format of \"30{1,8, or 9}XXXX\", skipping")
                    continue
            else:
                child_id = id
            if child_id not in tracker_df.index:
                print(child_id, "missing in tracker file, skipping")
                continue 
            subjects.append(child_id)
            # check for part. consent
            #if rc_df.loc[id, "consent_yn"]==1:
            #    tracker_df.loc[id, "consent" + ses_tag] = "1"
            #    subjects.append(id)
            #else:
            #    print("consent missing for " + str(id) + ", skipping")
            #    continue
            for key, value in redcheck_columns.items():
######################################################## temporary solution to identifying parental self-reports ######################
                if 'parent' in redcap_path and value.startswith(tuple(parental_reports)):
                    surv_re = re.search('^([a-zA-Z]+)_([a-zA-Z]_)?(s[0-9]+_r[0-9]+_e[0-9]+)$', value)
                    surv_version = '' if not surv_re.group(2) else surv_re.group(2)
                    value = surv_re.group(1) + surv_version + '_parent_' + surv_re.group(3)
                    # adds "parent" to central tracker column name
########################################################################################
                try:
                    val = rc_df.loc[id, key]
                    try:
                        if tracker_df.loc[child_id, value] == "1":
                            # if value already set continue
                            continue
                        else:
                            tracker_df.loc[child_id, value] = "1" if val == 2 else "0"
                    except:
                        tracker_df.loc[child_id, value] = "1" if val == 2 else "0"
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
        tasks = tasks.split(",")
        # TODO: Pipeline checks data already processed. 
        #for dir in (set(data_types) & set(pavpsy)):
            #for (dirpath, dirnames, filenames) in walk(checked_path + '/' + dir):
            #for (dirpath, dirnames, filenames) in walk(checked_path):
                #if dir in dirpath:
                #path = pathlib.PurePath(dirpath)
                #if path.name == dir:
                        # TODO: need better implementation.
                        # Need to apply better engineering principles here
                        #if "sub" in path.name:
                        #if "sub" in dirpath:
                        #del dir_id
                        #for subdir in dirpath.split('/'):
                        #    if "sub-" in subdir:
                        #        dir_id = int(subdir[4:])
                        #        break
                            #dir_id = int(path.name[4:])
                                #if dir_id not in ids:
                                    #continue
                            #else:
                            #    continue
                        #if 'dir_id' in locals():
                        #    for task in tasks:
                        #        if task in ''.join(filenames):
                        #            tracker_df.loc[dir_id, task] = "1"
                        #        else: 
                        #            tracker_df.loc[dir_id, task] = "0"
                        #else:
                        #    continue

        for data in (set(data_types) & set(pavpsy)):
            for subdir in listdir(checked_path):
                if "sub-" in subdir:
                    dir_id = int(subdir[4:])
                else:
                    continue
                for task in tasks:
                    try:
                        if task in ''.join(listdir(join(checked_path,subdir,session,data))):
                            tracker_df.loc[dir_id, task] = "1"
                        else:
                            tracker_df.loc[dir_id, task] = "0"
                    except:
                        tracker_df.loc[dir_id, task] = "0"

        tracker_df.to_csv(data_tracker_file)
    
    if bool(set(data_types) & set(audivid)):
        # check for audivid data?
        for data_type in list(set(data_types) & set(audivid)):
            for sub in subjects:
                dir_id = sub
                if isdir(join(checked_path,'sub-'+str(dir_id),session,data_type)):
                    for f in listdir(join(checked_path,'sub-'+str(dir_id),session,data_type)):
                        audi_vid_re = re.match('^.*_(audio|video|zoom|audacity)_(s[0-9]+_r[0-9]+_e[0-9]+)\.zip\.gpg$',f)
                        if audi_vid_re:
                            tracker_df.loc[dir_id, audi_vid_re.group(1) + "Data_" + audi_vid_re.group(2)] = "1"


                #collabel = data_type + "Data" + ses_tag
                #tracker_df.loc[dir_id, collabel] = "1" if dir_id in ids else "0"
    
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
                break
            if "egiData" in row["variable"]:
                egi_present = True
                break
        for sub in subjects:
            dir_id = sub
            # TODO: Need better implementation here
            if "eeg" in data_types:
                if bv_present:
                    if isdir(join(checked_path,'sub-'+str(dir_id),session,'eeg')):
                        for f in listdir(join(checked_path,'sub-'+str(dir_id),session,'eeg')):
                            eeg_re = re.match('^.*_(s[0-9]+_r[0-9]+_e[0-9]+)\.eeg$',f)
                            if eeg_re:
                                tracker_df.loc[dir_id, "bvData_" + eeg_re.group(1)] = "1"
                if egi_present:
                    if isdir(join(checked_path,'sub-'+str(dir_id),session,'eeg')):
                        for f in listdir(join(checked_path,'sub-'+str(dir_id),session,'eeg')):
                            eeg_re = re.match('^.*_(s[0-9]+_r[0-9]+_e[0-9]+)\.mff$',f)
                            if eeg_re:
                                tracker_df.loc[dir_id, "egiData_" + eeg_re.group(1)] = "1"
            if "digi" in data_types:
                if isdir(join(checked_path,'sub-'+str(dir_id),session,'digi')):
                    for f in listdir(join(checked_path,'sub-'+str(dir_id),session,'digi')):
                        digi_re = re.match('^.*_(s[0-9]+_r[0-9]+_e[0-9]+)\.zip\.gpg$',f)
                        if digi_re:
                            tracker_df.loc[dir_id, "digiData_" + digi_re.group(1)] = "1"


            # make remaining empty values equal to 0
            # tracker_df[collabel] = tracker_df[collabel].fillna("0")
        tracker_df.to_csv(data_tracker_file)
    print("Success: {} data tracker updated.".format(', '.join(data_types)))
