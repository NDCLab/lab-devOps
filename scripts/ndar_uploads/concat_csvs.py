import os
from os.path import basename, join, isdir
import sys
import re

### combines identically-named .csv files in multiple folders (up to sX_rX_eX) into single .csv files for NIH uploads
###
### USAGE: python3 concat_csvs.py <folder1,folder2,folder3...> <output folder>


if __name__ == "__main__":
    folders = sys.argv[1]
    out_path = sys.argv[2]
    folders = folders.split(',')
    if not isdir(out_path):
        os.mkdir(out_path)
    files_in_common = os.listdir(folders[0])
    unique_files = {}
    for file in files_in_common:
        file_re = re.match('^(.+)_s[0-9]+_r[0-9]+_e[0-9]+_incomplete.csv', file)
        if file_re:
            unique_files[file_re.group(1)] = [join(folders[0],file)]
    if len(unique_files) == 0:
        sys.exit("No unique files ending in \"sX_rX_eX_incomplete.csv\" seen in folders")
    for i in range(1, len(folders)):
        folder = folders[i]
        files = os.listdir(folder)
        files_in_folder = []
        for file in files:
            file_re = re.match('^(.+)_s[0-9]+_r[0-9]+_e[0-9]+_incomplete.csv', file)
            if file_re:
                files_in_folder.append(file_re.group(1))
                if file_re.group(1) not in unique_files.keys():
                    _ = unique_files.pop(file, None)
                else:
                    unique_files[file_re.group(1)].append(join(folder,file))
    file_dict = {}
    for filename_base in unique_files.keys():
        first_file = True
        with open(join(out_path, filename_base + "_combined_incomplete.csv"), 'w') as o:
            for file in unique_files[filename_base]:
                with open(file, 'r') as file_dict[i]:
                    lines = file_dict[i].readlines()
                    if first_file:
                        lines_to_write = range(0, len(lines))
                        first_file = False
                    else:
                        lines_to_write = range(2, len(lines))
                    for j in lines_to_write:
                        _ = o.write(lines[j])
                file_dict[i].close()
        print("wrote out " + join(out_path, filename_base + "_combined_incomplete.csv"))
        o.close()
