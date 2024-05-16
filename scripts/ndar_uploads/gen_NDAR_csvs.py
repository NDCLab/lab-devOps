import pandas as pd

import os
from os.path import basename, join

import sys
import json
import math
import re
import numpy as np
from datetime import datetime


def get_redcaps(datadict_df, redcaps):
    df = datadict_df
    redcaps_dict = {}
    for _, row in df.iterrows():
        if row["dataType"] not in ["consent", "assent", "redcap_data"]: #just redcap data
            continue
        prov = row["provenance"].split(" ")
        if "file:" in prov and "variable:" in prov:
            idx = prov.index("file:")
            rc_filename = prov[idx+1].strip("\";")
            if not rc_filename in redcaps_dict.keys():
                redcaps_dict[rc_filename] = {}
        else:
            continue
    for expected_rc in redcaps_dict.keys():
        present = False
        for redcap in redcaps:
            if expected_rc in basename(redcap.lower()) and present == False:
                redcap_path = redcap
                redcaps_dict[expected_rc] = pd.read_csv(redcap_path, index_col="record_id")
                present = True
            elif expected_rc in basename(redcap.lower()) and present == True:
                sys.error("Error: multiple redcaps found with name specified in datadict, " + redcap_path + " and " + redcap + ", exiting.")
        if present == False:
            sys.exit("Error: can't find redcap specified in datadict " + expected_rc + ", exiting.")
    return redcaps_dict

def map_race(ndar_df, ndar_json, sre):
    race_dict = { "10": "White", "11": "Black or African American", "12": "American Indian/Alaska Native", "13": "American Indian/Alaska Native", \
                  "14": "Hawaiian or Pacific Islander", "15": "Hawaiian or Pacific Islander", "16": "Hawaiian or Pacific Islander", \
                  "17": "Hawaiian or Pacific Islander", "18": "Asian", "19": "Asian", "20": "Asian", "21": "Asian", "22": "Asian", "23": "Asian", \
                  "24": "Asian", "25": "Other Non-White", "999": "Unknown or not reported" }
    rc_df = redcaps_dict['iqsparent']
    race_cols = []
    for col in rc_df.columns:
        if re.match('demo(es)?_d_race_s[0-9]+_r[0-9]+_e[0-9]+.*', col):
            race_cols.append(col)
    for id in rc_df.index:
        child_id = int(str(id)[0:2] + "0" + str(id)[3:])
        sum = 0
        for col in race_cols:
            sum += rc_df.loc[id, col]
        if sum == 1:
            for col in race_cols:
                if rc_df.loc[id, col] == 1:
                    race_num = re.match('^demo(es)?_d_race_s[0-9]+_r[0-9]+_e[0-9]+_+([0-9]+)$', col).group(2)
                    race = race_dict[race_num]
                    ndar_df.loc[child_id, "race"] = race
        elif sum > 1:
            ndar_df.loc[child_id, "race"] = "More than one race"


def map_interview_date(ndar_df, ndar_json, sre):
    rc_df = redcaps_dict['iqsparent']
    rc_variable = "infosht_" + sre + "_timestamp"
    rc_variable_es = "infoshtes_" + sre + "_timestamp"
    for id in rc_df.index:
        child_id = int(str(id)[0:2] + "0" + str(id)[3:])
        date_string = rc_df.loc[id, rc_variable]
        if not isinstance(date_string, str) and isinstance(rc_df.loc[id, rc_variable_es], str):
            date_string = rc_df.loc[id, rc_variable_es]
        if isinstance(date_string, str):
            date_string = date_string.split(" ")[0]
            date_obj = datetime.strptime(date_string, "%Y-%m-%d")
            val = date_obj.strftime("%m/%d/%Y")
            ndar_df.loc[child_id, "interview_date"] = val
        else:
            continue




def map_vals(ndar_df, ndar_col, ndar_csv, ndar_json, sre, parent=False):
    rc = ndar_json[ndar_csv]["req_columns"][ndar_col]["redcap"] if "redcap" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys() else math.nan
    rc_variable = ndar_json[ndar_csv]["req_columns"][ndar_col]["rc_variable"] if "rc_variable" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys() else math.nan
    #rc_variable = Column(ndar_json[ndar_csv]["req_columns"][ndar_col]["rc_variable"]) if "rc_variable" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys() else math.nan
    rc_df = redcaps_dict[rc] if isinstance(rc, str) else math.nan
    if isinstance(rc_df, pd.core.frame.DataFrame):
        if isinstance(rc_variable, str):
        #if isinstance(rc_variable, Column):
            if "sessionless" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                rc_column = rc_variable # "record_id" and "interview_date" don't have sX-rX-eX appended
            else:
                rc_column = rc_variable + "_" + sre
        else:
            rc_column = math.nan

    for id in ndar_df.index:
        if parent:
            id = int(str(id)[0:2] + "8" + str(id)[3:]) # will IDs always be XX8XXXX?
            col_re = re.match('^([a-zA-Z0-9]+)_(.*)$', rc_column)
            rc_column_es = col_re.group(1) + "es_" + col_re.group(2)
        else:
            rc_column_es = math.nan
        if str(id)[2] == "8" or str(id)[2] == "9":
            child_id = int(str(id)[0:2] + "0" + str(id)[3:])
        else:
            child_id = id
        # fill in session (i.e. "s1") in timepoint_label in ndar_subject01
        if ndar_col == "timepoint_label" and ndar_csv == "ndar_subject01":
            sess = sre[0:2]
            ndar_df.loc[child_id, ndar_col] = sess
            continue
        if isinstance(rc_df, pd.core.frame.DataFrame):
            if id not in rc_df.index:
                ndar_df.loc[child_id, ndar_col] = "" # "NA" ?
                continue
        if not isinstance(rc, str) or not isinstance(rc_variable, str):
            if "default" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                val = ndar_json[ndar_csv]["req_columns"][ndar_col]["default"]
                ndar_df.loc[child_id, ndar_col] = val
                continue
            elif "computed" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                if not "components" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                    sys.exit("Can't compute value for " + str(ndar_col) + ", must specify components to compute value from, exiting.")
                if ndar_json[ndar_csv]["req_columns"][ndar_col]["computed"] == "sum" and "components" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                    sum = 0
                    for comp in ndar_json[ndar_csv]["req_columns"][ndar_col]["components"]:
                        val = float(rc_df.loc[id, comp + "_" + sre])
                        sum += val
                    if math.isnan(sum) and "missing" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                        ndar_df.loc[child_id, ndar_col] = ndar_json[ndar_csv]["req_columns"][ndar_col]["missing"]
                    else:
                        sum = str(int(sum))
                        ndar_df.loc[child_id, ndar_col] = sum
                    continue
                elif ndar_json[ndar_csv]["req_columns"][ndar_col]["computed"] == "average" and "components" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                    sum = 0
                    ncols = len(ndar_json[ndar_csv]["req_columns"][ndar_col]["components"])
                    for comp in ndar_json[ndar_csv]["req_columns"][ndar_col]["components"]:
                        val = float(rc_df.loc[id, comp + "_" + sre])
                        sum += val
                    if math.isnan(sum) and "missing" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                        ndar_df.loc[child_id, ndar_col] = ndar_json[ndar_csv]["req_columns"][ndar_col]["missing"]
                    else:
                        avg = str(float(sum/ncols))
                        ndar_df.loc[child_id, ndar_col] = avg
                    continue
                else:
                    sys.exit("Can't compute value for " + str(ndar_col) + ", must specify \"sum\" or \"average.\", exiting.")
            else:
                sys.exit("Can't assign value for " + str(ndar_col) + ", name of redcap or redcap variable name missing, exiting.")
        if "conditional_column" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys() and "conditional_column_mapping" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
            # should really do this and "mapping" in a separate function
            conditional_rc = ndar_json[ndar_csv]["req_columns"][ndar_col]["conditional_column"]["redcap"]
            conditional_rc_variable = ndar_json[ndar_csv]["req_columns"][ndar_col]["conditional_column"]["rc_variable"]
            try:
                conditional_rc_df = redcaps_dict[conditional_rc]
            except KeyError:
                sys.exit("Can't find redcap " + conditional_rc + ", exiting.")
            for col in conditional_rc_df.columns:
                if col.startswith(conditional_rc_variable+"_"):
                    conditional_rc_column = col
                    if "parent" in ndar_json[ndar_csv]["req_columns"][ndar_col]["conditional_column"] and ndar_json[ndar_csv]["req_columns"][ndar_col]["conditional_column"]["parent"].lower() == 'true':
                        conditional_rc_column_es = Column(conditional_rc_column).coles
                    else:
                        conditional_rc_column_es = math.nan
                    # TODO: deal with when more than one column starts with cond_rc_variable (e1 and e2, etc?)
                    break
            conditional_rc_id = int(str(id)[0:2] + str(conditional_rc_df.index[0])[2] + str(id)[3:]) # conditional redcap could be parent or child, 300's or 308's or 309's
            val = conditional_rc_df.loc[conditional_rc_id, conditional_rc_column]
            #if math.isnan(val) and not math.isnan(conditional_rc_df.loc[conditional_rc_id, conditional_rc_column_es]): # look at "es" surveys too if it's a parent survey
            if math.isnan(val) and conditional_rc_column_es in conditional_rc_df.columns and not math.isnan(conditional_rc_df.loc[conditional_rc_id, conditional_rc_column_es]): # look at "es" surveys too if it's a parent survey
                val = conditional_rc_df.loc[conditional_rc_id, conditional_rc_column_es]
            if (isinstance(val, float) or isinstance(val, int)) and not math.isnan(val):
                val = str(int(val))
            if val in  ndar_json[ndar_csv]["req_columns"][ndar_col]["conditional_column_mapping"].keys():
                ndar_df.loc[child_id, ndar_col] = ndar_json[ndar_csv]["req_columns"][ndar_col]["conditional_column_mapping"][val]
                continue
        if "mapping" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
            val = rc_df.loc[id, rc_column]
            if math.isnan(val) and rc_column_es in rc_df.columns and not math.isnan(rc_df.loc[id, rc_column_es]):
                val = rc_df.loc[id, rc_column_es]
            if (isinstance(val, np.float64) or isinstance(val, np.float32) or isinstance(val, np.int32) or isinstance(val, np.int64)) and not math.isnan(val):
                val = str(int(val))
            if val in ndar_json[ndar_csv]["req_columns"][ndar_col]["mapping"].keys():
                ndar_df.loc[child_id, ndar_col] = ndar_json[ndar_csv]["req_columns"][ndar_col]["mapping"][val]
                continue
            if math.isnan(rc_df.loc[id, rc_column]) and "missing" in ndar_json[ndar_csv]["req_columns"][ndar_col]["mapping"].keys():
                ndar_df.loc[child_id, ndar_col] = ndar_json[ndar_csv]["req_columns"][ndar_col]["mapping"]["missing"]
                continue
            if "mapping_formula" in ndar_json[ndar_csv]["req_columns"][ndar_col].keys():
                x = rc_df.loc[id, rc_column]
                val = eval(ndar_json[ndar_csv]["req_columns"][ndar_col]["mapping_formula"])
                if -0.01 < val-round(val) < 0.01: # don't round if val is a decimal
                    val = str(int(val))
                ndar_df.loc[child_id, ndar_col] = val
                continue
            #if none of the above apply just take the exact value
            if isinstance(rc_df.loc[id, rc_column], float) and not math.isnan(rc_df.loc[id, rc_column]):
                val = str(int(rc_df.loc[id, rc_column]))
                ndar_df.loc[child_id, ndar_col] = val
            else:
                ndar_df.loc[child_id, ndar_col] = rc_df.loc[id, rc_column]
            continue
        else:
            if isinstance(rc_df.loc[id, rc_column], float) and not math.isnan(rc_df.loc[id, rc_column]):
                val = str(int(rc_df.loc[id, rc_column]))
                ndar_df.loc[child_id, ndar_col] = val
            else:
                ndar_df.loc[child_id, ndar_col] = rc_df.loc[id, rc_column]


def map_adis(ndar_df, ndar_col, ndar_csv, ndar_json, sre, all_columns=False, parent=False):
    rc_df = redcaps_dict[ndar_json[ndar_csv]["req_columns"]["pd_pdx"]["redcap"]]
    diagnoses_dict = { "0": "None", "1": "sad_pdx", "2": "sp_pdx", "3": "sph_pdx", "4": "pd_pdx", "5": "pdago_pdx", \
                        "6": "agorpdx", "7": "gad_pdx", "8": "ocd_pdx", "9": "ptsdpdx", "10": "mdd_pdx", "12": "adhdpdx", "13": "odd_pdx" }
    for col in ndar_json[ndar_csv]["req_columns"].keys():
        ndar_df.loc[:, col] = 0
    for id in ndar_df.index:
        diagnoses = []
        for i in range(1, 9):
            val = rc_df.loc[id, "adis_fn_dx" + str(i) + "_lb_" + sre]
            if not math.isnan(val):
                val = str(int(val))
                if val not in diagnoses:
                    diagnoses.append(val)
        for diagnosis in diagnoses:
            if diagnosis == "0":
                continue
            else:
                col = diagnoses_dict[diagnosis]
                ndar_df.loc[id, col] = "1"
        specific_phobias = []
        for i in range(1, 9):
            if not math.isnan(rc_df.loc[id, "adis_fn_dx" + str(i) + "_lb_" + sre]) and str(int(rc_df.loc[id, "adis_fn_dx" + str(i) + "_lb_" + sre])) == "3":
                specific_phobias.append(rc_df.loc[id, "adis_fn_dx" + str(i) + "_sp_" + sre])
        for i in range(1, len(specific_phobias)+1):
            ndar_df.loc[id, "sph_pdx" + str(i)] = "1"
            ndar_df.loc[id, "phobtype" + str(i)] = specific_phobias[i-1]

def save_csv(ndar_csv, ndar_df):
    ndar_df.to_csv('tmpfile.csv', index=False)
    f = open('tmpfile.csv', 'r')
    csvstring = f.read()
    f.close()
    with open(join(out_path, ndar_csv + '_incomplete.csv'), 'w') as f:
        f.write(ndar_csv[0:-2] + ",01" + ","*(len(df.columns)-2) + "\n")
        f.write(csvstring)
    f.close()
    os.remove('tmpfile.csv')

class Column:
    def __init__(self, col):
        self.col = col
        col_re = re.match('^([a-zA-Z0-9]+)(_.*)?$', col)
        if not col_re:
            raise ValueError('column ' + col + ' does not fit column naming conventions.')
        else:
            after_es_str = col_re.group(2) if col_re.group(2) else ""
            self.coles = col_re.group(1) + "es" + after_es_str


if __name__ == "__main__":
    redcaps = sys.argv[1] # comma-separated list of all input redcaps
    df_dd = sys.argv[2] # filename of data dictionary
    ndar_json = sys.argv[3] # json with mapping info
    sre = sys.argv[4] # session run event, like "s1_r1_e1"
    out_path = sys.argv[5] # output folder for CSVs

    redcaps = redcaps.split(',')
    df_dd = pd.read_csv(df_dd)
    with open(ndar_json, 'r') as json_file:
        ndar_json = json.load(json_file)
    json_file.close()

    redcaps_dict = get_redcaps(df_dd, redcaps) # dataframes of each redcap

    if "src_subject_id" in ndar_json["all"]["req_columns"].keys(): # src_subject_id required to get ids/indices at least for thrive
        redcap = ndar_json["all"]["req_columns"]["src_subject_id"]["redcap"]
        for rc in redcaps:
            if redcap in basename(rc).lower():
                id_redcap = pd.read_csv(rc, index_col = ndar_json["all"]["req_columns"]["src_subject_id"]["rc_variable"]) # record_id
                ids = list(id_redcap.index)
                break
        # for thrive, drop rows who haven't filled out infosht
        if "infosht_" + sre + "_complete" in id_redcap.columns:
            complete_infosht_ids = []
            for id in ids:
                if id_redcap.loc[id,"infosht_" + sre + "_complete"] == 2 or id_redcap.loc[id,"infoshtes_" + sre + "_complete"] == 2:
                    complete_infosht_ids.append(id)
            ids = [int(str(id)[0:2] + "0" + str(id)[3:]) for id in complete_infosht_ids] #quick fix to parent ids -> child ids
    for ndar_csv in ndar_json.keys():
        ndar_columns = ndar_json[ndar_csv]["all_columns"]
        df = pd.DataFrame(columns = ndar_columns, index = ids)
        if ndar_csv == "adis_v01":
            map_adis(df, col, ndar_csv, ndar_json, sre)
            save_csv(ndar_csv, df)
            continue
        for col in ndar_json["all"]["req_columns"].keys():
            if col == "interview_date":
                map_interview_date(df, ndar_json, sre)
                continue
            if col == "interview_age":
                df.loc[:, col] = "" # just ignore for now
                continue
            if col == "src_subject_id":
                df.loc[:, col] = ids
                continue
            parent_col = False
            if "parent" in ndar_json["all"]["req_columns"][col] and ndar_json["all"]["req_columns"][col]["parent"].lower() == "true":
                parent_col = True
            map_vals(df, col, "all", ndar_json, sre, parent=parent_col)
        for col in ndar_json[ndar_csv]["req_columns"]:
            if col == "race":
                map_race(df, ndar_json, sre)
                continue
            parent_col = False
            if "parent" in ndar_json[ndar_csv]["req_columns"][col] and ndar_json[ndar_csv]["req_columns"][col]["parent"].lower() == "true":
                parent_col = True
            map_vals(df, col, ndar_csv, ndar_json, sre, parent=parent_col)
        save_csv(ndar_csv, df)
