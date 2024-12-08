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

    def get_paths(self, base_dir: str):
        """Retrieve a list of relative file paths from a base directory.

        Args:
            base_dir (str): The path to the base directory to scan for files.

        Raises:
            FileNotFoundError: If the provided `base_dir` does not exist or is not a directory.

        Returns:
            list[str]: A list of relative file paths found in the base directory.
        """
        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            raise FileNotFoundError(f"{base_dir} does not exist, or is not a directory")

        paths = []
        for root, _, files in os.walk(base_dir):
            for filename in files:
                paths.append(os.path.relpath(os.path.join(root, filename), base_dir))

        return paths

    def get_base_paths(self):
        """
        Retrieve all relative file paths in the base subject directory. Paths will have the base
        subject ID replaced with this test case's assigned subject ID.

        Returns:
            list[str]: A list of relative file paths found in the base subject directory.
        """
        try:
            base_paths = self.get_paths(self.base_sub_dir)
            base_paths = [
                str(path).replace(str(TestCase.BASE_SUBJECT_ID), str(self.sub_id))
                for path in base_paths
            ]
        except FileNotFoundError as err:
            raise FileNotFoundError("Invalid base subject directory") from err

        return base_paths

    def read_files(self, base_dir: str):
        """Read all files in a base directory and return their contents in a dictionary.

        Args:
            base_dir (str): The path to the base directory to read files from.

        Raises:
            FileNotFoundError: If the provided `base_dir` does not exist or is not a directory.

        Returns:
            dict[str,str]: A dictionary where keys are relative file paths and values are file contents
        """
        new_files = {}

        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            raise FileNotFoundError(f"{base_dir} does not exist, or is not a directory")

        for root, _, files in os.walk(base_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.base_sub_dir)

                with open(file_path, "r") as f:
                    content = f.read()

                new_files[rel_path] = content

        return new_files

    def read_base_files(self) -> dict[str, str]:
        """
        Read all files in the base subject directory. Replace all references to the base subject ID with
        the test case's own subject ID.

        Returns:
            dict[str,str]: A dictionary where keys are filenames and values are file contents.
        """
        try:
            base_files = self.read_files(self.base_sub_dir)
        except FileNotFoundError as err:
            raise FileNotFoundError("Invalid base subject directory") from err

        def swap_in_subject_id(text: str):
            return text.replace(str(self.BASE_SUBJECT_ID), str(self.sub_id))

        base_files = {
            swap_in_subject_id(path): swap_in_subject_id(content)
            for path, content in base_files.items()
        }

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

            try:
                with open(full_path, "w") as f:
                    f.write(content)
            except IsADirectoryError:  # some test cases require empty directories
                continue

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

    def get_standard_args(self):
        """
        Create and return a mock namespace object representing the standard command-line arguments.

        Returns:
            MockNamespace: An object containing the standard arguments to hallMonitor 2.0.
        """

        class MockNamespace:
            dataset = self.case_dir
            child_data = None
            legacy_exceptions = False
            no_color = False
            no_qa = False
            # we typically do not want to gather logging output
            output = os.devnull
            checked_only = False
            raw_only = False
            verbose = False
            quiet = False
            replace = None
            map = None

        return MockNamespace()

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

    def run_qa_validation(self) -> str:
        """Run qa_validation() on the generated data directory.

        Returns:
            str: A string containing error text, if any error was raised during execution.
        """
        from hallmonitor.hallMonitor import qa_validation

        logger = logging.getLogger(f"{self.case_name}_logger")
        logger.setLevel(logging.ERROR)
        logger.propagate = False

        error_text = ""
        try:
            qa_validation(logger, dataset=self.case_dir)
        except Exception as err:
            error_text = str(err)

        return error_text

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

        if generated_errors_df.empty:
            # we may have no errors; in this case, all expected errors are missing
            missing = [
                f"{error.error_type}: {error.info_regex.replace('\\', '')} (missing {error.multiplicity})"
                for error in expected_errors
            ]

        else:
            missing = []
            for error in expected_errors:
                matching_errors = generated_errors_df[
                    (generated_errors_df["errorType"] == error.error_type)
                    & (
                        generated_errors_df["errorDetails"].str.fullmatch(
                            error.info_regex
                        )
                    )
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


class QATestCase(TestCase):
    """
    Base class for errors associated with the quality assurance (QA) stage.
    """

    case_name = "QATestCase"
    description = "Handles errors related to quality assurance."
    conditions = []
    expected_output = "Correct error generated for quality assurance issues."

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
        return "Tests for errors related to quality assurance."

    @abstractmethod
    def get_expected_file_changes(self) -> tuple[list[str], list[str]]:
        """
        Define the file changes expected in the test case directory.

        This method should be implemented by child classes to return two lists:
        - The first list contains file paths that are expected to be added.
        - The second list contains file paths that are expected to be missing.

        Returns:
            tuple[list[str],list[str]]: A tuple containing:
                - added_files (list[str]): A list of file paths expected to be added to the test case directory.
                - missing_files (list[str]): A list of file paths expected to be missing from the test case directory.
        """
        pass

    @abstractmethod
    def get_expected_error(self) -> str:
        """
        Define the expected error message for the QA validation.

        This method should be implemented by child classes to return the error message
        expected to occur during QA validation. If no error is expected, this method
        should return an empty string or None.

        Returns:
            str: The expected error message, or an empty string/None if no error is expected.
        """
        pass

    def validate_expected_files(self):
        """
        Validate that the expected files exist in the test case directory.

        Raises:
            AssertionError: If any expected files are missing or extraneous files are found.
        """
        # get relpaths for base subject and this test case
        actual_files = set(self.get_paths(self.case_dir))
        expected_files = set(self.get_base_paths())

        # fetch lists of new and removed files from the test case
        new, remove = self.get_expected_file_changes()
        new = set(new)
        remove = set(remove)

        # add new files and remove specified files from the expected set
        expected_files.update(set(new))
        expected_files.difference_update(set(remove))

        missing_files = expected_files - actual_files
        extra_files = actual_files - expected_files

        # raise error on mismatch
        if missing_files or extra_files:
            fail_reason = ""
            if missing_files:
                fail_reason += "Missing files:\n" + "\n".join(missing_files) + "\n"
            if extra_files:
                fail_reason += "Extra files:\n" + "\n".join(extra_files) + "\n"
            raise AssertionError(f"File layout validation failed:\n{fail_reason}")

    def validate(self):
        """
        Validate the QA outcome by checking for expected errors or file layouts.

        Raises:
            AssertionError: If the QA validation does not match the expected outcome.
        """
        expected_error = self.get_expected_error()

        if expected_error:
            error_text = self.run_qa_validation()
            if error_text.strip() != expected_error.strip():
                raise AssertionError(
                    f"QA validation error mismatch:\nExpected: {expected_error}\nGot: {error_text}"
                )
        else:
            # no error expected, check file layout instead
            error_text = self.run_qa_validation()
            if error_text:
                raise AssertionError(
                    f"Unexpected error during QA validation: {error_text}"
                )
            self.validate_expected_files()
