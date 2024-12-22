import os

import pandas as pd

from .base_cases import TrackerTestCase


class BaseUpdateTrackerTestCase(TrackerTestCase):
    """
    Validates the state of the base central tracker, with no modifications
    made to subject data.
    """

    case_name = "BaseUpdateTrackerTestCase"

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
