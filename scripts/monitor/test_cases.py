import json
import os
from abc import ABC, abstractmethod
from typing import Type


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

    _used_subject_ids = set()

    BASE_SUBJECT_ID = 3000000

    BASE_SUBJECT_SUBDIR = os.path.join("base_subject", "")
    TEST_CASES_SUBDIR = os.path.join("test_cases", "")

    SUB = "@subject_id@"
    VAR = "@variable@"
    SRE = "@sre@"
    EXT = "@ext@"

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
                    base_files[rel_path] = f.read()

        return base_files

    def write_files(self, files: dict[str, str]):
        """
        Write the modified files to the test case directory.

        Args:
            files (dict[str,str]): A dictionary where keys are relative paths to files and values are file contents.
        """
        for rel_path, content in files.items():
            full_path = os.path.join(self.case_dir, rel_path)
            os.makedirs(full_path)

            with open(full_path, "w") as f:
                f.write(content)

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


class TestCaseRegistry:
    next_id = TestCase.BASE_SUBJECT_ID + 1

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._cases: list[TestCase] = []

    @staticmethod
    def _get_next_subject_id():
        sub_id = TestCaseRegistry.next_id
        TestCaseRegistry.next_id += 1
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


        return output

    def _generate_unique_subject_id(self):
        base_id = 3000001
        while True:
            new_id = f"sub-{base_id}"
            if new_id not in TestCase._used_subject_ids:
                TestCase._used_subject_ids.add(new_id)
                return new_id
            base_id += 1


