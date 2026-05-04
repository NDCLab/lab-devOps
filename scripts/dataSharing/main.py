import os

from dataSharing import DataSharingProtocol
# get input by asking the user
import regex as re
from types import SimpleNamespace

    


def get_user_instruments():
    print("Please enter the following information:")
    print("Please type in each instrument you want to include")
    print("If you have multiple instruments, please enter them one by one.")
    print("If specific columns are ")
    print("Type 'done' when you are finished.")
    while True:
        instruments = []
        while True:
            instrument = input("Instrument: ")
            #check it it ends in sX_rX_eX
            if instrument.lower() == "done":
                break
            instruments.append(instrument)
        print("Please confirm the instruments you have entered:")
        for instrument in instruments:
            print(f"- {instrument}")
        confirm = input("Is this correct? (yes/no): ")
        if confirm.lower() == "yes":
            break
        else:
            print("Let's try again. Please enter the instruments again.")
    
    return instruments
if __name__ == "__main__":
    print("Welcome to the Data Sharing Protocol!")
    print("To run directly, do not include the --interactive flag.")

    print("What is the name of the dataset to get the data from?")
    dataset_name = input("Dataset name: ")
    if not os.path.exists(f"/home/data/NDClab/datasets/{dataset_name}"):
        print("Dataset not found. Please check the name and try again.")
        exit(1)
    
    print("Would you like to directly input the instruments you want to include, or would you like to use a template?")
    print("1. Direct input")
    print("2. Use template")
    choice = input("Please enter 1 or 2: ")
    direct = False
    if choice == "1":
        instruments = get_user_instruments()
        direct = True
    elif choice == "2":
        print("Please enter the path to the template file:")
        template_path = input("Template path: ")
        # check if the file exists
        try:
            with open(template_path, "r") as f:
                instruments = f.read().splitlines()
        except FileNotFoundError:
            print("File not found. Please check the path and try again.")
            exit(1)
    else:
        print("Invalid choice. Please enter 1 or 2.")
        exit(1)
    print("What is the name of the output xlsx? Please include the .xlsx extension.")
    output_file = input("Output file name: ")
    if not output_file.endswith(".xlsx"):
        print("Invalid file name. Please include the .xlsx extension.")
        exit(1)
    if direct:
        print("You have chosen to directly input the instruments. The following instruments will be included:")
        for instrument in instruments:
            print(f"- {instrument}")
        args = SimpleNamespace(
            name=dataset_name,
            instruments=instruments,
            output=output_file,
            vars=instruments
        )
    else:
        print("You have chosen to use a template. The following instruments will be included:")
        for instrument in instruments:
            print(f"- {instrument}")
        args = SimpleNamespace(
            name=dataset_name,
            instruments=instruments,
            output=output_file,
            input=template_path
        )
        datasharing = DataSharingProtocol(args)
        datasharing.run()

