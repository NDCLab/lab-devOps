import os
import tempfile

from tqdm import tqdm

from syllable_match.models import FeatureExtractor
from syllable_match.utils import extract_words_and_syllables

from .constructor import ScaffoldConstructor
from .utils import convert_xlsx_to_csv_string


def create_scaffolds(
    template_paths: list[str], scaffold_dir: str, extractors: list[FeatureExtractor]
):
    for template_path in tqdm(template_paths):
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
            scaffold_df.to_csv(
                os.path.join(scaffold_dir, f"{passage_name}-scaffold.csv"), index=False
            )
