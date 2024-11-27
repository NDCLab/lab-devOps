import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

import pandas as pd


@dataclass
class ExpectedError:
    """
    Represents an expected error with its type, details, and expected occurrence.

    Attributes:
        error_type (str): The type of the error (e.g., "Empty file").
        info_regex (str): A regex pattern to match the error details.
        multiplicity (int): The number of times this error is expected to occur. Default is 1.
    """

    error_type: str
    info_regex: str
    multiplicity: int = 1


class TestCase(ABC):
    """
    A base class for generating test cases by modifying a base dataset.

    Attributes:
        basedir (str): The base directory containing test case data.
        case_name (str): The name of the test case.
        description (str): A description of the test case.
        conditions (list[str]): A list of conditions applied in the test case.
        expected_output (str): A description of the expected output for the test case.
        case_dir (str): The directory where the test case files will be written.
    """

    BASE_SUBJECT_ID = 3000000
    SUB_PLACEHOLDER = "3XXXXXX"

    BASE_SUBJECT_SUBDIR = os.path.join("base_subject", "")
    TEST_CASES_SUBDIR = os.path.join("test_cases", "")

    def __init__(
        self, basedir, sub_id, case_name, description, conditions, expected_output
    ):
        """
        Initialize a TestCase.

        Args:
            basedir (str): The base directory containing test case data.
            sub_id (int): The subject ID assigned to the test case.
            case_name (str): The name of the test case.
            description (str): A description of the test case.
            conditions (list[str]): A list of conditions applied in the test case.
            expected_output (str): A description of the expected output for the test case.
        """
        self.basedir = basedir
        self.sub_id = sub_id
        self.case_name = case_name
        self.description = description
        self.conditions = conditions
        self.expected_output = expected_output

        self.base_sub_dir = os.path.join(basedir, self.BASE_SUBJECT_SUBDIR)
        self.case_dir = os.path.join(basedir, self.TEST_CASES_SUBDIR, case_name)
        self.rel_data_dir = os.path.join("sourcedata", "checked", f"sub-{self.sub_id}")

    def read_base_files(self) -> dict[str, str]:
        """
        Read all files in the base subject directory.

        Returns:
            dict[str,str]: A dictionary where keys are filenames and values are file contents.
        """
        base_files = {}

        for root, _, files in os.walk(self.base_sub_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.base_sub_dir)

                rel_path = rel_path.replace(
                    f"sub-{self.BASE_SUBJECT_ID}", f"sub-{self.sub_id}"
                )

                with open(file_path, "r") as f:
                    content = f.read()

                base_files[rel_path] = content.replace(
                    str(TestCase.BASE_SUBJECT_ID), str(self.sub_id)
                )

        return base_files

    def write_files(self, files: dict[str, str]):
        """
        Write the modified files to the test case directory.

        Args:
            files (dict[str,str]): A dictionary where keys are relative paths to files and values are file contents.
        """
        for rel_path, content in files.items():
            full_path = os.path.join(self.case_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w") as f:
                f.write(content)

    def build_path(self, ses: str, datatype: str, filename: str):
        """
        Constructs a file path by joining the base directory with session, datatype, and filename.

        Args:
            ses (str): The session identifier.
            datatype (str): The datatype.
            filename (str): The name of the file.

        Returns:
            str: The constructed file path.
        """
        p = os.path.join(self.rel_data_dir, ses, datatype, filename)
        return p

    def write_metadata(self):
        """
        Write metadata for the test case to a JSON file.

        Metadata includes the test case name, description, conditions, and expected output.
        """
        metadata = {
            "test_case": self.case_name,
            "description": self.description,
            "conditions": self.conditions,
            "expected_output": self.expected_output,
            "subject": f"sub-{self.sub_id}",
        }
        with open(os.path.join(self.case_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

    @property
    @abstractmethod
    def behavior_to_test(self) -> str:
        """Return a short description of the behavior being tested."""
        pass

    @property
    @abstractmethod
    def conditions(self) -> list[str]:
        """Return a list of conditions applied in the test case."""
        pass

    @abstractmethod
    def modify(self, base_files: dict[str, str]) -> dict[str, str]:
        """
        Apply modifications to the base files.

        Args:
            base_files (dict[str,str]): A dictionary where keys are filenames and values are file contents.

        Returns:
            dict[str,str]: A dictionary where keys are filenames and values are modified file contents.
        """
        pass

    @abstractmethod
    def get_expected_errors(self) -> list[ExpectedError]:
        """
        Generate a list of ExpectedError instances for this object.

        This method defines the expected errors that may occur,
        using dynamically generated file paths and error messages
        specific to the current object's state. Each error is
        represented as an ExpectedError instance.

        Returns:
            list[ExpectedError]: A list of ExpectedError objects
            encapsulating the error type and associated message.
        """
        pass

    def generate(self):
        """
        Generate the test case by reading the base subject, applying modifications,
        and writing the modified files and metadata.
        """
        os.makedirs(self.case_dir)
        base_files = self.read_base_files()
        modified_files = self.modify(base_files)
        self.write_files(modified_files)
        self.write_metadata()

    def run_validate_data(self):
        """
        Run validate_data() on the generated data directory and collect errors.

        Returns:
            pd.DataFrame: A DataFrame containing the errors reported by validate_data.
        """
        from hallmonitor.hallMonitor import validate_data

        # set up a logger to save hallMonitor output
        logger = logging.getLogger(f"{self.case_name}_logger")
        logger.setLevel(logging.ERROR)
        logger.propagate = False

        pending = validate_data(
            logger,
            dataset=self.case_dir,
            legacy_exceptions=False,
            is_raw=False,
        )

        pending_df = pd.DataFrame(pending)
        # 'datetime' and 'user' columns do not matter for verifying output
        cols_to_drop = ["datetime", "user"]
        if all(c in pending_df.columns for c in cols_to_drop):
            pending_df.drop(columns=cols_to_drop, inplace=True)

        return pending_df

    def compare_errors(self, generated_errors_df: pd.DataFrame):
        """
        Compare the generated errors DataFrame with the gold standard errors.

        Args:
            generated_errors_df (pd.DataFrame): A DataFrame containing the errors generated by validate_data.

        Raises:
            AssertionError: If there are differences between the generated errors and the gold standard errors.
        """
        expected_errors = self.get_expected_errors()

        # check for missing errors
        missing = []
        for error in expected_errors:
            matching_errors = generated_errors_df[
                (generated_errors_df["errorType"] == error.error_type)
                & (generated_errors_df["errorDetails"].str.fullmatch(error.info_regex))
            ]
            if len(matching_errors.index) < error.multiplicity:
                n_missing = error.multiplicity - len(matching_errors.index)
                missing.append(
                    f"{error.error_type}: {error.info_regex} (missing {n_missing})"
                )

        # check for extraneous errors
        extra = []
        for _, row in generated_errors_df.iterrows():
            is_expected = any(
                row["errorType"] == error.error_type
                and re.fullmatch(error.info_regex, row["errorDetails"])
                for error in expected_errors
            )
            if not is_expected:
                extra.append(f'{row["errorType"]}: {row["errorDetails"]}')

        # construct failure message
        fail_reason = ""
        if missing:
            fail_reason += "Missing errors:\n" + "\n".join(missing) + "\n"
        if extra:
            fail_reason += "Extra errors:\n" + "\n".join(extra) + "\n"

        if fail_reason:
            raise AssertionError(fail_reason)

    def validate(self):
        """
        Run the full validation, including running validate_data and comparing errors.
        """
        errors_df = self.run_validate_data()
        self.compare_errors(errors_df)


class _TestCaseRegistry:
    next_id = TestCase.BASE_SUBJECT_ID + 1

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._cases: list[TestCase] = []

    @staticmethod
    def _get_next_subject_id():
        sub_id = _TestCaseRegistry.next_id
        _TestCaseRegistry.next_id += 1
        return sub_id

    def add_case(self, test_type: Type[TestCase]):
        case = test_type(self.base_dir, sub_id=self._get_next_subject_id())
        self._cases.append(case)

    def add_cases(self, test_types: list[Type[TestCase]]):
        for test_type in test_types:
            self.add_case(test_type)

    def get_cases(self):
        return self._cases

    def generate_all(self):
        for case in self._cases:
            case.generate()


class FileNameTestCase(TestCase):
    """
    Base class for file name test cases.
    """

    case_name = "FileNameTestCase"
    description = "Handles errors related to file names."
    conditions = ["File name mismatch", "Incorrect variable name"]
    expected_output = "Correct error generated for file name issues."

    def __init__(self, basedir: str, sub_id: int):
        super().__init__(
            basedir,
            sub_id,
            self.case_name,
            self.description,
            self.conditions,
            self.expected_output,
        )

    @property
    def behavior_to_test(self) -> str:
        return "Tests for errors related to file names."

    def replace_file_name(self, base_files, old_name, new_name):
        """
        Searches for a file by its basename in the given dictionary of files and replaces its name if found.

        Args:
            base_files (dict[str, str]): A dictionary where keys are relative file paths and values are file contents.
            old_name (str): The basename of the file to search for.
            new_name (str): The new basename to replace the old one with.

        Returns:
            bool: True if the file was found and replaced; False otherwise.
        """
        for relpath in base_files:
            if os.path.basename(relpath) == old_name:
                old_dir = os.path.dirname(relpath)
                new_relpath = os.path.join(old_dir, new_name)
                base_files[new_relpath] = base_files.pop(relpath)
                return True

        return False

    def remove_file(self, base_files, file):
        """
        Removes a file from the given dictionary of files if it exists.

        Args:
            base_files (dict[str, str]): A dictionary where keys are relative file paths and values are file contents.
            file (str): The basename of the file to remove.

        Returns:
            bool: True if the file was found and removed, False otherwise.
        """
        path = ""
        for relpath in base_files:
            if os.path.basename(relpath) == file:
                path = relpath
                break
        if path:
            del base_files[path]
            return True
        else:
            return False


class InvalidVariableNameTestCase(FileNameTestCase):
    """
    Test case for incorrect variable names in file names.
    """

    case_name = "InvalidVariableNameTestCase"
    description = "Introduces an incorrect variable name in the file name."
    conditions = ["Variable name is invalid"]
    expected_output = "Error is raised for incorrect variable name in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        new_name = f"sub-{self.sub_id}_bad-taskname_s1_r1_e1.csv"

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class MissingVariableNameTestCase(FileNameTestCase):
    """
    Test case for missing variable names in file names.
    """

    case_name = "MissingVariableNameTestCase"
    description = "Removes the variable name from the file name, making it missing."
    conditions = ["Variable name is missing"]
    expected_output = "Error is raised for missing variable name in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        variable = "arrow-alert-v1-1_psychopy"
        old_name = f"sub-{self.sub_id}_{variable}_s1_r1_e1.csv"
        new_name = old_name.replace(variable, "")

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class MissingSubjectNumberTestCase(FileNameTestCase):
    """
    Test case for missing subject number in file names.
    """

    case_name = "MissingSubjectNumberTestCase"
    description = "Removes the subject number from the file name, leaving an incomplete subject identifier."
    conditions = ["Subject number is missing"]
    expected_output = "Error is raised for missing subject number in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        sub = f"sub-{self.sub_id}"
        old_name = f"{sub}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        new_name = old_name.replace(sub, "sub-")

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class InvalidSubjectNumberTestCase(FileNameTestCase):
    """
    Test case for invalid subject numbers in file names.
    """

    case_name = "InvalidSubjectNumberTestCase"
    description = "Replaces the valid subject number in the file name with an invalid subject number."
    conditions = ["Subject number is invalid"]
    expected_output = "Error is raised for invalid subject number in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        sub = f"sub-{self.sub_id}"
        old_name = f"{sub}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        new_name = old_name.replace(sub, "sub-303")

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class InvalidSessionSuffixTestCase(FileNameTestCase):
    """
    Test case for invalid session numbers in file names.
    """

    case_name = "InvalidSessionSuffixTestCase"
    description = "Replaces the valid session number in the file name with an invalid session suffix."
    conditions = ["Session number in suffix is invalid"]
    expected_output = "Error is raised for invalid session suffix in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_suffix = "s1_r1_e1"
        new_suffix = "s11_r1_e1"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{old_suffix}.csv"
        new_name = old_name.replace(old_suffix, new_suffix)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class InvalidRunSuffixTestCase(FileNameTestCase):
    """
    Test case for invalid run numbers in file names.
    """

    case_name = "InvalidRunSuffixTestCase"
    description = (
        "Replaces the valid run number in the file name with an invalid run suffix."
    )
    conditions = ["Run number in suffix is invalid"]
    expected_output = "Error is raised for invalid run suffix in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_suffix = "s1_r1_e1"
        new_suffix = "s1_r3_e1"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{old_suffix}.csv"
        new_name = old_name.replace(old_suffix, new_suffix)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class InvalidEventSuffixTestCase(FileNameTestCase):
    """
    Test case for invalid event numbers in file names.
    """

    case_name = "InvalidEventSuffixTestCase"
    description = (
        "Replaces the valid event number in the file name with an invalid event suffix."
    )
    conditions = ["Event number in suffix is invalid"]
    expected_output = "Error is raised for invalid event suffix in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_suffix = "s1_r1_e1"
        new_suffix = "s1_r1_e3"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{old_suffix}.csv"
        new_name = old_name.replace(old_suffix, new_suffix)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class MissingSessionSuffixTestCase(FileNameTestCase):
    """
    Test case for missing session numbers in file names.
    """

    case_name = "MissingSessionSuffixTestCase"
    description = "Removes the session number from the file name, making it incomplete."
    conditions = ["Session number in suffix is missing"]
    expected_output = "Error is raised for missing session number in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_suffix = "s1_r1_e1"
        new_suffix = "s_r1_e1"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{old_suffix}.csv"
        new_name = old_name.replace(old_suffix, new_suffix)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class MissingRunSuffixTestCase(FileNameTestCase):
    """
    Test case for missing run numbers in file names.
    """

    case_name = "MissingRunSuffixTestCase"
    description = "Removes the run number from the file name, making it incomplete."
    conditions = ["Run number in suffix is missing"]
    expected_output = "Error is raised for missing run number in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_suffix = "s1_r1_e1"
        new_suffix = "s1_r_e1"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{old_suffix}.csv"
        new_name = old_name.replace(old_suffix, new_suffix)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class MissingEventSuffixTestCase(FileNameTestCase):
    """
    Test case for missing event numbers in file names.
    """

    case_name = "MissingEventSuffixTestCase"
    description = "Removes the event number from the file name, making it incomplete."
    conditions = ["Event number in suffix is missing"]
    expected_output = "Error is raised for missing event number in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_suffix = "s1_r1_e1"
        new_suffix = "s1_r1_e"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{old_suffix}.csv"
        new_name = old_name.replace(old_suffix, new_suffix)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class InvalidExtensionTestCase(FileNameTestCase):
    """
    Test case for invalid file extensions in file names.
    """

    case_name = "InvalidExtensionTestCase"
    description = "Replaces the valid file extension with an invalid extension."
    conditions = ["File extension is invalid"]
    expected_output = "Error is raised for invalid file extension in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_ext = ".csv"
        new_ext = ".badext"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1{old_ext}"
        new_name = old_name.replace(old_ext, new_ext)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class MissingExtensionTestCase(FileNameTestCase):
    """
    Test case for missing file extensions in file names.
    """

    case_name = "MissingExtensionTestCase"
    description = "Removes the file extension from the file name, leaving it missing."
    conditions = ["File extension is missing"]
    expected_output = "Error is raised for missing file extension in file name."

    def modify(self, base_files):
        modified_files = base_files.copy()
        old_ext = ".csv"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1{old_ext}"
        new_name = old_name.replace(old_ext, "")

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class InsufficientFilesTestCase(FileNameTestCase):
    """
    Test case for incorrect number of files in a folder (not enough).
    """

    case_name = "InsufficientFilesTestCase"
    description = "Deletes a file from a folder that should contain multiple files."
    conditions = ["Folder contains fewer files than expected"]
    expected_output = "Error is raised for insufficient number of files in folder."

    def modify(self, base_files):
        modified_files = base_files.copy()
        target_file = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"

        if not self.remove_file(modified_files, target_file):
            raise FileNotFoundError(f"File matching basename {target_file} not found")

        return modified_files


class ExtraFilesInFolderTestCase(FileNameTestCase):
    """
    Test case for incorrect number of files in a folder (extra files present).
    """

    case_name = "ExtraFilesInFolderTestCase"
    description = (
        "Adds an additional file to the folder so it has more files than expected."
    )
    conditions = [
        "Folder contains more files than expected",
    ]
    expected_output = "Error is raised for folder containing extra files."

    def modify(self, base_files):
        modified_files = base_files.copy()

        original_suffix = "s1_r1_e1"
        new_suffix = "s1_r1_e2"

        base_file = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{original_suffix}.csv"
        base_file = self.build_path("s1_r1", "psychopy", base_file)
        additional_file = base_file.replace(original_suffix, new_suffix)

        # copy original file contents
        modified_files[additional_file] = modified_files[base_file]

        return modified_files

    def get_expected_errors(self):
        naming_info = r"Suffix s1_r1_e2 not in allowed suffixes.*"
        unexpected_info = f"Unexpected file sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e2.csv found"
        errors = [
            ExpectedError("Naming error", naming_info),
            ExpectedError("Unexpected file", re.escape(unexpected_info)),
        ]

        return errors


class DeviationAndNoDataErrorTestCase(FileNameTestCase):
    """
    Test case for presence of deviation.txt when no other data is present.
    """

    case_name = "DeviationAndNoDataErrorTestCase"
    description = (
        "Adds a 'deviation.txt' file and removes all other files from the folder."
    )
    conditions = [
        "Folder contains deviation.txt",
        "Folder contains no other data",
    ]
    expected_output = (
        "Error is raised for the presence of deviation.txt without any data files."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        deviation_file = self.build_path(
            "s1_r1", "psychopy", f"{identifier}-deviation.txt"
        )
        modified_files[deviation_file] = "Deviation reason: Testing no data condition."

        # remove all s1_r1 psychopy files except deviation.txt
        info = os.path.join("s1_r1", "psychopy", "")
        psychopy_files = [f for f in modified_files if info in f]
        for file in psychopy_files:
            if file != deviation_file:
                del modified_files[file]

        return modified_files


class DeviationAndNoDataFilesErrorTestCase(FileNameTestCase):
    """
    Test case for presence of both deviation.txt and no-data.txt in a folder.
    """

    case_name = "DeviationAndNoDataFilesErrorTestCase"
    description = "Adds both 'deviation.txt' and 'no-data.txt' files to the folder, leaving other files intact."
    conditions = [
        "Folder contains deviation.txt",
        "Folder contains no-data.txt",
    ]
    expected_output = "Error is raised for the presence of both deviation.txt and no-data.txt in the folder."

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        deviation_file = f"{identifier}-deviation.txt"
        deviation_file = self.build_path("s1_r1", "psychopy", deviation_file)
        no_data_file = f"{identifier}-no-data.txt"
        no_data_file = self.build_path("s1_r1", "psychopy", no_data_file)

        # add deviation.txt and no-data.txt files
        modified_files[deviation_file] = "Deviation reason: Testing with no-data.txt"
        modified_files[no_data_file] = "No data available for this test case."

        return modified_files

    def get_expected_errors(self):
        basename = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        errors = [
            ExpectedError(
                "Improper exception files",
                "Both deviation and no-data files present for identifier",
            ),
            ExpectedError(
                "Unexpected file", f"Unexpected file {basename + r"\..+"} found", 4
            ),
        ]

        return errors


class DeviationFileWithFolderMismatchTestCase(FileNameTestCase):
    """
    Test case for deviation.txt presence with file names that do not match their folder.
    """

    case_name = "DeviationFileWithFolderMismatchTestCase"
    description = "Adds a 'deviation.txt' file to the folder and renames a file so its name does not match the folder it is located in."
    conditions = [
        "Folder contains deviation.txt",
        "File name does not match the folder it is located in",
    ]
    expected_output = "Error is raised for the presence of deviation.txt when file names do not match their folder."

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        deviation_file = f"{identifier}-deviation.txt"
        deviation_file = self.build_path("s1_r1", "psychopy", deviation_file)
        modified_files[deviation_file] = "Deviation reason: Testing file mismatch."

        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        new_name = old_name.replace(str(self.sub_id), str(self.sub_id + 1))

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files

    def get_expected_errors(self):
        misplaced_info = re.escape(
            f"Found file in wrong directory: sub-{self.sub_id + 1}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv found in "
        )
        misplaced_info += r"(?:.*/)+"
        errors = [ExpectedError("Misplaced file", misplaced_info)]

        return errors


class DeviationFilePreventsErrorWithExtraFilesTestCase(FileNameTestCase):
    """
    Test case for deviation.txt preventing errors when the number of files in a folder differs from the data dictionary.
    """

    case_name = "DeviationFilePreventsErrorWithExtraFilesTestCase"
    description = "Adds a 'deviation.txt' file to the folder and includes an additional valid file with an extra string in its name."
    conditions = [
        "Folder contains deviation.txt",
        "Folder contains more files than expected",
    ]
    expected_output = (
        "No error is raised for extra files when deviation.txt is present."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        deviation_file = f"{identifier}-deviation.txt"
        deviation_file = self.build_path("s1_r1", "psychopy", deviation_file)
        modified_files[deviation_file] = "Deviation reason: Testing extra files."

        base_file = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        base_file = self.build_path("s1_r1", "psychopy/", base_file)
        # additional valid file with extra string
        additional_file = base_file.replace(".csv", "_extra.csv")

        if base_file not in modified_files:
            raise FileNotFoundError(f"File matching basename {base_file} not found")

        modified_files[additional_file] = modified_files[base_file]

        return modified_files

    def get_expected_errors(self):
        return []


class NoDataAdditionalFilesTestCase(FileNameTestCase):
    """
    Test case for presence of no-data.txt when additional files are present for the same identifier.
    """

    case_name = "NoDataAdditionalFilesTestCase"
    description = "Adds a 'no-data.txt' file to the folder while leaving other files for the same identifier intact."
    conditions = ["Folder contains no-data.txt"]
    expected_output = "Error is raised for the presence of no-data.txt when additional files are present for the same identifier."

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        no_data_file = f"{identifier}-no-data.txt"
        no_data_file = self.build_path("s1_r1", "psychopy", no_data_file)
        modified_files[no_data_file] = "No data available for this test case."

        return modified_files


class FolderSessionSuffixMismatchTestCase(FileNameTestCase):
    """
    Test case for mismatched session suffix in file name and folder.
    """

    case_name = "FolderSessionSuffixMismatchTestCase"
    description = "Renames a file so its session suffix doesn't match the session folder it's located in."
    conditions = ["File's session suffix does not match session folder"]
    expected_output = "Error is raised for file whose session suffix does not match its session folder."

    def modify(self, base_files):
        modified_files = base_files.copy()

        old_suffix = "s1_r1_e1"
        new_suffix = "s3_r1_e1"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{old_suffix}.csv"
        new_name = old_name.replace(old_suffix, new_suffix)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files

    def get_expected_errors(self):
        old_basename = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        new_basename = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s3_r1_e1.csv"
        misplaced_info = re.escape(
            f"Found file in wrong directory: {new_basename} found in "
        )
        misplaced_info += r"(?:.*/)+"

        errors = [
            ExpectedError("Misplaced file", misplaced_info),
            ExpectedError(
                "Missing file", re.escape(f"Expected file {old_basename} not found")
            ),
            ExpectedError(
                "Unexpected file", re.escape(f"Unexpected file {new_basename} found")
            ),
        ]

        return errors


class FolderRunSuffixMismatchTestCase(FileNameTestCase):
    """
    Test case for mismatched run suffix in file name and session folder.
    """

    case_name = "FolderRunSuffixMismatchTestCase"
    description = "Renames a file so its run suffix doesn't match the session folder it's located in."
    conditions = ["File's run suffix does not match session folder"]
    expected_output = (
        "Error is raised for file whose run suffix does not match its session folder."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        old_suffix = "s1_r1_e1"
        new_suffix = "s1_r3_e1"
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_{old_suffix}.csv"
        new_name = old_name.replace(old_suffix, new_suffix)

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class FolderSubjectMismatchTestCase(FileNameTestCase):
    """
    Test case for mismatched subject in file name and subject folder.
    """

    case_name = "FolderSubjectMismatchTestCase"
    description = "Renames a file so its specified subject does not match the subject folder it's located in."
    conditions = ["File's subject does not match subject folder"]
    expected_output = (
        "Error is raised for file whose subject does not match its subject folder."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        new_name = old_name.replace(str(self.sub_id), str(TestCase.BASE_SUBJECT_ID))

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files


class FolderVariableMismatchTestCase(FileNameTestCase):
    """
    Test case for variable name not matching the enclosing data type folder.
    """

    case_name = "FolderVariableMismatchTestCase"
    description = "Copies a file to a folder with an incorrect data type, causing a mismatch between the variable name and the folder."
    conditions = ["File's variable name does not match enclosing data type folder"]
    expected_output = "Error is raised for file whose variable name does not match the enclosing data type folder."

    def modify(self, base_files):
        modified_files = base_files.copy()

        old_folder = "psychopy"
        new_folder = "digi"
        old_path = self.build_path(
            "s1_r1",
            old_folder,
            f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv",
        )
        new_path = old_path.replace(old_folder, new_folder, count=1)

        if old_path not in modified_files:
            raise FileNotFoundError(f"File matching relative path {old_path} not found")

        modified_files[new_path] = modified_files[old_path]  # make copy of file

        return modified_files

    def get_expected_errors(self):
        file_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        misplaced_info = re.escape(
            f"Found file in wrong directory: {file_name} found in "
        )
        misplaced_info += r"(?:.*/)+digi/"
        errors = [
            ExpectedError("Misplaced file", misplaced_info),
            ExpectedError(
                "Unexpected file", re.escape(f"Unexpected file {file_name} found")
            ),
        ]

        return errors


class EmptyFileTestCase(FileNameTestCase):
    """
    Test case for correctly named files that are empty.
    """

    case_name = "EmptyFileTestCase"
    description = "Creates an empty (0 bytes) file, retaining its correct name."
    conditions = [
        "File is named correctly",
        "File is empty (0 bytes)",
    ]
    expected_output = (
        "Error is raised for file that is correctly named but contains no data."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        target = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        target = self.build_path("s1_r1", "psychopy", target)

        if target not in modified_files:
            raise FileNotFoundError(f"File matching relative path {target} not found")

        # simulate empty file (0 bytes)
        modified_files[target] = ""

        return modified_files

    def get_expected_errors(self):
        basename = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        info_regex = r"(?:.*/)+" + re.escape(basename)

        errors = [
            ExpectedError("Empty file", f"Found empty file {info_regex}"),
            ExpectedError("Psychopy error", f"No data found in {info_regex}"),
        ]

        return errors


class DeviationFileWithBadNamesTestCase(FileNameTestCase):
    """
    Test case for deviation.txt presence with incorrectly named files.
    """

    case_name = "DeviationFileWithBadNamesTestCase"
    description = "Adds a 'deviation.txt' file to the folder and renames a file so it does not match the naming convention."
    conditions = [
        "Folder contains deviation.txt",
        "File names in folder do not match naming convention",
    ]
    expected_output = "Error is raised for the presence of deviation.txt when file names do not match naming convention."

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        deviation_file = f"{identifier}-deviation.txt"
        deviation_file = self.build_path("s1_r1", "psychopy", deviation_file)
        modified_files[deviation_file] = "Deviation reason: Testing bad file names."

        # rename existing file to invalid name
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        new_name = "badfilename.csv"

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files

    def get_expected_errors(self):
        error_info = "File badfilename.csv does not match expected identifier format"
        errors = [ExpectedError("Naming error", re.escape(error_info))]

        return errors


class DeviationFileWithValidNamesTestCase(FileNameTestCase):
    """
    Test case for deviation.txt presence with valid file names containing additional strings.
    """

    case_name = "DeviationFileWithValidNamesTestCase"
    description = "Adds a 'deviation.txt' file to the folder and renames a file so it matches the naming convention up to an additional string."
    conditions = [
        "Folder contains deviation.txt",
        "File names match naming convention up to an additional string",
    ]
    expected_output = (
        "No error is raised for valid file names with deviation.txt present."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        deviation_file = f"{identifier}-deviation.txt"
        deviation_file = self.build_path("s1_r1", "psychopy", deviation_file)
        modified_files[deviation_file] = "Deviation reason: Testing valid file names."

        # rename existing file to include additional string
        old_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        new_name = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1_addstring.csv"

        if not self.replace_file_name(modified_files, old_name, new_name):
            raise FileNotFoundError(f"File matching basename {old_name} not found")

        return modified_files

    def get_expected_errors(self):
        return []


class IssueFileTestCase(FileNameTestCase):
    """
    Test case for presence of an issue.txt file in a folder.
    """

    case_name = "IssueFileTestCase"
    description = (
        "Adds an 'issue.txt' file to the folder, which should produce an error. "
        "'deviation.txt' and 'no-data.txt' files should not produce errors."
    )
    conditions = [
        "Folder contains issue.txt file",
    ]
    expected_output = (
        "Error is raised for the presence of issue.txt file in the folder."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()
        issue_file = self.build_path("s1_r1", "psychopy", "issue.txt")

        if issue_file in modified_files:
            raise FileExistsError(f"File matching relpath {issue_file} already exists")

        modified_files[issue_file] = "Generic issue message"

        return modified_files

    def get_expected_errors(self):
        issue_info = "Found issue.txt in identifier's directory"
        unexpected_info = "Unexpected file issue.txt found"
        errors = [
            ExpectedError("Issue file", re.escape(issue_info)),
            ExpectedError("Unexpected file", re.escape(unexpected_info)),
        ]

        return errors


class ExpectedFileMissingTestCase(FileNameTestCase):
    """
    Test case for missing expected files based on the data dictionary.
    """

    case_name = "ExpectedFileMissingTestCase"
    description = (
        "Deletes a file that is expected to be present based on the data dictionary."
    )
    conditions = [
        "File expected based on data dictionary is missing",
    ]
    expected_output = "Error is raised for missing expected file."

    def modify(self, base_files):
        modified_files = base_files.copy()
        target_file = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"

        if not self.remove_file(modified_files, target_file):
            raise FileNotFoundError(f"File matching basename {target_file} not found")

        return modified_files

    def get_expected_errors(self):
        basename = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        missing_info = re.escape(f"Expected file {basename} not found")

        errors = [
            ExpectedError("Missing file", missing_info),
        ]
        errors = []

        return errors


class MultipleTasksFromCombinationRowTestCase(FileNameTestCase):
    """
    Test case for the presence of multiple tasks from the same combination row.
    """

    case_name = "MultipleTasksFromCombinationRowTestCase"
    description = "Duplicates a file from a task in a combination row and renames it to appear as another task from the same row."
    conditions = ["Folder contains multiple tasks from the same combination row"]
    expected_output = (
        "Error is raised for multiple tasks present in the same combination row."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        template = f"sub-{self.sub_id}_VARNAME_s1_r1_e1.csv"
        template = self.build_path("s1_r1", "psychopy", template)
        existing_file = template.replace("VARNAME", "arrow-alert-v1-1_psychopy")
        duplicate_file = template.replace("VARNAME", "arrow-alert-v1-2_psychopy")

        if existing_file not in modified_files:
            raise FileNotFoundError(f"File matching basename {existing_file} not found")

        modified_files[duplicate_file] = modified_files[existing_file]

        return modified_files


class PsychopyFileIDMismatchTestCase(FileNameTestCase):
    """
    Test case for mismatched ID in a psychopy file and its filename.
    """

    case_name = "PsychopyFileIDMismatchTestCase"
    description = "Modifies the first 'id' in a psychopy .csv file so it does not match the subject ID in the filename."
    conditions = [
        "ID in psychopy file does not match subject ID in filename",
    ]
    expected_output = (
        "Error is raised for mismatched ID in the psychopy file and its filename."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        psychopy_file = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        psychopy_file = self.build_path("s1_r1", "psychopy", psychopy_file)
        if psychopy_file not in modified_files:
            raise FileNotFoundError(f"File matching basename {psychopy_file} not found")

        # modify the first ID in the file to be incorrect
        original_content = modified_files[psychopy_file]
        modified_content = original_content.replace(
            str(self.sub_id), str(TestCase.BASE_SUBJECT_ID), count=1
        )
        modified_files[psychopy_file] = modified_content

        return modified_files

    def get_expected_errors(self):
        id_info = f"ID value(s) [{TestCase.BASE_SUBJECT_ID}] in csvfile different from ID in filename ({self.sub_id})"
        errors = [ExpectedError("Psychopy error"), re.escape(id_info)]

        return errors


class EEGDataFileVHDRMismatchTestCase(FileNameTestCase):
    """
    Test case for mismatched DataFile line in an EEG .vhdr file.
    """

    case_name = "EEGDataFileVHDRMismatchTestCase"
    description = "Edits the DataFile line in a .vhdr file so it does not match the name of the .vhdr file itself."
    conditions = [
        "DataFile line in .vhdr file does not match the .vhdr file name",
    ]
    expected_output = "Error is raised for mismatched DataFile line in the .vhdr file."

    def modify(self, base_files):
        modified_files = base_files.copy()

        # define the .vhdr file and the incorrect DataFile line
        vhdr_file = f"sub-{self.sub_id}_all_eeg_s1_r1_e1.vhdr"
        vhdr_file = self.build_path("s1_r1", "eeg", vhdr_file)
        if vhdr_file not in modified_files:
            raise FileNotFoundError(f"File matching basename {vhdr_file} not found")

        # modify the DataFile line in the .vhdr file to introduce the mismatch
        original_content = modified_files[vhdr_file]
        updated_content = original_content.replace(
            f"DataFile=sub-{self.sub_id}_all_eeg_s1_r1_e1.eeg",
            f"DataFile=sub-{self.sub_id}_wrongname_s1_r1_e1.eeg",
        )
        modified_files[vhdr_file] = updated_content

        return modified_files

    def get_expected_errors(self):
        basename = f"sub-{self.sub_id}_PATTERN_s1_r1_e1.eeg"
        correct = basename.replace("PATTERN", "all_eeg")
        incorrect = basename.replace("PATTERN", "wrongname")

        eeg_info = f"Incorrect DataFile {incorrect} in .vhdr file, expected {correct}"
        errors = [ExpectedError("EEG error"), re.escape(eeg_info)]

        return errors


class EEGMarkerFileVHDRMismatchTestCase(FileNameTestCase):
    """
    Test case for mismatched MarkerFile line in an EEG .vhdr file.
    """

    case_name = "EEGMarkerFileVHDRMismatchTestCase"
    description = "Edits the MarkerFile line in a .vhdr file so it does not match the name of the .vhdr file itself."
    conditions = [
        "MarkerFile line in .vhdr file does not match the .vhdr file name",
    ]
    expected_output = (
        "Error is raised for mismatched MarkerFile line in the .vhdr file."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        # define the .vhdr file and the incorrect MarkerFile line
        vhdr_file = f"sub-{self.sub_id}_all_eeg_s1_r1_e1.vhdr"
        vhdr_file = self.build_path("s1_r1", "eeg", vhdr_file)
        if vhdr_file not in modified_files:
            raise FileNotFoundError(f"File matching basename {vhdr_file} not found")

        # modify the MarkerFile line in the .vhdr file to introduce the mismatch
        original_content = modified_files[vhdr_file]
        updated_content = original_content.replace(
            f"MarkerFile=sub-{self.sub_id}_all_eeg_s1_r1_e1.vmrk",
            f"MarkerFile=sub-{self.sub_id}_wrongname_s1_r1_e1.vmrk",
        )
        modified_files[vhdr_file] = updated_content

        return modified_files

    def get_expected_errors(self):
        basename = f"sub-{self.sub_id}_PATTERN_s1_r1_e1.vmrk"
        correct = basename.replace("PATTERN", "all_eeg")
        incorrect = basename.replace("PATTERN", "wrongname")

        eeg_info = f"Incorrect MarkerFile {incorrect} in .vhdr file, expected {correct}"
        errors = [ExpectedError("EEG error"), re.escape(eeg_info)]

        return errors


class EEGDataFileVMRKMismatchTestCase(FileNameTestCase):
    """
    Test case for mismatched DataFile line in an EEG .vmrk file.
    """

    case_name = "EEGDataFileVMRKMismatchTestCase"
    description = "Edits the DataFile line in a .vmrk file so it does not match the name of the .vmrk file itself."
    conditions = [
        "DataFile line in .vmrk file does not match the .vmrk file name",
    ]
    expected_output = "Error is raised for mismatched DataFile line in the .vmrk file."

    def modify(self, base_files):
        modified_files = base_files.copy()

        # define the .vmrk file and the incorrect DataFile line
        vmrk_file = f"sub-{self.sub_id}_all_eeg_s1_r1_e1.vmrk"
        vmrk_file = self.build_path("s1_r1", "eeg", vmrk_file)
        if vmrk_file not in modified_files:
            raise FileNotFoundError(f"File matching basename {vmrk_file} not found")

        # modify the DataFile line in the .vmrk file to introduce the mismatch
        original_content = modified_files[vmrk_file]
        updated_content = original_content.replace(
            f"DataFile=sub-{self.sub_id}_all_eeg_s1_r1_e1.eeg",
            f"DataFile=sub-{self.sub_id}_wrongname_s1_r1_e1.eeg",
        )
        modified_files[vmrk_file] = updated_content

        return modified_files

    def get_expected_errors(self):
        basename = f"sub-{self.sub_id}_PATTERN_s1_r1_e1.vmrk"
        correct = basename.replace("PATTERN", "all_eeg")
        incorrect = basename.replace("PATTERN", "wrongname")

        eeg_info = f"Incorrect MarkerFile {incorrect} in .vmrk file, expected {correct}"
        errors = [ExpectedError("EEG error"), re.escape(eeg_info)]

        return errors


class DeviationFileValidatesFolderTestCase(FileNameTestCase):
    pass


class DeviationFileInvalidatesFolderTestCase(FileNameTestCase):
    pass


class DeviationFileMissingDataTestCase(FileNameTestCase):
    pass


class VariableNameFolderMismatchTestCase(FileNameTestCase):
    pass


class MultipleTasksSameRowTestCase(FileNameTestCase):
    pass


class IssueFileErrorTestCase(FileNameTestCase):
    pass


class EmptyDirectoriesTestCase(FileNameTestCase):
    pass


class ContentTestCase(TestCase):
    pass


class TrackerCreationWithDeviationTestCase(ContentTestCase):
    pass


class TrackerCreationWithoutDeviationTestCase(ContentTestCase):
    pass


class TaskMissingInStatusRowTestCase(ContentTestCase):
    pass


class SubjectIDMismatchInFileTestCase(ContentTestCase):
    pass


class DataDictionaryModifiedTestCase(ContentTestCase):
    pass


class TrackerBehaviorTestCase(TestCase):
    pass


class BBSDataEmptyFolderTestCase(TrackerBehaviorTestCase):
    pass


class BBSDataNoDataFileTestCase(TrackerBehaviorTestCase):
    pass


class BBSDataIncorrectDataTestCase(TrackerBehaviorTestCase):
    pass


class BBSDataValidTestCase(TrackerBehaviorTestCase):
    pass


class BBSStatusErrorNoDataTestCase(TrackerBehaviorTestCase):
    pass


class BBSStatusValidTestCase(TrackerBehaviorTestCase):
    pass


class CentralTrackerNoDataTestCase(TrackerBehaviorTestCase):
    pass


class CentralTrackerDeviationTestCase(TrackerBehaviorTestCase):
    pass


class EEGTestCase(TestCase):
    pass


class VhdrDataFileMismatchTestCase(EEGTestCase):
    pass


class VhdrMarkerFileMismatchTestCase(EEGTestCase):
    pass


class VmrkDataFileMismatchTestCase(EEGTestCase):
    pass


class QATestCase(TestCase):
    pass


class MoveValidRawToPendingQATestCase(QATestCase):
    pass


class PendingQAToCheckedDirectoryTestCase(QATestCase):
    pass


class CheckedDirectoryCleanupTestCase(QATestCase):
    pass


class QAValidatedRecordTestCase(QATestCase):
    pass


class REDCapTestCase(TestCase):
    pass


class DuplicateColumnsTestCase(REDCapTestCase):
    pass


class MissingColumnTestCase(REDCapTestCase):
    pass


class RedcapNameMismatchTestCase(REDCapTestCase):
    pass


class RedcapFileInWrongFolderTestCase(REDCapTestCase):
    pass


class RemoteRedcapValidTestCase(REDCapTestCase):
    pass


class RemoteRedcapErrorTestCase(REDCapTestCase):
    pass
