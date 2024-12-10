import os
import re

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

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        # mock out copied files in sourcedata/pending-qa/
        data_folder = os.path.join(
            "sourcedata",
            "pending-qa",
            "s1_r1",
            "eeg",
            f"sub-{self.sub_id}",
        )
        identifier = f"sub-{self.sub_id}_all_eeg_s1_r1_e1"
        exts = {".eeg", ".vmrk", ".vhdr"}
        additional_files = {os.path.join(data_folder, identifier + ext) for ext in exts}

        expected_files = set(self.get_base_paths())
        expected_files.update(additional_files)

        actual_files = set(self.get_paths(self.case_dir))

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


class QAChecklistEntryTestCase(PendingQAFileTestCase):
    """
    Test case for verifying that only valid raw identifiers are given an entry in the QA checklist.
    """

    case_name = "QAChecklistEntryTestCase"
    description = "Sets up a valid raw identifier in the pending-files CSV and checks that an entry is given in the QA checklist."
    conditions = ["Valid raw identifiers have an entry in the QA checklist."]
    expected_output = "QA checklist details are given correctly for the specified identifier, and no other identifiers are present."

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        identifier = f"sub-{self.sub_id}_all_eeg_s1_r1_e1"

        qa_df = pd.read_csv(
            os.path.join(self.case_dir, "sourcedata", "pending-qa", "qa-checklist.csv")
        )
        assert len(qa_df.index) == 1  # should be only one entry

        qa_rows = qa_df[qa_df["identifier"] == identifier]
        assert len(qa_rows.index) == 1  # the only entry should match our identifier

        info = qa_rows.iloc[0].to_dict()

        assert info["identifierDetails"] == f"sub-{self.sub_id}/all_eeg/s1_r1_e1 (eeg)"
        assert not info["qa"]
        assert not info["localMove"]

        assert info["user"]
        assert re.match(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}", info["datetime"]) is not None


class QAPassMovedToCheckedTestCase(QATestCase):
    """
    Test case for verifying that only identifiers marked as both passing QA checks and
    being moved locally are sent to the checked directory.
    """

    case_name = "QAPassMovedToCheckedTestCase"
    description = (
        "Sets up three identifiers in pending-qa: one that passes QA and is moved locally, "
        "one that fails QA, and one that is not moved. Verifies proper directory placement."
    )
    conditions = [
        "Identifier 'A' is in sourcedata/pending-qa/ and passes QA checks and is moved locally.",
        "Identifier 'B' is in sourcedata/pending-qa/ and fails QA checks.",
        "Identifier 'C' is in sourcedata/pending-qa/ and is not moved locally.",
    ]
    expected_output = "sourcedata/checked/ contains 'A', while the 'pending-qa' directory retains 'B' and 'C'."

    def modify(self, base_files):
        modified_files = base_files.copy()

        pending_qa_dir = os.path.join("sourcedata", "pending-qa")

        # mock out presence of data for three identifiers in source/pending-qa
        data_dir = os.path.join(pending_qa_dir, "s1_r1", "eeg")
        ids = {1, 2, 3}
        for sub_id in ids:
            data_path = os.path.join(data_dir, f"sub-{sub_id}", "dummy.txt")
            modified_files[data_path] = f"Dummy data for mock subject {sub_id}"

        # mock out qa-checklist.csv
        qa_checklist_path = os.path.join(pending_qa_dir, "qa-checklist.csv")
        new_qa_checklist = {
            "identifier": [
                "sub-1_all_eeg_s1_r1_e1",
                "sub-2_all_eeg_s1_r1_e1",
                "sub-3_all_eeg_s1_r1_e1",
            ],
            "qa": [1, 0, 1],  # pass, fail, pass
            "localMove": [1, 1, 0],  # pass, pass, fail
            "datetime": ["2024-01-01_12-30"] * 3,
            "user": ["dummyuser"] * 3,
            "identifierDetails": ["Dummy details"] * 3,
        }
        new_qa_df = pd.DataFrame(new_qa_checklist)
        modified_files[qa_checklist_path] = new_qa_df.to_csv(index=False)

        return modified_files

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        actual_files = self.read_files(self.case_dir)

        checked_dir = os.path.join("sourcedata", "checked")

        sub1_checked_path = os.path.join(
            checked_dir, "sub-1", "s1_r1", "eeg", "dummy.txt"
        )
        assert sub1_checked_path in actual_files
        assert "subject 1" in str(actual_files[sub1_checked_path]).lower()

        checked_subs = {
            os.path.relpath(path, checked_dir).split("/")[0]
            for path in actual_files
            if str(path).startswith(checked_dir)
        }
        assert checked_subs == {"sub-1", f"sub-{self.sub_id}"}

        data_dir = os.path.join("sourcedata", "pending-qa", "s1_r1", "eeg")

        sub1_pending_path = os.path.join(data_dir, "sub-1", "dummy.txt")
        assert sub1_pending_path not in actual_files

        sub2_pending_path = os.path.join(data_dir, "sub-2", "dummy.txt")
        assert sub2_pending_path in actual_files
        assert "subject 2" in str(actual_files[sub2_pending_path]).lower()

        sub3_pending_path = os.path.join(data_dir, "sub-3", "dummy.txt")
        assert sub3_pending_path in actual_files
        assert "subject 3" in str(actual_files[sub3_pending_path]).lower()
