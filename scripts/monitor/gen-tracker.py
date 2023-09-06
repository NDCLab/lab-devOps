import sys
import pandas as pd
from os.path import basename

if __name__ == "__main__":
    filepath = sys.argv[1]
    project = sys.argv[2]
    redcaps = sys.argv[3]

    redcaps = redcaps.split(",")
    DATA_DICT = "/home/data/NDClab/datasets/{}/data-monitoring/data-dictionary/central-tracker_datadict.csv".format(project)
    df_dd = pd.read_csv(DATA_DICT)

    id_desc = df_dd.set_index("variable").loc["id", "description"].split(" ")
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
        sys.exit("Can\'t find", id_rc, "redcap to read IDs from")
    ids = consent_redcap.index.tolist()

    headers = []
    sessionless = ["id", "consent", "assent"]
    headers.extend(sessionless)
    for _, row in df_dd.iloc[0:].iterrows():
        # skip header
        # every row but 'id', 'consent', and assent should have allowed suffixes
        if row["variable"] not in sessionless:
            for suf in row["allowedSuffix"].split(', '):
                headers.append(row["variable"] + '_' + suf)
    # write ids 
    with open(filepath, "w") as file:
        # write columns
        file.write(','.join(headers) + "\n")
        for id in ids:
            file.write(str(id) + "\n")
