import os

import pandas as pd

from .base_cases import QATestCase


class PendingQAFileTestCase(QATestCase):
    """
    Test case for verifying that valid raw identifier files are copied to the pending-qa directory,
    and that no other files are copied.
    """

    case_name = "PendingQAFileTestCase"
    description = "Moves files for valid raw identifiers to the pending-qa directory and verifies that only those files are moved."
    conditions = ["Files for valid raw identifiers are copied to pending-qa"]
    expected_output = (
        "Files are copied correctly, and no extraneous files are present in pending-qa."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        pending_dir = os.path.join("data-monitoring", "pending")

        # remove old pending-files CSV, keep pending-errors
        modified_files = {
            path: contents
            for path, contents in modified_files.items()
            if "pending-errors" in path or not path.startswith(pending_dir)
        }

        # add in our own pending-files CSV
        identifier = f"sub-{self.sub_id}_all_eeg_s1_r1_e1"
        pending_files_path = os.path.join(
            pending_dir, "pending-files-2024-01-01_12-30.csv"
        )
        pending_df = pd.DataFrame(
            [
                {
                    "datetime": "2024-01-01_12-30",
                    "user": "dummy",
                    "passRaw": 1,
                    "identifier": identifier,
                    "identifierDetails": "Dummy details",
                    "errorType": "",
                    "errorDetails": "",
                }
            ]
        )

        pending_files_contents = pending_df.to_csv(index=False)
        modified_files[pending_files_path] = pending_files_contents

        return modified_files

    def get_expected_file_changes(self):
        data_folder = os.path.join(
            "sourcedata",
            "pending-qa",
            "s1_r1",
            "eeg",
            f"sub-{self.sub_id}",
        )
        identifier = f"sub-{self.sub_id}_all_eeg_s1_r1_e1"
        exts = {".eeg", ".vmrk", ".vhdr"}
        additional_files = [os.path.join(data_folder, identifier + ext) for ext in exts]

        return additional_files, []

    def get_expected_error(self):
        return ""
