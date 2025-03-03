import os

from syllable_match.models import FeatureExtractor
from syllable_match.utils import extract_words_and_syllables

from .constructor import ScaffoldConstructor


def create_scaffolds(
    template_paths: list[str], scaffold_dir: str, extractors: list[FeatureExtractor]
):
    for template_path in template_paths:
        # Extract the passage name from the template path
        passage_name = os.path.splitext(os.path.basename(template_path))[0]

        if template_path.endswith((".csv", ".tsv")):
            words, syllables = extract_words_and_syllables(template_path)
            constructor = ScaffoldConstructor(passage_name, words, syllables)
            constructor.register_extractors(extractors)
            scaffold_df = constructor.build()
            scaffold_df.to_csv(
                os.path.join(scaffold_dir, f"{passage_name}-scaffold.csv"), index=False
            )
