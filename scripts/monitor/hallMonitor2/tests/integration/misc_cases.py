import os
import re

import pytest

from .base_cases import ExpectedError, TestCase, ValidationTestCase


class MiscellaneousTestCase(ValidationTestCase):
    pass


class BaseTestCase(MiscellaneousTestCase):
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


class InsufficientFilesTestCase(MiscellaneousTestCase):
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

    def get_expected_errors(self):
        basename = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        missing_info = f"Expected file {basename} not found"
        errors = [ExpectedError("Missing file", re.escape(missing_info))]

        return errors


class ExtraFilesInFolderTestCase(MiscellaneousTestCase):
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


class EmptyFileTestCase(MiscellaneousTestCase):
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


class ExpectedFileMissingTestCase(MiscellaneousTestCase):
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

        return errors


class MultipleTasksFromCombinationRowTestCase(MiscellaneousTestCase):
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

    def get_expected_errors(self):
        basename_v1_1 = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"
        basename_v1_2 = f"sub-{self.sub_id}_arrow-alert-v1-2_psychopy_s1_r1_e1"
        ext_re = r"\..+"
        combination_info = "Multiple variables present for combination row arrow-alert_psychopy, expected one."
        missing_info = f"Expected file {basename_v1_2 + ext_re} not found"

        errors = [
            ExpectedError("Combination variable error", re.escape(combination_info), 2),
            ExpectedError("Missing file", missing_info, 2),
            ExpectedError(  # unexpected from the v1-2 identifier's "perspective"
                "Unexpected file", f"Unexpected file {basename_v1_1 + ext_re} found", 3
            ),
            ExpectedError(  # unexpected for the v1-1 identifier
                "Unexpected file", f"Unexpected file {basename_v1_2 + ext_re} found", 1
            ),
        ]

        return errors


class DataDictionaryHasChangesTestCase(TestCase):
    case_name = "DataDictionaryHasChangesTestCase"
    description = "Modifies the data dictionary to simulate unexpected changes."
    behavior_to_test = (
        "Validation should raise an error if the data dictionary has been modified."
    )
    conditions = [
        "Data dictionary contents differ from the expected format or version."
    ]
    expected_output = "Error is raised indicating that the data dictionary has changed."

    def __init__(self, basedir: str, sub_id: int):
        super().__init__(
            basedir,
            sub_id,
            self.case_name,
            self.description,
            self.conditions,
            self.expected_output,
        )

    def modify(self, base_files):
        modified_files = base_files.copy()

        datadict_path = os.path.join(
            "data-monitoring",
            "data-dictionary",
            "central-tracker_datadict.csv",
        )

        if datadict_path not in modified_files:
            raise FileNotFoundError(f"Could not find datadict at {datadict_path}")

        curr_content = modified_files[datadict_path]
        new_content = curr_content.replace("Participant ID", "participant ID")
        modified_files[datadict_path] = new_content

        return modified_files

    def validate(self):
        from hallmonitor.hallMonitor import main

        with pytest.raises(ValueError, match="Data dictionary has changed"):
            args = self.get_standard_args()
            main(args)
