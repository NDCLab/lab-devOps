import datetime
import os

LAB_DIR = os.path.join("/home", "data", "NDClab")
DATASET_DIR = os.path.join(LAB_DIR, "datasets")
BACKUP_DIR = os.path.join(LAB_DIR, "other", "backups")

DATE_STR = datetime.datetime.now().strftime("%m-%d-%Y")
BACKUP_LIST = {"sourcedata", "derivatives"}
SKIPPED_DATASETS = {"bug-testing-dataset"}


def main():
    print("Beginning backup...")
    print(f"Start time {datetime.datetime.now().isoformat()}")
    for dataset in os.listdir(DATASET_DIR):
        if dataset in SKIPPED_DATASETS:
            print(f"Skipping {dataset}")
            continue
        print(f"Backing up {dataset}")
        backup_dataset(dataset)

    print("Finished backup!")
    print(f"End time {datetime.datetime.now().isoformat()}")


def backup_dataset(dataset: str):
    dataset_backup = os.path.join(BACKUP_DIR, dataset)
    # ensure that our backup directory exists
    if not os.path.isdir(dataset_backup):
        os.makedirs(dataset_backup, exist_ok=True)

    for backup_subdir in BACKUP_LIST:
        source_dir = os.path.join(DATASET_DIR, dataset, backup_subdir)
        target_dir = os.path.join(dataset_backup, backup_subdir)

        if not os.path.isdir(source_dir):
            continue  # can't back up something that isn't there!

        # collect all files under the source dir
        # NB: we do this *once* to minimize costly file system API calls
        source_tree = {}
        for root, _, files in os.walk(source_dir):
            rel_path = os.path.relpath(root, source_dir)
            source_tree[rel_path] = files

        # mirror the dataset's directory structure to our backup path
        for rel_path in source_tree:
            backup_subdir_path = os.path.join(target_dir, rel_path)
            if not os.path.isdir(backup_subdir_path):
                os.makedirs(backup_subdir_path, exist_ok=True)

        for rel_path, files in source_tree.items():
            # current folder in the backup
            backup_subdir_path = os.path.join(target_dir, rel_path)

            try:
                existing_backup_items = os.listdir(backup_subdir_path)
            except FileNotFoundError:
                # if the folder somehow doesn't exist, create it and move on
                os.makedirs(backup_subdir_path, exist_ok=True)
                existing_backup_items = []

            # build a quick set of 'basenames' that already have a hard link
            # e.g. if "mydata-link-01-01-2025" exists, store "mydata" as linked
            already_linked_basenames = set()
            for item in existing_backup_items:
                if "-link-" in item:
                    # everything up to "-link-" is the original file's basename
                    base_before_link = item.split("-link-")[0]
                    already_linked_basenames.add(base_before_link)

            # for each file in this source directory, create a link if needed
            for filename in files:
                if filename in already_linked_basenames:
                    continue  # hard link already exists

                src_file = os.path.join(source_dir, rel_path, filename)
                link_name = f"{filename}-link-{DATE_STR}"
                backup_file_path = os.path.join(backup_subdir_path, link_name)

                print(f"Creating link {backup_file_path}")

                try:  # hard link creation
                    os.link(src_file, backup_file_path)
                except FileExistsError:
                    pass  # if link already exists, do nothing
                except OSError as err:
                    # could be permission issues, etc.
                    print(f"Could not create link for {src_file}. Error: {err}")


if __name__ == "__main__":
    main()
