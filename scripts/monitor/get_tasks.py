import csv 
import sys

if __name__ == "__main__":
    filepath = sys.argv[1]

    tasks = ""

    # take note of headers
    headers = []
    with open(filepath) as dd:
        reader = csv.DictReader(dd)
        for row in dd:
            if "task status" in row["description"]:
                tasks += row["variable"] + ","

    print(tasks[:-1])
