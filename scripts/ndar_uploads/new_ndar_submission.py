import os
from os.path import basename, join, isdir
import sys
import re
from collections import defaultdict

if __name__ == "__main__":
    dataset = sys.argv[1]
    current_submission = sys.argv[2]
    dataset = '/home/data/NDClab/datasets/' + dataset
    print("starting")
    if not isdir(join(dataset,'data-monitoring','ndar',current_submission)):
        sys.exit("Error, current submission folder doesn't exist")
    if not isdir(join(dataset,'data-monitoring','ndar',current_submission,'eeg')):
        os.mkdir(join(dataset,'data-monitoring','ndar',current_submission,'eeg'))
    prior_submissions = []
    for dir in os.listdir(join(dataset,'data-monitoring','ndar')):
        if dir != current_submission and isdir(join(dataset,'data-monitoring','ndar',dir)):
            prior_submissions.append(join(dataset,'data-monitoring','ndar',dir))
    if len(prior_submissions) == 0:
        #sys.exit("Error, no prior_submission directories seen in ndar folder")
        print("first submission")
    prior_sub_files = []
    for prior_submission in prior_submissions:
        for file in os.listdir(join(prior_submission,'eeg')):
            if re.match('(sub-[0-9]+)_[a-zA-Z0-9_-]+_(s[0-9]+_r[0-9]+)_e[0-9]+\.zip', file):
                prior_sub_files.append(file)
    current_sub_files = []
    for sub_folder in os.listdir(join(dataset,'sourcedata','checked')):
        if sub_folder.startswith('sub-'):
            for sess_folder in os.listdir(join(dataset,'sourcedata','checked',sub_folder)):
                if isdir(join(dataset,'sourcedata','checked',sub_folder,sess_folder,'eeg')):
                    if len(os.listdir(join(dataset,'sourcedata','checked',sub_folder,sess_folder,'eeg'))) > 0:
                        if not 'no-data.txt' in os.listdir(join(dataset,'sourcedata','checked',sub_folder,sess_folder,'eeg')):
                            current_sub_files.append(sub_folder+'_all_eeg_'+sess_folder+'_e1.zip')
    new_sub_files = set(current_sub_files).difference(set(prior_sub_files))
    if len(new_sub_files) == 0:
        sys.exit("Exiting, no new subjects seen")
    else:
        file_by_session = defaultdict(list)
        for file in new_sub_files:
            file_re = re.match('(sub-[0-9]+)_[a-zA-Z0-9_-]+_(s[0-9]+)_r[0-9]+_e[0-9]+\.zip', file)
            if file_re:
                sess = file_re.group(2)
                file_by_session[sess].append(file)
        new_sub_files = []
        sessions = list(file_by_session.keys())
        sessions.sort()
        for sess in sessions:
            file_by_session[sess].sort()
            new_sub_files.extend(file_by_session[sess])
    for new_sub_file in new_sub_files:
        file_re = re.match('(sub-[0-9]+)_[a-zA-Z0-9_-]+_(s[0-9]+_r[0-9]+)_e[0-9]+\.zip', file)
        if file_re:
            sub_folder = file_re.group(1)
            sess_folder = file_re.group(2)
            if not 'no-data.txt' in os.listdir(join(dataset,'sourcedata','checked',sub_folder,sess_folder,'eeg')):
                if not isdir(join(dataset,'data-monitoring','ndar',current_submission,'eeg',sub_folder+'_all_eeg_'+sess_folder+'_e1')):
                    _ = os.system('cp -R ' + join(dataset,'sourcedata','checked',sub_folder,sess_folder,'eeg') + ' ' + \
                                join(dataset,'data-monitoring','ndar',current_submission,'eeg',sub_folder+'_all_eeg_'+sess_folder+'_e1'))
    #experiment_id = "2232" # thrive = 2232
    experiment_id = "" # read leave blank
    with open(join(dataset,'data-monitoring','ndar',current_submission,'eeg_sub_files01.csv'), 'w') as o:
        _ = o.write('eeg_sub_files,01,,,,,,,\n')
        _ = o.write('subjectkey,src_subject_id,interview_date,interview_age,sex,experiment_id,data_file1,data_file1_type,timepoint_label\n')
        for new_sub_file in new_sub_files:
            file_re = re.match('sub-([0-9]+)_[a-zA-Z0-9_-]+_(s[0-9]+)_r[0-9]+_e[0-9]+\.zip', new_sub_file)
            if file_re:
                src_subject_id = file_re.group(1)
                timepoint_label = file_re.group(2)
                _ = o.write(','+src_subject_id+',,,,'+experiment_id+','+new_sub_file+',file folder,'+timepoint_label+'\n')
            else:
                print("doesn't match expected format?")
    o.close()
