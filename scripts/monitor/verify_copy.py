#!/usr/bin/env python3

import sys
import os
from os.path import join, isdir, isfile, splitext

import shutil
import pandas as pd
import re
import math

#print(sys.version)



if __name__ == "__main__":
    dataset = sys.argv[1]

    raw = join(dataset,"sourcedata","raw")
    checked = join(dataset,"sourcedata","checked")

    datadict = "{}/data-monitoring/data-dictionary/central-tracker_datadict.csv".format(dataset)

    sessions = False
    for dir in os.listdir(join(dataset,"sourcedata","raw")):
        if re.match("s[0-9]+_r[0-9]+(_e[0-9]+)?", dir):
            sessions = True
            break

    datatypes_to_ignore = ["id", "consent", "assent", "redcap_data", "redcap_scrd", "parent_info"]

    df_dd = pd.read_csv(datadict, index_col = "variable")
    dd_dict = dict()

    # build dict of expected files/datatypes from datadict
    for var, row in df_dd.iterrows():
        if row["dataType"] not in datatypes_to_ignore and (isinstance(row["dataType"], str) or not math.isnan(row["dataType"])):
            #dd_dict[row["variable"]] = [row["dataType"], row["allowedSuffix"], row["expectedFileExts"]]
            dd_dict[var] = [row["dataType"], row["allowedSuffix"], row["expectedFileExts"]]

    # now search sourcedata/raw for correct files
    for key, values in dd_dict.items():
        print("Verifying files for: ", key)
        #presence = False
        taskname = key
        datatype = values[0]
        allowed_suffixes = values[1].split(", ")
        fileexts = values[2].split(", ") # with or without . ?

        if sessions:
            expected_sessions = []
            for ses in allowed_suffixes:
                ses_re = re.match("(s[0-9]+_r[0-9]+)(_e[0-9]+)?", ses)
                if ses_re:
                    expected_sessions.append(ses_re.group(1))
        else:
            expected_sessions = [""]
        for ses in expected_sessions:
            if isdir(join(raw, ses, datatype):
                for subject in os.listdir(join(raw, ses, datatype)):
                    if not re.match("^sub-[0-9]+$", subject):
                        print("Error: subject directory ", subject, " does not match sub-# convention")
                        continue
                    corrected = False
                        for raw_file in os.listdir(join(raw, ses, datatype, subject)):
                            if re.match('^[Cc]orrected.*$', raw_file):
                                corrected = True
                                break
                    if corrected:
                        print("Corrected.txt seen in ", join(raw, ses, datatype, subject), ", skipping copy.")
                        continue
                    for raw_file in os.listdir(join(raw, ses, datatype, subject)):
                        #check sub-#, check session folder, check extension
                        file_re = re.match("^(sub-[0-9]+)_" + taskname + "_(s[0-9]+_r[0-9]+)_e[0-9]+(\.[a-zA-Z]+)+$", raw_file)
                        if file_re:
                            if file_re.group(1) != subject:
                                print("Error: file from subject ", file_re.group(1), " found in ", subject, " folder: ", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(2) != ses and len(ses) > 0:
                                print("Error: file from session ", file_re.group(2), " found in ", ses, " folder: ", join(raw, ses, datatype, subject, raw_file))
                            #possible_exts = list(np.concatenate([ext.split('|') for ext in fileexts]).flat)
                            possible_exts = sum([ext.split('|') for ext in fileexts], [])
                            if file_re.group(3) not in possible_exts:
                                print("Error: file with extension ", file_re.group(3), " found, doesn\'t match expected extensions ", ", ".join(possible_exts), ": ", join(raw, ses, datatype, subject, raw_file))
                        else:
                            print("Error: file ", raw_file, " does not match naming convention <sub-#>_<task-name>_<session>.<ext>"




                    #presence = False
                    for suffix in allowed_suffixes:
                        presence = False
                        copied_files = []
                        for req_ext in fileexts:
                            for ext in req_ext.split('|'):
                                for raw_file in os.listdir(join(raw, ses, datatype, subject)):
                                    if re.match(subject + "_" + taskname + "_" + suffix + ext, raw_file):
                                    #if re.match(subject + "_" + taskname + "_" + suffix + "." + ext, raw_file):
                                        presence = True
                                        # copy file to checked, unless "corrected" is seen
                                        
                                        if not isdir(join(checked, subject, ses, datatype):
                                            print("Creating ", join(subject, ses, datatype), " directory in checked")
                                            os.makedirs(join(checked, subject, ses, datatype)
                                        if not isfile(join(checked, subject, ses, datatype, raw_file)):
                                            print("Copying ", raw_file, " to checked")
                                            shutil.copy(join(raw, ses, datatype, subject, raw_file), join(checked, subject, ses, datatype, raw_file))
                                        copied_files.append(raw_file)
                        if len(copied_files) == len(req_ext):
                            #print("All files copied")
                        else:
                            #print("Not all files found")
                            #obs_exts = [splitext(file)[1][1:] for file in copied_files]
                            #obs_exts = {file: splitext(file)[1][1:] for file in copied_files} #obs_exts = {file: splitext(file)[1] for file in copied_files}
                            #obs_exts = {file: ".".join(file.split('.')[1:]) for file in copied_files} #".zip.gpg" ?
                            obs_exts = {file: "."+".".join(file.split('.')[1:]) for file in copied_files} #".zip.gpg" ?
                            for ext in fileexts:
                                if not ext in list(obs_exts.values()):
                                    print("Error: no .", subject + "_" + taskname + "_" + suffix + ext, " file found in ", join(raw, ses, datatype, subject))
                    if not presence:
                        print("Error: can\'t find: ", subject + "_" + taskname + "_" + suffix + ext, " file in ", join(raw, ses, datatype, subject))
            else:
                print("Error: can\'t find ", datatype, "directory under ", raw, "/", ses)

        
