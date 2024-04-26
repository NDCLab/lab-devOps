#!/usr/bin/env python3

import sys
from os import listdir, makedirs, system
from os.path import join, isdir, isfile, splitext

import pandas as pd
import re
from collections import defaultdict

if __name__ == "__main__":
    dataset = sys.argv[1]
    session = sys.argv[2] # "s1_r1"

    tracker_path = join("/home/data/NDClab/datasets",dataset,"data-monitoring","central-tracker_"+dataset+".csv")

    tracker_df = pd.read_csv(tracker_path, index_col="id")
    #out_location = join("/home/data/NDClab/datasets",dataset,"derivatives",session,"eeg","preprocessed")
    out_location = join("/home/data/NDClab/datasets",dataset,"derivatives","preprocessed")

    preprocessed_subjects = []
    eeg_tasks_preprocessed_subjects = {}
    for sub_folder in listdir(out_location):
        if sub_folder.startswith("sub-"):
            sub = sub_folder[4:]
            #for f in listdir(join(out_location,sub_folder)):
            for f in listdir(join(out_location,sub_folder,session,"eeg")):
                file_re = re.match('^MADE_preprocessing_report_(.+)\.csv$', f)
                if file_re:
                    task = file_re.group(1)
                    if task not in eeg_tasks_preprocessed_subjects.keys():
                        eeg_tasks_preprocessed_subjects[task] = []
                    eeg_tasks_preprocessed_subjects[task].append(int(sub))
#########################
                    # get field values from csv
                    #report_csv = pd.read_csv(join(out_location,sub_folder,f), index_col="datafile_names")
                    report_csv = pd.read_csv(join(out_location,sub_folder,session,"eeg",f))
                    #total_epochs_kept = report_csv.loc[sub_folder+"_"+task+"_"+session+"_e1.vhdr", "total_epochs_after_artifact_rejection"]
                    #total_epochs_kept = report_csv.loc[0, "total_epochs_after_artifact_rejection"]
                    total_epochs_kept = report_csv.loc[len(report_csv.index)-1, "total_epochs_after_artifact_rejection"] #most recent run (should be all the same regardless)
                    #no_usable_data = report_csv.loc[len(report_csv.index)-1, "no_usable_data"]
                    usable_data = report_csv.loc[len(report_csv.index)-1, "any_usable_data"]
                    # update tracker with columns
                    tracker_df.loc[int(sub), task+"_total_epochs_after_artifact_rejection_"+session+"_e1"] = total_epochs_kept
                    #tracker_df.loc[int(sub), task+"_no_usable_data_"+session+"_e1"] = no_usable_data # 1 if bad data, 0 if good
                    tracker_df.loc[int(sub), task+"_any_usable_data_"+session+"_e1"] = usable_data # 1 if good data, 0 if bad
#########################

    for task, subs in eeg_tasks_preprocessed_subjects.items():
        colname = task + "_preprocessing_" + session + "_e1_complete"
        tracker_df.loc[subs, colname] = 1

    tracker_df.to_csv(tracker_path)

    data_tracker_filename = splitext(tracker_path)[0]
    tracker_df_no_blank_columns = tracker_df.loc[:, tracker_df.notnull().any(axis=0)]
    tracker_df_no_blank_columns = tracker_df_no_blank_columns.fillna("NA")
    tracker_df_no_blank_columns.to_csv(data_tracker_filename + "_viewable.csv")
