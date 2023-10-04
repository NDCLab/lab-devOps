#!/usr/bin/env python3

import sys
import pandas as pd
from os.path import basename, splitext, isfile

if __name__ == "__main__":
    dpath = sys.argv[1]
    project = basename(dpath)
    DATA_DICT = "/home/data/NDClab/datasets/{}/data-monitoring/data-dictionary/central-tracker_datadict.csv".format(project)
    dd_last_setup = splitext(dd_filename)[0] + "_latest.csv"
    if isfile(dd_last_setup):
        dd_last_setup = pd.read_csv(dd_last_setup, index_col = "variable")
    else:
        print("Error: can't find latest data dictionary, please run setup.sh again.")
    dd_newest = pd.read_csv(DATA_DICT, index_col = "variable")
    dd_diff = dd_newest.compare(dd_last_setup)
    if dd_diff.empty:
        print("datadict up to date, proceeding")
    else:
        print("Error: modifications in data dictionary seen, please run setup.sh again to generate tracker with updated info.")
