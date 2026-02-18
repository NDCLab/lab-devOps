# Data Sharing Protocol 

This utility (`dataSharing.py`) is designed to extract, merge, and organize data from REDCap projects and associated instrument data dictionaries, producing a multi-sheet Excel file for data sharing and analysis.

## Features
- Selects columns from SCRD data files based on instrument definitions.
- Merges data from multiple REDCap projects and instruments into organized Excel sheets.

## How It Works
1. **Reads an input CSV** describing which instruments and REDCap projects to extract.
2. **Finds and loads the latest SCRD data files** for each project.
3. **Selects columns** based on instrument data dictionaries.
4. **Merges data** as needed and writes each result to a separate sheet in an Excel file.

## Usage
Run the script from the command line:

```bash
python dataSharing.py --input <input_csv> --name <dataset_name> --output <output_xlsx> [--verbose] --vars=<var1,var2,...>
```

- `--input`: Path to the input CSV file (see above).
- `--name`: Name of the dataset to process.
- `--output`: Path to the output Excel file.
- `--verbose`: (Optional) Enable verbose, color-coded logging.
- `--vars `: (Optional) Comma-separated list of variable names to extract directly instead of using an input CSV.

Note: (Cannot have both `--input` and `--vars` at the same time)



## Input CSV Format
The input CSV should contain at least the following columns:
- `columnName`: Name of the instrument/column to extract.
- `redcapProject`: Comma-separated list of REDCap project names to search for data.
- `sheetName`: Name of the Excel sheet to write the merged data to.
- `isColumn`: Boolean (True/False) indicating if `columnName` is a column prefix or a direct column name.

**Example:**
```csv
columnName,redcapProject,sheetName,isColumn
instrument1,ProjectA,Sheet1,True
instrument2,ProjectB,Sheet2,False
```


## File/Folder Structure
- **SCRD_PATH**: Folder containing SCRD data files (CSV format).
- **INSTRUMENTS_DATADICT_PATH**: Folder containing instrument data dictionaries (CSV format).
- **ALLMEASURES_PATH**: CSV file mapping instrument names to their data dictionaries.


## Example Command
```bash
python dataSharing.py --name dataset_name --input example_datadict.csv --output output.xlsx --verbose
```
```bash
python dataSharing.py --name thrive-dataset --output output.xlsx --verbose --vars=infosht,bfnep_b,infosht_agemos_s1_r1_e1
```



## Notes
- Ensure all referenced paths (SCRD, instruments, allMeasures) are correct and accessible.
- The script expects SCRD files and data dictionaries to follow specific naming conventions.
- Verbose mode is recommended for troubleshooting.

## TODO
- Add error handling for missing files or columns.
- highlight certain columns in the output Excel for easier review.

## License
See project-level LICENSE file for details.
