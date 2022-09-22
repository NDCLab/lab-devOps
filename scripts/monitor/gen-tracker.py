import sys

DATA_DICT = "/home/data/NDClab/datasets/test-rweeeg-v2/data-monitoring/data-dictionary/central-tracker_datadict.csv"
SUB_NUM = 1000

if __name__ == "__main__":
    filepath = sys.argv[1]
    filetypes = sys.argv[2]
    id_stand = int(sys.argv[3]) 

    # take note of headers
    headers = []
    with open(DATA_DICT) as dd:
        # skip header
        next(dd)
        for row in dd:
            headers.append(row.replace(',', '|', 1).split("|")[0])
    # append data-types as headers if not already included
    for type in filetypes:
        type_concat = type + "Data_s1_r1_e1"
        if type_concat not in headers:
            headers.append(type_concat)

    # write id 1000 numbers 
    with open(filepath, "w") as file:
        # write columns
        file.write(','.join(headers) + "\n")
        for id in range(id_stand, id_stand + SUB_NUM):
            file.write(str(id) + "\n")