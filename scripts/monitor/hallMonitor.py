#!/bin/python3

import logging
import os
import re
import subprocess
import time
from getpass import getuser

import pandas as pd

from hmutils import (
    CHECKED_SUBDIR,
    DATADICT_SUBPATH,
    FILE_RE,
    LOGGING_SUBPATH,
    PENDING_QA_SUBDIR,
    RAW_SUBDIR,
    UPDATE_TRACKER_SUBPATH,
    ColorfulFormatter,
    Identifier,
    clean_empty_dirs,
    datadict_has_changes,
    get_args,
    get_datadict,
    get_eeg_errors,
    get_expected_combination_rows,
    get_expected_files,
    get_expected_identifiers,
    get_file_record,
    get_identifier_files,
    get_new_redcaps,
    get_pending_files,
    get_present_identifiers,
    get_psychopy_errors,
    get_qa_checklist,
    get_timestamp,
    get_unique_sub_ses,
    get_variable_datatype,
    meets_naming_conventions,
    new_error_record,
    new_pass_record,
    new_qa_record,
    new_validation_record,
    write_file_record,
    write_pending_errors,
    write_pending_files,
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
    """
    Check if a given value is within the intervals specified in allowed_vals.

    Args:
        allowed_vals (str): A string representing allowed intervals, formatted as "[lower1,upper1][lower2,upper2]..." or "NA, 0, 1".
        value (int): The value to check against the allowed intervals.

    Returns:
        bool: True if the value is within any of the allowed intervals, False otherwise.

    Example:
        allowed_vals = "[1,5][10,15]"
        value = 3
        result = allowed_val(allowed_vals, value)  # Returns True
    """
    allowed_vals = allowed_vals.replace(" ", "")
    
    # Handle case where allowed_vals is a comma-separated list
    if "," in allowed_vals and "[" not in allowed_vals:
        allowed_values = allowed_vals.split(",")
        allowed_values = [val.strip() for val in allowed_values]
        return str(value) in allowed_values

    # Handle case where allowed_vals is a list of intervals
    intervals = re.split(r"[\[\]]", allowed_vals)
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


def checked_data_validation(dataset):
    # initialize variables
    logger = logging.getLogger(__name__)
    errors = []
    dd_df = get_datadict(dataset)
    checked_dir = os.path.join(dataset, CHECKED_SUBDIR)

    logger.info("Starting checked data validation")

    # create present and implied identifier lists
    present_ids = get_present_identifiers(dataset, is_raw=False)
    expected_ids = get_expected_identifiers(dataset, present_ids)
    missing_ids = list(set(present_ids) - set(expected_ids))

    # add errors for missing identifiers
    for id in missing_ids:
        errors.append(
            new_error_record(
                id, "Missing identifier", "Missing identifier in sourcedata/checked/"
            )
        )

    sub_sessions = get_unique_sub_ses(present_ids)

    # check conditions for combination rows
    combo_rows = get_expected_combination_rows(dataset)
    for combo in combo_rows:
        for sub, ses in sub_sessions:
            present_combo_ids = [
                id
                for id in present_ids
                if id.variable in combo.variables
                and id.sub == sub
                and id.session == ses
            ]
            num_combo_vars = len(present_combo_ids)

            if num_combo_vars == 1: # expected case
                continue  

            elif num_combo_vars == 0:  # raise an error for each possible identifier
                for var in combo.variables:
                    identifier = Identifier(sub, var, ses)
                    errors.append(
                        new_error_record(
                            logger,
                            dataset,
                            identifier,
                            "Combination variable error",
                            f"Combination row {combo.name} has no variables present.",
                        )
                    )

            else:  # more than one combination variable present; raise an error for each
                for identifier in present_combo_ids:
                    errors.append(
                        new_error_record(
                            logger,
                            dataset,
                            identifier,
                            "Combination variable error"
                            f"Multiple variables present for combination row {combo.name}, expected one.",
                        )
                    )

    logged_missing_ids = {}  # allow for multiple types of non-identifier-specific errors

    # loop over present identifiers (as Identifier objects)
    present_ids = [Identifier.from_str(id) for id in present_ids]
    missing_ids = [Identifier.from_str(id) for id in missing_ids]
    for id in present_ids:
        # initialize error tracking for this directory if it doesn't exist
        id_dir = id.to_dir(dd_df, is_raw=False)
        if id_dir not in logged_missing_ids:
            logged_missing_ids[id_dir] = set()

        # get files for identifier
        try:
            id_files = get_identifier_files(checked_dir, id, is_raw=False)
            logger.debug("Found %d file(s) for identifier %s", len(id_files), id)
        except FileNotFoundError as err:
            errors.append(
                new_error_record(id, "Improper directory structure", str(err))
            )
            logging.error("Error getting files for identifier %s: %s", id, err)
            continue

        # --- check for exception files, set flags ---
        has_deviation = str(id) + "-deviation.txt" in id_files
        has_no_data = str(id) + "-no-data.txt" in id_files
        logger.debug("has_deviation=%s, has_no_data=%s", has_deviation, has_no_data)
        if has_deviation and has_no_data:
            errors.append(
                new_error_record(
                    id,
                    "Improper exception files",
                    "Both deviation and no-data files present for identifier",
                )
            )

        # --- check naming conventions ---

        # get all files in identifier's directory
        try:
            dir_files = os.listdir(id_dir)
            logger.debug("Found %d file(s) in directory %s", len(dir_files), id_dir)
        except FileNotFoundError as err:
            errors.append(
                new_error_record(id, "Improper directory structure", str(err))
            )
            logging.error("Error getting files for identifier %s: %s", id, err)
            continue

        # construct list of missing identifiers that should be in this directory
        dir_missing_ids = [
            id for id in missing_ids if id.to_dir(dd_df, is_raw=False) == id_dir
        ]

        # handle misnamed files
        misnamed_files = [
            file
            for file in dir_files
            if not meets_naming_conventions(file, has_deviation)
        ]
        logger.debug("Found %d misnamed file(s)", len(misnamed_files))
        for file in misnamed_files:
            if file == "issue.txt":
                err_type = "Issue file"
                err = new_error_record(
                    id, err_type, "Found issue.txt in identifier's directory"
                )
            else:
                err_type = "Improper file name"
                err = new_error_record(
                    id, err_type, "Found file with improper name: " + file
                )
            errors.append(err)

            # log missing identifiers once for this directory and error type
            if err_type not in logged_missing_ids[id_dir]:
                for missing_id in dir_missing_ids:
                    err[id] = str(missing_id)
                    errors.append(err)
                logged_missing_ids[id_dir].add(err_type)

        # handle appropriately named but misplaced files
        correct_files = list(set(id_files) - set(misnamed_files))
        logger.debug("Found %d correctly named file(s)", len(correct_files))
        n_misplaced = 0
        for file in correct_files:
            # figure out which directory the file should be in
            id_match = re.fullmatch(FILE_RE, file)
            file_id = Identifier.from_str(id_match.group("id"))
            correct_dir = os.path.realpath(file_id.to_dir(dd_df, is_raw=False))

            # if the file is not in the right directory, raise errors
            if os.path.realpath(id_dir) != correct_dir:
                n_misplaced += 1
                err = new_error_record(
                    id,
                    "Misplaced file",
                    f"Found file in wrong directory: {file} found in {id_dir}",
                )
                errors.append(err)

                # log missing identifiers once for this directory and error type
                if err_type not in logged_missing_ids[id_dir]:
                    for missing_id in dir_missing_ids:
                        err[id] = str(missing_id)
                        errors.append(err)
                    logged_missing_ids[id_dir].add(err_type)

        logger.debug("Found %d misplaced file(s)", n_misplaced)

        # --- check file presence & count ---

        # handle exception file flags
        if has_no_data:
            # only expect one file called [identifier]-no-data.txt
            expected_files = [f"{id}-no-data.txt"]
        elif has_deviation:
            # expect at least 2 appropriately-named files
            # (deviation.txt and at least one other file)
            expected_files = id_files
            if len(expected_files) == 1:
                errors.append(
                    new_error_record(
                        id,
                        "Improper exception files",
                        "deviation.txt cannot signify only 1 file; use no-data.txt.",
                    )
                )
                logger.debug("Found only deviation.txt; expected more files")
        else:  # normal case
            expected_files = get_expected_files(id, dd_df)

        logger.debug("Expect %d file(s) for identifier %s", len(expected_files), id)

        # check for missing expected files
        n_missing = 0
        for file in expected_files:
            if file not in id_files:
                errors.append(
                    new_error_record(
                        id, "Missing file", f"Expected file {file} not found"
                    )
                )
                n_missing += 1
        logger.debug("Found %d missing files", n_missing)

        # check for unexpected file presence
        n_unexpected = 0
        for file in id_files:
            if file not in expected_files:
                errors.append(
                    new_error_record(
                        id, "Unexpected file", f"Unexpected file {file} found"
                    )
                )
                n_unexpected += 1
        logger.debug("Found %d unexpected files", n_unexpected)

        # --- special data checks ---

        datatype = get_variable_datatype(dd_df, id.variable)

        if datatype == "eeg":
            # do EEG-specific checks
            eeg_errors = get_eeg_errors(logger, dataset, id_files)
            errors.extend(eeg_errors)
            logger.debug("Found %d EEG error(s)", len(eeg_errors))

        elif datatype == "psychopy":
            # do psychopy-specific checks
            psychopy_errors = get_psychopy_errors(logger, dataset, id_files)
            errors.extend(psychopy_errors)
            logger.debug("Found %d psychopy error(s)", len(psychopy_errors))

        continue  # go to next present identifier

    # write errors to pending-errors-[datetime].csv
    error_df = pd.DataFrame(errors)
    timestamp = get_timestamp()
    write_pending_errors(dataset, error_df, timestamp)

    # remove failing identifiers from validated file record
    failing_ids = error_df["identifier"].unique()
    record_df = get_file_record(dataset)
    record_df = record_df[~record_df["identifier"].isin(failing_ids)]
    write_file_record(dataset, record_df)

    return


def raw_data_validation(dataset):
    # initialize variables
    logger = logging.getLogger(__name__)
    pending_df = get_pending_files(dataset)
    logger.info("Starting raw data validation...")

    # create present and implied identifier lists
    present_ids = get_present_identifiers(dataset, is_raw=True)

    # handle missing identifiers
    expected_ids = get_expected_identifiers(dataset, present_ids)
def qa_validation(dataset):
    logger = logging.getLogger(__name__)
    logger.info("Starting QA check...")

    # set up paths and dataframes
    pending_qa_dir = os.path.join(dataset, PENDING_QA_SUBDIR)

    dd_df = get_datadict(dataset)
    record_df = get_file_record(dataset)
    qa_df = get_qa_checklist(dataset)

    # get fully-verified identifiers
    passed_ids = qa_df[(qa_df["qa"] == 1) & (qa_df["localMove"] == 1)]["identifier"]
    logger.info("Found %d identifier(s) that passed QA checks", len(passed_ids.index))

    # move fully-verified files from pending-qa/ to checked/
    checked_dir = os.path.join(dataset, CHECKED_SUBDIR)
    for id in passed_ids:
        id = Identifier.from_str(id)
        identifier_subdir = Identifier.from_str(id).to_dir(dd_df, is_raw=False)
        dest_path = os.path.join(checked_dir, identifier_subdir)
        os.makedirs(dest_path, exist_ok=True)
        dtype = get_variable_datatype(dd_df, id.variable)
        id_files = get_identifier_files(pending_qa_dir, id, dtype)
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
    val_records = [new_validation_record(dd_df, id) for id in passed_ids]
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
        id = Identifier.from_str(id)
        identifier_subdir = id.to_dir(dd_df, is_raw=True)
        dest_path = os.path.join(pending_qa_dir, identifier_subdir)
        os.makedirs(dest_path, exist_ok=True)
        dtype = get_variable_datatype(dd_df, id.variable)
        id_files = get_identifier_files(raw_dir, id, dtype)
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
    new_qa = [new_qa_record(id) for id in new_qa["identifier"]]
    new_qa_df = pd.DataFrame(new_qa)
    qa_df = pd.concat([qa_df, new_qa_df])
    write_qa_tracker(dataset, qa_df)

    # recursively clean up empty directories in pending-qa/
    try:
        n_dirs = clean_empty_dirs(pending_qa_dir)
        logger.info("Cleaned up %d empty directories in pending-qa/", n_dirs)
    except subprocess.CalledProcessError as err:
        logger.error("Error cleaning up empty directories: %s", err)

    print("QA check done!")


if __name__ == "__main__":
    # initialization stage
    args = get_args()
    dataset = os.path.realpath(args.dataset)
    if not os.path.exists(dataset):
        raise FileNotFoundError(f"Dataset {dataset} not found")
    datadict_path = os.path.join(dataset, DATADICT_SUBPATH)
    dd_df = pd.read_csv(datadict_path, index_col="variable")

    # set up logging to file and console

    logger = logging.getLogger(__name__)
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

    logger.debug("Logging set up")

    # rename redcap columns
    redcaps = get_new_redcaps(os.path.join(dataset, RAW_SUBDIR))

    if args.map:
        for rc_file in redcaps:
            df = pd.read_csv(rc_file)
            # build the mapping dictionary
            col_map = {}
            for orig, new in args.map:  # args.map is a list of tuples
                for col in df.columns:
                    if col.startswith(orig + "_"):
                        col_map[col] = re.sub("^" + orig + "_", new + "_", col)
            df.rename(columns=col_map, inplace=True)
            df.to_csv(rc_file, index=False)

    elif args.replace:
        for rc_file in redcaps:
            df = pd.read_csv(rc_file)
            if len(df.columns) != len(args.replace):
                logger.critical(
                    "Column count mismatch in %s: %d vs %d",
                    rc_file,
                    len(df.columns),
                    len(args.replace),
                )
                exit(1)
            df.columns = args.replace
            df.to_csv(rc_file, index=False)

    # check data dictionary
    try:
        if datadict_has_changes(dataset):
            logger.error("Data dictionary has changed. Please rerun setup.sh.")
            exit(1)
    except FileNotFoundError as err:
        logger.error(err)
        exit(1)
    logger.debug("No changes to data dictionary")

    checked_pass = checked_data_validation(dataset)
    raw_data_validation(dataset, checked_pass)
    qa_validation(dataset)

    logger.info("All checks complete")

    # update central tracker
    script_location = os.path.join(dataset, UPDATE_TRACKER_SUBPATH)
    if not os.path.exists(script_location):
        logger.critical("update-tracker.py does not exist at expected location.")
        exit(1)
    try:
        redcaps = get_new_redcaps(os.path.join(dataset, CHECKED_SUBDIR))
        logger.info("Running update-tracker.py...")
        subprocess.check_call(
            [
                "python",
                script_location,
                os.path.join(dataset, CHECKED_SUBDIR),
                dataset,
                ",".join(redcaps),
                "none",
                "true" if args.child_data else "false",
            ]
        )
        logger.info("Finished running update-tracker.py")
    except ValueError as err:
        logger.critical("Could not get redcap files (%s)", err)
        exit(1)
    except subprocess.CalledProcessError as err:
        logger.critical("Could not update central tracker (%s)", err)
        exit(1)

    # everything completed successfully, exit with success
    exit(0)
