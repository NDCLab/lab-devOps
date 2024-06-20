import sys
import pandas as pd
import math
import sys

if __name__ == "__main__":
    id = sys.argv[1]
    file = sys.argv[2]
    
    # extract id col
    if pd.__version__ >= "1.4.0":
        file_df = pd.read_csv(file, on_bad_lines="skip")
    else:
        file_df = pd.read_csv(file, error_bad_lines=False, warn_bad_lines=False)
    if "id" in file_df:
        id_col = file_df["id"]
    elif "participant" in file_df:
        id_col = file_df["participant"]
    else:
        sys.exit("Error: cannot find id or participant column in"+ file)

    # check if first ids match vals listed
    if isinstance(id_col[0], float) and math.isnan(id_col[0]):
        print("Error: nan value seen in ID for", file, "file")
    else:
        if not int(id_col[0]) == int(id):
            print("Error: ID value in", file, str(id_col[0]), "does not match", id)
