import pandas as pd
import sys
from os.path import join
import os


if __name__ == "__main__":
    eeg_file_path = sys.argv[1]
    ndar_submissions = sys.argv[2]
    if ndar_submissions:
        sessions = ndar_submissions.split(',')
        eeg_df = pd.read_csv(eeg_file_path,header=1)
        redcap_dfs = dict()
        for sess in sessions:
            redcap_file = sess.strip()
            # get the folder name of the file
            dir = os.path.dirname(redcap_file)
            ses = os.path.basename(dir).split('_')[0]
            # find a file that starts with ndar_submissions
            if os.path.exists(redcap_file):
                redcap_dfs[ses] = pd.read_csv(redcap_file,header=1)
            else:
                raise FileNotFoundError(f"File {redcap_file} does not exist.")
        for index, row in eeg_df.iterrows():
            timepoint_label = row['timepoint_label']
            if timepoint_label in redcap_dfs:
                redcap_df = redcap_dfs[timepoint_label]
                print()
                src_subject_id = row['src_subject_id']
                matched_rows = redcap_df[redcap_df['src_subject_id'] == int(src_subject_id)]
                if len(matched_rows) == 1:
                    eeg_df.at[index, 'interview_date'] = matched_rows.iloc[0]['interview_date']
                    eeg_df.at[index, 'interview_age'] = matched_rows.iloc[0]['interview_age']
                    eeg_df.at[index, 'sex'] = matched_rows.iloc[0]['sex']
        eeg_df.to_csv(eeg_file_path, index=False)
