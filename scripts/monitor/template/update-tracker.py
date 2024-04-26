import pandas as pd
import sys
from os.path import basename, normpath, join, isdir, isfile, splitext
from os import listdir, walk
import pathlib
import re
import math
import datetime
from collections import defaultdict

# list hallMonitor key

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
    cols = {}
    key_counter = defaultdict(lambda: 0)
    allowed_duplicate_columns = []
    for _, row in df.iterrows():
        if row["dataType"] not in ["consent", "assent", "redcap_data"]: #just redcap data
            continue
        if isinstance(row["allowedSuffix"], float) and math.isnan(row["allowedSuffix"]):
            allowed_suffixes = [""]
        else:
            allowed_suffixes = row["allowedSuffix"].split(", ")
            allowed_suffixes = [x for x in allowed_suffixes if x.startswith(session)] # only from same session
            allowed_suffixes = ["_" + ses for ses in allowed_suffixes]
        prov = row["provenance"].split(" ")
        if "file:" in prov and "variable:" in prov:
            idx = prov.index("file:")
            rc_filename = prov[idx+1].strip("\";,")
            idx = prov.index("variable:")
            rc_variable = prov[idx+1].strip("\";,")
            if rc_variable == "":
                rc_variable = row["variable"].lower()
            if not rc_filename in cols.keys():
                cols[rc_filename] = {}
            if "id:" in prov:
                idx = prov.index("id:")
                rc_idcol = prov[idx+1].strip("\";,")
                cols[rc_filename]["id_column"] = rc_idcol
        else:
            continue
        for ses_tag in allowed_suffixes:
            #var = row["variable"]
            var = row["variable"]
            cols[rc_filename][rc_variable + ses_tag + completed] = var + ses_tag
            key_counter[rc_variable + ses_tag + completed] += 1
            # also map Sp. surveys to same column name in central tracker if completed
            surv_match = re.match('^([a-zA-Z0-9\-]+)(_[a-z0-9]{1,2})?(_scrd[a-zA-Z]+)?(_[a-zA-Z]{2,})?$', rc_variable)
            if surv_match and "redcap_data" in row["dataType"]:
                surv_version = '' if not surv_match.group(2) else surv_match.group(2)
                scrd_str = '' if not surv_match.group(3) else surv_match.group(3)
                multiple_report_tag = '' if not surv_match.group(4) else surv_match.group(4)
                surv_esp = surv_match.group(1) + 'es' + surv_version + scrd_str + multiple_report_tag + ses_tag
                cols[rc_filename][surv_esp + completed] = var + ses_tag
                key_counter[surv_esp + completed] += 1
            if "consent" in row["dataType"]:
                cols[rc_filename][rc_variable + "es" + completed] = var
    for key, value in key_counter.items():
        if value > 1:
            allowed_duplicate_columns.append(key)
    return cols, allowed_duplicate_columns

def get_tasks(datadict_df):
    df = datadict_df
    tasks_dict = dict()
    task_vars = []
    for _, row in df.iterrows():
        if not isinstance(row["expectedFileExt"], float):
            task_vars.append(row["variable"])
    for _, row in df.iterrows():
        if row["variable"] in task_vars:
            if isinstance(row["dataType"], str) and isinstance(row["expectedFileExt"], str):
                tasks_dict[row["variable"]] = [row["dataType"], row["expectedFileExt"], row["allowedSuffix"]]
            else:
                print(c.RED + "Error: Must have dataType, expectedFileExt, and allowedSuffix fields in datadict for ", row["variable"], ", skipping." + c.ENDC)
    return tasks_dict

def get_IDs(datadict_df):
    df_dd = datadict_df
    id_desc = df_dd.set_index("variable").loc["id", "provenance"].split(" ")
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

def get_study_no(datadict_df):
    allowed_vals = datadict_df.set_index("variable").loc["id", "allowedValues"]
    allowed_vals = allowed_vals.replace(" ", "")
    intervals = re.split("[\[\]]", allowed_vals)
    intervals = list(filter(lambda x: x not in [",", ""], intervals))
    return intervals[0][0:2] # first two digits should be study no.

def fill_combination_columns(tracker_df, dd_df):
    combos_dict = dict()
    for _, row in dd_df.iterrows():
        if row["dataType"] == "combination":
            idx = row["provenance"].split(" ").index("variables:")
            vars = "".join(row["provenance"].split(" ")[idx+1:]).split(",")
            vars = [var.strip("\"") for var in vars]
            for ses in row["allowedSuffix"].split(", "):
                combos_dict[row["variable"]+"_"+ses] = [var+"_"+ses for var in vars]
    for key, cols in combos_dict.items():
        if len(cols) == 0:
            print(c.RED + "Error: columns to combine not found for combination variable: " + key + ", can\'t update column." + c.ENDC)
            del combos_dict[key]
    for combined_col, cols in combos_dict.items():
        for id, row in tracker_df.iterrows():
            present = False
            for col in cols:
                try:
                    if str(tracker_df.loc[id, col]) == "1":
                        present = True
                except KeyError as e_msg:
                    sys.exit(c.RED + "Error: KeyError:" + e_msg + ", please fix central tracker." + c.ENDC)
            if present:
                tracker_df.loc[id, combined_col] = "1"
            else:
                tracker_df.loc[id, combined_col] = "0"
        if not any(tracker_df.loc[:, combined_col] == "1"):
            tracker_df.loc[:, combined_col] = "" # all zeros columns leave blank

def parent_columns(datadict_df):
    parent_info = dict()
    for _, row in datadict_df.iterrows():
        if row["dataType"] == "parent_identity":
            prov = row["provenance"].split(" ")
            if "file:" in prov and "variable:" in prov:
                idx = prov.index("file:")
                rc_filename = prov[idx+1].strip("\";")
                idx = prov.index("variable:")
                rc_variable = prov[idx+1].strip("\";")
                parent_info.setdefault(rc_filename,[]).append(row["variable"])
            else:
                continue
            rc_df = pd.read_csv(all_redcap_paths[rc_filename])
            parent_ids = list(rc_df.loc[:, rc_variable])
            for id in parent_ids:
                if re.search(study_no + '[089](\d{4})', str(id)):
                    child_id = study_no + '0' + re.search(study_no + '([089])(\d{4})', str(id)).group(2)
                    child_id = int(child_id)
                    parent = re.search(study_no + '([089])(\d{4})', str(id)).group(1)
                else:
                    continue
                try:
                    for suf in row["allowedSuffix"].split(", "):
                        if re.match("^" + session + "_e[0-9]+$", suf):
                            tracker_df.loc[child_id, row["variable"] + "_" + suf] = parent
                except:
                    continue
        elif row["dataType"] == "parent_lang":
            prov = row["provenance"].split(" ")
            if "file:" in prov and "variable:" in prov:
                idx = prov.index("file:")
                rc_filename = prov[idx+1].strip("\";")
                idx = prov.index("variable:")
                rc_variable = prov[idx+1].strip("\";")
                parent_info.setdefault(rc_filename,[]).append(row["variable"])
            else:
                continue
            rc_df = pd.read_csv(all_redcap_paths[rc_filename], index_col="record_id")
            for col in rc_df.columns:
                lang_re = re.match(rc_variable + "_(s[0-9]+_r[0-9]+_e[0-9]+)", col)
                if lang_re:
                    for _, rc_row in rc_df.iterrows():
                        if re.search(study_no + '[089](\d{4})', str(rc_row.name)):
                            child_id = study_no + '0' + re.search(study_no + '([089])(\d{4})', str(rc_row.name)).group(2)
                            child_id = int(child_id)
                            if str(rc_row[col]) == "1" or str(rc_row[col]) == "2":
                                try:
                                    for suf in row["allowedSuffix"].split(", "):
                                        if re.match("^" + session + "_e[0-9]+$", suf):
                                            tracker_df.loc[child_id, row["variable"] + "_" + suf] = str(rc_row[col])
                                except:
                                    continue
                            else:
                                print("Error: unknown value seen for parent language, should be 1 for English and 2 for Spanish.")
    return parent_info

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
    redcheck_columns, allowed_duplicate_columns = get_redcap_columns(df_dd)
    tasks_dict = get_tasks(df_dd)
    ids = get_IDs(df_dd)
    study_no = get_study_no(df_dd)
    
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
    all_redcap_paths = dict()
    
    if redcaps[0] != "none":
        all_rc_dfs = dict()
        all_rc_subjects = dict()
        for expected_rc in redcheck_columns.keys():
            present = False
            for redcap in redcaps:
                if expected_rc in basename(redcap.lower()) and present == False:
                    redcap_path = redcap
                    all_redcap_paths[expected_rc] = redcap_path
                    present = True
                elif expected_rc in basename(redcap.lower()) and present == True:
                    sys.error(c.RED + "Error: multiple redcaps found with name specified in datadict, " + redcap_path + " and " + redcap + ", exiting." + c.ENDC)
            if present == False:
                sys.exit(c.RED + "Error: can't find redcap specified in datadict " + expected_rc + ", exiting." + c.ENDC)
            if "id_column" in redcheck_columns[expected_rc].keys():
                id_col = redcheck_columns[expected_rc]["id_column"]
                for column in pd.read_csv(redcap_path).columns:
                    if column.startswith(id_col):
                        all_rc_dfs[expected_rc] = pd.read_csv(redcap_path, index_col = column)
            else:
                id_col = "record_id"
                all_rc_dfs[expected_rc] = pd.read_csv(redcap_path, index_col = id_col)
            # If hallMonitor passes "redcap" arg, data exists and passed checks 
            vals = pd.read_csv(redcap_path, header=None, nrows=1).iloc[0,:].value_counts()
            # Exit if duplicate column names in redcap
            if any(vals.values != 1):
                dupes = []
                for rc_col in vals.keys():
                    if vals[rc_col] > 1:
                        dupes.append(rc_col)
                sys.exit(c.RED + 'Error: Duplicate columns found in redcap ' + redcap_path + ': ' + ', '.join(dupes) + '. Exiting' + c.ENDC)
        for expected_rc in redcheck_columns.keys():
            rc_df = all_rc_dfs[expected_rc]
            rc_subjects = []
            rc_ids = rc_df.index.tolist()
            if child == 'true':
                for id in rc_ids:
                    if re.search(study_no + '[089](\d{4})', str(id)):
                        child_id = int(study_no + '0' + re.search(study_no + '[089](\d{4})', str(id)).group(1))
                        rc_subjects.append(child_id)
            else:
                rc_subjects = rc_ids
            rc_subjects.sort()

            all_rc_subjects[expected_rc] = rc_subjects

            all_keys = dict()
            for key, value in redcheck_columns[expected_rc].items():
                all_keys[key] = value
                if key.startswith("consent") or key.startswith("assent") or key.startswith("id_column"):
                #if key.startswith("consent") or key.startswith("assent") or key.startswith("id_column") or key.startswith("demo_e"):
                    continue
                if not re.match('^.*es(_[a-zA-Z])?_s[0-9]+_r[0-9]+_e[0-9]+_complete', key) and key not in all_rc_dfs[expected_rc].columns:
                    other_rcs = []
                    other_rc_dfs = {rc: all_rc_dfs[rc] for rc in all_rc_dfs if rc != expected_rc}
                    for redcap, other_rc_df in other_rc_dfs.items():
                        if key in other_rc_df.columns:
                            other_rcs.append(redcap)
                    if len(other_rcs) >= 1:
                        sys.exit(c.RED + "Error: can\'t find " + key + " in " + expected_rc + " redcap, but found in " + ", ".join(other_rcs) + " redcaps, exiting." + c.ENDC)
                    else:
                        sys.exit(c.RED + "Error: can\'t find " + key + " in " + expected_rc + " redcap, exiting." + c.ENDC)

            for index, row in rc_df.iterrows():
                if (isinstance(index, float) or isinstance(index, int)) and not math.isnan(index):
                    id = int(row.name)
                else:
                    print("skipping nan value in ", str(all_redcap_paths[expected_rc]), ": ", str(index))
                    continue
                if child == 'true':
                    if re.search(study_no + '[089](\d{4})', str(id)):
                        child_id = study_no + '0' + re.search(study_no + '[089](\d{4})', str(id)).group(1)
                        child_id = int(child_id)
                    else:
                        print(str(id), "doesn't match expected child or parent id format of \"" + study_no +"{0,8, or 9}XXXX\", skipping")
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

            # for subject IDs missing from redcap, fill in "0" in redcap columns
            for subj in set(subjects).difference(rc_subjects):
                for key, value in keys_in_redcap.items():
                    if re.match('^.*' + session + '_e[0-9]+$', value):
                        try:
                            tracker_df.loc[subj, value] = "0"
                        except Exception as e_msg:
                            continue

            duplicate_cols = []
            # drop any duplicate columns ending in ".NUMBER"
            for col, _ in tracker_df.iteritems():
                if re.match('^.*\.[0-9]+$', col):
                    duplicate_cols.append(col)
            tracker_df.drop(columns=duplicate_cols, inplace=True)
            tracker_df.to_csv(data_tracker_file)

            for col in rc_df.columns:
                if col.endswith(completed):
                    all_redcap_columns.setdefault(col,[]).append(all_redcap_paths[expected_rc])

        parent_info = parent_columns(df_dd)

        for expected_rc in redcheck_columns.keys():
            if expected_rc in parent_info.keys():
                for subj in set(subjects).difference(all_rc_subjects[expected_rc]):
                    for col in tracker_df.columns:
                        for var in parent_info[expected_rc]:
                            if re.match('^' + var + '_' + session + '_e[0-9]+$', col):
                                try:
                                    tracker_df.loc[subj, col] = "NA"
                                except Exception as e_msg:
                                    continue

        all_duplicate_cols = []
        redcaps_of_duplicates = []
        for col, rcs in all_redcap_columns.items():
            if len(all_redcap_columns[col]) > 1 and col not in allowed_duplicate_columns:
                all_duplicate_cols.append(col)
                redcaps_of_duplicates.append(', '.join(rcs))
        if len(all_duplicate_cols) > 0:
            errmsg = c.RED + "Error: Duplicate columns were found across Redcaps: "
            for i in range(0, len(all_duplicate_cols)):
                errmsg = errmsg + all_duplicate_cols[i] + " in " + redcaps_of_duplicates[i] + "; "
            sys.exit(errmsg + "Exiting." + c.ENDC)
    else:
        sys.exit('Can\'t find redcaps in ' + dataset + '/sourcedata/raw/redcap, skipping ')

    for task, values in tasks_dict.items():
        datatype = values[0]
        file_exts = values[1].split(", ")
        file_sfxs = values[2].split(", ")
        for subj in subjects:
            no_data = False
            subdir = "sub-" + str(subj)
            dir_id = int(subj)
            for sfx in file_sfxs:
                suf_re = re.match('^(s[0-9]+_r[0-9]+)_e[0-9]+$', sfx)
                if suf_re and suf_re.group(1) == session:
                    try:
                        corrected = False
                        for filename in listdir(join(checked_path, subdir, session, datatype)):
                            if re.match('^[Dd]eviation.*$', filename):
                                corrected = True
                                break
                            if re.match('^no-data\.txt$', filename):
                                tracker_df.loc[dir_id, task + "_" + sfx] = "0"
                                no_data = True
                                break
                        if no_data:
                            break
                        all_files_present = True
                        for ext in file_exts:
                            file_present = False
                            for filename in listdir(join(checked_path, subdir, session, datatype)):
                                if corrected:
                                    if re.match('^sub-' + str(dir_id) + '_' + task + '_' + sfx + '[a-zA-Z0-9_-]*\\' + ext + '$', filename):
                                    # when deviation.txt file present allow string between suffix and ext (e.g. "s1_r1_e1_firstrun_practice.eeg")
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

    fill_combination_columns(tracker_df, df_dd)

    tracker_df.to_csv(data_tracker_file)

    # Create more readable csv with no blank columns
    tracker_df = pd.read_csv(data_tracker_file, index_col="id")
    data_tracker_filename = splitext(data_tracker_file)[0]
    tracker_df_no_blank_columns = tracker_df.loc[:, tracker_df.notnull().any(axis=0)]
    tracker_df_no_blank_columns = tracker_df_no_blank_columns.fillna("NA")
    tracker_df_no_blank_columns.to_csv(data_tracker_filename + "_viewable.csv")

            # make remaining empty values equal to 0
            # tracker_df[collabel] = tracker_df[collabel].fillna("0")

    print(c.GREEN + "Success: {} data tracker updated.".format(', '.join([dtype[0] for dtype in list(tasks_dict.values())])) + c.ENDC)
