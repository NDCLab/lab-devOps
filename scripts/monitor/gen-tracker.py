import sys
import csv

DATA_DICT = "/home/data/NDClab/datasets/test-rweeeg-v2/data-monitoring/data-dictionary/central-tracker_datadict.csv"

if __name__ == "__main__":
    filepath = sys.argv[1]

    headers = []
    with open(DATA_DICT) as dd:
        for row in dd:
            headers.append(row.split()[0])

    with open(filepath, "w") as file:
        # write columns
        file.write(','.join(headers) + "\n")