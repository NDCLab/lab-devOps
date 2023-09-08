import pandas as pd
import sys
from os.path import basename, normpath, join, isdir, isfile, splitext
from os import listdir, walk
import pathlib
import re
import math
import datetime

# list hallMonitor key
provenance = ["code-hallMonitor", "code-instruments"]
completed = "_complete"

class c:
    RED = '\033[31m'
    GREEN = '\033[32m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# TODO: Make this occur once during construction
def get_redcap_columns(datadict_df):
    df = datadict_df

    # filter for prov
    df = df.loc[df['provenance'].isin(provenance)]

    cols = {}
    for _, row in df.iterrows():
        # skip redcap static
        if row["variable"].startswith("consent") or row["variable"].startswith("assent"):
            cols[row["variable"] + completed] = row["variable"]
            cols[row["variable"] + "es" + completed] = row["variable"]
            continue
        allowed_suffixes = row["allowedSuffix"].split(", ")
        for ses_tag in allowed_suffixes:
            cols[row["variable"] + "_" + ses_tag + completed] = row["variable"] + "_" + ses_tag
            # also map Sp. surveys to same column name in central tracker if completed
            surv_match = re.match('^([a-zA-Z0-9\-]+)(_[a-z])?(_scrd[a-zA-Z]+)?(_[a-zA-Z]{2,})?$', row["variable"])
            if surv_match and "redcap_data" in row["description"]:
                surv_version = '' if not surv_match.group(2) else surv_match.group(2)
                scrd_str = '' if not surv_match.group(3) else surv_match.group(3)
                multiple_report_tag = '' if not surv_match.group(4) else surv_match.group(4)
                surv_esp = surv_match.group(1) + 'es' + surv_version + scrd_str + multiple_report_tag + ses_tag
                cols[surv_esp + completed] = row["variable"]
    return cols

def get_multiple_reports_tags(datadict_df):
    # identical surveys with multiple reports (eg from both child and parent) should have a tag (<surv_name>_"parent"_s1_r1_e1) in var name in datadict
    df = datadict_df
    names_list = []
    for _, row in df.iterrows():
        surv_match = re.match('^([a-zA-Z0-9\-]+)(_[a-z])?(_scrd[a-zA-Z]+)?(_[a-zA-Z]{2,})?$', row.variable)
        if surv_match and surv_match.group(4) and surv_match.group(4)[1:] not in names_list and row["dataType"] == "redcap_data":
            names_list.append(surv_match.group(4)[1:])
    return names_list

def get_tasks(datadict_df):
    df = datadict_df
    tasks_dict = dict()
    datatypes_to_ignore = ["id", "consent", "assent", "redcap_data", "redcap_scrd", "parent_info"]
    for _, row in df.iterrows():
        if row["dataType"] not in datatypes_to_ignore:
            if isinstance(row["dataType"], str) and isinstance(row["expectedFileExt"], str):
                tasks_dict[row["variable"]] = [row["dataType"], row["expectedFileExt"], row["allowedSuffix"]]
            else:
                print(c.RED + "Error: Must have dataType, expectedFileExt, and allowedSuffix fields in datadict for ", row["variable"], ", skipping." + c.ENDC)
    return tasks_dict

def get_IDs(datadict_df):
    df_dd = datadict_df
    id_desc = df_dd.set_index("variable").loc["id", "description"].split(" ")
    # ID description column should contain redcap and variable from which to read IDs, in format 'file: "{name of redcap}"; variable: "{column name}"'
    for i in id_desc:
        if "file:" in i:
            idx = id_desc.index(i)+1
            id_rc = id_desc[idx].strip("\"\';,()")
        elif "variable:" in i:
            idx = id_desc.index(i)+1
            var = id_desc[idx].strip("\"\';,()")
    if "id_rc" not in locals() or "var" not in locals():
        sys.exit("Can\'t find redcap column to read IDs from in datadict")

    redcap_files = [join(checked_path,"redcap",f) for f in listdir(join(checked_path,"redcap")) if isfile(join(checked_path,"redcap",f))]
    for redcap in redcap_files:

        rc_re = re.match('^' + id_rc + '.*_data_(\d{4}-\d{2}-\d{2}_\d{4}).*$', basename(redcap).lower())
        if rc_re:
            timestamp = rc_re.group(1)
            date = datetime.datetime.strptime(timestamp,'%Y-%m-%d_%H%M')
            if "newest_date" not in locals():
                newest_date = date
                consent_redcap = redcap
            else:
                if date > newest_date:
                    newest_date = date
                    consent_redcap = redcap
            
    if "consent_redcap" not in locals():
        sys.exit("Can\'t find" + id_rc + "redcap to read IDs from")
    consent_redcap = pd.read_csv(consent_redcap, index_col=var)
    ids = consent_redcap.index.tolist()
    return ids


if __name__ == "__main__":
    checked_path = sys.argv[1]
    dataset = sys.argv[2]
    redcaps = sys.argv[3]
    session = sys.argv[4]
    child = sys.argv[5]

    redcaps = redcaps.split(',')
    if session == "none":
      session = ""
      ses_tag = ""
    else:
      ses_tag = "_" + session

    DATA_DICT = dataset + "/data-monitoring/data-dictionary/central-tracker_datadict.csv"
    df_dd = pd.read_csv(DATA_DICT)
    redcheck_columns = get_redcap_columns(df_dd)
    multiple_reports_tags = get_multiple_reports_tags(df_dd)
    tasks_dict = get_tasks(df_dd)
    ids = get_IDs(df_dd)
    
    # extract project path from dataset
    proj_name = basename(normpath(dataset))

    data_tracker_file = "{}/data-monitoring/central-tracker_{}.csv".format(dataset, proj_name)
    tracker_df = pd.read_csv(data_tracker_file)

    tracker_ids = tracker_df["id"].tolist()
    new_subjects = list(set(ids).difference(tracker_ids))
    if len(new_subjects) > 0:
        new_subjects_df = pd.DataFrame({"id": new_subjects})
        tracker_df = tracker_df.append(new_subjects_df)
    tracker_df = tracker_df.set_index("id")
    tracker_df.sort_index(axis="index", inplace=True)

    subjects = tracker_df.index.to_list()

    all_redcap_columns = dict() # list of all redcap columns whose names should be mirrored in central tracker
    
    if redcaps[0] != "none":
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
                sys.exit('Error: Duplicate columns found in redcap ' + redcap_path + ': ' + ', '.join(dupes) + '. Exiting')

            rc_subjects = []
            rc_ids = rc_df.index.tolist()
            if child == 'true':
                for id in rc_ids:
                    if re.search('30[089](\d{4})', str(id)):
                        child_id = int('300' + re.search('30[089](\d{4})', str(id)).group(1))
                        rc_subjects.append(child_id)
            else:
                rc_subjects = rc_ids
            rc_subjects.sort()

            all_keys = dict()
            for key, value in redcheck_columns.items():
                all_keys[key] = value
                for tag in multiple_reports_tags:
                    surv_re = re.match('^([a-zA-Z0-9\-]+)(_[a-z])?(_scrd[a-zA-Z]+)?(_[a-zA-Z]{2,})?(_s[0-9]+_r[0-9]+_e[0-9]+)$', value)
                    if tag in redcap_path and surv_re and surv_re.group(4) == '_' + tag:
                        surv_version = '' if not surv_re.group(2) else surv_re.group(2)
                        scrd_str = '' if not surv_re.group(3) else surv_re.group(3)
                        key = surv_re.group(1) + surv_version + scrd_str + surv_re.group(5) + completed
                        allowed_duplicate_columns.append(key)
                        all_keys[key] = value
                # adds "parent" to redcap column name in central tracker

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

                keys_in_redcap = dict()
                for key, value in all_keys.items():
                    try:
                        val = rc_df.loc[id, key]
                        keys_in_redcap[key] = value
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
                        if 'sess' in locals():
                            del sess
                        for key, value in row.items():
                            if key.startswith(session_type + 'paid_lang'):
                                lang_re = re.match('^' + session_type + 'paid_lang.*(s[0-9]+_r[0-9]+(_e[0-9]+)?)', key)
                                if lang_re:
                                    sess = lang_re.group(1)
                                    tracker_df.loc[child_id, 'plang' + session_type + '_' + sess] = str(int(value)) # 1 for english 2 for sp
                        parentid_re = re.match('30([089])\d{4}', str(row.name))
                        if parentid_re and 'sess' in locals():
                            if parentid_re.group(1) == '8':
                                tracker_df.loc[child_id, 'pidentity' + session_type + '_' + sess] = "8"
                            elif parentid_re.group(1) == '9':
                                tracker_df.loc[child_id, 'pidentity' + session_type + '_' + sess] = "9" # 8 for primary parent, 9 for secondary

            # for subject IDs missing from parent redcaps, fill in "0" for plang/pidentity
            for session_type in ['bbs', 'iqs']:
                if session_type + 'parent' in redcap_path:
                    for subj in set(subjects).difference(rc_subjects):
                        for col in tracker_df.columns:
                            if re.match('^p(lang|identity)' + session_type + '_' + session + '_e[0-9]+$', col):
                                try:
                                    tracker_df.loc[subj, col] = "0"
                                except Exception as e_msg:
                                    continue
            # for subject IDs missing from redcap, fill in "0" in redcap columns
            for subj in set(subjects).difference(rc_subjects):
                for key, value in keys_in_redcap.items():
                    if re.match('^.*' + session + '_e[0-9]+$', value):
                        try:
                            tracker_df.loc[subj, value] = "0"
                        except Exception as e_msg:
                            continue

            duplicate_cols = []
            for col, _ in tracker_df.iteritems():
                if re.match('^.*\.[0-9]+$', col):
                    duplicate_cols.append(col)
            tracker_df.drop(columns=duplicate_cols, inplace=True)
            tracker_df.to_csv(data_tracker_file)

            for col in rc_df.columns:
                if col.endswith(completed):
                    all_redcap_columns.setdefault(col,[]).append(redcap_path)

        all_duplicate_cols = []
        redcaps_of_duplicates = []
        for col, rcs in all_redcap_columns.items():
            if len(all_redcap_columns[col]) > 1 and col not in allowed_duplicate_columns:
                all_duplicate_cols.append(col)
                redcaps_of_duplicates.append(', '.join(rcs))
        if len(all_duplicate_cols) > 0:
            errmsg = "Error: Duplicate columns were found across Redcaps: "
            for i in range(0, len(all_duplicate_cols)):
                errmsg = errmsg + all_duplicate_cols[i] + " in " + redcaps_of_duplicates[i] + "; "
            sys.exit(errmsg + "Exiting.")
    else:
        sys.exit('Can\'t find redcaps in ' + dataset + '/sourcedata/raw/redcap, skipping ')

    for task, values in tasks_dict.items():
        datatype = values[0]
        file_exts = values[1].split(", ")
        file_sfxs = values[2].split(", ")
        for subj in subjects:
            subdir = "sub-" + str(subj)
            dir_id = int(subj)
            for sfx in file_sfxs:
                suf_re = re.match('^(s[0-9]+_r[0-9]+)_e[0-9]+$', sfx)
                if suf_re and suf_re.group(1) == session:
                    try:
                        corrected = False
                        for filename in listdir(join(checked_path, subdir, session, datatype)):
                            if re.match('^[Cc]orrected.*$', filename):
                                corrected = True
                                break
                        all_files_present = True
                        for ext in file_exts:
                            file_present = False
                            for filename in listdir(join(checked_path, subdir, session, datatype)):
                                if corrected:
                                    if re.match('^sub-' + str(dir_id) + '_' + task + '_' + sfx + '[a-zA-Z0-9_-]*\\' + ext + '$', filename):
                                    # when corrected.txt file present allow string between suffix and ext (e.g. "s1_r1_e1_firstrun_practice.eeg")
                                        file_present = True
                                        break
                                else:
                                    if re.match('^sub-' + str(dir_id) + '_' + task + '_' + sfx + '\\' + ext + '$', filename):
                                        file_present = True
                                        break
                            if not file_present:
                                all_files_present = False
                        if all_files_present:
                            tracker_df.loc[dir_id, task + "_" + sfx] = "1"
                        else:
                            tracker_df.loc[dir_id, task + "_" + sfx] = "0"
                    except:
                        tracker_df.loc[dir_id, task + "_" + sfx] = "0"

    tracker_df.to_csv(data_tracker_file)

            # make remaining empty values equal to 0
            # tracker_df[collabel] = tracker_df[collabel].fillna("0")

    print(c.GREEN + "Success: {} data tracker updated.".format(', '.join([dtype[0] for dtype in list(tasks_dict.values())])) + c.ENDC)
