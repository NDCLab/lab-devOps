import csv 
import sys

if __name__ == "__main__":
    filepath = sys.argv[1]

    tasks = ""
    with open(filepath, "r") as dd:
        reader = csv.DictReader(dd)
        for row in reader:
            if "task status" in row["description"]:
                tasks += row["\xef\xbb\xbfvariable"] + ","

    print(tasks[:-1])
