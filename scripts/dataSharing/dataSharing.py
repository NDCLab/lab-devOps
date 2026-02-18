
# =========================
# Imports and Constants
# =========================
import sys
import argparse
import os
import re
import pandas as pd
from datetime import datetime

# Paths and Configurations
INSTRUMENTS_DATADICT_PATH = '/home/data/NDClab/tools/instruments'
ALLMEASURES_PATH = 'allMeasures.csv'
COLOR_MAP = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "reset": "\033[0m"
}

# =========================
# Utility Functions
# =========================
def parse_args():
    parser = argparse.ArgumentParser(description="Data Sharing Protocol")
    parser.add_argument('--name', type=str, help='Name of the dataset')
    parser.add_argument('--input', type=str, help='Input file path')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--vars', type=str, help='Variables to process, comma-separated')
    return parser.parse_args()

def formatted_print(message, color="white"):
    if color != "white":
        color_code = COLOR_MAP.get(color, COLOR_MAP["red"])
        sys.stdout.write(f"{color_code}{message}{COLOR_MAP['reset']}\n")
        sys.stdout.flush()
    else:
        print(message)

# =========================
# Main Data Sharing Class
# =========================
class DataSharingProtocol:
    def __init__(self, args):
        self.args = args
        self.SCRD_PATH = f"/home/data/NDClab/datasets/{self.args.name}/derivatives/preprocessed/redcap"
        if not self.args.vars:
            self.inputDF = pd.read_csv(self.args.input)
            self.inputDF['redcapProject'] = self.inputDF['redcapProject'].apply(lambda x: [item.strip() for item in x.split(',')])

    # ========== Logging ==========
    def verbose_log(self, message, color="white"):
        if self.args.verbose:
            formatted_print(message, color)

    # ========== File/Column Utilities ==========
    def save_dfs_to_xlsx(self, df_list, output_file):
        """Save a dictionary of DataFrames to an Excel file, with each key as a sheet name."""
        with pd.ExcelWriter(output_file) as writer:
            for sheet_name, df in df_list.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        self.verbose_log(f"DataFrames saved to {output_file}", color="green")

    def get_cols(self, name, instrument, instr_cols=None, isCol=True):
        """Extract columns from a CSV file that match the instrument prefix."""
        df = pd.read_csv(name)
        cols = []
        index_col = "record_id"
        if not isCol:
            self.verbose_log(f"Using instrument as column directly: {instrument}", color="cyan")
            instr_cols = [instrument]
        for instr_col in instr_cols:
            matched_cols = [col for col in df.columns if col.startswith(instr_col)]
            cols.extend(matched_cols)
        full_cols = cols
        self.verbose_log(f"Selected columns for instrument {instrument}: {len(full_cols)}", color="yellow")
        full_cols.insert(0, index_col)
        return df[full_cols]

    def find_files_with_prefix(self, root_dir, prefix):
        """Search for a file in a directory that starts with the given prefix and ends with '_datadict.csv'."""
        full_name = prefix.lower() + "_datadict.csv"
        self.verbose_log(f"Searching for files with prefix: {full_name} in {root_dir}")
        if not os.path.exists(root_dir):
            self.verbose_log(f"Root directory does not exist: {root_dir}")
            raise FileNotFoundError(f"Root directory does not exist: {root_dir}")
        for root, dirs, files in os.walk(root_dir):
            for filename in files:
                filename_lower = filename.lower()
                if filename_lower.startswith(full_name):
                    return os.path.join(root, filename)
        return []

    def find_best_match(self, instrument, all_instruments):
        base_instrument = re.sub(r'_s\d+_r\d+_e\d+$', '', instrument)
        for instr in all_instruments:
            if base_instrument.startswith(instr):
                return instr
        return None

    def get_instrument_data_dict(self, instrument):
        allMeasures = pd.read_csv(ALLMEASURES_PATH)
        if re.search(r'_s\d+_r\d+_e\d+$', instrument):
            instrument = re.sub(r'_s\d+_r\d+_e\d+$', '', instrument)
        instrument = self.find_best_match(instrument, allMeasures['Instrument Name'].values)
        if instrument not in allMeasures['Instrument Name'].values:
            raise ValueError(f"Instrument {instrument} not found in allMeasures.csv")
        datadictLink = allMeasures[allMeasures['Instrument Name'] == instrument]['Data Dict']
        if datadictLink.empty:
            raise ValueError(f"No Data Dict link found for instrument {instrument} in allMeasures.csv")
        datadict = datadictLink.values[0]
        return os.path.join(INSTRUMENTS_DATADICT_PATH, datadict)

    def get_instrument_cols(self, instrument):
        sess = dict()
        base_name = instrument.split('_')[0]
        based_name = base_name[:-1] if base_name.endswith('p') else base_name
        instrument_path = f"{INSTRUMENTS_DATADICT_PATH}/{based_name}/"
        self.verbose_log(f"Base name: {base_name}, Based name: {based_name}, Instrument path: {instrument_path}")
        instrumentes = base_name + 'es' + instrument[len(base_name):]
        instrument_list = [instrument, instrumentes]
        datadict = self.get_instrument_data_dict(instrument)
        datadict_es = self.find_files_with_prefix(instrument_path, instrumentes)
        if not datadict_es:
            self.verbose_log(f"No datadict found for instrument: {instrumentes}, proceeding with single instrument", color="red")
            instrument_list = [instrument]
            datadicts = [datadict]
        else:
            datadicts = [datadict, datadict_es]
        self.verbose_log(f"Instrument list to search for datadict: {instrument_list}")
        #self.verbose_log(f"Datadict files to read: {datadicts}")
        for i in range(len(instrument_list)):
            inst = instrument_list[i]
            datadict = datadicts[i]
            ndx = pd.read_csv(datadict)
            for _, row in ndx.iterrows():
                suffixes = row['allowedSuffix'].split(',')
                session_num = [re.search(r's(\d+)', val).group(1) for val in suffixes]
                suffixes = [f"s{num}" for num in session_num]
                for suffix in suffixes:
                    if suffix not in sess:
                        sess[suffix] = []
                    col_name = f"{row['variable']}_{suffix}"
                    sess[suffix].append(col_name)
        self.verbose_log(f"Total columns for instrument {instrument}: {len(sess)}", color="yellow")
        return sess

    def get_scrd_df(self, instrument, suffix=""):
        allMeasures = pd.read_csv(ALLMEASURES_PATH)
        self.verbose_log(f"Getting SCRD DF for instrument: {instrument} with suffix: {suffix}", color="blue")
        if re.search(r'_s\d+_r\d+_e\d+$', instrument):
            instrument_prefix = re.sub(r'_s\d+_r\d+_e\d+$', '', instrument)
            matched_instruments = [inst for inst in allMeasures['Instrument Name'].values if instrument_prefix.startswith(inst)]
            if not matched_instruments:
                raise ValueError(f"No matching instrument found for {instrument} in allMeasures.csv")
            if len(matched_instruments) > 1:
                self.verbose_log(f"Multiple matched instruments for {instrument}: {matched_instruments}", color="red")
                raise ValueError(f"Multiple matched instruments for {instrument}: {matched_instruments}")
            if len(matched_instruments) == 1:
                instrument = matched_instruments[0]
            self.verbose_log(f"Matched instrument for {instrument}: {instrument}", color="cyan")
        if instrument not in allMeasures['Instrument Name'].values:
            raise ValueError(f"Instrument {instrument} not found in allMeasures.csv")
        redCapProject = allMeasures[allMeasures['Instrument Name'] == instrument]['REDCap Project']
        if redCapProject.empty:
            raise ValueError(f"No REDCap Project found for instrument {instrument} in allMeasures.csv")
        projectName = redCapProject.values[0].replace('_', '') if '_' in redCapProject.values[0] else redCapProject.values[0]
        projectName = projectName + suffix
        return [projectName]

    def get_latest_file(self, files, key):
        date_re = re.compile(r'_SCRD_(\d{4}-\d{2}-\d{2})_\d{4}')
        latest_file = max(
            (f for f in files if key in f.lower() and date_re.search(f)),
            key=lambda f: datetime.strptime(date_re.search(f).group(1), "%Y-%m-%d"),
            default=None
        )
        if latest_file is None:
            raise FileNotFoundError(f"No file found for {key}")
        return latest_file

    # ========== Main Data Sharing Logic ==========
    def data_sharing(self):
        df_list = dict()
        for _, row in self.inputDF.iterrows():
            scrdFiles = os.listdir(self.SCRD_PATH)
            instrumentName = row["columnName"]
            if row['isColumn']:
                instr_cols = [instrumentName]
            else:
                sess = self.get_instrument_cols(row["columnName"])
                instr_cols = [col for sublist in sess.values() for col in sublist]
            df_names = row['redcapProject']
            sheetName = row['sheetName']
            self.verbose_log(f"Processing {instrumentName}: for {df_names}", color="magenta")
            for dfName in df_names:
                scrdFile = self.get_latest_file(scrdFiles, dfName.lower())
                scrdFilePath = os.path.join(self.SCRD_PATH, scrdFile)
                self.verbose_log(f"Reading file: {scrdFile}")
                if sheetName not in df_list:
                    df_list[sheetName] = self.get_cols(scrdFilePath, instrumentName, instr_cols, row['isColumn'])
                else:
                    new_df = self.get_cols(scrdFilePath, instrumentName, instr_cols, row['isColumn'])
                    df_list[sheetName] = pd.merge(df_list[sheetName], new_df, on='record_id', how='outer')
        self.save_dfs_to_xlsx(df_list, self.args.output)

    def direct_data_sharing(self, vars):
        df_list = dict()
        for variable in vars:
            scrdFiles = os.listdir(self.SCRD_PATH)
            instrumentName = variable
            suffix = ""
            if re.search(r'_s\d+_r\d+_e\d+$', instrumentName):
                instr_cols = [instrumentName]
                index = re.search(r'_s(\d+)_r\d+_e\d+$', instrumentName)
                if index:
                    session_number = index.group(1)
                    suffix = f"s{session_number}"
            else:
                sess = self.get_instrument_cols(instrumentName)
                suffix = list(sess.keys())[0]
                instr_cols = [col for sublist in sess.values() for col in sublist]
            df_names = self.get_scrd_df(instrumentName, suffix)
            self.verbose_log(f"DF names for {instrumentName}: {df_names}", color="cyan")
            sheetName = variable
            self.verbose_log(f"Processing {instrumentName}: for {df_names}", color="magenta")
            for dfName in df_names:
                self.verbose_log(f"DF Name: {dfName}", color="blue")
                scrdFile = self.get_latest_file(scrdFiles, dfName.lower())
                scrdFilePath = os.path.join(self.SCRD_PATH, scrdFile)
                self.verbose_log(f"Reading file: {scrdFile}")
                if sheetName not in df_list:
                    df_list[sheetName] = self.get_cols(scrdFilePath, instrumentName, instr_cols)
        self.save_dfs_to_xlsx(df_list, self.args.output)

    # ========== Main Entrypoint ==========
    def run(self):
        formatted_print("Starting Data Sharing Protocol...", color="green")
        if self.args.vars:
            vars = [var.strip() for var in self.args.vars.split(',')]
            self.direct_data_sharing(vars)
        else:
            self.data_sharing()
        formatted_print("Data Sharing Protocol completed", color="green")

# =========================
# Script Entrypoint
# =========================
if __name__ == "__main__":
    args = parse_args()
    app = DataSharingProtocol(args)
    app.run()
