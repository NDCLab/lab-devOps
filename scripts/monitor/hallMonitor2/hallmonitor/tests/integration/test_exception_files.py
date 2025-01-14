import os
import re

from hallmonitor.tests.integration.base_cases import ExpectedError, ValidationTestCase


class ExceptionTestCase(ValidationTestCase):
    pass


class DeviationAndNoDataErrorTestCase(ExceptionTestCase):
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
            "s1_r1", "psychopy", f"{identifier}_deviation.txt"
        )
        modified_files[deviation_file] = "Deviation reason: Testing no data condition."

        # remove all s1_r1 psychopy files except deviation.txt
        info = os.path.join("s1_r1", "psychopy", "")
        psychopy_files = [f for f in modified_files if info in f]
        for file in psychopy_files:
            if file != deviation_file:
                del modified_files[file]

        return modified_files

    def get_expected_errors(self):
        error_info = "deviation.txt cannot signify only 1 file; use no-data.txt."
        combo_info = "Combination row arrow-alert_psychopy has no variables present."
        errors = [
            ExpectedError("Improper exception files", re.escape(error_info)),
            ExpectedError("Combination variable error", re.escape(combo_info), 2),
        ]

        return errors


def test_deviation_and_no_data_error(request):
    DeviationAndNoDataErrorTestCase.run_test_case(request)


class DeviationAndNoDataFilesErrorTestCase(ExceptionTestCase):
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
        deviation_file = f"{identifier}_deviation.txt"
        deviation_file = self.build_path("s1_r1", "psychopy", deviation_file)
        no_data_file = f"{identifier}_no-data.txt"
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
                "Unexpected file", f"Unexpected file {basename + r'.+'} found", 4
            ),
        ]

        return errors


def test_deviation_and_no_data_files_error(request):
    DeviationAndNoDataFilesErrorTestCase.run_test_case(request)


class DeviationFileWithFolderMismatchTestCase(ExceptionTestCase):
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
        deviation_file = f"{identifier}_deviation.txt"
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


def test_deviation_file_with_folder_mismatch(request):
    DeviationFileWithFolderMismatchTestCase.run_test_case(request)


class DeviationFilePreventsErrorWithExtraFilesTestCase(ExceptionTestCase):
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
        deviation_file = f"{identifier}_deviation.txt"
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


def test_deviation_file_prevents_error_with_extra_files(request):
    DeviationFilePreventsErrorWithExtraFilesTestCase.run_test_case(request)


class NoDataAdditionalFilesTestCase(ExceptionTestCase):
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
        no_data_file = f"{identifier}_no-data.txt"
        no_data_file = self.build_path("s1_r1", "psychopy", no_data_file)
        modified_files[no_data_file] = "No data available for this test case."

        return modified_files

    def get_expected_errors(self):
        file_re = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1" + r"\..+"
        extra_info = f"Unexpected file {file_re} found"

        errors = [ExpectedError("Unexpected file", extra_info, 3)]

        return errors


def test_no_data_additional_files(request):
    NoDataAdditionalFilesTestCase.run_test_case(request)


class DeviationFileWithBadNamesTestCase(ExceptionTestCase):
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
        deviation_file = f"{identifier}_deviation.txt"
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


def test_deviation_file_with_bad_names(request):
    DeviationFileWithBadNamesTestCase.run_test_case(request)


class DeviationFileWithValidNamesTestCase(ExceptionTestCase):
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
        deviation_file = f"{identifier}_deviation.txt"
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


def test_deviation_file_with_valid_names(request):
    DeviationFileWithValidNamesTestCase.run_test_case(request)


class IssueFileTestCase(ExceptionTestCase):
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


def test_issue_file(request):
    IssueFileTestCase.run_test_case(request)


class MissingIdentifierWithoutNoDataTestCase(ExceptionTestCase):
    """
    Test case for no data in a folder without an accompanying no-data.txt file.
    """

    case_name = "MissingIdentifierWithoutNoDataTestCase"
    description = "Removes all data from a datatype folder without replacing it with a no-data file."
    conditions = [
        "Folder is empty.",
    ]
    expected_output = "Error is raised for the missing identifier."

    def modify(self, base_files):
        modified_files = base_files.copy()
        basename = f"sub-{self.sub_id}_all_digi_s1_r1_e1.zip.gpg"

        if not self.replace_file_name(modified_files, basename, ""):
            raise FileNotFoundError(f"File matching basename {basename} not found")

        return modified_files

    def get_expected_errors(self):
        missing_info = re.escape("Missing identifier (")
        missing_info += r".*(?:.*/)+.*" + re.escape(")") + r".*"
        errors = [ExpectedError("Missing identifier", missing_info)]

        return errors


def test_missing_identifier_without_no_data(request):
    MissingIdentifierWithoutNoDataTestCase.run_test_case(request)


class MissingIdentifierNoDataTestCase(ExceptionTestCase):
    """
    Test case for no data in a folder with an accompanying no-data.txt file.
    """

    case_name = "MissingIdentifierNoDataTestCase"
    description = (
        "Removes all data from a datatype folder, replacing it with a no-data file."
    )
    conditions = ["Folder is empty.", "Folder contains a no-data.txt file."]
    expected_output = "No error is raised for the missing identifier."

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_all_digi_s1_r1_e1"
        old_basename = f"{identifier}.zip.gpg"
        new_basename = f"{identifier}_no-data.txt"

        if not self.replace_file_name(modified_files, old_basename, new_basename):
            raise FileNotFoundError(f"File matching basename {old_basename} not found")

        return modified_files

    def get_expected_errors(self):
        return []


def test_missing_identifier_no_data(request):
    MissingIdentifierNoDataTestCase.run_test_case(request)
