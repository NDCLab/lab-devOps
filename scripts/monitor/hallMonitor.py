#!/bin/python3

import argparse
import datetime
import os

import pandas as pd
import pytz


def get_args():
    """Get the arguments passed to hallMonitor

    Returns:
        Namespace: Arguments passed to the script (access using dot notation)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dataset", type=str, help="A path to the study's root directory."
    )
    parser.add_argument(
        "--child-data",
        action="store_true",
        help="Include this switch if the study includes child data.",
    )
    parser.add_argument_group()  # TODO: -r/-m options

    return parser.parse_args()


def get_file_record(dataset):
    file_record_path = os.path.join(
        dataset, "data-monitoring", "validated-file-record.csv"
    )
    return pd.read_csv(file_record_path)


def write_file_record(dataset, record):
    file_record_path = os.path.join(
        dataset, "data-monitoring", "validated-file-record.csv"
    )
    record.to_csv(file_record_path)


def handle_raw_unchecked(dataset):
    record = get_file_record(dataset)


def get_latest_pending(dataset):
    pending_path = os.path.join(dataset, "data-monitoring", "pending")
    pending_files = os.listdir(pending_path)
    pending_df = pd.read_csv(pending_files[-1])
    return pending_df


def get_passed_raw_check(dataset):
    pass


def new_qa_checklist():
    colmap = {
        "date-time": "str",
        "user": "str",
        "dataType": "str",
        "identifier": "str",
        "qa": "int",
        "local-move": "int",
    }
    checklist = pd.DataFrame({c: pd.Series(dtype=t) for c, t in colmap.items()})
    return checklist


def write_qa_checklist(dataset, qa_df):
    qa_checklist_path = os.path.join(
        dataset, "sourcedata", "pending-qa", "qa-checklist.csv"
    )
    qa_df.to_csv(qa_checklist_path)


def handle_qa_unchecked(dataset):
    qa_checklist_path = os.path.join(
        dataset, "sourcedata", "pending-qa", "qa-checklist.csv"
    )
    if os.path.exists(qa_checklist_path):
        qa_df = pd.read_csv(qa_checklist_path)
    else:
        qa_df = new_qa_checklist()

    cols = ["identifier", "user"]
    passed_qa = qa_df[(qa_df["qa"] == 1) & (qa_df["local-move"] == 1)][cols]
    # move to checked

    # raw dir order is session/datatype/subject
    # checked dir order is subject/session/datatype

    # remove passed IDs from qa_df
    qa_df = qa_df[qa_df["identifier"] != passed_qa["identifier"]]
    write_qa_checklist(dataset, qa_df)

    # write passed IDs to validated-file-record.csv
    dt = datetime.datetime.now(pytz.timezone("US/Eastern"))
    passed_qa["date-time"] = dt
    passed_qa["raw"] = 1
    passed_qa["qa"] = 1
    passed_qa["checked"] = 1
    record = get_file_record(dataset)
    record = pd.concat(record, passed_qa)
    write_file_record(dataset, record)

    pending = get_latest_pending(dataset)
    passed_raw = pending[pending["pass-raw"] == 1]["identifier"]


def handle_validated():
    pass


if __name__ == "__main__":
    args = get_args()

    dataset = args.dataset
    raw_dir = os.path.join(dataset, "sourcedata", "raw")
    checked_dir = os.path.join(dataset, "sourcedata", "checked")
    datadict_path = os.path.join(dataset, "data-monitoring", "?")

    dd_df = pd.read_csv(datadict_path)

    # handle raw unchecked identifiers
    handle_raw_unchecked(dataset)

    # handle QA unchecked identifiers
    handle_qa_unchecked(dataset)

    # handle fully-validated identifiers
    handle_validated(dataset)
