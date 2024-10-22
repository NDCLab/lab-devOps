import argparse
import datetime
import logging
import math
import os
import re
import subprocess
from copy import copy
from dataclasses import dataclass, field
from functools import lru_cache, wraps
from getpass import getuser

import pandas as pd
import pytz

#  :------------------------- formats and paths ------------------------:

DT_FORMAT = r"%Y-%m-%d_%H-%M"
TZ_INFO = pytz.timezone("US/Eastern")
IDENTIFIER_RE = r"(?P<id>(?P<subject>sub-\d+)_(?P<var>[\w\-]+)_(?P<sre>(s\d+_r\d+)_e\d+))"
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
DATASET_DIR = os.path.join("/home", "data", "NDClab", "datasets")
LOGGING_SUBPATH = os.path.join("data-monitoring", "logs", "")
UPDATE_TRACKER_SUBPATH = os.path.join("data-monitoring", "update-tracker.py")

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
    "identifier",
    "errorType",
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


def cache_with_metadata(maxsize=64):
    # wrap a function with an lru_cache decorator, carrying over all
    # metadata / docstring information from the original function.
    def decorator(func):
        cached_func = lru_cache(maxsize=maxsize)(func)

        @wraps(func)
        def wrapper(*args, use_cache=True, **kwargs):
            if use_cache:
                return cached_func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        # allows us to clear the cache externally
        wrapper.cache_clear = cached_func.cache_clear

        return wrapper

    return decorator


@cache_with_metadata(maxsize=64)
def get_variable_datatype(dataset, varname):
    """Retrieve a variable's dataType from the data dictionary

    Args:
        dataset (str): The path to the dataset directory.
        varname (str): The name of the variable to be checked in dd_df

    Raises:
        ValueError: Raised when the number of rows in dd_df matching varname is not exactly 1

    Returns:
        str: The dataType associated with varname
    """
    dd_df = get_datadict(dataset)
    var_rows = dd_df[dd_df["variable"] == varname]
    num_rows = len(var_rows.index)
    if num_rows == 0:
        raise ValueError(f"No variable named {varname}")
    elif num_rows > 1:
        raise ValueError(f"Multiple variables named {varname}")
    else:
        return str(var_rows["dataType"].iloc[0])


def get_allowed_suffixes(dd_df, variable):
    """
    Retrieve the allowed suffixes for a given variable from a data dictionary DataFrame.

    Args:
        dd_df (pd.DataFrame): The data dictionary DataFrame containing variable information.
        variable (str): The variable name for which allowed suffixes are to be retrieved.

    Returns:
        List[str]: A list of allowed suffixes for the specified variable. If no suffixes are allowed,
                   an empty list is returned.

    Raises:
        ValueError: If the specified variable is not found in the data dictionary.
    """
    var_row = dd_df[dd_df["variable"] == variable]
    if var_row.empty:
        raise ValueError(f"Variable {variable} not found in data dictionary")
    allowed = str(var_row["allowedSuffixes"].iloc[0])
    if allowed == "NA":
        return []
    allowed = allowed.split(",") if allowed else []
    allowed = [suffix.strip() for suffix in allowed]
    return allowed


def get_possible_exts(dd_df, variable):
    """
    Retrieve possible file extensions for a given variable from a data dictionary DataFrame.

    Args:
        dd_df (pd.DataFrame): The data dictionary DataFrame containing variable information.
        variable (str): The variable name for which to retrieve possible file extensions.

    Returns:
        list: A list of possible file extensions for the given variable. If no extensions are found,
              an empty list is returned.

    Raises:
        ValueError: If the specified variable is not found in the data dictionary.
    """
    var_row = dd_df[dd_df["variable"] == variable]
    if var_row.empty:
        raise ValueError(f"Variable {variable} not found in data dictionary")
    exts = str(var_row["expectedFileExt"].iloc[0])
    if exts == "NA":
        return []
    exts = exts.split(",") if exts else []
    exts = [ext.strip() for ext in exts]
    return exts


@dataclass
class Identifier:
    PATTERN = re.compile(IDENTIFIER_RE)

    subject: str
    variable: str
    session: str

    def __str__(self):
        s = f"{self.subject}_{self.variable}_{self.session}"
        return s

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash((self.subject, self.variable, self.session))

    def to_dir(self, dataset, is_raw=True):
        """
        Generates a directory path based on the provided DataFrame and whether the data is raw or checked.

        Args:
            dataset (str): The path to the dataset directory.
            is_raw (bool, optional): Flag indicating if the data is raw. Defaults to True.

        Returns:
            str: The generated directory path.
        """
        datatype = get_variable_datatype(dataset, self.variable)
        ses = re.fullmatch(r"(s\d+_r\d+)_e\d+", self.session).group(1)
        # generate full path based on whether the data is raw or checked
        if is_raw:
            return os.path.join(ses, datatype, self.subject, "")
        else:
            return os.path.join(self.subject, ses, datatype, "")

    def to_detailed_str(self, dataset):
        """
        Provides detailed information for the Data Monitor.

        Args:
            dataset (str): The path to the dataset directory.

        Returns:
            str: A string representation of the detailed information, including
                 subject, variable, session, datatype, and whether it is a combination variable.
        """
        datatype = get_variable_datatype(dataset, self.variable)
        s = f"{self.subject}/{self.variable}/{self.session} ({datatype})"
        if is_combination_var(dataset, self.variable):
            s += " (combination)"
        return s

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
        color_levelname = "\033[{0}m{1}\033[0m".format(seq, levelname)
        color_record.levelname = color_levelname
        return logging.Formatter.format(self, color_record)


def validated_dataset(input):
    dataset = os.path.realpath(input)
    # only run on direct children of /home/data/NDClab/datasets
    parent_dir = os.path.realpath(os.path.join(dataset, os.pardir))
    if parent_dir != DATASET_DIR:
        raise argparse.ArgumentTypeError(f"{dataset} is not a valid dataset")
    return dataset


def validated_redcap_replace(input):
    col_re = r"[^:\s]+"
    if not re.fullmatch(col_re, input):
        raise argparse.ArgumentTypeError(
            f"{input} is not a valid replacement column map"
        )
    return input


def validated_redcap_map(input):
    map_re = r"[^:\s]+:[^:\s]+"
    if not re.fullmatch(map_re, input):
        raise argparse.ArgumentTypeError(
            f"{input} is not a valid modification column map"
        )
    return tuple(input.split(":"))


def get_args():
    """Get the arguments passed to hallMonitor

    Returns:
        Namespace: Arguments passed to the script (access using dot notation)
    """
    parser = argparse.ArgumentParser(
        description="The hallMonitor.py script ensures data integrity by validating files within raw and checked directories against a central tracker and data dictionary. It performs checks for expected files, naming conventions, and handles exceptions such as no-data.txt and deviation.txt files. It logs errors for missing, extra, or misnamed files, runs special checks for data types like EEG and Psychopy, and prepares valid files for QA. The script outputs errors and updates logs to assist the data monitor in verifying and resolving issues."
    )
    parser.add_argument(
        "dataset",
        type=validated_dataset,
        help="path to the dataset's root directory (can be relative)",
    )
    parser.add_argument(
        "-c",
        "--child-data",
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
        type=validated_redcap_replace,
        help="replace all REDCap columns with the passed values. e.g. col1 col2 ...",
    )
    redcap_colmap.add_argument(
        "-m",
        "--map",
        nargs="+",
        type=validated_redcap_map,
        help="remap the names of specified REDCap columns. e.g. old1:new1 old2:new2 ...",
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
    latest_df = pd.read_csv(latest_dd_path)

    if not os.path.isfile(dd_path):
        raise FileNotFoundError("Data dictionary not found")
    dd_df = pd.read_csv(dd_path)

    try:
        dd_diff = dd_df.compare(latest_df, align_axis="index")
        return not dd_diff.empty
    except ValueError:
        return True


def get_timestamp():
    dt = datetime.datetime.now(TZ_INFO)
    return dt.strftime(DT_FORMAT)


class SharedTimestamp:
    """
    A singleton class to ensure a shared timestamp across different instances.

    This class is critical to ensure that the timestamp portion of pending-files
    and pending-errors CSVs are identical.

    Attributes:
        _ts (str): A class-level attribute to store the shared timestamp.

    Methods:
        __new__(cls): Overrides the default new method to ensure a single instance
                      of the timestamp is created and shared.
    """
    _ts = None

    def __new__(cls):
        if cls._ts is None:
            cls._ts = get_timestamp()
        return cls._ts


@cache_with_metadata(maxsize=2)
def get_datadict(dataset, index_col=None):
    """Get the data dictionary for the specified dataset.

    Args:
        dataset (str): The dataset's base directory path

    Returns:
        pd.DataFrame: The data dictionary DataFrame
    """
    datadict_path = os.path.join(dataset, DATADICT_SUBPATH)
    if index_col:
        return pd.read_csv(datadict_path, index_col=index_col)
    else:
        return pd.read_csv(datadict_path)


def get_file_record(dataset):
    """Get the file record for the specified dataset. If one
    does not exist, instantiate and return an empty file record.

    Args:
        dataset (str): The dataset's base directory path

    Returns:
        pd.DataFrame: The file record DataFrame
    """
    record_path = os.path.join(dataset, FILE_RECORD_SUBPATH)
    if os.path.exists(record_path):
        return pd.read_csv(record_path)
    else:
        return new_file_record_df()


def write_file_record(dataset, df):
    """Writes out the file record.

    Args:
        dataset (str): The dataset's base directory path
        df (pandas.DataFrame): The file record to be written out

    Raises:
        KeyError: If the DataFrame does not contain the required columns for a file record DataFrame.

    Notes:
    - The DataFrame is first filtered to include only the columns specified in FILE_RECORD_COLS.
    - The DataFrame is then sorted by the 'datetime' and 'identifier' columns before being written to the CSV file.
    """
    record_path = os.path.join(dataset, FILE_RECORD_SUBPATH)
    if set(FILE_RECORD_COLS).issubset(set(df.columns)):  # df has at least FILE_RECORD_COLS
        df = df[FILE_RECORD_COLS]
    else:
        missing_cols = set(FILE_RECORD_COLS) - set(df.columns)
        missing_cols = ", ".join(missing_cols)
        raise KeyError(
            f"DataFrame does not contain required columns for a file record (missing {missing_cols})"
        )

    df = df.sort_values(by=["datetime", "identifier"])
    df.to_csv(record_path, index=False)


@cache_with_metadata(maxsize=64)
def is_combination_var(dataset, variable):
    """Returns bool for whether a variable is present in a combination row
    """
    dd_df = get_datadict(dataset)
    dtype = dd_df[dd_df["variable"] == variable]["dataType"]
    if dtype.empty:
        raise ValueError(f"Variable {variable} not valid")
    combos_df = dd_df[dd_df["dataType"] == "combination"]
    for _, row in combos_df.iterrows():
        prov = str(row["provenance"])
        if "variables:" in prov:
            vars = prov.removeprefix("variables:").strip()
            vars = vars.replace('"', "")
            vars = vars.split(",")
            vars = [v.strip() for v in vars]
            if variable in vars:
                return True
    return False


@cache_with_metadata(maxsize=64)
def get_present_identifiers(dataset, is_raw=True):
    """
    Extracts and returns a list of present identifiers from a dataset directory, excluding combination variables.

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

    present_ids = set()
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
                dtype = get_variable_datatype(dataset, var)
            except KeyError:
                dtype = ""
            except ValueError:  # variable does not exist
                continue
            ses = match.group(5)
            # Check that each identifier matches the subject, session, and datatype corresponding to its
            # directory path. If this does not match up, the identifier is not appended to present_ids.
            if is_raw:
                if not all([ses == dirs[0], dtype == dirs[1], sub == dirs[2]]):
                    continue
            else:
                if not all([sub == dirs[0], ses == dirs[1], dtype == dirs[2]]):
                    continue

            try:
                new_id = Identifier.from_str(identifier)
                present_ids.add(new_id)
            except ValueError:
                continue

    return list(present_ids)


def get_expected_identifiers(dataset, present_ids):
    """
    Generate a list of expected identifiers based on the provided present identifiers and data dictionary DataFrame.

    More specifically, get unique pairs of subject and session from the present identifiers, then get all expected
    variables from the data dictionary that are associated with visit data. Finally, generate all possible combinations
    of subject, session, and variable to create a list of expected identifiers.

    Args:
        present_ids: A list of present identifier strings or Identifier objects.
        dd_df (pandas.DataFrame): A DataFrame containing the data dictionary.

    Returns:
        list of Identifier: A list of expected Identifier objects based on the present identifiers and data dictionary.

    Raises:
        ValueError: If any of the present_ids are not valid strings.
    """
    try:
        present_sub_ses = get_unique_sub_ses(present_ids)
    except ValueError as err:
        raise err

    dd_df = get_datadict(dataset)

    # get rows for visit variables, e.g. iqs_status, bbs_status
    visit_vars = dd_df[dd_df["dataType"] == "visit_data"]

    visit_prov = visit_vars["provenance"]
    visit_prov = visit_prov[visit_prov.str.startswith("variables:")]
    visit_prov = visit_prov.str.removeprefix("variables:").str.strip()
    visit_prov = visit_prov.str.replace('"', "")

    expected_vars = []
    for prov in visit_prov:
        variables = str(prov).split(",")
        variables = [v.strip() for v in variables]
        # exclude combination variables
        for v in variables:
            try:
                if get_variable_datatype(dataset, v) != "combination":
                    expected_vars.append(v)
            except ValueError:  # problematic variable in visit data
                continue

    expected_ids = [
        Identifier(sub, var, ses)
        for sub, ses in present_sub_ses
        for var in expected_vars
    ]

    return expected_ids


@dataclass
class CombinationRow:
    name: str
    variables: list[str]


def get_expected_combination_rows(dataset) -> list[CombinationRow]:
    """
    Extracts and returns a list of expected combination rows from the given dataset.

    Args:
        dataset (str): The dataset's base directory path.

    Returns:
        A list of CombinationRow objects, each representing a combination variable
        and its associated variables as specified in the dataset's data dictionary.
    """
    dd_df = get_datadict(dataset)
    combo_vars = dd_df[dd_df["dataType"] == "combination"]

    expected_combos = []
    for _, row in combo_vars.iterrows():
        prov = str(row["provenance"])
        if prov.startswith("variables:"):
            vars = prov.removeprefix("variables:").strip()
            vars = vars.replace('"', "")
            vars = vars.split(",")
            vars = [v.strip() for v in vars]
            expected_combos.append(CombinationRow(row["variable"], vars))

    return expected_combos


def get_unique_sub_ses(identifiers):
    """Get unique subject-session pairs from a list of identifiers.

    Args:
        identifiers (list): A list of identifiers, which can be strings or Identifier objects.

    Raises:
        ValueError: If any of the identifiers are not valid strings.

    Returns:
        list: A list of unique (subject, session) tuples extracted from the identifiers.
    """
    if not identifiers:
        return []
    if any([isinstance(id, str) for id in identifiers]):
        try:
            identifiers = [Identifier.from_str(str(id)) for id in identifiers]
        except ValueError as err:
            raise err

    sub_ses = [(id.subject, id.session) for id in identifiers]
    sub_ses = list(set(sub_ses))  # remove duplicates
    return sub_ses


def get_identifier_files(basedir, identifier, datatype, is_raw=True):
    """
    Retrieve files matching a specific identifier within a directory structure.

    This function navigates through a directory structure based on the provided
    identifier and returns a list of files that match a predefined pattern.

    Args:
        basedir (str): The base directory from which to start the search.
        identifier (str or Identifier): The identifier used to navigate the directory
            structure. If a string is provided, it will be converted to an Identifier object.
        datatype (str): The identifier's datatype, used to filter the files.
        is_raw (bool, optional): Determines the order of directory traversal.
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

    ses_run_re = r"(s\d+_r\d+)_e\d+"
    ses_run = re.fullmatch(ses_run_re, identifier.session).group(1)

    if is_raw:
        # session / datatype / subject
        dirs = [ses_run, datatype, identifier.subject]
    else:
        # subject / session / datatype
        dirs = [identifier.subject, ses_run, datatype]

    # root all directories at basedir
    dirs[0] = os.path.join(basedir, dirs[0])
    for idx, dirname in enumerate(dirs[1:], start=1):
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
    pending_dir = os.path.join(dataset, PENDING_SUBDIR)
    pending_files = os.listdir(pending_dir)

    PF_RE = r"pending-files-\d{4}-\d{2}-\d{2}_\d{2}-\d{2}\.csv"
    pending_files = [f for f in pending_files if re.fullmatch(PF_RE, f)]

    if pending_files:
        latest_pending = os.path.join(pending_dir, pending_files[-1])
        pending_df = pd.read_csv(latest_pending)
    else:
        pending_df = new_pending_df()

    return pending_df


def write_pending_files(dataset, df, timestamp):
    """
    Writes a DataFrame of pending files to a CSV file in a specified dataset directory.

    Args:
        dataset (str): The path to the dataset directory where the CSV file will be saved.
        df (pandas.DataFrame): The DataFrame containing the pending files data.
        timestamp (str): A timestamp string to be included in the output filename.

    Raises:
        KeyError: If the DataFrame does not contain the required columns specified in PENDING_FILES_COLS.

    The output CSV file will be named in the format 'pending-files-{timestamp}.csv' and will be saved
    in the 'PENDING_SUBDIR' subdirectory of the specified dataset directory. The DataFrame will be
    sorted by 'identifier' and 'datetime' columns before being written to the CSV file.
    """
    out = os.path.join(dataset, PENDING_SUBDIR, f"pending-files-{timestamp}.csv")
    if set(PENDING_FILES_COLS).issubset(set(df.columns)):  # df has at least PENDING_FILES_COLS
        df = df[PENDING_FILES_COLS]
    else:
        missing_cols = set(PENDING_FILES_COLS) - set(df.columns)
        missing_cols = ", ".join(missing_cols)
        raise KeyError(
            f"DataFrame does not contain required columns for a QA checklist (missing {missing_cols})"
        )
    df = df.sort_values(by=["identifier", "datetime"])
    df.to_csv(out, index=False)


def df_from_colmap(colmap):
    """Generates a Pandas DataFrame from a column-datatype dictionary

    Args:
        colmap (dict[str,str]): A dictionary containing entries of the form "name": "float|str|int"

    Returns:
        pandas.DataFrame: An empty DataFrame, generated as specified by colmap
    """
    return pd.DataFrame({col: pd.Series(dtype=dtype) for col, dtype in colmap.items()})


def new_file_record_df():
    colmap = {
        "datetime": "str",
        "user": "str",
        "dataType": "str",
        "identifier": "str",
    }
    return df_from_colmap(colmap)


def new_pending_df():
    """
    Creates a new DataFrame with predefined columns and their data types.

    The DataFrame will have the following columns:
    - datetime (str): The date and time of the entry.
    - user (str): The user associated with the entry.
    - dataType (str): The type of data.
    - identifier (str): A unique identifier for the entry.
    - passRaw (int): A raw pass value.
    - errorType (str): The type of error, if any.
    - errorDetails (str): Details about the error, if any.

    Returns:
        pandas.DataFrame: A DataFrame with the specified columns and data types.
    """
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


def new_error_record(logger, dataset, identifier, error_type, error_details):
    """
    Creates a new error record with the given details and logs it to the logger object.

    Args:
        logger (logging.Logger): The logger object used to log the error.
        dataset (str): The path to the dataset directory.
        identifier (str or Identifier): A unique identifier for the error.
        error_type (str): The type/category of the error.
        error_details (str): Detailed information about the error.

    Returns:
        dict: A dictionary containing the error record with the following keys:
    - "datetime" (str): The timestamp when the error occurred.
    - "user" (str): The user who encountered the error.
    - "passRaw" (bool): Always False, indicating that an error has occurred.
    - "identifier" (str): The unique identifier for the error.
    - "errorType" (str): The type/category of the error.
    - "errorDetails" (str): Detailed information about the error.

    Raises:
        ValueError: If the identifier string cannot be converted to an Identifier object.
    """
    if isinstance(identifier, str):
        try:
            identifier = Identifier.from_str(identifier)
        except ValueError as err:
            raise err

    logger.error(
        "Error occurred with identifier %s: %s - %s",
        identifier.to_detailed_str(dataset),
        error_type,
        error_details,
    )
    return {
        "datetime": get_timestamp(),
        "user": getuser(),
        "passRaw": False,
        "identifier": str(identifier),
        "errorType": error_type,
        "errorDetails": error_details,
    }


def new_pass_record(identifier):
    """
    Creates a new pass record dictionary with the given identifier.

    Args:
        identifier (str): The unique identifier for the pass record.

    Returns:
        dict: A dictionary containing the following keys:
    - "datetime" (str): The current timestamp.
    - "user" (str): The username of the current user.
    - "passRaw" (int): Always True, indicating no error has occurred.
    - "identifier" (str): The provided identifier converted to a string.
    - "errorType" (None): Placeholder for error type, initially None.
    - "errorDetails" (None): Placeholder for error details, initially None.
    """
    return {
        "datetime": get_timestamp(),
        "user": getuser(),
        "passRaw": 1,
        "identifier": str(identifier),
        "errorType": None,
        "errorDetails": None,
    }


def new_validation_record(dataset, identifier):
    """
    Creates a new validation record.

    This function generates a dictionary containing validation information
    based on the provided data dictionary DataFrame and identifier. The
    identifier can be either a string or an instance of the Identifier class.

    Args:
        dataset (str): The path to the dataset directory.
        identifier (str or Identifier): The identifier for which the validation
                                        record is being created. If a string is
                                        provided, it will be converted to an
                                        Identifier instance.

    Returns:
        dict: A dictionary containing the following keys:
            - "datetime" (str): The current timestamp.
            - "user" (str): The username of the current user.
            - "dataType" (str): The data type of the variable associated with
                                the identifier.
            - "identifier" (str): The string representation of the identifier.

    Raises:
        ValueError: If the identifier string cannot be converted to an
                    Identifier instance or if the data type of the variable
                    cannot be determined.
    """
    dd_df = get_datadict(dataset)
    if isinstance(identifier, str):
        try:
            identifier = Identifier.from_str(identifier)
        except ValueError as err:
            raise err

    try:
        datatype = get_variable_datatype(dataset, identifier.variable)
    except ValueError as err:
        raise err

    return {
        "datetime": get_timestamp(),
        "user": getuser(),
        "dataType": datatype,
        "identifier": str(identifier),
    }


def new_qa_record(identifier):
    """
    Creates a new QA record dictionary with the provided identifier.

    Args:
        identifier (str or Identifier): The identifier for the QA record. If a string is provided,
                                        it will be converted to an Identifier object.

    Returns:
        dict: A dictionary containing the QA record with the following keys:
    - "identifier" (str): The string representation of the identifier.
    - "datetime" (str): The current timestamp.
    - "user" (str): The username of the current user.
    - "qa" (int): The QA status, initialized to 0.
    - "localMove" (int): The local move status, initialized to 0.
    - "dataType" (str): The data type of the identifier.

    Raises:
        ValueError: If the identifier string cannot be converted to an Identifier object.
    """
    if isinstance(identifier, str):
        try:
            identifier = Identifier.from_str(identifier)
        except ValueError as err:
            raise err
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
    errors = pending_df[pending_df["passRaw"] == 0]
    # errors has at least PENDING_ERRORS_COLS
    if set(PENDING_ERRORS_COLS).issubset(set(errors.columns)):
        return errors[PENDING_ERRORS_COLS]
    else:
        missing_cols = set(PENDING_ERRORS_COLS) - set(errors.columns)
        missing_cols = ", ".join(missing_cols)
        raise KeyError(
            f"DataFrame does not contain required columns for a pending error CSV (missing {missing_cols})"
        )


def write_pending_errors(dataset, df, timestamp):
    logger = logging.getLogger()
    out = os.path.join(dataset, PENDING_SUBDIR, f"pending-errors-{timestamp}.csv")
    df = df[PENDING_ERRORS_COLS]
    df = df.sort_values(by=["identifier", "datetime"])
    df.to_csv(out, index=False)


def get_qa_checklist(dataset):
    """
    Retrieves or creates a QA checklist for the given dataset.

    This function attempts to read a QA checklist from a specified subpath within the dataset directory.
    If the checklist does not exist, it creates a new one with predefined columns.

    Args:
        dataset (str): The path to the dataset directory.

    Returns:
        pandas.DataFrame: A DataFrame containing the QA checklist.
    """
    checklist_path = os.path.join(dataset, QA_CHECKLIST_SUBPATH)
    if os.path.exists(checklist_path):
        return pd.read_csv(checklist_path)
    else:
        return new_qa_checklist()


def write_qa_tracker(dataset, df):
    """
    Writes a QA checklist to a CSV file within the specified dataset directory.

    Args:
        dataset (str): The path to the dataset directory where the QA checklist will be saved.
        df (pandas.DataFrame): The DataFrame containing the QA checklist data.

    Returns:
        None
    """
    checklist_path = os.path.join(dataset, QA_CHECKLIST_SUBPATH)
    if set(QA_CHECKLIST_COLS).issubset(set(df.columns)):  # df has at least QA_CHECKLIST_COLS
        df = df[QA_CHECKLIST_COLS]
    else:
        missing_cols = set(QA_CHECKLIST_COLS) - set(df.columns)
        missing_cols = ", ".join(missing_cols)
        raise KeyError(
            f"DataFrame does not contain required columns for a QA checklist (missing {missing_cols})"
        )
    df.to_csv(checklist_path, index=False)


def clean_empty_dirs(basedir):
    """
    Removes empty directories within the specified base directory.

    This function uses the `find` command to locate and delete empty directories
    within the given `basedir`. It logs the removal of each directory and returns
    the count of directories removed.

    Args:
        basedir (str): The base directory to search for empty directories.

    Returns:
        int: The number of empty directories removed.

    Raises:
        FileNotFoundError: If basedir does not exist.
        subprocess.CalledProcessError: If the `find` command fails to execute.
    """
    if not os.path.isdir(basedir):
        raise FileNotFoundError(f"Directory {basedir} does not exist")

    try:
        proc = subprocess.run(
            ["find", basedir, "-depth", "-empty", "-type", "d", "-delete", "-print"],
            stdout=subprocess.PIPE,
            check=True,
        )
        dirs = [line for line in proc.stdout.decode().splitlines() if line]
        return len(dirs)
    except subprocess.CalledProcessError as err:
        raise err


def get_visit_pairs(datadict: pd.DataFrame):
    vars = datadict[["variable", "dataType", "provenance"]]
    vars["root"] = vars["variable"].str.removesuffix("_status").str.removesuffix("_data")

    # get visit status vars, strip out type suffix
    status_vars = vars[vars["dataType"] == "visit_status"]
    # ignore results that did not have the type suffix
    status_vars = status_vars[status_vars["root"] != status_vars["variable"]]
    # disregard provenance column for status vars
    status_vars = status_vars.drop(columns=["provenance"])
    # rename column to avoid collision on merge
    status_vars.rename(columns={"variable": "statusvar"}, inplace=True)

    data_vars = vars[vars["dataType"] == "visit_data"]
    data_vars.rename(columns={"variable": "datavar"}, inplace=True)

    # TODO Does this drop all rows without root match? It should, so figure out how to make that happen if not.
    var_pairs = status_vars.merge(data_vars, on="root")

    visit_pairs = []
    for _, pair in var_pairs.iterrows():
        if "variables:" in pair["provenance"]:
            data_files = get_datafiles_from_provenance(pair["provenance"])
            visit_pairs += VisitPair(pair["datavar"], pair["statusvar"], data_files)
    return visit_pairs


def get_datafiles_from_provenance(provenance: str):
    idx = provenance.find('variables:') + len('variables:')
    provenance = provenance[idx:] # take the substring after "variables"
    task_files = []
    for task in provenance.split(","):
        task = task.strip("\";, ")
        task_files.append(task)
    return task_files


def get_expected_files(dataset, identifier):
    """
    Generate a list of expected file names based on the provided identifier and a DataFrame.

    Args:
        dataset (str): The path to the dataset directory.
        identifier (str | Identifier): The identifier for which to generate expected file names.
                                        It can be a string or an instance of the Identifier class.

    Returns:
        list: A list of expected file names with the appropriate extensions.

    Raises:
        ValueError: If the identifier string or its variable is invalid.
    """
    if isinstance(identifier, str):
        try:
            identifier = Identifier.from_str(identifier)
        except ValueError:
            raise ValueError("Invalid identifier string")

    dd_df = get_datadict(dataset)

    expected_exts = dd_df[dd_df["variable"] == identifier.variable]["expectedFileExt"]
    if expected_exts.empty:
        raise ValueError(f"Variable {identifier.variable} has no extensions")
    expected_exts = expected_exts.iloc[0]
    expected_exts = str(expected_exts).strip('"').replace(" ", "").split(",")
    expected_files = [f"{identifier}.{ext}" for ext in expected_exts if ext]
    return expected_files

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

def parse_datadict(dd_df):
    dd_dict = dict()
    task_vars = []
    combination_rows = {}
    allowed_subs = dd_df.loc["id", "allowedValues"]
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
            #dd_dict[var] = [row["dataType"], allowed_sfxs, expected_exts, row["encrypted"]]
            allowed_sfxs = [x.strip() for x in row["allowedSuffix"].split(",")]
            expected_exts = [x.strip() for x in row["expectedFileExt"].split(",")]
            dd_dict[var] = [row["dataType"], allowed_sfxs, expected_exts]
    return dd_dict, combination_rows, allowed_subs

def meets_naming_conventions(logger, dataset, filename, dd_dict, allowed_subs, has_deviation=False):
    """
    Check if a filename meets the naming conventions for a data file.

    Args:
        logger (logging.Logger): The logger object used to log the error.
        dataset (str): The path to the dataset directory.
        filename (str): The name of the file to check.
        dd_dict (dict): Dictionary containing information about each variable drawn from the datadict.
        allowed_subs (str): String of allowed values for a subject ID in interval notation
        has_deviation (bool, optional): A flag indicating if the file has a deviation. Defaults to False.

    Returns:
        errors: List of errors associated with the file name.
    """
    errors = []
    file_match = re.fullmatch(FILE_RE, filename)
    if not file_match:
        errors.append(
            new_error_record(
                logger,
                dataset,
                "Unknown", #? I forget how we said we'd deal with this
                "Naming error",
                f"File {filename} does not match expected identifier format"
            )
        )
        return errors
    id = file_match.group("id")
    var = file_match.group("var")
    datatype, allowed_suffixes, possible_exts = dd_dict[var]
    allowed_subs = allowed_subs
    combination_rows = {}
    if file_match.group('ext') not in dd_dict[var][2] and len(file_match.group('ext')) > 0:
        errors.append(
            new_error_record(
                logger,
                dataset,
                id,
                "Naming error",
                f"File extension {file_match.group('ext')} doesn't match expected extensions {str(dd_dict[var][2])} in file {filename}"
            )
        )
    if file_match.group('subject')[4:] != '' and not allowed_val(allowed_subs, file_match.group('subject')[4:]):
        errors.append(
            new_error_record(
                logger,
                dataset,
                id,
                "Naming error",
                f"Subject number {file_match.group('subject')[4:]} not an allowed subject value {str(allowed_subs)} in file {filename}"
            )
        )
    if datatype not in file_match.group('var'):
        errors.append(
            new_error_record(
                logger,
                dataset,
                id,
                "Naming error",
                f"Variable name {file_match.group('var')} does not contain the name of the variable datatype {datatype}"
            )
        )
    if file_match.group('sre') not in allowed_suffixes:
        errors.append(
            new_error_record(
                logger,
                dataset,
                id,
                "Naming error",
                f"Suffix {file_match.group('sre')} not in allowed suffixes {str(allowed_suffixes)}"
            )
        )
    # Other checks to perform elsewhere: session matches enclosing folder, datatype matches enclosing folder, subject matches enclosing folder
    return errors

def get_eeg_errors(logger, dataset, files):
    """
    Checks for errors in EEG files by verifying the consistency of header (.vhdr), marker (.vmrk), and data (.eeg) files.

    Args:
        logger (logging.Logger): The logger object used to log errors.
        dataset (str): The path to the dataset directory.
        files (list of str): List of file paths to check. The list should contain paths to .vhdr, .vmrk, and .eeg files.

    Returns:
        list: A list of error records if any inconsistencies are found. Each error record is generated by the `new_error_record` function.

    Raises:
        ValueError: If any identifier found in the file names is invalid.
    """
    errors = []
    if not files:
        return []

    ids = []
    misnamed = []
    for file in files:
        id_match = re.match(FILE_RE, os.path.basename(file))
        if id_match is None:
            misnamed.append(file)
        else:
            ids.append(id_match.group("id"))

    if misnamed:
        raise ValueError(f"Invalid EEG file name(s) {', '.join(misnamed)}")

    id = ids[0]

    # don't error on missing files here, since they are handled in presence checks
    headerfile = markerfile = datafile = ""
    for file in files:
        file_ext = os.path.splitext(file)[1]
        if file_ext == ".vhdr":
            headerfile = file
        elif file_ext == ".vmrk":
            markerfile = file
        elif file_ext == ".eeg":
            datafile = file

    expected_eeg = os.path.basename(datafile) if datafile else "(no file)"
    expected_vmrk = os.path.basename(markerfile) if markerfile else "(no file)"

    if headerfile:
        with open(headerfile, "r") as f:
            contents = f.read()

        # look for .vmrk file in header file
        marker_match = re.search(r"MarkerFile=(.+)", contents)
        if marker_match is not None:
            found_markerfile = marker_match.group(1).strip()
            if found_markerfile != expected_vmrk:
                errors.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "EEG error",
                        f"Incorrect MarkerFile {found_markerfile} in .vhdr file, expected {expected_vmrk}",
                    )
                )
        else:
            errors.append(
                new_error_record(
                    logger,
                    dataset,
                    id,
                    "EEG error",
                    "No MarkerFile found in .vhdr file",
                )
            )

        # look for .eeg file in header file
        data_match = re.search(r"DataFile=(.+)", contents)
        if data_match is not None:
            found_datafile = data_match.group(1)
            if found_datafile != expected_eeg:
                errors.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "EEG error",
                        f"Incorrect DataFile {found_datafile} in .vhdr file, expected {expected_eeg}",
                    )
                )
        else:
            errors.append(
                new_error_record(
                    logger, dataset, id, "EEG error", "No DataFile found in .vhdr file"
                ),
            )

    if markerfile:
        with open(markerfile, "r") as f:
            contents = f.read()

        # look for .eeg file in marker file
        data_match = re.search(r"DataFile=(.+)", contents)
        if data_match:
            found_datafile = data_match.group(1).strip("'\" ")
            if found_datafile != expected_eeg:
                errors.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "EEG error",
                        f"Incorrect DataFile {found_datafile} in .vmrk file, expected {expected_eeg}",
                    )
                )
        else:
            errors.append(
                new_error_record(
                    logger, dataset, id, "EEG error", "No DataFile found in .vmrk file"
                )
            )

    return errors


def get_psychopy_errors(logger, dataset, files):
    """
    Checks for errors in PsychoPy output files.

    This function examines a list of files to determine if there are any errors
    in the PsychoPy output. It specifically checks for inconsistencies between
    .log, .csv, and .psydat files.

    Args:
        logger (logging.Logger): The logger object used to log errors.
        dataset (str): The path to the dataset directory.
        files (list of str): List of file paths to check. The list can contain
                             .csv, .log, and .psydat files.

    Returns:
        list: A list of error records. Each error record is generated by the
              `new_error_record` function and contains details about the error
              found.

    Raises:
        ValueError: If the identifier found in the file name is invalid, or if no ID column is found.
    """
    errors = []
    if not files:
        return []

    ids = []
    misnamed = []
    for file in files:
        id_match = re.match(FILE_RE, os.path.basename(file))
        if id_match is None:
            misnamed.append(file)
        else:
            ids.append(id_match.group("id"))

    if misnamed:
        raise ValueError(f"Invalid Psychopy file name(s) {', '.join(misnamed)}")

    id_num = ids[0]

    # don't error on missing files here, since they are handled in presence checks
    csvfile = logfile = psydatfile = ""
    for file in files:
        file = str(file)
        file_ext = os.path.splitext(file)[1]
        if file_ext == ".csv":
            csvfile = file
        elif file_ext == ".log":
            logfile = file
        elif file_ext == ".psydat":
            psydatfile = file

    expected_csv = os.path.basename(csvfile) if csvfile else "(no file)"
    expected_psydat = os.path.basename(psydatfile) if psydatfile else "(no file)"

    if logfile:
        with open(logfile, "r") as f:
            contents = f.read()

        psydat_match = re.search(r"saved data to\s(.+\.psydat)", contents)
        if psydat_match is not None:
            found_psydat = psydat_match.group(1).strip("'\" ")
            found_psydat = os.path.basename(found_psydat)
            if found_psydat != expected_psydat:
                errors.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "Psychopy error",
                        f"Incorrect .psydat file {found_psydat} in .log file, expected {expected_psydat}",
                    )
                )
        else:
            errors.append(
                new_error_record(
                    logger,
                    dataset,
                    id,
                    "Psychopy error",
                    "No .psydat file found in .log file",
                )
            )

        csv_match = re.search(r"saved data to\s(.+\.csv)", contents)
        if csv_match is not None:
            found_csv = csv_match.group(1).strip("'\" ")
            found_csv = os.path.basename(found_csv)
            if found_csv != expected_csv:
                errors.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "Psychopy error",
                        f"Incorrect .csv file {found_csv} in .log file, expected {expected_csv}",
                    )
                )
        else:
            errors.append(
                new_error_record(
                    logger,
                    dataset,
                    id,
                    "Psychopy error",
                    "No .csv file found in .log file",
                )
            )

    # functionality ported from check-id.py:
    #   if csv is present, make sure id inside matches file name
    if csvfile:
        # leading zeroes are significant for subject ID, so read as string
        file_df = pd.read_csv(csvfile, dtype=str)
        if "id" in file_df:
            id_col = file_df["id"]
        # Column sometimes called "participant"
        elif "participant" in file_df:
            id_col = file_df["participant"]
        else:
            raise ValueError("No ID column found in .csv file")

        if id_col.isna().any():
            errors.append(
                new_error_record(
                    logger,
                    dataset,
                    id,
                    "Psychopy error",
                    f"NaN value seen under ID in .csv file, expected {id_num}",
                )
            )

        else:
            bad_ids = id_col[id_col != id_num]
            if not bad_ids.empty:
                errors.append(
                    new_error_record(
                        logger,
                        dataset,
                        id,
                        "Psychopy error",
                        f"ID value(s) [{', '.join(bad_ids)}] in csvfile different from ID in filename ({id_num})",
                    )
                )

    return errors


def get_new_redcaps(basedir):
    """
    Retrieves the newest REDCap files from a given directory.

    This function searches through the specified dataset directory for files
    that match a specific naming convention, extracts the unique stems, and
    returns the most recent file for each unique stem.

    Args:
        basedir (str): The path to the directory to search for REDCap files.

    Returns:
        list[str]: A list of the newest REDCap files for each unique stem.

    Raises:
        ValueError: If a file does not follow the expected naming convention.
    """
    redcaps = []
    for root, _, files in os.walk(basedir):
        for file in files:
            redcaps.append(os.path.join(root, file))

    time_stamp_re = r"\d{4}-\d{2}-\d{2}_\d{4}"
    stem_re = r"_DATA_" + time_stamp_re + r"\.csv$"

    rc_arr = []
    for file in redcaps:
        stem = re.search(stem_re, file)
        if stem:
            rc_arr.append(file[: stem.start()])

    unique_rcs = sorted(set(rc_arr))

    newest_files = []
    for unique_rc in unique_rcs:
        newest_time = None
        newest_file = None
        for file in redcaps:
            if file.startswith(unique_rc):
                file_time = re.search(time_stamp_re, file)
                if file_time:
                    file_time = file_time.group()
                    if not newest_time or file_time > newest_time:
                        newest_time = file_time
                        newest_file = file

        if newest_file:
            segment = re.search(stem_re, newest_file)
            if not segment:
                raise ValueError(
                    f"Error: Improper stem name in {newest_file}, does not follow convention."
                )
            newest_files.append(newest_file)

    return newest_files
