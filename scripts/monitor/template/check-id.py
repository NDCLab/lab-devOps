import sys
import pandas as pd

if __name__ == "__main__":
    id = sys.argv[1]
    file = sys.argv[2]
    
    # extract id col
    file_df = pd.read_csv(file, error_bad_lines=False, warn_bad_lines=False)
    if "id" in file_df:
        id_col = file_df["id"]
    elif "participant" in file_df:
        id_col = file_df["participant"]
    else:
        print("False, cannot find id or participant column")

    # check if first ids match vals listed
    print(id_col[0] == int(id))
