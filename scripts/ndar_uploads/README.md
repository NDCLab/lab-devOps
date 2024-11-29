# NDAR_Uploads

These scripts should generate a series of output CSV files that can be uploaded (with additional editing) to the NDA archive website https://nda.nih.gov/nda/data-contribution

Required arguments are the dataset's redcaps and a JSON file containing information on mapping the Redcap columns to the output CSVs.

```
python3 gen_NDAR_csvs.py <redcap1,redcap2,redcap3> <data dictionary> <JSON file> <sre string> <output path> [any redcaps from a prior session needed or "None"]
```

Example command:
```
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/thrive-dataset/ /home/data/NDClab/datasets/thrive-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/thrive_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/s1_r1
```
^ thrive s1

```
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/thrive-dataset/ /home/data/NDClab/datasets/thrive-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/thrive_s2_r1.json s2_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/s2_r1 /home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/Thriveiqsparents1r1_DATA_2024-07-12_1200.csv
```
^ thrive s2

```
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/read-study1-dataset/ /home/data/NDClab/datasets/read-study1-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study1-dataset/read-study1_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study1-dataset/s1_r1
```
^ read study1

```
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/read-study2-dataset/ /home/data/NDClab/datasets/read-study2-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study2-dataset/read-study2_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study2-dataset/s1_r1
```
^ read study2
