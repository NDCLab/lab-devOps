import csv 
import sys

if __name__ == "__main__":
    filepath = sys.argv[1]

    tasks = []
    with open(filepath, "r") as dd:
        reader = csv.DictReader(dd)
        for row in reader:
            if "task status" in row["description"]:
                tasks.append(row["\xef\xbb\xbfvariable"]) #works for Python-2.7.5
                #tasks.append(row["\ufeffvariable"]) #works for Python-3.6.8
    print(','.join(tasks))
