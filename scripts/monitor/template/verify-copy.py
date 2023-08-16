#!/usr/bin/env python3

import sys
from os import listdir, makedirs
from os.path import join, isdir, isfile, splitext

import shutil
import pandas as pd
import re
import math
import subprocess

#print(sys.version)

class bcolors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW  = '\033[33m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    WHITE   = '\033[37m'
    RESET   = '\033[39m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



if __name__ == "__main__":
    dataset = sys.argv[1]

    raw = join(dataset,"sourcedata","raw")
    checked = join(dataset,"sourcedata","checked")

    datadict = "{}/data-monitoring/data-dictionary/central-tracker_datadict.csv".format(dataset)

    sessions = False
    for dir in listdir(join(dataset,"sourcedata","raw")):
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
            dd_dict[var] = [row["dataType"], row["allowedSuffix"], row["expectedFileExts"], row["allowedValues"]]

    allowed_subs = df_dd.loc["id", "allowedValues"]
    allowed_subs_re = "^(" + allowed_subs.replace(" ", "").replace("X", ".").replace(",", "|") + ")$"

    # now search sourcedata/raw for correct files
    for key, values in dd_dict.items():
        print("Verifying files for:", key)
        #presence = False
        variable = key
        datatype = values[0]
        allowed_suffixes = values[1].split(", ")
        fileexts = values[2].split(", ") # with or without . ?
        allowed_vals = values[3].split(", ")
        possible_exts = sum([ext.split('|') for ext in fileexts], [])
        numfiles = len(fileexts)

        if sessions:
            expected_sessions = []
            for ses in allowed_suffixes:
                ses_re = re.match("(s[0-9]+_r[0-9]+)(_e[0-9]+)?", ses)
                if ses_re:
                    expected_sessions.append(ses_re.group(1))
        else:
            expected_sessions = [""]
        for ses in expected_sessions:
            if isdir(join(raw, ses, datatype)):
                for subject in listdir(join(raw, ses, datatype)):
                    if not re.match("^sub-[0-9]+$", subject):
                        print("Error: subject directory ", subject, " does not match sub-# convention")
                        continue
                    obs_files = []
                    corrected = False
                    for raw_file in listdir(join(raw, ses, datatype, subject)):
                        if re.match('^[Cc]orrected.*$', raw_file):
                            corrected = True
                        else:
                            obs_files.append(raw_file)
                    if corrected:
                        print("Corrected.txt seen in ", join(raw, ses, datatype, subject), ", skipping copy.")
                        for raw_file in listdir(join(raw, ses, datatype, subject)):
                            # still check that files are in the correct subject folder and session folder
                            file_re = re.match("^(sub-[0-9]*)_([a-zA-Z0-9_-]*_)?(s[0-9]*_r[0-9]*)_e[0-9]*.*$", raw_file)
                            if file_re and file_re.group(1) != subject:
                                print("Error: file from subject", file_re.group(1), "found in", subject, "folder:", join(raw, ses, datatype, subject, raw_file))
                            if file_re and len(ses) > 0 and file_re.group(3) != ses:
                                print("Error: file from session", file_re.group(3), "found in", ses, "folder:", join(raw, ses, datatype, subject, raw_file))
                        continue
                    if len(obs_files) > numfiles:
                        print("Error: number of", datatype, "data files in subject folder", subject, len(obs_files), "greater than the expected number", numfiles)
                    elif len(obs_files) < numfiles:
                        print("Error: number of", datatype, "data files in subject folder", subject, len(obs_files), "less than the expected number", numfiles)
                    for raw_file in listdir(join(raw, ses, datatype, subject)):
                        #check sub-#, check session folder, check extension
                        file_re = re.match("^(sub-([0-9]*))_([a-zA-Z0-9_-]*)_((s([0-9]*)_r([0-9]*))_e([0-9]*))((?:\.[a-zA-Z]+)*)$", raw_file)
                        if file_re:
                            if file_re.group(1) != subject:
                                print("Error: file from subject", file_re.group(1), "found in", subject, "folder:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(5) != ses and len(ses) > 0:
                                print("Error: file from session", file_re.group(5), "found in", ses, "folder:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(9) not in possible_exts and len(file_re.group(9)) > 0:
                                print("Error: file with extension", file_re.group(9), "found, doesn\'t match expected extensions", ", ".join(possible_exts), ":", join(raw, ses, datatype, subject, raw_file))
                            if not re.match(allowed_subs_re, file_re.group(2)) and file_re.group(2) != '':
                                print("Error: subject number", file_re.group(2), "not an allowed subject value", allowed_subs, "in file:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(3) not in dd_dict.keys():
                                print("Error: variable name", file_re.group(3), "does not match any datadict variables, in file:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(4) not in allowed_suffixes:
                                print("Error: suffix", file_re.group(4), "not in allowed suffixes", ", ".join(allowed_suffixes), "in file:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(2) == "":
                                print("Error: subject # missing from file:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(3) == "":
                                print("Error: variable name missing from file:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(6) == "":
                                print("Error: session # missing from file:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(7) == "":
                                print("Error: run # missing from file:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(8) == "":
                                print("Error: event # missing from file:", join(raw, ses, datatype, subject, raw_file))
                            if file_re.group(9) == "":
                                print("Error: extension missing from file:", join(raw, ses, datatype, subject, raw_file))
                            if datatype == "psychopy" and file_re.group(9) == ".csv" and file_re.group(2) != "":
                                # Call check-id.py for psychopy files
                                subprocess.run(["python3", "check-id.py", file_re.group(2), join(raw, ses, datatype, subject, raw_file)], shell=False)
                        else:
                            print("Error: file ", join(raw, ses, datatype, subject, raw_file), " does not match naming convention <sub-#>_<variable/task-name>_<session>.<ext>")






                    #presence = False
                    for suffix in allowed_suffixes:
                        presence = False
                        copied_files = []
                        for req_ext in fileexts:
                            for ext in req_ext.split('|'):
                                for raw_file in listdir(join(raw, ses, datatype, subject)):
                                    # Errors for: task name incorret, task name missing, subject # missing,
                                    # invalid suffix (s#, r#, e# different errors), missing suffix (s#, r#, e#),
                                    # invalid extension, missing extension,
                                    #
                                    # wrong session folder, wrong subject folder


                                    if re.match(subject + "_" + variable + "_" + suffix + ext, raw_file):
                                    #if re.match(subject + "_" + taskname + "_" + suffix + "." + ext, raw_file):
                                        presence = True
                                        # copy file to checked, unless "corrected" is seen
                                        
                                        if not isdir(join(checked, subject, ses, datatype)):
                                            print("Creating ", join(subject, ses, datatype), " directory in checked")
                                            makedirs(join(checked, subject, ses, datatype))
                                        if not isfile(join(checked, subject, ses, datatype, raw_file)):
                                            print("Copying ", raw_file, " to checked")
                                            shutil.copy(join(raw, ses, datatype, subject, raw_file), join(checked, subject, ses, datatype, raw_file))
                                        copied_files.append(raw_file)
                        if len(copied_files) == len(req_ext):
                            #print("All files copied")
                            print("etc")
                        else:
                            #print("Not all files found")
                            #obs_exts = [splitext(file)[1][1:] for file in copied_files]
                            #obs_exts = {file: splitext(file)[1][1:] for file in copied_files} #obs_exts = {file: splitext(file)[1] for file in copied_files}
                            #obs_exts = {file: ".".join(file.split('.')[1:]) for file in copied_files} #".zip.gpg" ?
                            obs_exts = {file: "."+".".join(file.split('.')[1:]) for file in copied_files} #".zip.gpg" ?
                            for ext in fileexts:
                                if not ext in list(obs_exts.values()):
                                    pass
                                    #print("No ", subject + "_" + taskname + "_" + suffix + ext, " file found in ", join(raw, ses, datatype, subject))
                            #if not presence:
                            #    print("Can\'t find: ", subject + "_" + taskname + "_" + suffix + ext, " file in ", join(raw, ses, datatype, subject))
            else:
                print("Error: can\'t find ", datatype, "directory under ", raw, "/", ses)

        
