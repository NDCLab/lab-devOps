import requests
import pandas as pd
from io import StringIO
from dataclasses import dataclass

@dataclass
class Report:
    name: str
    report_id: str
    report_df: pd.DataFrame = None

    def get_value_counts(self, column_suffix: str):
        if self.report_df is None:
            return None
        column_name = [col for col in self.report_df.columns if col.endswith(column_suffix)]
        if not column_name:
            print(f"All Column Names: {self.report_df.columns}")
            return None
        
        report_df = self.report_df.copy()
        value_counts = report_df[column_name[0]].value_counts()
        # transfrom the value counts series into a dataframe with the column name as the index and a count column
        value_counts_df = value_counts.reset_index()
        value_counts_df.columns = [column_suffix, "count"]
        return value_counts_df
    
    def get_year_month_groupings(self, date_time_col: str, year_month: tuple = None):
        if self.report_df is None:
            return None
        if date_time_col not in self.report_df.columns:
            return None
        
        dt_col = pd.to_datetime(self.report_df[date_time_col], errors='coerce')
        report_df = self.report_df.copy()
        report_df["year"] = dt_col.dt.year
        report_df["month"] = dt_col.dt.month
        if year_month:
            print(f"Filtering by year and month: {year_month}")
            year = year_month[0]
            month = year_month[1]
            filtered_df = report_df[(report_df["year"] == year) & (report_df["month"] == month)]
            filtered_df =  filtered_df.groupby([report_df["year"], report_df["month"]]).size()
        else:
            filtered_df = report_df.groupby([report_df["year"], report_df["month"]]).size()
        # turn the multi-index series into a dataframe with year-month as a column and count as another column
        filtered_df = filtered_df.reset_index(name="count")
        filtered_df["year_month"] = filtered_df["year"].astype(str) + "-" + filtered_df["month"].astype(str).str.zfill(2)
        filtered_df = filtered_df[["year_month", "count"]]
        return filtered_df
    