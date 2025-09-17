#!/usr/bin/env python3

import sys
import pandas as pd
import math
import os

if __name__ == "__main__":
    dataset = sys.argv[1]
    session = sys.argv[2]

    central_tracker = "/home/data/NDClab/datasets/" + dataset + "/data-monitoring/central-tracker_" + dataset + ".csv"
    tracker_df = pd.read_csv(central_tracker, index_col = "id")
    datadict_df = pd.read_csv("/home/data/NDClab/datasets/" + dataset + "/data-monitoring/data-dictionary/central-tracker_datadict.csv")

    # get task names
    tasks = []
    for _, row in datadict_df.iterrows():
        if row["dataType"] == "eeg":
            tasks.append(row["variable"])

    all_ids = tracker_df.index.tolist()
    if tasks[0] + "_preprocessing_finished_" + session + "_e1" not in tracker_df.columns: #if nobody's been processed yet create column in tracker
        tracker_df.loc[:, tasks[0] + "_preprocessing_finished_" + session + "_e1"] = 0
    processed_ids = tracker_df.index[tracker_df[tasks[0] + "_preprocessing_finished_" + session + "_e1"] == 1].tolist() #TODO work for multiple eeg tasks
    unprocessed_ids = list(set(all_ids).difference(set(processed_ids)))
    unprocessed_ids = [str(x) for x in unprocessed_ids]
    # only process subjects that currently have EEG data
    tmplist = unprocessed_ids.copy() # have to make a copy so it doesn't get super confused
    for subj in tmplist:
        eegdir = os.path.join("/home/data/NDClab/datasets",dataset,"sourcedata","raw",session,"eeg","sub-"+subj)
        if os.path.isdir(eegdir):
            eegdata = os.listdir(eegdir)
            if not any(file.endswith(".eeg") for file in eegdata):
                unprocessed_ids.remove(subj)
        else:
            unprocessed_ids.remove(subj)

    print("/".join(unprocessed_ids))
