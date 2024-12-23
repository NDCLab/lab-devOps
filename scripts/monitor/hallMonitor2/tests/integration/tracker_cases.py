import os

import pandas as pd

from .base_cases import TrackerTestCase


class BaseUpdateTrackerTestCase(TrackerTestCase):
    """
    Validates the state of the base central tracker, with no modifications
    made to subject data.
    """

    case_name = "BaseUpdateTrackerTestCase"
    description = "Ensures that update_tracker runs correctly with no modifications."
    conditions = ["No modifications made to base subject files"]
    expected_output = "update_tracker runs without issues."

    def modify(self, base_files):
        return base_files.copy()

    def validate(self):
        try:
            self.run_update_tracker(child=True, session="s1")
        except Exception as err:
            raise AssertionError from err

        tracker_path = os.path.join(
            self.case_dir,
            "data-monitoring",
            f"central-tracker_{self.case_name}.csv",
        )
        assert os.path.exists(tracker_path)

        tracker_df = pd.read_csv(tracker_path)
        assert not tracker_df.empty

        # only our subject should be present
        assert len(tracker_df.index) == 1
        assert tracker_df["id"].astype(int).iloc[0] == self.sub_id

        # helpful to break out our subject's row as a separate variable
        sub_row = tracker_df[tracker_df["id"].astype(int) == self.sub_id].iloc[0]

        # check consent and assent separately, since they don't follow
        # the same pattern as the other columns
        assert sub_row["consent"] == 1
        assert sub_row["assent"] == 1

        # extract only the columns that follow the `variable_s_r_e` pattern
        exclude_cols = {"id", "consent", "assent"}
        cols = tracker_df.columns
        cols = cols[~cols.isin(exclude_cols)].tolist()

        expected_sre = ["s1_r1_e1", "s2_r1_e1", "s3_r1_e1"]
        expected_vars = [
            # ordinary variables
            "arrow-alert-v1-1_psychopy",
            "arrow-alert-v1-2_psychopy",
            "all_audacity",
            "all_zoom",
            "all_eeg",
            "all_digi",
            # combination variables
            "arrow-alert_psychopy",
            # status variables
            "iqs_status",
            "bbs_status",
            # data variables
            "iqs_data",
            "bbs_data",
        ]

        expected_cols = set()
        for var in expected_vars:
            for sre in expected_sre:
                expected_cols.add(f"{var}_{sre}")

        # no extra or missing columns
        assert set(cols) == expected_cols

        # all values should be 1 for the base case

        failed_cols = {col for col in cols if sub_row[col] != 1}
        assert len(failed_cols) == 0, f"Failed column(s): {', '.join(failed_cols)}"


class DeviationCheckedUpdateTrackerTestCase(TrackerTestCase):
    """
    Validates that addition of a deviation.txt file for a file that has been
    moved to sourcedata/checked/ does not affect tracker generation.
    """

    case_name = "DeviationCheckedUpdateTrackerTestCase"
    description = (
        "Ensures that presence of deviation.txt file doesn't disturb tracker creation."
    )
    conditions = [
        "File name modified to be incorrect",
        "Deviation.txt file added",
        "File moved to sourcedata/checked",
    ]
    expected_output = "update_tracker runs without issues."

    def modify(self, base_files):
        modified_files = base_files.copy()

        identifier = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1"

        # rename file incorrectly
        old_name = f"{identifier}.csv"
        new_name = old_name.replace(".csv", "_deviation.csv")
        for _ in range(2):  # do once for raw and once for checked
            if not self.replace_file_name(modified_files, old_name, new_name):
                raise FileNotFoundError(f"Could not find basename {new_name}")

        # add deviation.txt to raw/ and checked/
        deviation_file = f"{identifier}-deviation.txt"
        deviation_content = "Deviation reason: Testing update_tracker."
        deviation_raw = self.build_path("s1_r1", "psychopy", deviation_file, True)
        deviation_checked = self.build_path("s1_r1", "psychopy", deviation_file, False)
        modified_files[deviation_raw] = deviation_content
        modified_files[deviation_checked] = deviation_content

        return modified_files

    def validate(self):
        try:
            self.run_update_tracker(child=True, session="s1")
        except Exception as err:
            raise AssertionError from err

        tracker_path = os.path.join(
            self.case_dir,
            "data-monitoring",
            f"central-tracker_{self.case_name}.csv",
        )
        assert os.path.exists(tracker_path)

        tracker_df = pd.read_csv(tracker_path)
        assert not tracker_df.empty
        assert len(tracker_df.index) == 1

        sub_row = tracker_df[tracker_df["id"].astype(int) == self.sub_id].iloc[0]
        assert sub_row["consent"] == 1
        assert sub_row["assent"] == 1


class DeviationNoCheckedUpdateTrackerTestCase(DeviationCheckedUpdateTrackerTestCase):
    """
    Validates that addition of a deviation.txt file for a file that has not been
    moved to sourcedata/checked/ does not affect tracker generation.
    """

    case_name = "DeviationNoCheckedUpdateTrackerTestCase"
    description = (
        "Ensures that presence of deviation.txt file doesn't disturb tracker creation."
    )
    conditions = [
        "File name modified to be incorrect",
        "Deviation.txt file added",
        "File not moved to sourcedata/checked",
    ]
    expected_output = "update_tracker runs without issues."

    def modify(self, base_files):
        modified_files = base_files.copy()

        # rename file only in sourcedata/raw/
        filename = f"sub-{self.sub_id}_arrow-alert-v1-1_psychopy_s1_r1_e1.csv"
        old_name = os.path.join(
            "sourcedata", "raw", "s1_r1", "psychopy", f"sub-{self.sub_id}", filename
        )
        new_name = old_name.replace(".csv", "_deviation.csv")
        modified_files[new_name] = modified_files.pop(old_name)

        # add deviation.txt to raw/
        deviation_file = f"{filename}-deviation.txt"
        deviation_file = self.build_path("s1_r1", "psychopy", deviation_file, True)
        modified_files[deviation_file] = "Deviation reason: Testing update_tracker."

        return modified_files
