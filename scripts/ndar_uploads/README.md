# NDAR_Uploads

These scripts should generate a series of output CSV files that can be uploaded (with additional editing) to the NDA archive website https://nda.nih.gov/nda/data-contribution

## Steps
1. Use `gen_NDAR_csvs.py` to generate NDAR CSV files for each session of your dataset, using the appropriate REDCap data and mapping configuration.
2. After generating the CSV files for all sessions, use `copy_zip_eeg_parallel2.sub` to copy and zip the EEG and create the template csv files for the EEG upload to NDAR. (**Note: new_ndar_submission.py is the base file but copy_zip_eeg_parallel2.sub utilizes the HPC for parallel processing and is more efficient for large datasets)**.
3. Finally, use `concat_csvs.py` to copy key columns from the session-specific CSV files generated in step 1 and combine into the eeg csv files created in step 2, which can then be uploaded to NDAR.

## Gen_NDAR_csvs.py  Overview
Required arguments are the dataset's redcap directory and a JSON file containing information on mapping the Redcap columns to the output CSVs.
Gen_NDAR_csvs.py creates output csv files for uploading to NDAR based on the provided REDCap data and mapping configuration. The script takes the following command line arguments:
```
python3 gen_NDAR_csvs.py <path/to/redcap/dir> <data dictionary> <JSON file> <sre string> <output path>
```




### Command Line Arguments

1. **`redcap_dir`** 
   - Path to the top-level directory containing your REDCap data
   - Should contain `sourcedata/checked/redcap/` subdirectory

2. **`data_dict`** 
   - Path to your data dictionary CSV file
   - Example: `central-tracker_datadict.csv`

3. **`ndar_json`** 
   - Path to your NDAR mapping configuration JSON file
   - Example: `ndar_mapping.json`

4. **`session`**
   - Session identifier in format: `s[X]_r[Y]_e[Z]`
   - Example: `s1_r1_e1` (session 1, run 1, event 1)

5. **`output_path`**
   - Directory where generated CSV files will be saved
   - Will be created if it doesn't exist


## Copy_Zip_EEG_Parallel2.sub (new_ndar_submission.py) Overview
copy_zip_eeg_parallel2.sub is a SLURM job script that automates the copying and zipping of EEG data for NDAR uploads. It processes multiple sessions in parallel on an HPC cluster, creating zipped EEG files and corresponding template CSVs for each session.

It uses new_ndar_submission.py as the base script for copying and zipping EEG data, but is optimized for parallel processing on an HPC cluster using SLURM.
The script takes the following command line arguments:
```
sbatch copy_zip_eeg_parallel2.sub <dataset> <current_submission>
```
### Command Line Arguments
1. **`dataset`** 
   - Name of the dataset being processed
   - Example: `thrive-dataset`
2. **`current_submission`**
   - Identifier for the current NDAR submission (e.g., `jan-2026-submission`)



## concat_csvs.py  Overview

concat_csvs.py combines identically-named NDAR CSV files from multiple session folders into single, combined CSVs for NIH/NDAR uploads. It is designed to merge files with names like [instrument]_sX_rX_eX_incomplete.csv across several folders, producing a single [instrument]_combined_incomplete.csv for each unique instrument.
```
python3 concat_csvs.py <folder1,folder2,folder3,...> <output_folder>
```

**PLEASE NOTE: Only run  concat_csvs.py after you have generated all the necessary CSV files for each session using gen_NDAR_csvs.py. This ensures that all relevant data is included in the final combined CSVs for upload to NDAR.**


### Command Line Arguments

- `<folder1,folder2,folder3,...>`: Comma-separated list of input folders containing the session CSVs to combine.
- `<output_folder>`: Directory where the combined CSVs will be writte, looks for csv that ends with "_incomplete.csv"


## Example Commands
### EEG CSV Generation
```bash
sbatch copy_zip_eeg_parallel2.sub thrive-dataset jan-2026-submission
``` 
### Concatenating CSVs
```bash
python3 concat_csvs.py thrive/dataset/s1_r1_e1,s2_r1_e1,s3_r1_e1 ../eeg/ndar/
```

### Thrive Dataset
Example command:
```bash
# Thrive S1
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/ /home/data/NDClab/datasets/thrive-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/thrive_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/s1_r1
```

```bash
# Thrive S2
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/ /home/data/NDClab/datasets/thrive-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/thrive_s2_r1.json s2_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/s2_r1 
```

```bash
# Thrive S3
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/thrive-dataset/sourcedata/checked/redcap/ /home/data/NDClab/datasets/thrive-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/thrive_s3_r1.json s3_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/thrive-dataset/s3_r1 
```
### Read-Study Example Commands
```bash
# Read S1
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/read-study1-dataset/sourcedata/checked/redcap/ /home/data/NDClab/datasets/read-study1-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study1-dataset/read-study1_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study1-dataset/s1_r1
```

```bash
# Read S2
python3 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/gen_NDAR_csvs.py /home/data/NDClab/datasets/read-study2-dataset/sourcedata/checked/redcap/ /home/data/NDClab/datasets/read-study2-dataset/data-monitoring/data-dictionary/central-tracker_datadict.csv /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study2-dataset/read-study2_s1_r1.json s1_r1_e1 /home/data/NDClab/tools/lab-devOps/scripts/ndar_uploads/read-study2-dataset/s1_r1
```
