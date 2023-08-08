import sys
import pandas as pd

if __name__ == "__main__":
    filepath = sys.argv[1]
    id_stand = int(sys.argv[2]) 
    project = sys.argv[3]

    DATA_DICT = "/home/data/NDClab/datasets/{}/data-monitoring/data-dictionary/central-tracker_datadict.csv".format(project)
    SUB_NUM = 1000

    df_dd = pd.read_csv(DATA_DICT)

    headers = []
    headers.append('id')
    for _, row in df_dd.iloc[1:].iterrows():
        # skip header
        # every row but 'id' should have allowed suffixes
        for suf in row["allowedSuffix"].split(', '):
            headers.append(row["variable"] + '_' + suf)

    # write id 1000 numbers 
    with open(filepath, "w") as file:
        # write columns
        file.write(','.join(headers) + "\n")
        for id in range(id_stand, id_stand + SUB_NUM):
            file.write(str(id) + "\n")
        
