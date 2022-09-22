import sys

DATA_DICT = "/home/data/NDClab/datasets/test-rweeeg-v2/data-monitoring/data-dictionary/central-tracker_datadict.csv"
SUB_NUM = 1000

if __name__ == "__main__":
    filepath = sys.argv[1]
    id = sys.argv[2]

    headers = []
    with open(DATA_DICT) as dd:
        for row in dd:
            headers.append(row.replace(',', '|', 1).split("|")[0])

    # include arbitrary number of parts

    with open(filepath, "w") as file:
        # write columns
        file.write(','.join(headers) + "\n")