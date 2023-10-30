#!/usr/bin/env python3

import sys
import pandas as pd
from os.path import basename, splitext, isfile

class c:
    RED = '\033[31m'
    GREEN = '\033[32m'
    ENDC = '\033[0m'

if __name__ == "__main__":
    dpath = sys.argv[1]
    project = basename(dpath)
    dd_filename = "/home/data/NDClab/datasets/{}/data-monitoring/data-dictionary/central-tracker_datadict.csv".format(project)
    dd_last_setup = splitext(dd_filename)[0] + "_latest.csv"
    if isfile(dd_last_setup):
        dd_last_setup = pd.read_csv(dd_last_setup, index_col = "variable")
    else:
        print(c.RED + "Error: can't find latest data dictionary, please run setup.sh again." + c.ENDC)
    dd_newest = pd.read_csv(dd_filename, index_col = "variable")
    try:
        dd_diff = dd_newest.compare(dd_last_setup)
    except ValueError:
        sys.exit(c.RED + "Error: modifications in data dictionary rows seen, please run setup.sh again to generate tracker with updated info." + c.ENDC)
    if dd_diff.empty:
        print(c.GREEN + "datadict up to date, proceeding" + c.ENDC)
    else:
        print(c.RED + "Error: modifications in data dictionary seen, please run setup.sh again to generate tracker with updated info." + c.ENDC)
