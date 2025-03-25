import math
import os
import re
import sys
from collections import defaultdict

import pandas as pd

from hallmonitor.hmutils import (
    REMOTE_REDCAP_PREFIX,
    Identifier,
    get_allowed_suffixes,
    get_datadict,
    get_expected_combination_rows,
    get_new_redcaps,
    get_variable_datatype,
)

COMPLETED_SUFFIX = "_complete"


class c:
    RED = "\033[31m"
    GREEN = "\033[32m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def get_redcap_columns(datadict_df: pd.DataFrame, session: str):
    """Obtains column mappings for all Redcap columns from the data dictionary.

    Args:
        datadict_df (pd.DataFrame): Data dictionary dataframe

    Returns:
        dict[dict[str, str]]: A dict of expected redcaps, and dicts of column mappings from column
        names in the redcap (including Sp. language surveys) to column names in the central tracker,
        drawn from the provenance column in the datadict.
    """
    valid_datatypes = {"consent", "assent", "redcap_data"}
    # only look at REDCap data
    df = datadict_df[datadict_df["dataType"].isin(valid_datatypes)]
    # filter for prov
    cols = {}
    key_counter = defaultdict(lambda: 0)
    allowed_duplicate_columns = []
    for _, row in df.iterrows():
        if isinstance(row["allowedSuffix"], float) and math.isnan(row["allowedSuffix"]):
            allowed_suffixes = [""]
        else:
            allowed_suffixes = str(row["allowedSuffix"]).split(", ")
            allowed_suffixes = [
                x for x in allowed_suffixes if x.startswith(session)
            ]  # only from same session
            allowed_suffixes = ["_" + ses for ses in allowed_suffixes]

        prov = str(row["provenance"]).split()
        if "file:" not in prov or "variable:" not in prov:
            continue

        var_idx = prov.index("variable:")
        rc_variable = str(prov[var_idx + 1]).strip('";,')
        if rc_variable == "":
            rc_variable = str(row["variable"]).lower()

        file_idx = prov.index("file:")
        rc_filename = prov[file_idx + 1].strip('";,')
        if rc_filename not in cols:
            cols[rc_filename] = {}

        if "id:" in prov:
            id_idx = prov.index("id:")
            rc_idcol = prov[id_idx + 1].strip('";,')
            cols[rc_filename]["id_column"] = rc_idcol

        for ses_tag in allowed_suffixes:
            var = row["variable"]
            cols[rc_filename][rc_variable + ses_tag + COMPLETED_SUFFIX] = var + ses_tag
            key_counter[rc_variable + ses_tag + COMPLETED_SUFFIX] += 1
            # also map Sp. surveys to same column name in central tracker if completed
            surv_match = re.fullmatch(
                r"(\w+)(_[a-z0-9]{1,2})?(_scrd[a-zA-Z]+)?(_[a-zA-Z]{2,})?", rc_variable
            )
            if surv_match is not None:
                surv_version = surv_match.group(2) or ""
                scrd_str = surv_match.group(3) or ""
                multiple_report_tag = surv_match.group(4) or ""
                surv_esp = (
                    surv_match.group(1)
                    + "es"
                    + surv_version
                    + scrd_str
                    + multiple_report_tag
                    + ses_tag
                )
                cols[rc_filename][surv_esp + COMPLETED_SUFFIX] = var + ses_tag
                key_counter[surv_esp + COMPLETED_SUFFIX] += 1
            if "consent" in row["dataType"]:
                cols[rc_filename][rc_variable + "es" + COMPLETED_SUFFIX] = var
    for key, value in key_counter.items():
        if value > 1:
            allowed_duplicate_columns.append(key)
    return cols, allowed_duplicate_columns


def get_all_subject_ids(dataset):
    """
    Get a list of subject IDs from the dataset's specified ID REDCap column.

    Args:
        dataset (str): The path to the dataset's base directory.

    Raises:
        ValueError: If the dataset's data dictionary contains an invalid provenance for the ID variable.
        FileNotFoundError: If no file matches the specified REDCap stem.
        FileExistsError: If multiple files match the specified REDCap stem.

    Returns:
        list[int]: A list of the dataset's subject IDs.
    """
    dd_df = get_datadict(dataset)
    redcap_dir = os.path.join(dataset, "sourcedata", "checked", "redcap")
    id_row = dd_df[dd_df["variable"] == "id"].iloc[0]
    id_prov = str(id_row["provenance"])

    filename_match = re.search(r"file:\s*\"([^\s]+)\"", id_prov)
    if filename_match is None:
        raise ValueError(f"No ID REDCap given in provenance '{id_prov}'")
    redcap_stem = filename_match.group(1).lower()

    variable_match = re.search(r"variable:\s*\"([^\s]+)\"", id_prov)
    if variable_match is None:
        raise ValueError(f"No ID variable given in provenance '{id_prov}'")
    id_variable = variable_match.group(1)

    newest_redcaps = get_new_redcaps(redcap_dir)
    matching_redcaps = [
        redcap
        for redcap in newest_redcaps
        if redcap_stem in os.path.basename(redcap).lower()
    ]
    if len(matching_redcaps) == 0:
        raise FileNotFoundError(f"Can't find '{redcap_stem}' REDCap to read IDs from")
    elif len(matching_redcaps) > 1:
        raise FileExistsError(
            f"Found multiple REDCaps matching '{redcap_stem}': {', '.join(matching_redcaps)}"
        )

    redcap_df = pd.read_csv(matching_redcaps[0], usecols={id_variable})
    all_sub_ids = redcap_df[id_variable].astype(int).tolist()
    return all_sub_ids


def get_study_num(dataset):
    """
    Get the study's two-digit study number from allowed values for subject ID.

    Args:
        dataset (str): The path to the dataset's base directory.

    Raises:
        ValueError: If the dataset's study number cannot be determined.

    Returns:
        str: The dataset's two-digit study number.
    """
    dd_df = get_datadict(dataset)
    id_row = dd_df[dd_df["variable"] == "id"].iloc[0]
    allowed_vals = str(id_row["allowedValues"])
    allowed_vals = allowed_vals.replace(" ", "")
    intervals = re.split(r"[\[\]]", allowed_vals)

    for interval in intervals:
        interval = str(interval)
        if interval not in {"", ","}:
            return interval[:2]

    raise ValueError("Could not find study number")


def fill_combination_columns(dataset: str, tracker_df: pd.DataFrame):
    """
    Fill in combination columns by checking for the presence of one or more "child variables".

    Args:
        dataset (str): The path to the dataset's base directory.
        tracker_df (pd.DataFrame): The dataset's central tracker.
    Returns:
        pd.DataFrame: The updated central tracker.
    """
    combination_rows = get_expected_combination_rows(dataset)

    for combo in combination_rows:
        combo_suffixes = get_allowed_suffixes(dataset, combo.name)
        for suffix in combo_suffixes:
            combo_col = f"{combo.name}_{suffix}"
            var_cols = pd.Index([f"{var}_{suffix}" for var in combo.variables])
            # some variables may not be valid for this suffix, skip them
            var_cols = var_cols[var_cols.isin(tracker_df.columns)]
            # we treat the combination column as an aggregator that is 1 if
            #   any of its "child variables" are truthy and 0 otherwise
            tracker_df[combo_col] = tracker_df[var_cols].any(axis="columns").astype(int)

            if (tracker_df[combo_col] == 0).all():
                # if the combination column is all 0, we leave it blank
                tracker_df[combo_col] = ""

    return tracker_df


def fill_status_data_columns(dataset: str, tracker_df: pd.DataFrame):
    """
    Fill in "status" and "data" columns based on their specified values.

    Args:
        dataset (str): The path to the dataset's base directory.
        tracker_df (pd.DataFrame): The dataset's central tracker.
    Returns:
        pd.DataFrame: The updated central tracker.
    """
    dd_df = get_datadict(dataset)
    redcaps = get_new_redcaps(os.path.join(dataset, "sourcedata", "checked", "redcap"))

    status_var_rows = dd_df[dd_df["dataType"] == "visit_status"]
    data_var_rows = dd_df[dd_df["dataType"] == "visit_data"]

    for _, row in status_var_rows.iterrows():
        prov = str(row["provenance"])
        suffixes = get_allowed_suffixes(dataset, row["variable"])
        prov_file = re.search(r'file:\s*"([^"\s]+)"', prov)
        prov_var = re.search(r'variable:\s*"([^"\s]+)"', prov)
        if None not in {prov_file, prov_var}:  # ensure both matches exist
            prov_file = str(prov_file.group(1))
            prov_var = str(prov_var.group(1))

            for suffix in suffixes:
                prov_id_match = re.search(r'id:\s*"([^"\s]+)"', prov)
                if prov_id_match:
                    prov_id = f"{prov_id_match.group(1)}_{suffix}"
                else:
                    prov_id = "record_id"

                # get session from suffix
                ses = suffix.split("_")[0]
                # find matching redcap files
                matching_rc = [
                    rc
                    for rc in redcaps
                    if prov_file.lower() in rc.lower() and ses in rc
                ]
                if len(matching_rc) == 0:
                    continue
                rc_df = pd.read_csv(matching_rc[0])
                # find matching columns in redcap dataframe
                matching_cols = rc_df.columns[
                    (rc_df.columns.str.contains(f"{prov_var}_{suffix}"))
                    & (rc_df.columns.str.endswith(COMPLETED_SUFFIX))
                ]
                if len(matching_cols) == 0:
                    continue
                matching_col = matching_cols[0]
                # set index to the provenance id column
                rc_df = rc_df.set_index(prov_id)
                # get matching column data and convert to int
                matching_col_data = (rc_df[matching_col].astype(int) == 2).astype(int)
                # update tracker dataframe with matching column data
                tracker_df.loc[
                    tracker_df.index.intersection(rc_df.index),
                    row["variable"] + "_" + suffix,
                ] = matching_col_data

    for _, row in data_var_rows.iterrows():
        prov = str(row["provenance"])
        suffixes = get_allowed_suffixes(dataset, row["variable"])
        if "variables:" in prov and "file:" not in prov:
            prov_vars = re.findall(r'"([^"]+)"', prov)
            for suffix in suffixes:
                # create column names by combining each variable with the current suffix
                colnames = [f"{var}_{suffix}" for var in prov_vars]
                # filter out any column names that don't exist in the tracker
                valid_colnames = [col for col in colnames if col in tracker_df.columns]
                if not valid_colnames:
                    continue
                # check if all specified columns are True for each row
                all_true = tracker_df[valid_colnames].all(axis="columns")
                # set the status column to 1 where all components are True
                status_colname = f"{row['variable']}_{suffix}"
                tracker_df[status_colname] = all_true.astype(int)

        elif "file:" in prov:
            prov_files = re.findall(r'"([^\s"]+)"', prov)
            for suffix in suffixes:
                ses = suffix.split("_")[0]
                colname = f"{row['variable']}_{suffix}"
                # set to 1 by default; we set to 0 if any file is missing
                tracker_df[colname] = 1
                for file in prov_files:
                    matching_rc = [
                        rc for rc in redcaps if file.lower() in rc.lower() and ses in rc
                    ]
                    if len(matching_rc) == 0:
                        tracker_df[colname] = 0
                        break
                    rc_df = pd.read_csv(matching_rc[0])
                    common_subjects = tracker_df.index.intersection(rc_df["record_id"])
                    tracker_df.loc[~tracker_df.index.isin(common_subjects), colname] = 0

    return tracker_df


def get_parent_columns(
    datadict_df: pd.DataFrame,
    tracker_df: pd.DataFrame,
    study_no,
    session,
    all_redcap_paths,
):
    """
    Populate parent_identity (pidentity) and parent_language (plang) columns in central tracker (8 = primary
    parent, 9 = secondary parent), return a dict of Redcaps with their respective plang and pidentity columns
    """
    parent_info = defaultdict(list)
    for _, row in datadict_df.iterrows():
        if row["dataType"] == "parent_identity":
            prov = str(row["provenance"]).split()
            if "file:" in prov and "variable:" in prov:
                file_idx = prov.index("file:")
                rc_filename = prov[file_idx + 1].strip('";')
                var_idx = prov.index("variable:")
                rc_variable = prov[var_idx + 1].strip('";')
                parent_info[rc_filename].append(row["variable"])
            else:
                continue
            rc_df = pd.read_csv(all_redcap_paths[rc_filename])
            parent_ids = rc_df[rc_variable].to_list()
            for id in parent_ids:
                child_id_match = re.search(study_no + r"([089])(\d{4})", str(id))
                if child_id_match is None:
                    continue
                child_id = study_no + "0" + child_id_match.group(2)
                child_id = int(child_id)
                parent = study_no + child_id_match.group(1)

                try:
                    for suf in str(row["allowedSuffix"]).split(","):
                        suf = suf.strip()
                        if re.fullmatch(session + r"_e\d$", suf):
                            tracker_df.loc[child_id, row["variable"] + "_" + suf] = int(
                                parent
                            )
                except Exception:  # FIXME
                    continue

        elif row["dataType"] == "parent_lang":
            prov = str(row["provenance"]).split()

            if "file:" not in prov or "variable:" not in prov:
                continue

            idx = prov.index("file:")
            rc_filename = prov[idx + 1].strip('";')
            idx = prov.index("variable:")
            rc_variable = prov[idx + 1].strip('";')
            parent_info[rc_filename].append(row["variable"])

            rc_df = pd.read_csv(all_redcap_paths[rc_filename], index_col="record_id")
            for col in rc_df.columns:
                lang_re = re.match(rc_variable + r"_(s\d+_r\d+_e\d+)", col)
                if lang_re is not None:
                    for _, rc_row in rc_df.iterrows():
                        child_id_match = re.search(
                            study_no + r"[089](\d{4})", str(rc_row.name)
                        )
                        if child_id_match is not None:
                            child_id = study_no + "0" + child_id_match.group(1)
                            child_id = int(child_id)
                            # FIXME consider splitting into constants
                            if rc_row[col] not in {1, 2}:
                                raise ValueError(
                                    f"Unknown value {rc_row[col]} seen for parent language, "
                                    + "should be 1 for English and 2 for Spanish."
                                )

                            try:
                                for suf in str(row["allowedSuffix"]).split(", "):
                                    if re.fullmatch(session + r"_e\d+", suf):
                                        tracker_df.loc[
                                            child_id, row["variable"] + "_" + suf
                                        ] = int(rc_row[col])
                            except Exception:  # FIXME
                                continue

    return dict(parent_info)


def main(
    dataset: str,
    redcaps: list[str],
    session: str,
    child: bool,
    passed_id_list: list[str],
    failed_id_list: list[str],
):
    dataset = os.path.abspath(dataset)
    if not os.path.exists(dataset):
        raise FileNotFoundError(f"{dataset} does not exist")
    elif not os.path.isdir(dataset):
        raise NotADirectoryError(f"{dataset} is not a directory")

    if not redcaps:
        raise ValueError(f"No REDCaps passed for dataset {dataset}")

    if not session:
        raise ValueError(f"No session passed for dataset {dataset}")

    if not passed_id_list and not failed_id_list:
        raise ValueError("No passed or failed identifiers passed")

    passed_ids = [(Identifier.from_str(s), 1) for s in passed_id_list]
    failed_ids = [(Identifier.from_str(s), 0) for s in failed_id_list]
    all_ids = passed_ids + failed_ids
    id_df = pd.DataFrame(
        [
            {
                "id": int(id.subject.removeprefix("sub-")),
                "colname": f"{id.variable}_{id.session}_{id.run}_{id.event}",
                "variable": id.variable,
                "datatype": get_variable_datatype(dataset, id.variable),
                "passed": pass_val,  # 1 for verified IDs, 0 for failing IDs
            }
            for id, pass_val in all_ids
        ]
    )

    dd_df = get_datadict(dataset)
    redcheck_columns, allowed_duplicate_columns = get_redcap_columns(dd_df, session)
    ids = get_all_subject_ids(dataset)
    study_no = get_study_num(dataset)

    tracker_df = get_central_tracker(dataset)
    proj_name = os.path.basename(os.path.normpath(dataset)).removesuffix("-dataset")
    data_tracker_file = os.path.join(
        dataset, "data-monitoring", f"central-tracker_{proj_name}.csv"
    )

    # add new subjects to the central tracker, if there are any
    tracker_ids = tracker_df["id"].tolist()
    new_subjects = list(set(ids).difference(tracker_ids))
    new_subjects_df = pd.DataFrame({"id": new_subjects})
    tracker_df = pd.concat([tracker_df, new_subjects_df])

    tracker_df = tracker_df.set_index("id").sort_index()

    subjects = tracker_df.index.to_list()

    # list of all redcap columns whose names should be mirrored in central tracker
    all_redcap_columns = defaultdict(list)
    all_redcap_paths = dict()

    all_rc_dfs = dict()
    all_rc_subjects = dict()
    for expected_rc in redcheck_columns.keys():
        present = False
        remote_rcs = [
            r
            for r in redcaps
            if os.path.basename(r).startswith(REMOTE_REDCAP_PREFIX + proj_name)
        ]
        normal_rcs = [r for r in redcaps if r not in remote_rcs]

        matching_rcs = list(
            filter(
                lambda rc: expected_rc.lower() in os.path.basename(rc).lower(),
                normal_rcs,
            )
        )
        if len(matching_rcs) == 0:
            raise FileNotFoundError(f"Could not find a file matching {expected_rc}")
        elif len(matching_rcs) > 1:
            raise FileExistsError(
                f'Multiple REDCaps found with name "{expected_rc}" specified in datadict: '
                + ", ".join(matching_rcs)
            )
        else:  # desired case with N=1 match
            redcap_path = matching_rcs[0]
            all_redcap_paths[expected_rc] = redcap_path

        remote_rc = ""
        for redcap in remote_rcs:
            rc_basename = os.path.basename(redcap.lower())
            if expected_rc not in rc_basename:
                continue

            present = True
            if expected_rc in all_redcap_paths:
                # save remote redcap for later
                remote_rc = redcap
            else:
                # treat remote redcap as the only redcap
                redcap_path = redcap
                all_redcap_paths[expected_rc] = redcap

            break

        if not present:
            FileNotFoundError(
                f'Can\'t find redcap "{expected_rc}" specified in datadict'
            )

        # re-index redcap and save to redcheck_columns

        if "id_column" in redcheck_columns[expected_rc].keys():
            # ID column has been specified
            id_col = str(redcheck_columns[expected_rc]["id_column"])
        else:  # no ID column specified, use default
            id_col = "record_id"

        rc_df = pd.read_csv(redcap_path)

        # get matching ID column
        rc_cols = rc_df.columns
        col_matches = rc_cols[rc_cols.str.startswith(id_col)]
        if col_matches.empty:  # column match not found, raise an error
            raise ValueError(f"Column {id_col} not found for RedCAP {redcap_path}")
        rc_id_col = col_matches[0]

        if remote_rc:  # if there is both a remote and in-person redcap...
            remote_df = pd.read_csv(remote_rc)

            # ...ensure that each subject is only in one redcap or the other, then...
            duped_subs = set(remote_df[rc_id_col]) & set(rc_df[rc_id_col])
            if duped_subs:
                raise ValueError(
                    "The following subjects are in the remote-only and in-person REDCaps: "
                    + ", ".join(str(sub) for sub in duped_subs)
                )

            # ...append remote RC to in-person RC, since variables are the same
            rc_df = pd.concat([rc_df, remote_df])

        # re-index rc_df on the selected column
        all_rc_dfs[expected_rc] = rc_df.set_index(rc_id_col)

        # If hallMonitor passes "redcap" arg, data exists and passed checks
        vals = pd.read_csv(redcap_path, header=None, nrows=1).iloc[0, :].value_counts()
        # Exit if duplicate column names in redcap
        if any(vals.values != 1):
            dupes = []
            for rc_col in vals.keys():
                if vals[rc_col] > 1:
                    dupes.append(rc_col)
            raise ValueError(
                f"Duplicate columns found in redcap {redcap_path}: " + ", ".join(dupes)
            )

    for expected_rc in redcheck_columns.keys():
        rc_df = all_rc_dfs[expected_rc]
        rc_subjects = []
        rc_ids = rc_df.index.tolist()
        if child:
            for id in rc_ids:
                # FIXME magic numbers, repeated code
                child_id_match = re.search(study_no + r"[089](\d{4})", str(id))
                if child_id_match is not None:
                    child_id = int(study_no + "0" + child_id_match.group(1))
                    rc_subjects.append(child_id)
        else:
            rc_subjects = rc_ids
        rc_subjects.sort()

        all_rc_subjects[expected_rc] = rc_subjects

        all_keys = dict()
        for key, value in redcheck_columns[expected_rc].items():
            all_keys[key] = value
            if str(key).startswith(("consent", "assent", "id_column")):
                continue
            if (
                not re.match(r"^.*es(?:_[a-zA-Z])?_s\d+_r\d+_e\d+_complete", key)
                and key not in all_rc_dfs[expected_rc].columns
            ):
                other_rcs = []
                other_rc_dfs = {
                    rc: all_rc_dfs[rc] for rc in all_rc_dfs if rc != expected_rc
                }
                for redcap, other_rc_df in other_rc_dfs.items():
                    if key in other_rc_df.columns:
                        other_rcs.append(redcap)
                if len(other_rcs) >= 1:
                    raise KeyError(
                        f'Can\'t find "{key}" in {expected_rc} redcap, but found in '
                        + ", ".join(other_rcs)
                        + " redcaps"
                    )
                else:
                    raise KeyError(f'Can\'t find "{key}" in {expected_rc} redcap')

        for index, row in rc_df.iterrows():
            if (isinstance(index, float) or isinstance(index, int)) and not math.isnan(
                index
            ):
                id = int(row.name)
            else:
                print(
                    "skipping nan value in ",
                    str(all_redcap_paths[expected_rc]),
                    ": ",
                    str(index),
                )
                continue
            if child:
                # FIXME magic numbers
                child_id_match = re.search(study_no + r"[089](\d{4})", str(id))
                if child_id_match is not None:
                    child_id = study_no + "0" + child_id_match.group(1)
                    child_id = int(child_id)
                else:
                    print(
                        str(id),
                        "doesn't match expected child or parent id format of \""
                        + study_no
                        + '{0,8, or 9}XXXX", skipping',
                    )
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
                        if tracker_df.loc[child_id, value] == 1:
                            # if value already set continue
                            continue
                        else:
                            # FIXME magic number
                            tracker_df.loc[child_id, value] = 1 if val == 2 else 0
                    except Exception:  # FIXME
                        # FIXME magic number
                        tracker_df.loc[child_id, value] = 1 if val == 2 else 0
                except Exception:  # FIXME
                    continue

        # for subject IDs missing from redcap, fill in "0" in redcap columns
        for subj in set(subjects).difference(rc_subjects):
            for key, value in keys_in_redcap.items():
                if re.fullmatch(r".*" + session + r"_e\d+", value):
                    try:
                        tracker_df.loc[subj, value] = 0
                    except Exception:  # FIXME
                        continue

        duplicate_cols = []
        # drop any duplicate columns ending in ".NUMBER"
        for col in tracker_df.columns:
            if re.fullmatch(r".*\.\d+", col):
                duplicate_cols.append(col)
        tracker_df.drop(columns=duplicate_cols, inplace=True)
        tracker_df.to_csv(data_tracker_file)

        for col in rc_df.columns:
            if str(col).endswith(COMPLETED_SUFFIX):
                all_redcap_columns[col].append(all_redcap_paths[expected_rc])

    parent_info = get_parent_columns(
        dd_df, tracker_df, study_no, session, all_redcap_paths
    )

    # Fill in "NA"s in parent cols for all subjects not present in redcap
    # FIXME deep nesting with minimal comments
    for expected_rc in redcheck_columns.keys():
        if expected_rc in parent_info.keys():
            for subj in set(subjects).difference(all_rc_subjects[expected_rc]):
                for col in tracker_df.columns:
                    for var in parent_info[expected_rc]:
                        if re.fullmatch(f"{var}_{session}" + r"_e\d+", col):
                            try:
                                tracker_df.loc[subj, col] = None
                            except Exception:  # FIXME
                                continue

    all_duplicate_cols = []
    redcaps_of_duplicates = []
    for col, rcs in all_redcap_columns.items():
        if len(all_redcap_columns[col]) > 1 and col not in allowed_duplicate_columns:
            all_duplicate_cols.append(col)
            redcaps_of_duplicates.append(", ".join(rcs))

    if len(all_duplicate_cols) > 0:
        errmsg = c.RED + "Error: Duplicate columns were found across Redcaps: "
        for i in range(0, len(all_duplicate_cols)):
            errmsg = (
                errmsg
                + all_duplicate_cols[i]
                + " in "
                + redcaps_of_duplicates[i]
                + "; "
            )
        print(errmsg + "Exiting." + c.ENDC)
        raise ValueError(errmsg)

    # update central tracker with a 1 for each fully-verified identifier

    # ...but first, make sure all column names are valid
    invalid_cols = id_df[~id_df["colname"].isin(tracker_df.columns)]["colname"]
    if not invalid_cols.empty:
        print(f"Invalid column(s) found: {', '.join(invalid_cols.unique())}, skipping")
        id_df = id_df[~id_df["colname"].isin(invalid_cols)]

    # ...and do the same for subject IDs

    invalid_ids = id_df[~id_df["id"].isin(tracker_df.index)]["id"]
    if not invalid_ids.empty:
        print(f"Invalid ID(s) found: {', '.join(invalid_ids.unique())}, skipping")
        id_df = id_df[~id_df["id"].isin(invalid_ids)]

    # we're all set, update the tracker with an appropriate pass/fail value
    for _, row in id_df.iterrows():
        tracker_df.loc[int(row["id"]), row["colname"]] = row["passed"]

    # fill in combination columns based on the values of their "child variables"
    tracker_df = fill_combination_columns(dataset, tracker_df)

    # fill in "status"/"data" columns based on their specified values
    tracker_df = fill_status_data_columns(dataset, tracker_df)

    # save the updated tracker as our final step
    tracker_df.to_csv(data_tracker_file)

    # Create more readable csv with no blank columns
    tracker_df = pd.read_csv(data_tracker_file, index_col="id")
    data_tracker_filename = os.path.splitext(data_tracker_file)[0]
    tracker_df_no_blank_columns = tracker_df.loc[:, tracker_df.notnull().any(axis=0)]
    tracker_df_no_blank_columns = tracker_df_no_blank_columns.fillna("NA")
    tracker_df_no_blank_columns.to_csv(data_tracker_filename + "_viewable.csv")

    updated_datatypes = ", ".join(id_df["variable"].unique())
    if updated_datatypes:
        print(c.GREEN + f"Success: {updated_datatypes} data tracker updated." + c.ENDC)
    else:
        print(c.GREEN + "Success: No datatypes updated." + c.ENDC)

    return True


def get_central_tracker(dataset):
    """
    Returns the given dataset's central tracker as a DataFrame.

    Args:
        dataset (str): The path to the dataset's base directory.

    Returns:
        pandas.DataFrame: The dataset's central tracker.
    """
    proj_name = os.path.basename(os.path.normpath(dataset))
    data_tracker_file = os.path.join(
        dataset, "data-monitoring", f"central-tracker_{proj_name}.csv"
    )
    tracker_df = pd.read_csv(data_tracker_file)
    return tracker_df


if __name__ == "__main__":
    dataset = sys.argv[1]
    redcaps = sys.argv[2]
    session = sys.argv[3]
    child = sys.argv[4]
    passed_ids = sys.argv[5]
    failed_ids = sys.argv[6]

    main(
        dataset,
        redcaps.split(","),
        session,
        bool(child == "true"),
        passed_ids.split(","),
        failed_ids.split(","),
    )
    exit(0)
