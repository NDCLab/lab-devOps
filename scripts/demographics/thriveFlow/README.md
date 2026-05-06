# ThriveFlow

## Overview

ThriveFlow is a Python application designed to fetch and analyze reports from **REDCap** (Research Electronic Data Capture). It retrieves data from specified REDCap projects using API tokens, processes the reports, and performs configurable aggregations such as value counts and temporal groupings.

This tool is particularly useful for extracting flow data and analyzing research study reports without directly querying the REDCap interface.

## Project Structure

```
thriveFlow/
├── app.py                  # Main application script
├── extractFlow.ipynb       # Jupyter notebook for data exploration
├── json/                   # Configuration files
│   ├── bbs2.json          # BBS (Behavior Baseline Survey) configuration
│   └── iqs2.json          # IQS (Intake Questionnaire Survey) configuration
└── utils/
    ├── Report.py          # Report data class and methods
    └── reportService.py   # REDCap API service
```

## Features

- **REDCap Integration**: Connect to REDCap API using authentication tokens
- **Automated Report Fetching**: Retrieve reports from multiple projects and datasets
- **Data Aggregation**: 
  - Value counts for categorical columns
  - Year-month grouping and temporal analysis
- **Configurable Processing**: Define reports and aggregations via JSON configuration files
- **DataFrame-based**: Uses pandas for efficient data manipulation

## Requirements

- Python 3.x
- pandas
- requests

## Installation

```bash
pip install pandas requests
```

## Configuration

Reports are configured using JSON files in the `json/` directory. Each JSON file should contain an array of report definitions.

### JSON Configuration Format

```json
[
  {
    "report_name": "Name of the Report",
    "project_name": "PROJECT_KEY",
    "report_id": "12345",
    "aggregation": [
      {
        "type": "value_counts",
        "column_suffix": "_some_column"
      },
      {
        "type": "year_month_grouping",
        "date_time_col": "date_column_name",
        "year_month": [2024, 3]
      }
    ]
  }
]
```

### Configuration Fields

- **report_name** (string): Human-readable name for the report
- **project_name** (string): Key used to look up the API token in `api_tokens` dictionary
- **report_id** (string): REDCap report ID
- **aggregation** (array): List of aggregation operations to perform
  - **type** (string): `"value_counts"` or `"year_month_grouping"`
  - **column_suffix** (string): For value_counts, the suffix of the column to count
  - **date_time_col** (string): For year_month_grouping, the datetime column name
  - **year_month** (optional array): For year_month_grouping, `[year, month]` to filter specific month

## Usage

### Running the Application

```bash
cd thriveFlow
python app.py
```

The application will:
1. Scan the `json/` directory for all `.json` configuration files
2. Load each configuration
3. Fetch reports from REDCap using configured tokens and report IDs
4. Perform specified aggregations
5. Print results to console

### Example Output

```
Getting flow numbers...
Getting SEARCHER reports...
Report: My Report Name
Total Length: 150 records.
Value counts for _column_suffix:
  value_name    count
0     option1      95
1     option2      55

Year-Month groupings:
  year_month  count
0    2024-01      30
1    2024-02      45
...
```

### Using the Jupyter Notebook

The `extractFlow.ipynb` notebook provides an interactive environment for:
- Exploring report structure
- Testing aggregation logic
- Developing new analyses

```bash
jupyter notebook extractFlow.ipynb
```

## API Configuration

API tokens must be configured in `app.py` in the `api_tokens` dictionary:

```python
api_tokens = {
    "PROJECT_KEY": "YOUR_API_TOKEN_HERE",
    "ANOTHER_PROJECT": "ANOTHER_TOKEN_HERE",
}
```

**Important**: API tokens are sensitive credentials. Keep them secure and never commit them to version control.

## Core Classes and Methods

### ReportService

Handles REDCap API communication.

#### Methods

- **`get_report(token, report_id)`**
  - Fetches a report from REDCap
  - **Parameters**:
    - `token`: API token for authentication
    - `report_id`: REDCap report ID
  - **Returns**: `Report` object or `None` if request fails

### Report

Represents a REDCap report with data analysis methods.

#### Attributes

- `name`: Report name
- `report_id`: REDCap report ID
- `report_df`: pandas DataFrame containing the report data

#### Methods

- **`get_value_counts(column_suffix)`**
  - Counts occurrences of values in a column (matched by suffix)
  - **Parameters**:
    - `column_suffix`: Suffix of the column to analyze
  - **Returns**: DataFrame with columns (suffix, count)

- **`get_year_month_groupings(date_time_col, year_month=None)`**
  - Groups records by year and month
  - **Parameters**:
    - `date_time_col`: Name of the datetime column
    - `year_month`: Optional tuple `(year, month)` to filter specific month
  - **Returns**: DataFrame with columns (year_month, count)

## Example Configuration Files

### bbs2.json

Configuration for Behavior Baseline Survey reports.

### iqs2.json

Configuration for Intake Questionnaire Survey reports.

## Workflow

1. **Define Reports**: Create or modify JSON configuration files with report IDs and aggregations
2. **Configure Tokens**: Add API tokens to `app.py` for each project
3. **Run Analysis**: Execute `app.py` to fetch and analyze all configured reports
4. **Explore Data**: Use `extractFlow.ipynb` for deeper analysis or visualization

## Error Handling

The application handles common errors:

- **Missing Reports**: If a report fetch fails, it prints an error and continues to the next report
- **Empty Reports**: Reports with no data are identified and skipped
- **Missing Columns**: Column suffix mismatches are logged with available column names

### Troubleshooting

**Issue**: `Failed to fetch report`
- **Solution**: Verify the API token is correct and the report ID exists in that project

**Issue**: `Column not found`
- **Solution**: Check the column suffix matches columns in the report (use `print(df.columns)`)

**Issue**: `Unauthorized (401)`
- **Solution**: Verify API token is valid and has permissions to access the report

## Performance Notes

- Large reports (>10,000 records) may take longer to fetch from REDCap
- Aggregations are performed in-memory, so very large datasets may require optimization
- Consider filtering data within REDCap rather than in the application for better performance

## Future Enhancements

- Add output to CSV/Excel files
- Support for more aggregation types (e.g., sum, mean, custom functions)
- Caching to avoid re-fetching unchanged reports
- Dashboard/visualization outputs
- Parallel report fetching
- Data quality checks and validation

## References

- [REDCap API Documentation](https://redcap.fiu.edu/)
- [Pandas Documentation](https://pandas.pydata.org/)
