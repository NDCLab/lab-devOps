# NDAR_Uploads

These scripts should generate a series of output CSV files that can be uploaded (with additional editing) to the NDA archive website https://nda.nih.gov/nda/data-contribution

Required arguments are the dataset's redcaps and a JSON file containing information on mapping the Redcap columns to the output CSVs.

```
python3 gen_NDAR_csvs.py <redcap1,redcap2,redcap3> <data dictionary> <JSON file> <sre string> <output path> [any redcaps from a prior session needed or "None"]
```

Example command:
```
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thrivebbschilds1r1_DATA_2024-07-12_1158.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thrivebbsparents1r1_DATA_2024-07-12_1200.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/ThrivebbsRAs1r1_DATA_2024-07-12_1159.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveconsent_DATA_2024-07-12_1200.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveiqschilds1r1_DATA_2024-07-12_1200.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveiqsclinicians1_DATA_2024-07-12_1158.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveiqsparents1r1_DATA_2024-07-12_1200.csv /home/data/NDClab/datasets/thrive-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/thrive_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/s1_r1
```
^ thrive s1

```
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thrivebbschilds2r1_DATA_2024-07-12_1203.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thrivebbsparents2r1_DATA_2024-07-12_1203.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/ThrivebbsRAs2r1_DATA_2024-07-12_1203.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveconsent_DATA_2024-07-12_1200.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveiqschilds2r1_DATA_2024-07-12_1203.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveiqsclinicians2_DATA_2024-07-12_1203.csv,/home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveiqsparents2r1_DATA_2024-07-12_1203.csv /home/data/NDClab/datasets/thrive-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/thrive_s2_r1.json s2_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/s2_r1 /home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveiqsparents1r1_DATA_2024-07-12_1200.csv
```
^ thrive s2

```
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/read-study1-dataset/sourcedata/checked/redcap/Readbbschilds1r1_DATA_2024-01-30_1711.csv,/home/data/NDClab/datasets/read-study1-dataset/sourcedata/checked/redcap/Readbbsparents1r1_DATA_2024-01-30_1120.csv,/home/data/NDClab/datasets/read-study1-dataset/sourcedata/checked/redcap/ReadbbsRAs1r1_DATA_2024-01-30_1121.csv,/home/data/NDClab/datasets/read-study1-dataset/sourcedata/checked/redcap/Readconsent_DATA_2024-02-06_1259.csv,/home/data/NDClab/datasets/read-study1-dataset/sourcedata/checked/redcap/Readinterviewss1r1_DATA_2024-02-06_1259.csv,/home/data/NDClab/datasets/read-study1-dataset/sourcedata/checked/redcap/Readiqsclinicians1r1_DATA_2024-01-30_1121.csv /home/data/NDClab/datasets/read-study1-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study1-dataset/read-study1_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study1-dataset/s1_r1
```
^ read study1

```
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/read-study2-dataset/sourcedata/checked/redcap/Read2bbschilds1r1_DATA_2024-07-02_1630.csv,/home/data/NDClab/datasets/read-study2-dataset/sourcedata/checked/redcap/Read2bbsparents1r1_DATA_2024-07-02_1630.csv,/home/data/NDClab/datasets/read-study2-dataset/sourcedata/checked/redcap/Read2bbsRAs1r1_DATA_2024-07-02_1629.csv,/home/data/NDClab/datasets/read-study2-dataset/sourcedata/checked/redcap/Read2consent_DATA_2024-07-02_1629.csv,/home/data/NDClab/datasets/read-study2-dataset/sourcedata/checked/redcap/Read2iqsclinicians1r_DATA_2024-07-02_1629.csv /home/data/NDClab/datasets/read-study2-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study2-dataset/read-study2_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study2-dataset/s1_r1
```
^ read study2
