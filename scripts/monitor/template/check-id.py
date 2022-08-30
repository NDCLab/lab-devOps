import sys
import pandas as pd

if __name__ == "__main__":
    id = sys.argv[1]
    file = sys.argv[2]
    print(file)
    
    # extract id col
    file_df = pd.read_csv(file)
    id_col = file_df["id"]

    # check if all ids match vals listed
    print(all(id_col == int(id)))
