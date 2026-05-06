
import json
import sys
sys.path.append("../..")
from LabTesting.thriveFlow.utils.reportService import ReportService
import argparse
import os
api_tokens = {}
def get_flow_numbers(reports):
    print("Getting flow numbers...")
    report_service = ReportService()
    print("Getting SEARCHER reports...")
    for report in reports:
            print(f"Report: {report['report_name']}")
            api_token = api_tokens.get(report["project_name"])
            report_data = report_service.get_report(api_token, report["report_id"])
            if report_data is None:
                print(f"Failed to fetch report {report['report_name']}. Skipping.")
                break
            report_df = report_data.report_df
            print(f"Total Length: {len(report_df)} records.")
            if report_df.empty:
                print(f"Report {report['report_name']} is empty. Skipping aggregations.")
                print("\n------------------------------\n")
                continue
            for agg in report["aggregation"]:
                if agg["type"] == "value_counts":
                     value_cnt = report_data.get_value_counts(agg["column_suffix"])
                     print(f"Value counts for {agg['column_suffix']}:\n{value_cnt}\n")
                elif agg["type"] == "year_month_grouping":
                     groupings = report_data.get_year_month_groupings(agg["date_time_col"], agg.get("year_month"))
                     print(f"Year-Month groupings:\n{groupings}\n")
            print("\n------------------------------\n")
if __name__ == "__main__":
    # read it from a folder
    project_names = set()
    for i in os.listdir("json"):
        if i.endswith(".json"):
            js_file = os.path.join("json", i)
            with open(js_file, "r") as f:
                json_data = json.load(f)
                for report in json_data:
                    project_names.add(report["project_name"])
    for project_name in project_names:
        api_tokens[project_name] = input(f"Enter API token for {project_name}: ")

    for i in os.listdir("json"):
        if i.endswith(".json"):
            with open(os.path.join("json", i), "r") as f:
                json_ex = json.load(f)
            get_flow_numbers(json_ex)
