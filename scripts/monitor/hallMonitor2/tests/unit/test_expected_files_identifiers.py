import os
import re

import pandas as pd
import pytest
from hallmonitor.hmutils import (
    Identifier,
    get_expected_files,
    get_expected_identifiers,
)


@pytest.fixture
def mock_Identifier_re(monkeypatch):
    id_pattern = r"(?P<subject>\w+)_(?P<var>\w+)_(?P<sre>\w+)"
    monkeypatch.setattr("hallmonitor.hmutils.Identifier.PATTERN", re.compile(id_pattern))


@pytest.fixture
def mock_datadict(monkeypatch):
    dd_df = pd.DataFrame(
        {
            "variable": ["var1", "var2", "var3"],
            "expectedFileExt": ['"eeg,vmrk,vhdr"', '"txt,csv"', '""'],
            "dataType": ["visit_data", "other", "visit_data"],
            "provenance": ["variables: var1, var2", "variables: var3", ""],
        }
    )
    monkeypatch.setattr("hallmonitor.hmutils.get_datadict", lambda _: dd_df)


@pytest.fixture
def mock_dataset(tmp_path, mock_datadict, mock_Identifier_re):
    dataset_path = tmp_path / "mock_dataset"
    os.makedirs(dataset_path)
    return str(dataset_path)


# -- test get_expected_files() --


def test_get_expected_files_valid_string(mock_dataset):
    identifier = "subject1_var1_ses1"

    # The mocked data dictionary specifies that var1
    # has expected extensions "eeg, vmrk, vhdr"
    expected_files = [
        "subject1_var1_ses1.eeg",
        "subject1_var1_ses1.vmrk",
        "subject1_var1_ses1.vhdr",
    ]

    assert get_expected_files(mock_dataset, identifier) == expected_files


def test_get_expected_files_invalid_string(mock_dataset):
    invalid_identifier = "invalid_identifier"

    with pytest.raises(ValueError, match="Invalid identifier string"):
        get_expected_files(mock_dataset, invalid_identifier)


def test_get_expected_files_valid_Identifier(mock_dataset):
    identifier = Identifier("subject1", "var1", "ses1")

    expected_files = [
        "subject1_var1_ses1.eeg",
        "subject1_var1_ses1.vmrk",
        "subject1_var1_ses1.vhdr",
    ]

    assert get_expected_files(mock_dataset, identifier) == expected_files


def test_get_expected_files_no_extensions(mock_dataset):
    # var3 has no extensions in the mock data dictionary
    identifier = "subject1_var3_ses1"
    assert get_expected_files(mock_dataset, identifier) == []


# -- test get_expected_identifiers() --


def test_get_expected_identifiers_valid(mock_dataset):
    present_ids = ["subject1_var1_ses1", "subject2_var1_ses2"]

    # Based on the mock data dictionary, var1 and var2 are associated with visit data
    # So, we expect combinations of subject1, subject2 with var1 and var2 for the same sessions
    expected_ids = [
        Identifier("subject1", "var1", "ses1"),
        Identifier("subject1", "var2", "ses1"),
        Identifier("subject2", "var1", "ses2"),
        Identifier("subject2", "var2", "ses2"),
    ]

    result = get_expected_identifiers(mock_dataset, present_ids)

    assert len(result) == len(expected_ids)

    for id in expected_ids:
        assert id in result


def test_get_expected_identifiers_invalid_present_ids(mock_dataset):
    with pytest.raises(ValueError):
        get_expected_identifiers(mock_dataset, ["invalid_identifier"])


def test_get_expected_identifiers_no_visit_vars(mock_dataset, monkeypatch):
    # Mock data dictionary without any visit variables
    def mock_get_datadict_no_visit_vars(dataset):
        return pd.DataFrame(
            {
                "variable": ["var1", "var2"],  # No "visit_data"
                "expectedFileExt": ['"eeg,vmrk,vhdr"', '"txt,csv"'],
                "dataType": ["other", "other"],  # Not associated with visit_data
                "provenance": ["", ""],
            }
        )

    monkeypatch.setattr("hallmonitor.hmutils.get_datadict", mock_get_datadict_no_visit_vars)

    # Present identifiers, but since no variables are associated with visit_data,
    # we expect an empty list of expected identifiers
    present_ids = ["subject1_var1_ses1", "subject2_var2_ses2"]

    result = get_expected_identifiers(mock_dataset, present_ids)
    assert result == []


def test_get_expected_identifiers_no_present_ids(mock_dataset):
    result = get_expected_identifiers(mock_dataset, [])
    assert result == []
