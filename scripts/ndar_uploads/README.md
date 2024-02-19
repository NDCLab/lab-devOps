# NDAR_Uploads

These scripts should generate a series of output CSV files that can be uploaded (with additional editing) to the NDA archive website https://nda.nih.gov/nda/data-contribution

Required arguments are the dataset's redcaps and a JSON file containing information on mapping the Redcap columns to the output CSVs.

```
python3 gen_NDAR_csvs.py <redcap1,redcap2,redcap3> <data dictionary> <sre string> <output path>
```

Example command:
```
python3 /mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/gen_NDAR_csvs.py /mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/redcaps/Thrivebbschilds1r1_DATA_2023-12-27_1034.csv,/mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/redcaps/Thrivebbsparents1r1_DATA_2023-12-27_1035.csv,/mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/redcaps/ThrivebbsRAs1r1_DATA_2023-12-27_1035.csv,/mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/redcaps/Thriveconsent_DATA_2023-12-27_1035.csv,/mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/redcaps/Thriveiqschilds1r1_DATA_2023-12-27_1035.csv,/mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/redcaps/Thriveiqsclinicians1_DATA_2023-12-27_1034.csv,/mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/redcaps/Thriveiqsparents1r1_DATA_2024-01-05_1506.csv /mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/redcaps/central-tracker_datadict.csv /mnt/c/Users/davhu/OneDrive/Documents/ndar_json.json s1_r1_e1 /mnt/c/Users/davhu/OneDrive/Documents/NDAR_upload_scripts/outputs
```
