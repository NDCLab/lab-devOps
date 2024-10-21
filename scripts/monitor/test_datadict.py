import os
from unittest import mock

import pandas as pd
import pytest
from hmutils import datadict_has_changes, get_datadict, parse_datadict


@pytest.fixture
def dataset(tmp_path):
    dataset_path = tmp_path / "mock_dataset"
    os.makedirs(dataset_path)
    return str(dataset_path)


# -- test get_datadict() --


@pytest.fixture()
def datadict():
    df = pd.DataFrame(
        {
            "col1": [1, 5, 7],
            "col2": [2, 3, 5],
        }
    )
    return df


@pytest.fixture
def mock_read_csv(monkeypatch, datadict):
    monkeypatch.setattr("pandas.read_csv", lambda _: datadict)


@pytest.fixture
def mock_local_datadict(monkeypatch, dataset, datadict):
    datadict_path = "datadict.csv"
    datadict.to_csv(os.path.join(dataset, datadict_path))
    monkeypatch.setattr("hmutils.DATADICT_SUBPATH", datadict_path)


def test_get_datadict_valid(dataset, mock_read_csv):
    df = get_datadict(dataset, use_cache=False)
    assert list(df.columns) == ["col1", "col2"]
    assert list(df.col1) == [1, 5, 7]
    assert list(df.col2) == [2, 3, 5]


def test_get_datadict_DATADICT_SUBPATH(dataset):
    # make sure get_datadict() uses DATADICT_SUBPATH by varying its value
    mock_subpaths = ["mock_subpath", "another_subpath", "ndclab"]
    for subpath in mock_subpaths:
        with (
            mock.patch("hmutils.DATADICT_SUBPATH", subpath),
            mock.patch("pandas.read_csv") as read_csv,
        ):
            get_datadict(dataset, use_cache=False)
            read_csv.assert_called_once_with(os.path.join(dataset, subpath))


def test_get_datadict_file_does_not_exist(dataset):
    with pytest.raises(FileNotFoundError):
        get_datadict(dataset, use_cache=False)


def test_get_datadict_uses_index_col(dataset, mock_local_datadict):
    df = get_datadict(dataset, "col1", use_cache=False)
    assert list(df.index) == [1, 5, 7]
    assert "col1" not in df.columns

    df = get_datadict(dataset, "col2", use_cache=False)
    assert list(df.index) == [2, 3, 5]
    assert "col2" not in df.columns


def test_get_datadict_index_col_does_not_exist(dataset, mock_local_datadict):
    with pytest.raises(ValueError):
        get_datadict(dataset, "invalid_col", use_cache=False)


def test_get_datadict_no_index_col(dataset, mock_local_datadict):
    # ensure default index if index_col is None
    df = get_datadict(dataset, index_col=None, use_cache=False)
    assert list(df.index) == [0, 1, 2]

    # ensure default index if index_col not passed
    df = get_datadict(dataset, use_cache=False)
    assert list(df.index) == [0, 1, 2]

