import sys
import pandas as pd
from os.path import basename, splitext, isfile
import collections
import shutil

def check_data_dict_variables(df_dd):
    all_tracker_cols = []
    for _, row in df_dd.iterrows():
        if not isinstance(row["allowedSuffix"], float):
            for suf in row["allowedSuffix"].split(', '):
                all_tracker_cols.append(row["variable"] + "_" + suf)
    duplicates = [col for col, count in collections.Counter(all_tracker_cols).items() if count > 1]
    if len(duplicates) > 0:
        sys.exit("Error in data dictionary, duplicate column names seen: " + ", ".join(duplicates))

def check_data_dict_provenance(df_dd):
    all_redcap_cols = []
    for _, row in df_dd.iterrows():
        if row["dataType"] == "redcap_data":
            prov = row["provenance"].split(" ")
            for i in prov:
                if "file:" in i:
                    idx = prov.index(i)+1
                    redcap_file = prov[idx].strip("\"\';,()")
                elif "variable:" in i:
                    idx = prov.index(i)+1
                    redcap_var = prov[idx].strip("\"\';,()")
                    if redcap_var == "":
                        redcap_var = row["variable"]
            for suf in row["allowedSuffix"].split(', '):
                all_redcap_cols.append("redcap: " + redcap_file + ", variable: " + redcap_var + "_" + suf)
    duplicates = [col for col, count in collections.Counter(all_redcap_cols).items() if count > 1]
    if len(duplicates) > 0:
        sys.exit("Error in data dictionary, duplicate provenances seen: " + "; ".join(duplicates))

if __name__ == "__main__":
    filepath = sys.argv[1]
    project = sys.argv[2]
    redcaps = sys.argv[3]
    
    redcaps = redcaps.split(",")
    DATA_DICT = "/home/data/NDClab/datasets/{}/data-monitoring/data-dictionary/central-tracker_datadict.csv".format(project)
    df_dd = pd.read_csv(DATA_DICT)
    check_data_dict_variables(df_dd)
    check_data_dict_provenance(df_dd)

    if not changes_in_dict.empty:
        print("Error: changes found, listed belowe")
        print(changes_in_dict)
    else:
        
    
    id_desc = df_dd.set_index("variable").loc["id", "provenance"].split(" ")
    # ID description column should contain redcap and variable from which to read IDs, in format 'file: "{name of redcap}"; variable: "{column name}"'
    for i in id_desc:
        if "file:" in i:
            idx = id_desc.index(i)+1
            id_rc = id_desc[idx].strip("\"\';,()")
        elif "variable:" in i:
            idx = id_desc.index(i)+1
            var = id_desc[idx].strip("\"\';,()")
    if "id_rc" not in locals() or "var" not in locals():
        sys.exit("Can\'t find redcap column to read IDs from in datadict")
    for redcap in redcaps:
        if basename(redcap).lower().startswith(id_rc):
            consent_redcap = pd.read_csv(redcap, index_col=var)
            break
    if "consent_redcap" not in locals():
        sys.exit("Can\'t find" + id_rc + "redcap to read IDs from")
    ids = consent_redcap.index.tolist()
    
    headers = []
    for _, row in df_dd.iloc[0:].iterrows():
        # skip header
        # every row but 'id', 'consent', and assent should have allowed suffixes
        if not isinstance(row["allowedSuffix"], float):
            for suf in row["allowedSuffix"].split(', '):
                headers.append(row["variable"] + '_' + suf)
        else:
            headers.append(row["variable"])





    # write ids 
    with open(filepath, "w") as file:
        # write columns
        file.write(','.join(headers) + "\n")
        for id in ids:
            file.write(str(id) + "\n")


    dd_latest = splitext(DATA_DICT)[0] + "_latest.csv"
    shutil.copy(DATA_DICT, dd_latest)
