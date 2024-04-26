import pandas as pd
import sys
from os.path import basename, normpath, join, isdir, isfile, splitext
from os import listdir, walk
import pathlib
import re

if __name__ == "__main__":
    dataset = sys.argv[1]
    redcaps = sys.argv[2]
    session = sys.argv[3]

    redcaps = redcaps.split(',')
    redcap_list = [basename(redcap).lower() for redcap in redcaps]
    datadict = "{}/data-monitoring/data-dictionary/central-tracker_datadict.csv".format(dataset)
    dataset_base = basename(dataset)
    tracker = "{}/data-monitoring/central-tracker_{}.csv".format(dataset,dataset_base)

    df_dd = pd.read_csv(datadict, index_col = "variable")
    tracker_df = pd.read_csv(tracker, index_col = "id")

    visit_dict = {}
    for var, row in df_dd.iterrows():
        if row['dataType'] == "visit_status":
            try:
                visit = re.match('(.+)_status', var).group(1)
            except:
                sys.exit("Unexpected row name for visit status " + var + ", exiting.")
            prov = row["provenance"].split(" ")
            if "file:" in prov and "variable:" in prov:
                idx = prov.index("file:")
                rc_filename = prov[idx+1].strip("\";,")
                idx = prov.index("variable:")
                rc_variable = prov[idx+1].strip("\";,")
            if "id:" in prov:
                idx = prov.index("id:")
                rc_idcol = prov[idx+1].strip("\";,")
                rc_idcol = rc_idcol + '_' + session + '_e1'
            else:
                rc_idcol = "record_id"
            datarow = df_dd.loc[visit + '_data',:]
            tasks = []
            #dprov = datarow['provenance'].split(' ')
            dprov = datarow['provenance'].split(':')
            #if "dataType:" in dprov:
            if "variables" in dprov:
                #idx = dprov.index("dataType:")
                idx = dprov.index("variables")
                ####
                for task in dprov[idx+1].split(','):
                #for task in dprov[idx+1:]:
                    task = task.strip("\";, ")
                    tasks.append(task)
                ###
            visit_dict[visit] = [rc_filename, rc_variable, rc_idcol, tasks]

    for visit, vals in visit_dict.items():
        found_rc = False
        for i in range(0, len(redcap_list)):
            if vals[0] in redcap_list[i]:
                redcap = redcaps[i]
                found_rc = True
                break
        if not found_rc:
            sys.exit("Can't find redcap with name " + vals[0] +", exiting.")
        rc_df = pd.read_csv(redcap, index_col = vals[2])
        rc_var = vals[1]
        #subs_w_data = list(rc_df[rc_df[rc_var+"_"+session+"_e1_complete"] != 0].index) #? always be a _complete column?
        subs_w_data = list(rc_df[rc_df[rc_var+"_"+session+"_e1_complete"] == 2].index) #? always be a _complete column?
        tracker_df.loc[subs_w_data, visit+'_status_'+session+'_e1'] = 1
        #if len(vals[3]) == 0: #?
            #allpresent = True
            #continue
        for sub in subs_w_data:
            allpresent = True
            #corrected = False
            checked = join(dataset, 'sourcedata', 'checked')
            missing_tasks = []
            for task in vals[3]:
                if not tracker_df.loc[sub, task + '_' + session + '_e1'] == 1:
                    allpresent = False
                    missing_tasks.append(task)
            if allpresent:
                tracker_df.loc[sub, visit+'_data_'+session+'_e1'] = 1
            else:
                tracker_df.loc[sub, visit+'_data_'+session+'_e1'] = 0
                print("\033[31mError: Expected tasks " + ", ".join(missing_tasks) + " not seen in subject " + str(sub) + ", session " + session + ".\033[0m")
        # check raw
        #raw = join(dataset, 'sourcedata', 'raw', session)
        #for task in vals[3]:
        #    if not isdir(join(raw, task)):
        #        #error
        #    else:
        #        for sub in subs_w_data:
        #            if not isdir(join(raw, task, 'sub-'+str(int(sub)))):
        #                #error
        ## check checked
        #checked = join(dataset, 'sourcedata', 'checked')
        #for task in vals[3]:
        #    allpresent = True
        #    for sub in subs_w_data:
        #        if not isdir(join(checked, 'sub-'+str(int(sub)), session, task)):
        #            #error
        #            allpresent = False
        #if allpresent:
        #    tracker_df.loc[sub, visit+'_data_'+session+'_e1'] = 1
        #else:
        #    tracker_df.loc[sub, visit+'_data_'+session+'_e1'] = 0
    tracker_df.to_csv(tracker)


















