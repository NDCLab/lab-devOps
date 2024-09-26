import argparse
import datetime
import logging
import os
import re
import subprocess
from copy import copy
from dataclasses import dataclass, field
from getpass import getuser

import pandas as pd
import pytz

#  :------------------------- formats and paths ------------------------:

DT_FORMAT = r"%Y-%m-%d_%H-%M"
TZ_INFO = pytz.timezone("US/Eastern")
IDENTIFIER_RE = r"(?P<id>(?P<subject>sub-\d+)_(?P<var>\D+)_(?P<sre>(s\d+_r\d+)_e\d+))"
FILE_RE = IDENTIFIER_RE + r"(?P<info>_[\w\-]+)?(?P<ext>(?:\.[a-zA-Z0-9]+)+)"

FILE_RECORD_SUBPATH = os.path.join("data-monitoring", "validated-file-record.csv")
DATADICT_SUBPATH = os.path.join(
    "data-monitoring", "data-dictionary", "central-tracker_datadict.csv"
)
DATADICT_LATEST_SUBPATH = os.path.join(
    "data-monitoring", "data-dictionary", "central-tracker_datadict_latest.csv"
)
PENDING_SUBDIR = os.path.join("data-monitoring", "pending", "")
RAW_SUBDIR = os.path.join("sourcedata", "raw", "")
CHECKED_SUBDIR = os.path.join("sourcedata", "checked", "")
PENDING_QA_SUBDIR = os.path.join("sourcedata", "pending-qa", "")
QA_CHECKLIST_SUBPATH = os.path.join(PENDING_QA_SUBDIR, "qa-checklist.csv")
DATASET_DIR = os.path.join("/home", "data", "NDClab", "datasets", "")
LOGGING_SUBPATH = os.path.join("data-monitoring", "logs", "")

FILE_RECORD_COLS = [
    "datetime",
    "user",
    "dataType",
    "identifier",
]
PENDING_FILES_COLS = [
    "datetime",
    "user",
    "passRaw",
    "identifier",
    "errorType",
    "errorDetails",
]
PENDING_ERRORS_COLS = [
    "datetime",
    "user",
    "dataType",
    "errorType",
    "identifier",
    "errorDetails",
]
QA_CHECKLIST_COLS = [
    "datetime",
    "user",
    "dataType",
    "identifier",
    "qa",
    "localMove",
]

#  :------------------- helper functions and classes -------------------:


def get_variable_datatype(dd_df, varname):
    """Retrieve a variable's dataType from the data dictionary

    Args:
        dd_df (pd.DataFrame): The project's data dictionary as a DataFrame
        varname (str): The name of the variable to be checked in dd_df

    Raises:
        ValueError: Raised when the number of rows in dd_df matching varname is not exactly 1

    Returns:
        str: The dataType associated with varname
    """
    var_rows = dd_df[dd_df["variable"] == varname]
    num_rows = len(var_rows.index)
    if num_rows == 0:
        raise ValueError(f"No variable named {varname}")
    elif num_rows > 1:
        raise ValueError(f"Multiple variables named {varname}")
    else:
        return str(var_rows["dataType"].iloc[0])


@dataclass
class Identifier:
    PATTERN = re.compile(IDENTIFIER_RE)

    subject: str
    variable: str
    session: str

    def __str__(self):
        s = f"{self.subject}_{self.variable}_{self.session}"
        return s

    def to_dir(self, dataset, is_raw=True):
        """
        Generates a directory path for the given dataset based on the data type and whether the data is raw or checked.

        Args:
            dataset (str): The dataset's base path.
            is_raw (bool, optional): Flag indicating if the data is raw. Defaults to True.

        Returns:
            str: The generated directory path, rooted at dataset.
        """
        dd_df = get_datadict(dataset)
        datatype = get_variable_datatype(dd_df, self.variable)
        # generate full path based on whether the data is raw or checked
        if is_raw:
            return os.path.join(dataset, self.session, datatype, self.subject, "")
        else:
            return os.path.join(dataset, self.subject, self.session, datatype, "")

    @staticmethod
    def from_str(input):
        """Instantiate an Identifier from an identifier string

        Args:
            input (str): The input to parse into an Identifier object

        Raises:
            ValueError: Raised when input is not a valid identifier string

        Returns:
            Identifier: An Identifier object with fields corresponding to the input string
        """
        match = Identifier.PATTERN.fullmatch(input)
        if not match:
            raise ValueError("Passed string is not a valid data identifier")
        sub_id = match.group("subject")
        var = match.group("var")
        sre = match.group("sre")
        return Identifier(sub_id, var, sre)


@dataclass
class VisitPair:
    data_var: str
    status_var: str
    data_files: list[str]


class ColorfulFormatter(logging.Formatter):
    COLORMAP = {
        "DEBUG": 37,  # white
        "INFO": 32,  # green
        "WARNING": 33,  # yellow
        "ERROR": 31,  # red
        "CRITICAL": 41,  # white on red bg
    }

    def __init__(self, pattern):
        logging.Formatter.__init__(self, pattern)

    def format(self, record):
        color_record = copy(record)
        levelname = color_record.levelname
        seq = self.COLORMAP.get(levelname, 37)  # default white
        color_levelname = "\033[{1}m{2}\033[0m".format(seq, levelname)
        color_record.levelname = color_levelname
        return logging.Formatter.format(self, color_record)


def dataset(input):
    dataset = os.path.realpath(input)
    # only run on direct children of /home/data/NDClab/datasets
    parent_dir = os.path.abspath(os.path.join(dataset, os.pardir))
    if parent_dir != DATASET_DIR:
        raise argparse.ArgumentTypeError(f"{dataset} is not a valid dataset")
    return dataset


def redcap_replace(input):
    map_re = r"[^:]+"
    if not re.fullmatch(map_re, input):
        raise argparse.ArgumentTypeError(
            f"{input} is not a valid replacement column map"
        )
    return input


def redcap_modify(input):
    map_re = r"[^:\s]+:[^:\s]+"
    if not re.fullmatch(map_re, input):
        raise argparse.ArgumentTypeError(
            f"{input} is not a valid modification column map"
        )
    return input


def get_args():
    """Get the arguments passed to hallMonitor

    Returns:
        Namespace: Arguments passed to the script (access using dot notation)
    """
    parser = argparse.ArgumentParser(description="")  # TODO: Write a short description
    parser.add_argument(
        "dataset",
        type=dataset,
        help="path to the dataset's root directory (can be relative)",
    )
    parser.add_argument(
        "-c",
        "--child-data",
        dest="childdata",  # could this be removed? will default be child_data?
        action="store_true",
        help="dataset includes child data",
    )

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print additional debugging information to the console",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="do not print any information to the console",
    )

    redcap_colmap = parser.add_mutually_exclusive_group()
    redcap_colmap.add_argument(
        "-r",
        "--replace",
        nargs="+",
        type=redcap_replace,
        help="replace all REDCap columns with the passed values. e.g. col1 col2 ...",
    )
    redcap_colmap.add_argument(
        "-m",
        "--modify",
        nargs="+",
        type=redcap_modify,
        help="modify the names of specified REDCap columns. e.g. old1:new1 old2:new2 ...",
    )

    return parser.parse_args()


def datadict_has_changes(dataset):
    """Check whether the given dataset has changes in its project data dictionary

    Args:
        dataset (str): The dataset's base directory path

    Raises:
        FileNotFoundError: Raised when the project data dictionary
            or "latest" data dictionary is not found

    Returns:
        bool: True if there is a difference between the project data dictionary
            and the latest data dictionary, False otherwise
    """
    dd_path = os.path.join(dataset, DATADICT_SUBPATH)
    latest_dd_path = os.path.join(dataset, DATADICT_LATEST_SUBPATH)

    if not os.path.isfile(latest_dd_path):
        raise FileNotFoundError("Latest data dictionary not found")
    latest_df = pd.read_csv(latest_dd_path, index_col="variable")

    if not os.path.isfile(dd_path):
        raise FileNotFoundError("Data dictionary not found")
    dd_df = pd.read_csv(dd_path, index_col="variable")

    try:
        dd_diff = dd_df.compare(latest_df)
        return bool(dd_diff.empty)
    except ValueError:
        return False

    return bool(dd_diff.empty)


def get_timestamp():
    dt = datetime.datetime.now(TZ_INFO)
    return dt.strftime(DT_FORMAT)


def get_datadict(dataset):
    """Get the data dictionary for the specified dataset.

    Args:
        dataset (str): The dataset's base directory path

    Returns:
        pd.DataFrame: The data dictionary DataFrame
    """
    datadict_path = os.path.join(dataset, DATADICT_SUBPATH)
    return pd.read_csv(datadict_path)


def get_file_record(dataset):
    """Get the file record for the specified dataset. If one
    does not exist, instantiate and return an empty file record.

    Args:
        dataset (str): The dataset's base directory path

    Returns:
        pd.DataFrame: The file record DataFrame
    """
    logger = logging.getLogger()
    record_path = os.path.join(dataset, FILE_RECORD_SUBPATH)
    if os.path.exists(record_path):
        record_df = pd.read_csv(record_path)
        logger.debug("Read in existing file record from %s", record_path)
    else:
        logger.debug("Existing file record not found at %s, making new", record_path)
        colmap = {
            "datetime": "str",
            "user": "str",
            "dataType": "str",
            "identifier": "str",
        }
        record_df = df_from_colmap(colmap)
    return record_df


def write_file_record(dataset, df):
    """Writes out the file record.

    Args:
        dataset (str): The dataset's base directory path
        df (pandas.DataFrame): The file record to be written out
    """
    logger = logging.getLogger()
    record_path = os.path.join(dataset, FILE_RECORD_SUBPATH)
    df = df[FILE_RECORD_COLS]

def get_present_identifiers(dataset, is_raw=True):
    """
    Extracts and returns a list of present identifiers from a dataset directory.

    This function traverses the directory structure of the given dataset and
    extracts identifiers from filenames that match a specific pattern. The
    directory structure and filename patterns differ based on whether the data
    is raw or checked.

    Args:
        dataset (str): The path to the dataset directory.
        is_raw (bool, optional): A flag indicating whether the dataset is raw
                                 or checked. Defaults to True.

    Returns:
        list: A list of identifiers extracted from the filenames in the dataset
              directory.
    """
    SES_RE = r"s\d+_r\d+"
    DTYPE_RE = r"\D+"
    SUB_RE = r"sub-\d+"

    if is_raw:
        source_dir = os.path.join(dataset, RAW_SUBDIR)
        FIRST_RE, SECOND_RE, THIRD_RE = SES_RE, DTYPE_RE, SUB_RE
    else:
        source_dir = os.path.join(dataset, CHECKED_SUBDIR)
        FIRST_RE, SECOND_RE, THIRD_RE = SUB_RE, SES_RE, DTYPE_RE

    dd_df = get_datadict(dataset)

    present_ids = []
    for path, _, files in os.walk(source_dir):
        relpath = os.path.relpath(path, source_dir)
        dirs = relpath.split("/")
        if len(dirs) != 3:
            continue
        # Check if directory names match expected format
        regex_dir_pairs = zip((FIRST_RE, SECOND_RE, THIRD_RE), dirs)
        if not all(re.fullmatch(regex, dir) for regex, dir in regex_dir_pairs):
            continue
        # Extract identifiers from filenames
        id_matches = [
            match for filename in files if (match := re.fullmatch(FILE_RE, filename))
        ]
        for match in id_matches:
            identifier = match.group("id")
            sub = match.group("subject")
            try:
                var = match.group("var")
                dtype = get_variable_datatype(dd_df, var)
            except KeyError:
                dtype = ""
            ses = match.group(5)
            # Check that each identifier matches the subject, session, and datatype corresponding to its
            # directory path. If this does not match up, the identifier is not appended to present_ids.
            if is_raw:
                if not all(ses == dirs[0], dtype == dirs[1], sub == dirs[2]):
                    continue
            else:
                if not all(sub == dirs[0], ses == dirs[1], dtype == dirs[2]):
                    continue
            present_ids.append(identifier)

    return present_ids

def get_identifier_files(basedir, identifier, datatype, raw_order=True):
    """
    Retrieve files matching a specific identifier within a directory structure.

    This function navigates through a directory structure based on the provided
    identifier and returns a list of files that match a predefined pattern.

    Args:
        basedir (str): The base directory from which to start the search.
        identifier (str or Identifier): The identifier used to navigate the directory
            structure. If a string is provided, it will be converted to an Identifier object.
        datatype (str): The identifier's datatype, used to filter the files.
        raw_order (bool, optional): Determines the order of directory traversal.
            If True, the order is session/datatype/subject. If False, the order is
            subject/session/datatype. Defaults to True.

    Returns:
        list: A list of file paths, rooted at basedir, that match
        the identifier pattern within the final directory.

    Raises:
        ValueError: If the identifier string cannot be converted to an Identifier object.
        FileNotFoundError: If any of the directories in the path do not exist.
    """
    if isinstance(identifier, str):
        try:
            identifier = Identifier.from_str(identifier)
        except ValueError as err:
            raise err

    if raw_order:
        # session / datatype / subject
        dirs = [identifier.session, datatype, identifier.subject]
    else:
        # subject / session / datatype
        dirs = [identifier.subject, identifier.session, datatype]

    # root all directories at basedir
    dirs[0] = os.path.join(basedir, dirs[0])
    for idx, dirname in enumerate(dirs, 1):
        dirs[idx] = os.path.join(dirs[idx - 1], dirname)

    for dirname in dirs:
        if not os.path.isdir(dirname):
            raise FileNotFoundError(f"Could not find directory {dirname}")

    id_files = [
        os.path.join(dirs[-1], file)
        for file in os.listdir(dirs[-1])
        if re.fullmatch(FILE_RE, file)
    ]

    return id_files


def get_pending_files(dataset):
    """Get the most recent pending file. If one does not
    exist, instantiate and return an empty pending DataFrame.

    Args:
        dataset (str): The dataset's base directory path

    Returns:
        pd.DataFrame: The pending file DataFrame
    """
    logger = logging.getLogger()

    pending_dir = os.path.join(dataset, PENDING_SUBDIR)
    pending_files = os.listdir(pending_dir)
    logger.debug("Found %d file(s) in %s", len(pending_files), pending_dir)

    PF_RE = r"pending-files-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}\.csv"
    pending_files = [f for f in pending_files if re.fullmatch(PF_RE, f)]
    logger.debug("Found %d pending file(s) in %s", len(pending_files), pending_dir)

    if pending_files:
        latest_pending = os.path.join(pending_dir, pending_files[-1])
        pending_df = pd.read_csv(latest_pending)
        logger.debug("Read in pending file from %s", latest_pending)
    else:
        logger.debug("Existing pending file not found, making new")
        pending_df = new_pending_df()

    return pending_df


def write_pending_files(dataset, df, timestamp):
    logger = logging.getLogger()
    out = os.path.join(dataset, PENDING_SUBDIR, f"pending-files-{timestamp}.csv")
    df = df[PENDING_FILES_COLS]
    df = df.sort_values(by=["identifier", "datetime"])
    df.to_csv(out)
    logger.debug("Wrote pending files to %s", out)


def df_from_colmap(colmap):
    """Generates a Pandas DataFrame from a column-datatype dictionary

    Args:
        colmap (dict[str,str]): A dictionary containing entries of the form "name": "float|str|int"

    Returns:
        pandas.DataFrame: An empty DataFrame, generated as specified by colmap
    """
    df = pd.DataFrame({c: pd.Series(dtype=t) for c, t in colmap.items()})
    return df


def new_pending_df():
    colmap = {
        "datetime": "str",
        "user": "str",
        "dataType": "str",
        "identifier": "str",
        "passRaw": "int",
        "errorType": "str",
        "errorDetails": "str",
    }
    return df_from_colmap(colmap)


def new_error_record(identifier, error_type, error_details):
    """Generates and returns a new error record.

    Args:
        identifier (str|Identifier): The identifier that the record is about
        error_type (str): The general class of the error
        error_details (str): A more detailed description of the error

    Returns:
        dict[str,str]: The error record with all fields populated
    """
    return {
        "datetime": get_timestamp(),
        "user": getuser(),
        "passRaw": False,
        "identifier": str(identifier),
        "errorType": error_type,
        "errorDetails": error_details,
    }


def new_pass_record(identifier):
    """Generates and returns a new passing record.

    Args:
        identifier (str|Identifier): The identifier that the record is about

    Returns:
        dict: The passing record with all fields populated
    """
    return {
        "datetime": get_timestamp(),
        "user": getuser(),
        "passRaw": 1,
        "identifier": str(identifier),
        "errorType": None,
        "errorDetails": None,
    }


def new_qa_record(identifier):
    if isinstance(identifier, str):
        identifier = Identifier.from_str(identifier)
    return {
        "identifier": str(identifier),
        "datetime": get_timestamp(),
        "user": getuser(),
        "qa": 0,
        "localMove": 0,
        "dataType": identifier.datatype,
    }


def new_qa_checklist():
    """
    Creates a new QA checklist DataFrame with predefined column names and types.

    The columns and their corresponding data types are:
    - "datetime": str
    - "user": str
    - "dataType": str
    - "identifier": str
    - "qa": int
    - "localMove": int

    Returns:
        pd.DataFrame: A DataFrame with the specified columns and data types.
    """
    colmap = {
        "datetime": "str",
        "user": "str",
        "dataType": "str",
        "identifier": "str",
        "qa": "int",
        "localMove": "int",
    }
    return df_from_colmap(colmap)

def get_pending_errors(pending_df):
    errors = pending_df[pending_df["passRaw"] == False]
    errors = errors[PENDING_ERRORS_COLS]
    return errors


def write_pending_errors(dataset, df, timestamp):
    logger = logging.getLogger()
    out = os.path.join(dataset, PENDING_SUBDIR, f"pending-errors-{timestamp}.csv")
    df = df[PENDING_ERRORS_COLS]
    df = df.sort_values(by=["identifier", "datetime"])
    df.to_csv(out)
    logger.debug("Wrote pending errors to %s", out)


def get_qa_tracker(dataset):
    logger = logging.getLogger()
    checklist_path = os.path.join(dataset, QA_CHECKLIST_SUBPATH)
    if os.path.exists(checklist_path):
        checklist_df = pd.read_csv(checklist_path)
        logger.debug("Read in QA checklist from %s", checklist_path)
    else:
        logger.debug("QA checklist not found at %s, making new", checklist_path)
        checklist_df = new_qa_checklist()
    return checklist_df


def write_qa_tracker(dataset, df):
    logger = logging.getLogger()
    checklist_path = os.path.join(dataset, QA_CHECKLIST_SUBPATH)
    df = df[QA_CHECKLIST_COLS]
    df.to_csv(checklist_path)
    logger.debug("Wrote QA checklist to %s", checklist_path)


def remove_from_checked(dataset, identifier):
    pass


def clean_empty_dirs(basedir):
    """Starting at the lowest level, recursively remove all
    empty directories under `basedir`. `basedir` is preserved even
    if all directories under it are removed.

    Args:
        basedir (str): A path to the base directory to be cleaned

    Returns:
        int: The number of empty directories cleaned by this function
    """
    logger = logging.getLogger()

    if not os.path.isdir(basedir):
        logger.error("%s is not a valid directory", basedir)
        return 0

    proc = subprocess.run(
        [
            "find",
            basedir,
            "-depth",
            "-empty",
            "-type",
            "d",
            "-delete",
            "-print",
        ],
        stdout=subprocess.PIPE,
    )
    dirs = [line for line in proc.stdout.decode().splitlines() if line]
    for dir in dirs:
        logger.debug("Removed empty directory %s", dir)

    return len(dirs)


def get_visit_pairs(datadict: pd.DataFrame):
    vars = datadict[["variable", "dataType", "provenance"]]
    vars["root"] = vars["variable"].str.removesuffix("_status")

    # get visit status vars, strip out type suffix
    status_vars = vars[vars["dataType"] == "visit_status"]
    # ignore results that did not have the type suffix
    status_vars = status_vars[status_vars["root"] != status_vars["variable"]]
    # disregard provenance column for status vars
    status_vars = status_vars.drop(columns=["provenance"])
    # rename column to avoid collision on merge
    status_vars.rename(columns={"variable": "statusvar"})

    data_vars = vars[vars["dataType"] == "visit_data"]
    data_vars = data_vars[data_vars["root"] != data_vars["variable"]]
    data_vars.rename(columns={"variable": "datavar"})

    # TODO Does this drop all rows without root match? It should, so figure out how to make that happen if not.
    var_pairs = list(status_vars.merge(data_vars, on="root"))

    visit_pairs = []
    for pair in var_pairs:
        data_files = get_datafiles_from_provenance(pair["provenance"])
        visit_pairs += VisitPair(pair["datavar"], pair["statusvar"], data_files)

    return visit_pairs


def get_datafiles_from_provenance(provenance: str):
    # TODO: Write this method
    pass


def meets_naming_conventions(filename, has_deviation=False):
    """
    Check if a filename meets the naming conventions for a data file.

    Args:
        filename (str): The name of the file to check.
        has_deviation (bool, optional): A flag indicating if the file has a deviation. Defaults to False.

    Returns:
        bool: True if the filename meets the naming conventions, False otherwise.
    """
    file_match = re.fullmatch(FILE_RE, filename)
    if not file_match:
        return False
    elif not has_deviation and file_match.group("info"):
        return False
    else:
        return True


def get_eeg_errors(files):
    """
    Checks for errors in EEG files by verifying the consistency of header (.vhdr), marker (.vmrk), and data (.eeg) files.

    Args:
        files (list of str): List of file paths to check. The list should contain paths to .vhdr, .vmrk, and .eeg files.

    Returns:
        list: A list of error records if any inconsistencies are found. Each error record is generated by the `new_error_record` function.

    Raises:
        ValueError: If the identifier found in the file name is invalid.
    """
    errors = []
    id = re.match(FILE_RE, files[0])
    if id is None:
        raise ValueError("Invalid EEG file name")
    id = id.group("id")

    # don't error on missing files here, since they are handled in presence checks
    headerfile = markerfile = datafile = None
    for file in files:
        file_ext = os.path.splitext(file)[1]
        if file_ext == ".vhdr":
            headerfile = file
        elif file_ext == ".vmrk":
            markerfile = file
        elif file_ext == ".eeg":
            datafile = file

    if headerfile:
        with open(headerfile, "r") as f:
            contents = f.read()

        # look for .vmrk file in header file
        marker_match = re.match(r"MarkerFile=(.+)", contents)
        if marker_match is not None:
            found_markerfile = marker_match.group(1).strip()
            if found_markerfile != markerfile:
                errors.append(
                    new_error_record(
                        id,
                        "EEG error",
                        f"Incorrect MarkerFile {found_markerfile} in .vhdr file, expected {markerfile}",
                    )
                )
        else:
            errors.append(
                new_error_record(
                    id,
                    "EEG error",
                    "No MarkerFile found in .vhdr file",
                )
            )

        # look for .eeg file in header file
        data_match = re.search(r"DataFile=(.+)", contents)
        if data_match is not None:
            found_datafile = data_match.group(1).strip("'\" ")
            if found_datafile != datafile:
                errors.append(
                    new_error_record(
                        id,
                        "EEG error",
                        f"Incorrect DataFile {found_datafile} in .vhdr file, expected {datafile}",
                    )
                )
        else:
            errors.append(
                new_error_record(id, "EEG error", "No DataFile found in .vhdr file")
            )

    if markerfile:
        with open(markerfile, "r") as f:
            contents = f.read()

        # look for .eeg file in marker file
        data_match = re.search(r"DataFile=(.+)", contents)
        if data_match:
            found_datafile = data_match.group(1).strip("'\" ")
            if found_datafile != datafile:
                errors.append(
                    new_error_record(
                        id,
                        "EEG error",
                        f"Incorrect DataFile {found_datafile} in marker file, expected {datafile}",
                    )
                )
        else:
            errors.append(
                new_error_record(id, "EEG error", "No DataFile found in .vmrk file")
            )

    return errors


def get_psychopy_errors(files):
    """
    Checks for errors in PsychoPy output files.

    This function examines a list of files to determine if there are any errors
    in the PsychoPy output. It specifically checks for inconsistencies between
    .log, .csv, and .psydat files.

    Args:
        files (list of str): List of file paths to check. The list can contain
                             .csv, .log, and .psydat files.

    Returns:
        list: A list of error records. Each error record is generated by the
              `new_error_record` function and contains details about the error
              found.

    Raises:
        ValueError: If the identifier found in the file name is invalid.
    """
    errors = []
    id = re.match(FILE_RE, files[0])
    if id is None:
        raise ValueError("Invalid EEG file name")
    id = id.group("id")

    # don't error on missing files here, since they are handled in presence checks
    csvfile = logfile = psydatfile = None
    for file in files:
        file_ext = os.path.splitext(file)[1]
        if file_ext == ".csv":
            csvfile = file
        elif file_ext == ".log":
            logfile = file
        elif file_ext == ".psydat":
            psydatfile = file

    if logfile:
        with open(logfile, "r") as f:
            contents = f.read()

        psydat_match = re.search(r"saved data to\s(.+\.psydat)", contents)
        if psydat_match is not None:
            found_psydat = psydat_match.group(1).strip("'\" ")
            found_psydat = os.path.basename(found_psydat)
            if found_psydat != psydatfile:
                errors.append(
                    new_error_record(
                        id,
                        "Psychopy error",
                        f"Incorrect .psydat file {found_psydat} in .log file, expected {psydatfile}",
                    )
                )
        else:
            errors.append(
                new_error_record(
                    id, "Psychopy error", "No .psydat file found in .log file"
                )
            )

        csv_match = re.search(r"saved data to\s(.+\.csv)", contents)
        if csv_match is not None:
            found_csv = csv_match.group(1).strip("'\" ")
            found_csv = os.path.basename(found_csv)
            if found_csv != csvfile:
                errors.append(
                    new_error_record(
                        id,
                        "Psychopy error",
                        f"Incorrect .csv file {found_csv} in .log file, expected {csvfile}",
                    )
                )
        else:
            errors.append(
                new_error_record(
                    id, "Psychopy error", "No .csv file found in .log file"
                )
            )

    return errors