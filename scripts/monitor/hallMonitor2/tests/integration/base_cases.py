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
            use_legacy_exceptions=False,
            is_raw=False,
        )

        pending_df = pd.DataFrame(pending)
        # 'datetime' and 'user' columns do not matter for verifying output
        cols_to_drop = ["datetime", "user"]
        if all(c in pending_df.columns for c in cols_to_drop):
            pending_df.drop(columns=cols_to_drop, inplace=True)

        return pending_df

    @abstractmethod
    def validate(self):
        """
        Validate the test case as appropriate for its type.
        """
        pass


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


class ValidationTestCase(TestCase):
    """
    Base class for test cases associated with the data validation stage.
    """

    case_name = "ValidationTestCase"
    description = "Handles errors related to data validation."
    conditions = []
    expected_output = "Correct error generated for data validation issues."

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
        return "Tests for errors related to pending errors."

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
                    f"{error.error_type}: {error.info_regex.replace('\\', '')} (missing {n_missing})"
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
        errors_df = self.run_validate_data()
        self.compare_errors(errors_df)


class BaseTestCase(ValidationTestCase):
    """
    Test case for no modifications to the base subject data.
    """

    case_name = "BaseTestCase"
    description = "Copies the base subject data exactly."
    conditions = ["No variations to base subject data"]
    expected_output = "No errors are raised."

    @property
    def behavior_to_test(self) -> str:
        return "Tests to make sure no errors are raised for unaltered data."

    def modify(self, base_files):
        return base_files.copy()

    def get_expected_errors(self):
        return []
