import re

from .base_cases import ExpectedError, TestCase, ValidationTestCase


class PsychopyTestCase(ValidationTestCase):
    pass


class PsychopyFileIDMismatchTestCase(PsychopyTestCase):
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
        errors = [ExpectedError("Psychopy error", re.escape(id_info))]

        return errors
