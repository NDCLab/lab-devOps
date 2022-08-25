import sys

DEF_COLS = ("id", "consent")
DATA_LAB = "Data"
INCREMENT = 20

if __name__ == "__main__":
    filepath = sys.argv[1]
    datatypes = sys.argv[2]
    ids = int(sys.argv[3])

    # list and label the available datatypes
    header = list(DEF_COLS) + [dt + DATA_LAB for dt in datatypes.split(",")]

    with open(filepath, "w") as file:
        # write columns
        file.write(','.join(header))
        for i in range(INCREMENT):
            file.write(ids)
            ids += 1