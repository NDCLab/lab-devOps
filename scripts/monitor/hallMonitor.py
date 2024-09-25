#!/bin/python3

import logging
import os
from os.path import join, isdir, isfile, abspath, dirname, basename
import re
import subprocess
from getpass import getuser

import pandas as pd

from hmutils import (
    CHECKED_SUBDIR,
    DATADICT_SUBPATH,
    LOGGING_SUBPATH,
    PENDING_QA_SUBDIR,
    QA_CHECKLIST_SUBPATH,
    RAW_SUBDIR,
    ColorfulFormatter,
    Identifier,
    new_validation_record,
    clean_empty_dirs,
    datadict_has_changes,
    get_args,
    get_expected_combination_rows,
    get_expected_identifiers,
    get_file_record,
    get_identifier_files,
    get_pending_files,
    get_present_identifiers,
    get_timestamp,
    new_error_record,
    new_qa_checklist,
    write_file_record,
    write_qa_tracker,
)


def parse_datadict(dd_df):
    dd_dict = dict()
    task_vars = []
    combination_rows = {}
    for _, row in dd_df.iterrows():
        if not isinstance(row["expectedFileExt"], float): # all rows in datadict with extensions i.e. with data files
            task_vars.append(row.name)
        if row["dataType"] == "combination":
            idx = row["provenance"].split(" ").index("variables:")
            vars = "".join(row["provenance"].split(" ")[idx+1:]).split(",")
            vars = [var.strip("\"") for var in vars]
            combination_rows[row.name] = vars
    # build dict of expected files/datatypes from datadict
    for var, row in dd_df.iterrows():
        if row.name in task_vars:
            #dd_dict[var] = [row["dataType"], allowed_sfxs, expected_exts, row["allowedValues"], row["encrypted"]]
            allowed_sfxs = [x.strip() for x in row["allowedSuffix"].split(",")]
            expected_exts = [x.strip() for x in row["expectedFileExt"].split(",")]
            dd_dict[var] = [row["dataType"], allowed_sfxs, expected_exts, row["allowedValues"]]
    return dd_dict, combination_rows

def allowed_val(allowed_vals, value):
    allowed_vals = allowed_vals.replace(" ", "")
    intervals = re.split("[\[\]]", allowed_vals)
    intervals = list(filter(lambda x: x not in [",", ""], intervals))
    allowed = False
    for interval in intervals:
        lower = float(interval.split(",")[0])
        upper = float(interval.split(",")[1])
        if lower <= int(value) <= upper:
            allowed = True
            break
    return allowed

def has_deviation(identifier, parentdirs):
    # is there a deviation.txt in the folder
    # return list of True and/or False for deviation and no-data
    deviation = False
    no_data = False
    for parentdir in parentdirs:
        for file in os.listdir(parentdir):
            if re.match('^'+identifier+'-deviation\.txt$', file):
                deviation = True
            elif re.match('^'+identifier+'-no-data\.txt$', file):
                no_data = True
    return [deviation, no_data]

def write_to_pending_files(identifier, errors, pending_df):
    user = getuser()
    dt = datetime.datetime.now(pytz.timezone("US/Eastern"))
    dt = timestamp.strftime(DT_FORMAT)
    datatype = re.match("^sub-[0-9]*_([a-zA-Z0-9_-]*)_s[0-9]*_r[0-9]*_e[0-9]*(_[a-zA-Z0-9_-]+)?$", identifier).group(1)
    pass_raw = True if len(errors) == 0 else False
    #error_type
    #error_details = "NA" if error == "" else error
    idx = len(pending_df)
    if len(errors) == 0:
        error_type = "NA"
        error_details = "NA"
        pending_df.loc[idx] = [identifier, dt, user, datatype, pass_raw, error_type, error_details]
    else:
        for error in errors:
            pending_df.loc[idx] = [identifier, dt, user, datatype, pass_raw, error[1], error[0]]
            idx+=1
    return pending_df

def check_filenames(variable, files, deviation, raw_or_checked):
    [datatype, allowed_suffixes, possible_exts, allowed_subs] = variable_dict[identifier]
    allowed_suffixes = allowed_suffixes.split(",")
    allowed_suffixes = [x.strip() for x in allowed_suffixes]
    possible_exts = sum([ext.split('|') for ext in fileexts], [])
    #errors = {}
    #errors["error_detail"] = []
    errors = []
    if deviation[1] == True: # no data
        return errors
    for filename in files:
        parent_dirs = file.split('/')
        if raw_or_checked == "raw": # raw directory structure
            sub = parent_dirs[-2]
            ses = parent_dirs[-4]
            #datatype = parent_dirs[-3]
        elif raw_or_checked == "checked": # checked directory structure
            sub = parent_dirs[-4]
            ses = parent_dirs[-3]
            #datatype = parent_dirs[-2]
        file_re = re.match("^(sub-([0-9]*))_([a-zA-Z0-9_-]*)_((s([0-9]*)_r([0-9]*))_e([0-9]*))(_[a-zA-Z0-9_-]+)?((?:\.[a-zA-Z]+)*)$", filename)
        if file_re:
        #####################
            # all filename checks (not number of files checks, not _data or _status checks), write any errors to "errors"
            #TODO need possible_exts, allowed_vals, allowed_suffixes, possible variable names from dd_df
            if file_re.group(1) != sub:
                errors.append(["Error: file from subject " + file_re.group(1) + " found in " + sub + " folder: " + filename, "name"])
            if file_re.group(5) != ses:
                errors.append(["Error: file from session " + file_re.group(5) + " found in " + ses + " folder: " + filename, "name"]) 
            if file_re.group(10) not in possible_exts and len(file_re.group(10)) > 0:
                errors.append(["Error: file with extension " + file_re.group(10) + " found, doesn\'t match expected extensions " + ", ".join(possible_exts) + ": " + filename, "name"]) 
            if file_re.group(2) != '' and not allowed_val(allowed_subs, file_re.group(2)):
                errors.append(["Error: subject number " + file_re.group(2) + " not an allowed subject value " + allowed_subs + " in file: " + filename, "name"])
            if file_re.group(3) not in variable_dict.keys():
                errors.append(["Error: variable name " + file_re.group(3) + " does not match any datadict variables, in file: " + filename, "name"])
            if datatype not in file_re.group(3):
                errors.append(["Error: variable name " + file_re.group(3) +  " does not contain the name of the enclosing datatype folder " + datatype + " in file: " + filename, "name"])
            if file_re.group(4) not in allowed_suffixes:
                errors.append(["Error: suffix " + file_re.group(4) + " not in allowed suffixes " + ", ".join(allowed_suffixes) + " in file: " + filename, "name"])
            if file_re.group(2) == "":
                errors.append(["Error: subject # missing from file: " + filename, "name"])
            if file_re.group(3) == "":
                errors.append(["Error: variable name missing from file: " + filename, "name"])
            if file_re.group(6) == "":
                errors.append(["Error: session # missing from file: " + filename, "name"])
            if file_re.group(7) == "":
                errors.append(["Error: run # missing from file: " + filename, "name"])
            if file_re.group(8) == "":
                errors.append(["Error: event # missing from file: " +filename, "name"])
            if file_re.group(10) == "":
                errors.append(["Error: extension missing from file, does\'nt match expected extensions " + ", ".join(possible_exts) + ": " + filename, "name"])
            #TODO check-id.py
            #if datatype == "psychopy" and file_re.group(10) == ".csv" and file_re.group(2) != "":
            #
                # Call check-id.py for psychopy files
                #check_id.check_id(file_re.group(2), filename)
        ###########
        else:
            errors.append(["Error: file " + join(path, filename) + " does not match naming convention <sub-#>_<variable/task-name>_<session>.<ext>", "name"])
    return errors


def check_identifiers(identifiers_dict, source_data, pending_files_df):
    #for source_data in ["raw", "checked"]:
        for key, vals in identifiers_dict:
            var_name = re.match("^sub-[0-9]*_([a-zA-Z0-9_-]*)_s[0-9]*_r[0-9]*_e[0-9]*(_[a-zA-Z0-9_-]+)?(?:\.[a-zA-Z]+)?*$", key).group(1)
            raw_files = get_identifier_files(key, vals)
            deviation = has_deviation(key, vals['parentdirs'])
            errors = check_filenames(var_name, raw_files, deviation, source_data)
            #passed = True if len(errors) == 0 else False
            pending_files_df = write_to_pending_files(key, errors, pending_files_df)
        return pending_files_df

def check_all_data_present(identifiers_dict, source_data, pending_files_df, variable_dict):
    # check that for each identifier that has data for one variable, it has data for each variable or a "no-data.txt" file
    expected_data = set(variable_dict.keys())
    ####
    for key, vals in identifiers_dict:
        allpresent = True
        identifier_re = re.fullmatch(r"(sub-\d+)_([\w\-]*)_((s\d+_r\d+)_e\d)*", key)
        if identifier_re:
            [sub, var, sre, sess] = list(identifier_re.groups())
            for var in expected_data:
                dtype = variable_dict[var]["dataType"]
                exts = variable_dict[var["expectedFileExt"]]
                if source_data == "raw":
                    parent = join(dataset, "sourcedata", source_data, sess, dtype, sub)
                elif source_data == "checked":
                    parent = join(dataset, "sourcedata", source_data, sub, sess, dtype)
                for ext in exts:
                    ext_present = False
                    for file in os.listdir(parent):
                        ext_re = sub + "_" + var + "_" + sre + "(_[\w\-]+)?\." + ext
                        if re.fullmatch(re.escape(ext_re), file):  # allow deviation str
                            ext_present = True
                            break
                    if not ext_present:
                        allpresent = False
                        missing_files.append(parent+"/"+sub+"_"+var+"_"+sre+"."+ext)
        if not allpresent:
            error = "Error: not all expected files seen, " + ", ".join(missing_files) + "not present."
            pending_files_df = write_to_pending_files(key, error, pending_files_df)
                                  # #TODO write error to pending-files csv "not all expected files present"
                        #TODO deal with combination rows
                        #TODO deal with deviation files or "no-data"
    ####
    return pending_files_df

def get_identifier_files(identifier, vals):
    variable = re.match("^sub-[0-9]*_([a-zA-Z0-9_-]*)_s[0-9]*_r[0-9]*_e[0-9]*?$", identifier).group(1)
    exts = dd_df[dd_df['variable'] == variable]['expectedFileExt'].iloc[0]
    exts = exts.split(',')
    exts = [ext.strip() for ext in exts]
    expected_files = []
    for parentdir in vals['parentdirs']:
        for ext in exts:
            expected_files.append(join(parentdir, identifier+ext))
    return expected_files
    # should return all files expected for the given identifier (minus any "deviation" strings)


def handle_raw_unchecked(dataset):
    #record = get_file_record(dataset)
    timestamp = datetime.datetime.now(pytz.timezone("US/Eastern"))
    timestamp = timestamp.strftime(DT_FORMAT)
    pending_files_name = join(dataset, "data-monitoring", "logs", "pending-files-" + timestamp + ".csv")
    pending_errors_name = join(dataset, "data-monitoring", "logs", "pending-errors-" + timestamp + ".csv")
    pending_files_df = new_pending_df()
    for source_data in ["raw", "checked"]:
        identifiers = get_identifiers(dataset, source_data)
        pending_files_df = check_identifiers(identifiers, source_data, pending_files_df)
        pending_files_df = check_all_data_present(identifiers, source_data, pending_files_df, variable_dict)
    pending_files_df.set_index('identifier')
    pending_files_df.to_csv(pending_files_name)
    pending_errors = pending_files_df[pending_files_df['error_type'] != "NA"]
    pending_errors.to_csv(pending_errors_name)



def get_latest_pending(dataset):
    pending_path = os.path.join(dataset, "data-monitoring", "pending")
    pending_files = os.listdir(pending_path)
    pending_df = pd.read_csv(pending_files[-1])
    return pending_df


def df_from_colmap(colmap):
    """Generates a Pandas DataFrame from a column-datatype dictionary

    Args:
        colmap (dict[str, str]): A dictionary containing entries of the form "name": "float|str|int"

    Returns:
        pandas.DataFrame: An empty DataFrame, generated as specified by colmap
    """
    df = pd.DataFrame({c: pd.Series(dtype=t) for c, t in colmap.items()})
    return df


def new_pending_df():
    colmap = {
        "identifier": "str",
        "datetime": "str",
        "user": "str",
        "dataType": "str",
        "passRaw": "int",
        "errorType": "str",
        "errorDetails": "str",
    }
    #df = df_from_colmap(colmap)
    #df.set_index('identifier', inplace=True)
    return df_from_colmap(colmap)


def get_passed_raw_check(dataset):
    pass


def qa_validation(dataset):
    logger.info("Starting QA check...")

    # get QA tracker and identifier record
    record_df = get_file_record(dataset)
    pending_qa_dir = os.path.join(dataset, PENDING_QA_SUBDIR)
    qa_checklist_path = os.path.join(dataset, QA_CHECKLIST_SUBPATH)
    if os.path.exists(qa_checklist_path):
        qa_df = pd.read_csv(qa_checklist_path)
    else:  # first run
        qa_df = new_qa_checklist()

    # get fully-verified identifiers
    passed_ids = qa_df[(qa_df["qa"] == 1) & (qa_df["localMove"] == 1)]["identifier"]
    logger.info("Found %d new identifiers that passed QA checks", len(passed_ids.index))

    # move fully-verified files from pending-qa/ to checked/
    checked_dir = os.path.join(dataset, CHECKED_SUBDIR)
    for id in passed_ids:
        identifier_subdir = Identifier.from_str(id).to_dir(is_raw=False)
        dest_path = os.path.join(checked_dir, identifier_subdir)
        os.makedirs(dest_path, exist_ok=True)
        id_files = get_identifier_files(pending_qa_dir, id) or []
        n_moved = 0
        for file in id_files:
            try:
                subprocess.run(["mv", file, dest_path])
                logger.debug("Moved file %s to %s", file, dest_path)
                n_moved += 1
            except subprocess.CalledProcessError as err:
                logger.error("Could not move file %s to %s (%s)", file, dest_path, err)
        logger.info("Moved %d files for identifier %s", n_moved, id)

    # remove fully-verified identifiers from QA checklist
    qa_df = qa_df[~qa_df["identifier"].isin(passed_ids)]
    write_qa_tracker(dataset, qa_df)

    # add fully-verified identifiers to validated file record
    val_records = [new_validation_record(id) for id in passed_ids]
    val_df = pd.DataFrame(val_records)
    record_df = pd.concat(record_df, val_df)
    try:
        write_file_record(dataset, record_df)
    except Exception as err:
        logger.error("Error writing to file record: %s", err)

    # get new raw-validated identifiers
    pending_df = get_pending_files(dataset)
    pending_ids = pending_df[pending_df["passRaw"] == 1]
    new_qa = pending_ids[~pending_ids["identifier"].isin(record_df["identifier"])]

    # copy files for new raw-validated identifiers to pending-qa/
    raw_dir = os.path.join(dataset, RAW_SUBDIR)
    for id in new_qa["identifier"]:
        identifier_subdir = Identifier.from_str(id).to_dir()
        dest_path = os.path.join(pending_qa_dir, identifier_subdir)
        os.makedirs(dest_path, exist_ok=True)
        id_files = get_identifier_files(raw_dir, id) or []
        n_copied = 0
        for file in id_files:
            try:
                subprocess.run(["cp", file, dest_path])
                logger.debug("Copied file %s to %s", file, dest_path)
                n_copied += 1
            except subprocess.CalledProcessError as err:
                logger.error("Could not copy file %s to %s (%s)", file, dest_path, err)
        logger.info("Copied %d files for identifier %s", n_copied, id)

    # add new raw-validated identifiers to QA tracker
    new_qa = new_qa[["identifier", "dataType"]]
    new_qa["dateTime"] = get_timestamp()
    new_qa["user"] = getuser()
    new_qa[["qa", "localMove"]] = 0
    qa_df = pd.concat([qa_df, new_qa])
    qa_df.to_csv(qa_checklist_path)

    # recursively clean up empty directories in pending-qa/
    try:
        n_dirs = clean_empty_dirs(pending_qa_dir)
        logger.info("Cleaned up %d empty directories in pending-qa/", n_dirs)
    except subprocess.CalledProcessError as err:
        logger.error("Error cleaning up empty directories: %s", err)

    print("QA check done!")


def handle_validated():
    pass


if __name__ == "__main__":
    args = get_args()
    dataset = os.path.realpath(args.dataset)
    raw = join(dataset, 'sourcedata/raw')
    checked = join(dataset, 'sourcedata/checked')
    datadict_path = os.path.join(
        dataset, "data-monitoring", "data-dictionary", "central-tracker_datadict.csv"
    )
    dd_df = pd.read_csv(datadict_path, index_col = "variable")
    variable_dict, combination_rows_dict = parse_datadict(dd_df)

    # set up logging to file and console

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    log_path = os.path.join(dataset, LOGGING_SUBPATH)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "[%(asctime)s] (%(levelname)s)\t%(funcname)s(): %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColorfulFormatter(
        "[%(relativeCreated)dms] (%(levelname)s)\t%(message)s"
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # check data dictionary
    try:
        if datadict_has_changes(dataset):
            logger.error("Data dictionary has changed. Please rerun setup.sh.")
            exit(1)
    except FileNotFoundError as err:
        logger.error(err)
        exit(1)
    logger.debug("No changes to data dictionary")
