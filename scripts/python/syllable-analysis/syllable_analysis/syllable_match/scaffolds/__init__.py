import os
import tempfile
import pandas as pd
from ..models import FeatureExtractor
from .constructor import ScaffoldConstructor
from .utils import convert_xlsx_to_csv_string, extract_words_and_syllables

def get_carriage_returns(file_path,total_length):
    # check if result matches with syllables_list
    # 1. Get the integer index position of the matching row
    df = pd.read_excel(file_path, header=None)
    row_pos = df.index.get_loc(
        df[df.iloc[:, 1].str.contains("Carriage Return", na=False)].index[0]
    )
    if row_pos is None:
        raise ValueError("No row containing 'Carriage Return' found in the second column.")

    # 2. Get columns after the 2nd column (index 2 onwards) for that row
    result = df.iloc[row_pos, 2:total_length+2]
    

    # make sure they're all integers
    result = result.astype(int)
    before_carriage_list = result.tolist()
    after_carriage_list = result.shift(1, fill_value=0).tolist()

    return before_carriage_list, after_carriage_list



def create_scaffolds(
    template_paths: list[str], scaffold_dir: str, extractors: list[FeatureExtractor]
):
    print(f"Creating scaffolds in {scaffold_dir}...")
    for template_path in template_paths:
        # Extract the passage name from the template path
        passage_name = os.path.splitext(os.path.basename(template_path))[0]

        if template_path.endswith(".xlsx"):
            # Convert the Excel file to a CSV string with tabs as separators
            tsv_string = convert_xlsx_to_csv_string(template_path, sep="\t")
            # Create a temporary file to write the CSV string to
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
                # Write the CSV string to the temporary file, then go back to the beginning of the file
                temp_file.write(tsv_string)
                temp_file.seek(0)
                words, syllables = extract_words_and_syllables(temp_file.name)

            constructor = ScaffoldConstructor(passage_name, words, syllables)
            constructor.register_extractors(extractors)
            # Build and save the scaffold DataFrame
            scaffold_df = constructor.build()

            total_length = len(scaffold_df["syllable_id"])
            before_carriage, after_carriage = get_carriage_returns(template_path, total_length)
            scaffold_df["word-before-carriage"] = before_carriage
            scaffold_df["word-after-carriage"] = after_carriage
            scaffold_df["word-before-carriage"] = scaffold_df.groupby("word_id")["word-before-carriage"].transform("max")
            scaffold_df["word-after-carriage"] = scaffold_df.groupby("word_id")["word-after-carriage"].transform("max")
            print(f"Written carriage return information for {passage_name} to {scaffold_dir}")
            # check if columns are present in the dataframe
            if "word-before-carriage" not in scaffold_df.columns or "word-after-carriage" not in scaffold_df.columns:
                raise ValueError("Required columns are missing from the DataFrame.")
            scaffold_df.to_csv(
                os.path.join(scaffold_dir, f"{passage_name}-scaffold.csv"), index=False
            )
