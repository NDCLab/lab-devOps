# RMR (Racial/Minority Response) Analysis Script

## Overview

RMR.py is a Python script designed to analyze demographic data from REDCap CSV exports and generate a **Racial/Minority Response (RMR) report**. It processes race and ethnicity information to count white-only respondents versus minority respondents, with specific support for Hispanic/Latinx identification.

## Features

- **Race Classification**: Identifies respondents who selected only "White" versus those with minority identifications
- **Hispanic/Latinx Tracking**: Separately counts Hispanic/Latinx respondents
- **Multi-language Support**: Handles both English and Spanish demographic forms (with `_es` suffix columns)
- **Data Validation**: Ensures data completeness by filtering for fully completed demographic sections
- **Summary Report**: Generates a formatted report with total responses, minority counts, and Hispanic counts

## Requirements

- Python 3.x
- pandas
- argparse (standard library)

## Installation

```bash
pip install pandas
```

## Usage

```bash
python RMR.py <path_to_csv_file>
```

### Arguments

- `df_path` (required): Path to the CSV file containing the demographic data

### Example

```bash
python RMR.py data/demographics.csv
```

## Input File Format

The script expects a CSV file with the following demographic columns (from REDCap):

### Required Columns:
- `demo_d_race_s1_r1_e1___*`: Race response columns (checkbox fields, one column per option)
- `demoes_d_race_s1_r1_e1___*`: Spanish version of race columns
- `demo_d_race_s1_r1_e1___10`: White race indicator (binary: 0 or 1)
- `demoes_d_race_s1_r1_e1___10`: Spanish white race indicator
- `demo_d_latinx_s1_r1_e1`: Hispanic/Latinx indicator (binary)
- `demoes_d_latinx_s1_r1_e1`: Spanish Hispanic/Latinx indicator
- `demo_d_s1_r1_e1_complete`: Completion status (2 = complete)
- `demoes_d_s1_r1_e1_complete`: Spanish completion status

### Data Requirements:
- Only records where the demographic section is marked as complete (value = 2) are included in the analysis
- Missing values are treated as 0 (no response)

## Output

The script prints a summary report with the following format:

```
RMR Report Summary
-------------------
Total responses: [number]
 Minority Response: [number]
 Hispanic Response: [number]
```

### Definitions:
- **Total responses**: Number of completed demographic responses
- **Minority Response**: Total responses minus white-only respondents
- **Hispanic Response**: Count of respondents who identified as Hispanic/Latinx

## Functions

### `only_white_res(df, white_col)`
Counts respondents who selected only "White" (no other race selected) in the given column.

- **Parameters**: 
  - `df`: DataFrame containing race columns
  - `white_col`: Column name for the white race indicator
- **Returns**: Count of white-only respondents

### `get_race_count(df, col)`
Returns the count of respondents who selected "yes" (value = 1) for a specific race/ethnicity column.

- **Parameters**:
  - `df`: DataFrame
  - `col`: Column name to count
- **Returns**: Count of respondents with value = 1

### `compute_rmr(df_path)`
Main function that orchestrates the analysis workflow.

- **Parameters**:
  - `df_path`: Path to the CSV file
- **Returns**: None (prints summary to console)

## Notes

- The script handles both English and Spanish data collection forms automatically
- REDCap checkbox fields create multiple columns (one per option), which the script filters and processes
- The analysis only includes records with completed demographic information
- White-only determination requires checking that the row sum equals 1 (only one race selected)

## Example Data Structure

```
record_id,demo_d_race_s1_r1_e1___1,demo_d_race_s1_r1_e1___2,...,demo_d_race_s1_r1_e1___10,demo_d_latinx_s1_r1_e1,demo_d_s1_r1_e1_complete
001,0,0,...,1,0,2
002,1,0,...,0,0,2
003,0,1,...,0,1,2
```

## Troubleshooting

**Issue**: "Please provide a path to the CSV file containing the data"
- **Solution**: Make sure you're providing the file path as an argument: `python RMR.py path/to/file.csv`

**Issue**: KeyError for demographic columns
- **Solution**: Verify that your CSV file contains the expected REDCap demographic columns (`demo_d_race_s1_r1_e1___*`, etc.)

**Issue**: No output or unexpected results
- **Solution**: Check that your data has records with completion status = 2 for the demographic section

## Future Enhancements

- Add output to file option (currently prints to console)
- Add options for filtering by other demographics
- Generate visualizations of RMR data
- Add support for additional demographic fields
