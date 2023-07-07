import pandas as pd
import sys
from os.path import basename, normpath, join, isdir
from os import listdir, walk
import pathlib
import re
import math

# list audio-vid data
audivid = ["zoom", "audio", "video", "audacity"]
# list pav-psy data
pavpsy = ["pavlovia", "psychopy"]
# list eeg systems
eeg = ["eeg", "digi"]
# list hallMonitor key
provenance = ["code-hallMonitor", "code-instruments"]
completed = "_complete"

# TODO: Make this occur once during construction
def get_redcap_columns(datadict_df):
    df = datadict_df

    # filter for prov
    df = df.loc[df['provenance'].isin(provenance)]

    cols = {}
    for _, row in df.iterrows():
        # skip redcap static
        if "redcap" in row["variable"]:
            continue
        # skip other data checks
        if "audacity" in row["variable"] or "bv" in row["variable"]:
            continue
        cols[row["variable"] + completed] = row["variable"]
        # also map Sp. surveys to same column name in central tracker if completed
        surv_match = re.match('^([a-zA-Z0-9\-]+)(_[a-z])?(_scrd[a-zA-Z]+)?(_[a-zA-Z]{2,})?(_s[0-9]+_r[0-9]+_e[0-9]+)$', row["variable"])
        if surv_match and "redcap_data" in row["description"]:
            surv_version = '' if not surv_match.group(2) else surv_match.group(2)
            scrd_str = '' if not surv_match.group(3) else surv_match.group(3)
            multiple_report_tag = '' if not surv_match.group(4) else surv_match.group(4)
            surv_esp = surv_match.group(1) + 'es' + surv_version + scrd_str + multiple_report_tag + surv_match.group(5)
            cols[surv_esp + completed] = row["variable"]
    cols["consentes_complete"] = "consent" # Redcap col name is consent_es_complete not consentes_complete
    return cols

def get_multiple_reports_tags(datadict_df):
    # identical surveys with multiple reports (eg from both child and parent) should have a tag (<surv_name>_"parent"_s1_r1_e1) in var name in datadict
    df = datadict_df
    names_list = []
    for _, row in df.iterrows():
        surv_match = re.match('^([a-zA-Z0-9\-]+)(_[a-z])?(_scrd[a-zA-Z]+)?(_[a-zA-Z]{2,})?(_s[0-9]+_r[0-9]+_e[0-9]+)$', row.variable)
        if surv_match and surv_match.group(4) and surv_match.group(4)[1:] not in names_list:
            names_list.append(surv_match.group(4)[1:])
    return names_list

if __name__ == "__main__":
    checked_path = sys.argv[1]
    data_types = sys.argv[2]
    dataset = sys.argv[3]
    redcaps = sys.argv[4]
    session = sys.argv[5]
    tasks = sys.argv[6]
    child = sys.argv[7]

    redcaps = redcaps.split(',')
    if session == "none":
      session = ""
      ses_tag = ""
    else:
      ses_tag = "_" + session

    data_types = data_types.split(',')
    DATA_DICT = dataset + "/data-monitoring/data-dictionary/central-tracker_datadict.csv"
    df_dd = pd.read_csv(DATA_DICT)
    redcheck_columns = get_redcap_columns(df_dd)
    multiple_reports_tags = get_multiple_reports_tags(df_dd)
    
    # extract project path from dataset
    proj_name = basename(normpath(dataset))

    data_tracker_file = "{}/data-monitoring/central-tracker_{}.csv".format(dataset, proj_name)
    tracker_df = pd.read_csv(data_tracker_file, index_col="id")
    ids = [id for id in tracker_df.index]
    subjects = []

    all_redcap_columns = [] # list of all redcap columns whose names should be mirrored in central tracker
    
    if "redcap" in data_types and redcaps[0] != "none":
        allowed_duplicate_columns = []
        for redcap_path in redcaps:
            # for bbsRA REDcap get thrive IDs from 'bbsratrk_acthrive_s1_r1_e1' column
            if 'ThrivebbsRA' in redcap_path:
                for column in pd.read_csv(redcap_path).columns:
                    if column.startswith('bbsratrk_acthrive'):
                        rc_df = pd.read_csv(redcap_path, index_col=column)
                        break
            else:
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
                if (isinstance(index, float) or isinstance(index, int)) and not math.isnan(index):
                    id = int(row.name)
                else:
                    print("skipping nan value in ", str(redcap_path), ": ", str(index))
                    continue
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
                if child_id not in subjects:
                    subjects.append(child_id)
                for key, value in redcheck_columns.items():
                    for tag in multiple_reports_tags:
                        surv_re = re.match('^([a-zA-Z0-9\-]+)(_[a-z])?(_scrd[a-zA-Z]+)?(_[a-zA-Z]{2,})?(_s[0-9]+_r[0-9]+_e[0-9]+)$', value)
                        if tag in redcap_path and surv_re and surv_re.group(4) == '_' + tag:
                            surv_version = '' if not surv_re.group(2) else surv_re.group(2)
                            scrd_str = '' if not surv_re.group(3) else surv_re.group(3)
                            key = surv_re.group(1) + surv_version + scrd_str + surv_re.group(5) + completed
                            allowed_duplicate_columns.append(key)
                    # adds "parent" to redcap column name in central tracker

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

                for session_type in ['bbs', 'iqs']:
                    if session_type + 'parent' in redcap_path:
                        for key, value in row.items():
                            if key.startswith(session_type + 'paid_lang'):
                                lang_re = re.match('^' + session_type + 'paid_lang.*(s[0-9]+_r[0-9]+(_e[0-9]+)?)', key)
                                if lang_re:
                                    sess = lang_re.group(1)
                                    tracker_df.loc[child_id, 'plang' + session_type + '_' + sess] = str(value) # 1 for english 2 for sp?
                        parentid_re = re.match('30([089])\d{4}', str(row.name))
                        if parentid_re and 'sess' in locals():
                            if parentid_re.group(1) == '8':
                                tracker_df.loc[child_id, 'pidentity' + session_type + '_' + sess] = "1"
                            elif parentid_re.group(1) == '9':
                                tracker_df.loc[child_id, 'pidentity' + session_type + '_' + sess] = "2" # 1 for primary parent, 2 for secondary?

            duplicate_cols = []
            for col, _ in tracker_df.iteritems():
                if re.match('^.*\.[0-9]+$', col):
                    duplicate_cols.append(col)
            tracker_df.drop(columns=duplicate_cols, inplace=True)
            tracker_df.to_csv(data_tracker_file)

            for col in rc_df.columns:
                if col.endswith(completed):
                    all_redcap_columns.append(col)

        all_duplicate_cols = []
        for col in all_redcap_columns:
            if all_redcap_columns.count(col) > 1 and col not in allowed_duplicate_columns:
                all_duplicate_cols.append(col)
        if len(all_duplicate_cols) > 0:
            sys.exit("Duplicate columns were found across Redcaps: ",", ".join(all_duplicate_cols),", Exiting.")
    else:
        print('Can\'t find redcaps in ' + dataset + '/sourcedata/raw/redcap, skipping ')

    if bool(set(data_types) & set(pavpsy)):
        tasks = tasks.split(",")
        # TODO: Pipeline checks data already processed. 

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
        for data_type in list(set(data_types) & set(audivid)):
            for sub in subjects:
                dir_id = sub
                if isdir(join(checked_path,'sub-'+str(dir_id),session,data_type)):
                    for f in listdir(join(checked_path,'sub-'+str(dir_id),session,data_type)):
                        audi_vid_re = re.match('^.*_(audio|video|zoom|audacity)_(s[0-9]+_r[0-9]+_e[0-9]+)\.zip\.gpg$',f)
                        if audi_vid_re:
                            if audi_vid_re.group(1) == 'zoom' or audi_vid_re.group(1) == 'video':
                                data_modality = 'zoom'
                            elif audi_vid_re.group(1) == 'audacity' or audi_vid_re.group(1) == 'audio':
                                data_modality = 'audacity'
                            tracker_df.loc[dir_id, data_modality + "Data_" + audi_vid_re.group(2)] = "1"


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
