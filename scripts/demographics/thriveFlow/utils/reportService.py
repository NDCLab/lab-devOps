import requests
import pandas as pd
from io import StringIO
import sys
sys.path.append("../..")
from LabTesting.thriveFlow.utils.Report import Report


class ReportService:
    URL  = "https://redcap.fiu.edu/api/"
    def __init__(self):
        pass

    def get_report(self, token, report_id):
        payload = {
            "token": token,
            "content": "report",
            "format": "csv",
            "report_id": report_id,
            "csvDelimiter": "",
            "rawOrLabel": "label",
            "rawOrLabelHeaders": "raw",
            "exportCheckboxLabel": "false",
            "returnFormat": "csv"
        }
        response = requests.post(self.URL, data=payload)
        if response.status_code == 200:
            if not response.text.strip():
                print(f"Report {report_id} is empty.")
                return Report(name=f"Report {report_id}", report_id=report_id, report_df=pd.DataFrame())
            df = pd.read_csv(StringIO(response.text))
            report = Report(name=f"Report {report_id}",  report_id=report_id, report_df=df)
            return report
        else:
            print(f"Error fetching report {report_id}: {response.status_code}")
            return None