#!/bin/python3

import logging
import os
import re
import subprocess
from argparse import Namespace
from datetime import datetime

import pandas as pd

from .hmutils import (
    CHECKED_SUBDIR,
    FILE_RE,
    LOGGING_SUBPATH,
    PENDING_QA_SUBDIR,
    PENDING_SUBDIR,
    RAW_SUBDIR,
    UPDATE_TRACKER_SUBPATH,
    ColorfulFormatter,
    Identifier,
    SharedTimestamp,
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
    get_misplaced_redcaps,
    get_naming_errors,
    get_new_redcaps,
    get_pending_errors,
    get_pending_files,
    get_present_identifiers,
    get_psychopy_errors,
    get_qa_checklist,
    get_timestamp,
    get_unique_sub_ses_run,
    get_variable_datatype,
    new_error_record,
    new_pass_record,
    new_qa_record,
    new_validation_record,
    write_file_record,
    write_pending_errors,
    write_pending_files,
    write_qa_tracker,
)


def validate_data(logger, dataset, use_legacy_exceptions=False, is_raw=True):
    """
    Validates the data in the specified dataset.

    Parameters:
        logger (logging.Logger): Logger object for logging information and errors.
        dataset (str): Path to the dataset to be validated.
        is_raw (bool): Flag indicating whether the dataset is raw or checked. Defaults to True.

    Returns:
        list[dict]: A list of error records found during validation.

    The function performs the following checks:
    - Initializes variables and sets the base directory based on the dataset type.
    - Logs the start of the data validation process.
    - Creates lists of present and expected identifiers, and identifies missing identifiers.
    - Adds errors for missing identifiers.
    - Checks conditions for combination rows and adds errors for combination variable issues.
    - Loops over present identifiers to:
        - Initialize error tracking for directories.
        - Get files for each identifier and handle exceptions.
        - Check for exception files and set flags.
        - Check naming conventions and handle misnamed files.
        - Handle appropriately named but misplaced files.
        - Check file presence and count.
        - Perform special data checks based on the datatype (e.g., EEG, psychopy).

    The function logs detailed debug information and errors throughout the validation process.
    """
    # initialize variables
    pending = []
    dd_df = get_datadict(dataset)
    if is_raw:
        base_dir = os.path.join(dataset, RAW_SUBDIR)
    else:
        base_dir = os.path.join(dataset, CHECKED_SUBDIR)

    # create present and implied identifier lists
    present_ids = get_present_identifiers(dataset, is_raw=is_raw)
    expected_ids = get_expected_identifiers(dataset, present_ids)
    missing_ids = list(set(expected_ids) - set(present_ids))
    logger.debug(
        "Found %d present id(s), %d expected id(s), %d missing id(s)",
        len(present_ids),
        len(expected_ids),
        len(missing_ids),
    )

    # raise errors for missing identifiers without a no-data.txt
    for id in missing_ids:
        id.is_missing = True  # included in detailed stringification
        id_as_dir = id.to_dir(dataset, is_raw=is_raw)

        if use_legacy_exceptions:
            no_data_file = "no-data.txt"
        else:
            no_data_file = f"{id}-no-data.txt"

        if any([file == no_data_file for file in os.listdir(id_as_dir)]):
            logger.debug("Skipping %s, no-data.txt found", str(id))
            continue
        pending.append(
            new_error_record(
                logger,
                dataset,
                id,
                "Missing identifier",
                f"Missing identifier in {id_as_dir}",
            )
        )

    sub_ses_run = get_unique_sub_ses_run(present_ids)
    logger.debug("Found %d unique subject/session/run combinations", len(sub_ses_run))

    # check conditions for combination rows
    combo_rows = get_expected_combination_rows(dataset)
    for combo in combo_rows:
        for sub, ses, run in sub_ses_run:
            present_combo_ids = [
                id
                for id in present_ids
                if id.variable in combo.variables
                and not id.is_from_deviation
                and id.subject == sub
                and id.session == ses
                and id.run == run
            ]
            num_combo_vars = len(present_combo_ids)

            if num_combo_vars == 1:  # expected case
                continue

            elif num_combo_vars == 0:  # raise an error for each possible identifier
                for var in combo.variables:
                    identifier = Identifier(sub, var, ses, run)
                    pending.append(
                        new_error_record(
                            logger,
                            dataset,
                            identifier,
                            "Combination variable error",
                            f"Combination row {combo.name} has no variables present.",
                        )
                    )

            else:  # more than one combination variable present; raise an error for each
                logger.debug(
                    "Found %d combination variables for combination row %s",
                    num_combo_vars,
                    combo.name,
                )
                for identifier in present_combo_ids:
                    pending.append(
                        new_error_record(
                            logger,
                            dataset,
                            identifier,
                            "Combination variable error",
                            f"Multiple variables present for combination row {combo.name}, expected one.",
                        )
                    )

    logged_missing_ids = {}  # allow for multiple types of non-identifier-specific errors

    # loop over present identifiers (as Identifier objects)
    for id in present_ids:
        logger.debug("Checking identifier %s", str(id))
        # initialize error tracking for this directory if it doesn't exist
        id_dir = id.to_dir(dataset, is_raw=is_raw)
        logger.debug("Initialized id_dir as %s", id_dir)
        if id_dir not in logged_missing_ids:
            logged_missing_ids[id_dir] = set()

        # get files for identifier
        try:
            datatype = get_variable_datatype(dataset, id.variable)
            logger.debug("Identifier datatype is %s", datatype)
            id_files = get_identifier_files(base_dir, id, datatype, is_raw=is_raw)
            logger.debug("Found %d file(s) for identifier %s", len(id_files), id)
        except FileNotFoundError as err:
            pending.append(
                new_error_record(
                    logger, dataset, id, "Improper directory structure", str(err)
                )
            )
            continue

        # --- check for empty files ---
        for file in id_files:
            if os.path.getsize(file) == 0:
                pending.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "Empty file",
                        f"Found empty file {file}",
                    )
                )

        # --- check naming conventions ---

        # get all files in identifier's directory
        try:
            dir_filenames = os.listdir(id_dir)
            logger.debug(
                "Found %d file(s) in directory %s: %s",
                len(dir_filenames),
                id_dir,
                dir_filenames,
            )
        except FileNotFoundError as err:
            pending.append(
                new_error_record(
                    logger, dataset, id, "Improper directory structure", str(err)
                )
            )
            continue

        # --- check for exception files, set flags ---
        if use_legacy_exceptions:
            has_deviation = "deviation.txt" in dir_filenames
            has_no_data = "no-data.txt" in dir_filenames
        else:
            has_deviation = f"{id}-deviation.txt" in dir_filenames
            has_no_data = f"{id}-no-data.txt" in dir_filenames

        logger.debug("has_deviation=%s, has_no_data=%s", has_deviation, has_no_data)
        if has_deviation and has_no_data:
            pending.append(
                new_error_record(
                    logger,
                    dataset,
                    id,
                    "Improper exception files",
                    "Both deviation and no-data files present for identifier",
                )
            )

        # construct list of missing identifiers that should be in this directory
        dir_missing_ids = [
            id for id in missing_ids if id.to_dir(dataset, is_raw=is_raw) == id_dir
        ]
        logger.debug("Found %d missing identifier(s)", len(dir_missing_ids))

        # handle misnamed files

        if use_legacy_exceptions:
            deviation_file = "deviation.txt"
        else:
            deviation_file = f"{id}-deviation.txt"

        misnamed_files = []
        for file in dir_filenames:
            if file == deviation_file:
                continue
            elif file == "issue.txt":
                pending.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "Issue file",
                        "Found issue.txt in identifier's directory",
                    )
                )
                continue

            naming_errors = get_naming_errors(logger, dataset, file, has_deviation)
            if len(naming_errors) > 0:
                pending.extend(naming_errors)
                logger.debug(
                    "Found %d naming error(s) in file %s", len(naming_errors), file
                )
                misnamed_files.append(file)

        logger.debug("Found %d misnamed file(s)", len(misnamed_files))
        for file in misnamed_files:
            err_type = "Improper file name"
            err_msg = f"Found file with improper name: {file}"

            # log missing identifiers once for this directory and error type
            if err_type not in logged_missing_ids[id_dir]:
                for missing_id in dir_missing_ids:
                    pending.append(
                        new_error_record(
                            logger,
                            dataset,
                            missing_id,
                            err_type,
                            err_msg,
                        )
                    )
                logged_missing_ids[id_dir].add(err_type)
                logger.debug(
                    "Logged error %s for missing identifiers in dir %s",
                    err_type,
                    id_dir,
                )

        # handle appropriately named but misplaced files
        correct_files = list(set(id_files) - set(misnamed_files))
        logger.debug("Found %d correctly named file(s)", len(correct_files))
        n_misplaced = 0
        for file in correct_files:
            # figure out which directory the file should be in
            base_name = os.path.basename(file)
            id_match = re.fullmatch(FILE_RE, base_name)
            file_id = Identifier.from_str(id_match.group("id"))
            try:
                correct_dir = os.path.realpath(file_id.to_dir(dataset, is_raw=is_raw))
            except ValueError:
                logger.debug("File %s contains bad variable name", base_name)
                continue
            logger.debug("Correct directory for file %s is %s", base_name, correct_dir)

            # if the file is not in the right directory, raise errors
            if os.path.realpath(id_dir) != correct_dir:
                n_misplaced += 1
                err_type = "Misplaced file"
                err = new_error_record(
                    logger,
                    dataset,
                    id,
                    err_type,
                    f"Found file in wrong directory: {os.path.basename(file)} found in {id_dir}",
                )
                pending.append(err)

                # log missing identifiers once for this directory and error type
                if err_type not in logged_missing_ids[id_dir]:
                    for missing_id in dir_missing_ids:
                        err[id] = str(missing_id)
                        pending.append(err)
                    logged_missing_ids[id_dir].add(err_type)

        logger.debug("Found %d misplaced file(s)", n_misplaced)

        # --- check file presence & count ---

        # handle exception file flags
        if has_no_data:
            # only expect the "no data" exception file
            if use_legacy_exceptions:
                expected_files = ["no-data.txt"]
            else:
                expected_files = [f"{id}-no-data.txt"]
        elif has_deviation:
            # expect at least 2 appropriately-named files
            # (deviation.txt and at least one other file)
            expected_files = dir_filenames
            if len(expected_files) == 1:
                pending.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "Improper exception files",
                        "deviation.txt cannot signify only 1 file; use no-data.txt.",
                    )
                )
        else:  # normal case
            expected_files = [
                os.path.basename(file) for file in get_expected_files(dataset, id)
            ]

        logger.debug(
            "Expect %d file(s) for identifier %s: %s",
            len(expected_files),
            id,
            expected_files,
        )

        # check for missing expected files
        n_missing = 0
        for file in expected_files:
            if file not in dir_filenames:
                pending.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "Missing file",
                        f"Expected file {file} not found",
                    )
                )
                n_missing += 1
        logger.debug("Found %d missing file(s)", n_missing)

        # check for unexpected file presence
        n_unexpected = 0
        for file in dir_filenames:
            if file not in expected_files:
                pending.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "Unexpected file",
                        f"Unexpected file {file} found",
                    )
                )
                n_unexpected += 1
        logger.debug("Found %d unexpected file(s)", n_unexpected)

        # --- special data checks ---

        datatype = get_variable_datatype(dataset, id.variable)

        if datatype == "eeg":
            # do EEG-specific checks
            eeg_errors = get_eeg_errors(logger, dataset, id_files)
            pending.extend(eeg_errors)
            logger.debug("Found %d EEG error(s)", len(eeg_errors))

        elif datatype == "psychopy":
            # do psychopy-specific checks
            psychopy_errors = get_psychopy_errors(logger, dataset, id_files)
            pending.extend(psychopy_errors)
            logger.debug("Found %d psychopy error(s)", len(psychopy_errors))

        if is_raw:  # only log pass rows for raw data
            # check if this identifier has any errors
            if not any(p["identifier"] == id and p["passRaw"] == 0 for p in pending):
                pending.append(new_pass_record(dataset, id))
                logger.debug("Identifier %s had no errors", str(id))

        continue  # go to next present identifier

    return pending


def checked_data_validation(dataset, use_legacy_exceptions=False):
    logger = logging.getLogger(__name__)
    logger.info("Starting checked data validation...")

    # perform data validation for checked directory
    pending = validate_data(logger, dataset, use_legacy_exceptions, is_raw=False)

    logger.info("Checked data validation complete, found %d errors", len(pending))

    # write errors to pending-errors-[datetime].csv
    # (checked data validation does not have "pending" files)
    pending_df = pd.DataFrame(pending)
    timestamp = SharedTimestamp()
    write_pending_errors(dataset, pending_df, timestamp)

    # remove failing identifiers from validated file record
    failing_ids = pending_df["identifier"].unique()
    record_df = get_file_record(dataset)
    record_df = record_df[~record_df["identifier"].isin(failing_ids)]
    write_file_record(dataset, record_df)

    return  # go to raw data validation


def raw_data_validation(dataset, use_legacy_exceptions=False):
    logger = logging.getLogger(__name__)
    logger.info("Starting raw data validation...")

    # perform data validation for raw directory
    pending = validate_data(logger, dataset, use_legacy_exceptions, is_raw=True)

    errors = [r for r in pending if not r["passRaw"]]
    logger.info("Raw data validation complete, found %d errors", len(errors))
    logger.info("Found %d identifiers with no errors", len(pending) - len(errors))

    # write pending rows to pending-files-[datetime].csv
    pending_df = pd.DataFrame(pending)
    timestamp = SharedTimestamp()
    write_pending_files(dataset, pending_df, timestamp)

    # append errors to pending-errors-[datetime].csv (populated by checked data validation step)
    error_df = get_pending_errors(pending_df)
    write_pending_errors(dataset, error_df, timestamp)

    return  # go to QA checks


def qa_validation(dataset):
    logger = logging.getLogger(__name__)
    logger.info("Starting QA check...")

    # set up paths and dataframes
    pending_qa_dir = os.path.join(dataset, PENDING_QA_SUBDIR)
    raw_dir = os.path.join(dataset, RAW_SUBDIR)
    checked_dir = os.path.join(dataset, CHECKED_SUBDIR)

    record_df = get_file_record(dataset)
    qa_df = get_qa_checklist(dataset)

    # get fully-verified identifiers
    passed_ids = qa_df[qa_df["qa"] & qa_df["localMove"]]["identifier"]
    logger.info("Found %d identifier(s) that passed QA checks", len(passed_ids.index))

    # move fully-verified files from pending-qa/ to checked/
    for id in passed_ids:
        id = Identifier.from_str(id)
        identifier_dir = id.to_dir(dataset, is_raw=True)
        identifier_subdir = os.path.relpath(identifier_dir, raw_dir)
        src_path = os.path.join(pending_qa_dir, identifier_subdir)
        dest_path = os.path.join(checked_dir, identifier_subdir)
        try:
            subprocess.run(["mv", src_path, dest_path], check=True)
            logger.debug("Moved file(s) for ID %s to %s", id, dest_path)
        except subprocess.CalledProcessError as err:
            logger.error("Could not move file(s) for %s to %s (%s)", id, dest_path, err)

    # remove fully-verified identifiers from QA checklist
    qa_df = qa_df[~qa_df["identifier"].isin(passed_ids)]
    write_qa_tracker(dataset, qa_df)

    # add fully-verified identifiers to validated file record
    val_records = [new_validation_record(dataset, id) for id in passed_ids]
    val_df = pd.DataFrame(val_records)
    record_df = pd.concat([record_df, val_df])
    try:
        write_file_record(dataset, record_df)
    except Exception as err:
        logger.error("Error writing to file record: %s", err)

    # get new raw-validated identifiers
    pending_df = get_pending_files(dataset)
    pending_ids = pending_df[pending_df["passRaw"]]
    new_qa = pending_ids[~pending_ids["identifier"].isin(record_df["identifier"])]

    # copy files for new raw-validated identifiers to pending-qa/
    for id in new_qa["identifier"]:
        id = Identifier.from_str(id)
        identifier_dir = id.to_dir(dataset, is_raw=True)
        identifier_subdir = os.path.relpath(identifier_dir, raw_dir)
        dest_path = os.path.join(pending_qa_dir, identifier_subdir, os.pardir)
        dest_path = os.path.abspath(dest_path)
        os.makedirs(dest_path, exist_ok=True)
        try:
            subprocess.run(["cp", "-uR", identifier_dir, dest_path], check=True)
            logger.debug("Copied ID %s to %s, or no update was needed", id, dest_path)
        except subprocess.CalledProcessError as err:
            logger.error("Could not copy file(s) for %s to %s (%s)", id, dest_path, err)

    # add new raw-validated identifiers to QA tracker
    new_qa = [new_qa_record(dataset, id) for id in new_qa["identifier"]]
    new_qa_df = pd.DataFrame(new_qa)
    qa_df = pd.concat([qa_df, new_qa_df])
    write_qa_tracker(dataset, qa_df)

    # recursively clean up empty directories in pending-qa/
    try:
        n_dirs = clean_empty_dirs(pending_qa_dir)
        logger.info("Cleaned up %d empty directories in pending-qa/", n_dirs)
    except subprocess.CalledProcessError as err:
        logger.error("Error cleaning up empty directories: %s", err)

    logger.info("QA check done!")


def main(args: Namespace):
    # initialization stage
    dataset = os.path.realpath(str(args.dataset))
    if not os.path.exists(dataset):
        raise FileNotFoundError(f"Dataset {dataset} not found")

    pending_dir = os.path.join(dataset, PENDING_SUBDIR)
    os.makedirs(pending_dir, exist_ok=True)

    pending_qa_dir = os.path.join(dataset, PENDING_QA_SUBDIR)
    os.makedirs(pending_qa_dir, exist_ok=True)

    # set up logging to file and console

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if args.output:
        log_file = args.output
    else:
        log_path = os.path.join(dataset, LOGGING_SUBPATH)
        os.makedirs(log_path, exist_ok=True)
        file_name = f"hallMonitor-{get_timestamp()}.log"
        log_file = os.path.join(log_path, file_name)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("[%(asctime)s]\t(%(levelname)s)\t%(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    if not args.quiet:
        console_handler = logging.StreamHandler()
        if args.verbose:
            console_handler.setLevel(logging.DEBUG)
        else:
            console_handler.setLevel(logging.INFO)
        console_format = "[%(relativeCreated)-6dms] (%(levelname)s)\t%(message)s"
        if args.no_color:
            console_formatter = logging.Formatter(console_format)
        else:
            console_formatter = ColorfulFormatter(console_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    logger.info("Logging initialized")
    logger.debug("%s", get_timestamp())

    # rename redcap columns

    raw_dir = os.path.join(dataset, RAW_SUBDIR)
    checked_dir = os.path.join(dataset, CHECKED_SUBDIR)
    redcaps = get_new_redcaps(raw_dir)

    # redcaps in the wrong session folder are considered a critical error
    misplaced = get_misplaced_redcaps(redcaps)
    if misplaced:
        msg = f"Found misplaced redcaps: {', '.join(misplaced)}"
        logger.critical(msg)
        raise RuntimeError(msg)

    if args.map:
        for rc_file in redcaps:
            df = pd.read_csv(rc_file)
            # build the mapping dictionary
            col_map = {}
            for orig, new in args.map:  # args.map is a list of tuples
                for col in df.columns:
                    if col.startswith(orig + "_"):
                        col_map[col] = re.sub("^" + orig + "_", new + "_", col)
            df = df.rename(columns=col_map)

            # output RedCAP should be in checked directory with current datetime in file name
            current_dt = datetime.now().strftime("%Y-%m-%d_%H%M")  # 2024-03-20_1522
            rc_base = os.path.basename(rc_file)
            old_dt = re.fullmatch(r".*_DATA_(.+)\.csv", rc_base).group(1)
            rc_base = rc_base.replace(old_dt, current_dt)
            rc_out = os.path.join(checked_dir, "redcap", rc_base)
            df.to_csv(rc_out, index=False)

    elif args.replace:
        for rc_file in redcaps:
            df = pd.read_csv(rc_file)
            if len(df.columns) != len(args.replace):
                msg = (
                    f"Column count mismatch in {rc_file}: {len(df.columns)} vs {len(args.replace)}",
                )
                logger.critical(msg)
                raise ValueError(msg)
            df.columns = args.replace

            # see above
            current_dt = datetime.now().strftime("%Y-%m-%d_%H%M")  # 2024-03-20_1522
            rc_base = os.path.basename(rc_file)
            old_dt = re.fullmatch(r".*_DATA_(.+)\.csv", rc_base).group(1)
            rc_base = rc_base.replace(old_dt, current_dt)
            rc_out = os.path.join(checked_dir, "redcap", rc_base)
            df.to_csv(rc_out, index=False)

    # check data dictionary
    try:
        if datadict_has_changes(dataset):
            msg = "Data dictionary has changed. Please rerun setup.sh."
            logger.error(msg)
            raise ValueError(msg)
    except FileNotFoundError as err:
        logger.error(err)  # ensure this is caught in file logs
        raise err
    logger.debug("No changes to data dictionary")

    use_legacy_exceptions = bool(args.legacy_exceptions)
    logger.debug(
        "Using %s exception file naming",
        "legacy" if use_legacy_exceptions else "standard",
    )

    # limit scope of data validation to raw or checked, if requested
    if args.raw_only:
        logger.info("Only running data validation for sourcedata/raw/")
        raw_data_validation(dataset, use_legacy_exceptions)
    elif args.checked_only:
        logger.info("Only running data validation for sourcedata/checked/")
        checked_data_validation(dataset, use_legacy_exceptions)
    else:
        checked_data_validation(dataset, use_legacy_exceptions)
        raw_data_validation(dataset, use_legacy_exceptions)

    if args.no_qa:
        logger.info("Skipping QA stage")
    else:
        qa_validation(dataset)

    logger.info("All checks complete")

    # update central tracker

    script_location = os.path.join(dataset, UPDATE_TRACKER_SUBPATH)
    if not os.path.exists(script_location):
        msg = "update-tracker.py does not exist at expected location."
        logger.critical(msg)
        raise FileNotFoundError(msg)

    # get passed/failed IDs as specified by pending-files.csv
    pending = get_pending_files(dataset)
    failed_ids = pending[
        (pending["passRaw"] == 0) & (pending["identifier"] != "Unknown Identifier")
    ]["identifier"].unique()
    failed_ids = list(failed_ids)
    passed_ids = pending[~pending["identifier"].isin(failed_ids)]["identifier"].tolist()
    passed_ids = [p for p in passed_ids if Identifier.PATTERN.fullmatch(p)]

    try:
        redcaps = get_new_redcaps(checked_dir)
    except ValueError as err:
        logger.critical("Could not get new redcaps: %s", err)
        raise ValueError("Could not get new redcaps") from err

    universal_redcaps = [
        rc for rc in redcaps if not re.fullmatch(r".*s\d+.*", os.path.basename(rc))
    ]

    ids = get_present_identifiers(dataset)
    unique_sr = set((id.session, id.run) for id in ids)

    failed_sr = []
    for ses, run in sorted(unique_sr):
        sr = f"{ses}_{run}"
        sr_redcaps = [
            rc
            for rc in redcaps
            if re.fullmatch(rf".*{ses}({run})?_DATA.*", os.path.basename(rc))
        ]
        sr_redcaps += universal_redcaps
        try:
            logger.info("Running update-tracker.py for session/run %s...", sr)
            subprocess.check_call(
                [
                    "python",
                    script_location,
                    checked_dir,
                    dataset,
                    ",".join(sr_redcaps),
                    sr,
                    "true" if args.child_data else "false",
                    ",".join(passed_ids),
                    ",".join(failed_ids),
                ]
            )
        except subprocess.CalledProcessError as err:
            logger.error("update-tracker.py failed for ses/run %s (%s)", sr, err)
            failed_sr.append(sr)

    if failed_sr:
        failed_sr = ", ".join(failed_sr)
        msg = f"Could not update tracker for {failed_sr}"
        logger.critical(msg)
        raise RuntimeError(msg)

    success_sr = ", ".join(f"{s}_{r}" for s, r in unique_sr)
    logger.info("Successfully updated tracker for %s ", success_sr)

    # everything completed successfully, return success
    logger.info("hallMonitor pipeline complete")
    return True


if __name__ == "__main__":
    script_args = get_args()
    main(script_args)
