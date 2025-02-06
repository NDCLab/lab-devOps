import csv
import os
import re
import string
import sys
from abc import ABC, abstractmethod

import pandas as pd


class FeatureExtractor(ABC):
    @property
    @abstractmethod
    def feature_name(self) -> str:
        pass

    @abstractmethod
    def extract(self, syllable_dict: dict[str, list[str]]) -> list:
        pass


class ScaffoldConstructor:
    def __init__(self, passage_name: str, words: list[str], syllables: list[str]):
        self.passage_name = passage_name

        self._words = words
        self._syllables = syllables
        self._extractors: list[FeatureExtractor] = []

    def register_extractor(self, extractor: FeatureExtractor):
        self._extractors.append(extractor)

    def register_extractors(self, extractors: list[FeatureExtractor]):
        self._extractors.extend(extractors)

    def build(self) -> pd.DataFrame:
        syllable_dict = self.build_syllable_dict()

        # Create a list of all syllables and their corresponding words
        syllables = []
        words = []
        word_ids = []
        syllable_ids = []
        word_index = 1
        syllable_index = 1
        for word, syllable_list in syllable_dict.items():
            for syllable in syllable_list:
                syllables.append(syllable)
                words.append(word)
                word_ids.append(f"{self.passage_name}_word{word_index}")
                syllable_ids.append(f"{self.passage_name}_syll{syllable_index}")
                syllable_index += 1
            word_index += 1

        # Extract features
        features = {
            extractor.feature_name: extractor.extract(syllable_dict)
            for extractor in self._extractors
        }

        features["syllables"] = syllables
        features["words"] = words
        features["word_id"] = word_ids
        features["syllable_id"] = syllable_ids

        return pd.DataFrame(features)

    def build_syllable_dict(self) -> dict[str, list[str]]:
        syllable_dict = {}
        syllable_queue = self._syllables.copy()

        for word in self._words:
            syllable_dict[word] = []
            current_length = 0
            word_no_hyphen = word.replace("-", "")
            word_length = len(word_no_hyphen)

            while syllable_queue and current_length < word_length:
                syllable = syllable_queue.pop(0)
                # Check if the syllable matches the start of the remaining word
                if word_no_hyphen.startswith(syllable, current_length):
                    syllable_dict[word].append(syllable)
                    current_length += len(syllable)

        return syllable_dict


class SyllableCountExtractor(FeatureExtractor):
    feature_name = "totalWordSyllables"

    def extract(self, syllable_dict: dict[str, list[str]]) -> list[int]:
        syllable_counts = []
        for syllables in syllable_dict.values():
            count = len(syllables)
            syllable_counts.extend([count] * count)
        return syllable_counts


class StartSyllableExtractor(FeatureExtractor):
    feature_name = "syllableAtWordOnset"

    def extract(self, syllable_dict: dict[str, list[str]]) -> list[int]:
        starts = []
        for syllables in syllable_dict.values():
            for syllable in syllables:
                is_start = int(syllable == syllables[0])
                starts.append(is_start)
        return starts


class EndSyllableExtractor(FeatureExtractor):
    feature_name = "syllableAtWordEnd"

    def extract(self, syllable_dict: dict[str, list[str]]) -> list[int]:
        ends = []
        for syllables in syllable_dict.values():
            for syllable in syllables:
                is_end = int(syllable == syllables[-1])
                ends.append(is_end)
        return ends


class PunctuationStartExtractor(FeatureExtractor):
    feature_name = "syllableAtSentenceOnset"

    def extract(self, syllable_dict: dict[str, list[str]]) -> list[int]:
        starts = []
        # Assume start of text is a sentence start
        previous_ends_with_punctuation = True

        for syllables in syllable_dict.values():
            for syllable in syllables:
                if previous_ends_with_punctuation:
                    starts.append(1)
                else:
                    starts.append(0)
                previous_ends_with_punctuation = any(
                    syllable[-1] in {".", "!", "?"} for syllable in syllables
                )

        return starts


class PunctuationEndExtractor(FeatureExtractor):
    feature_name = "syllableAtSentenceEnd"

    def extract(self, syllable_dict: dict[str, list[str]]) -> list[int]:
        ends = []
        for syllables in syllable_dict.values():
            for syllable in syllables:
                if syllable == syllables[-1] and syllable[-1] in {".", "!", "?"}:
                    ends.append(1)
                else:
                    ends.append(0)
        return ends


class WordFrequencyExtractor(FeatureExtractor):
    feature_name = "wordFrequency"

    def __init__(self, frequency_file: str):
        self.word_frequencies = self.load_frequencies(frequency_file)

    def load_frequencies(self, frequency_file: str) -> dict[str, int]:
        frequencies = {}
        with open(frequency_file, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            for row in reader:
                word = row["Word"].lower().strip(string.punctuation)
                freq_count = int(row["FREQcount"])
                frequencies[word] = freq_count
        return frequencies

    def extract(self, syllable_dict: dict[str, list[str]]) -> list[int]:
        frequencies = []
        for word, syllables in syllable_dict.items():
            word_lower = word.lower().strip(string.punctuation)
            frequency = self.word_frequencies.get(word_lower, 0)
            frequencies.extend([frequency] * len(syllables))
        return frequencies


class SyllablePositionExtractor(FeatureExtractor):
    feature_name = "syllablePosition"

    def extract(self, syllable_dict: dict[str, list[str]]) -> list[int]:
        positions = []
        for syllables in syllable_dict.values():
            positions.extend(range(1, len(syllables) + 1))
        return positions


def extract_words_and_syllables(
    file_path: str, sep: str = "\t"
) -> tuple[list[str], list[str]]:
    words = []
    syllables = []

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=sep)

        # Read the first row for "TARGET TEXT"
        first_row = next(reader, [])
        if "TARGET TEXT" in first_row:
            target_text_index = first_row.index("TARGET TEXT")
            words = [
                cell.strip()
                for cell in first_row[target_text_index + 1 :]
                if cell.strip()
            ]

        # Read the second row for "TARGET SYLLABLES"
        second_row = next(reader, [])
        if "TARGET SYLLABLES" in second_row:
            target_syllables_index = second_row.index("TARGET SYLLABLES")
            syllables = [
                cell.strip()
                for cell in second_row[target_syllables_index + 1 :]
                if cell.strip()
            ]

    return words, syllables


def main(data_dir: str):
    extractors = [
        StartSyllableExtractor(),
        EndSyllableExtractor(),
        SyllableCountExtractor(),
        PunctuationStartExtractor(),
        PunctuationEndExtractor(),
        WordFrequencyExtractor("SUBTLEXus74286wordstextversion.txt"),
        SyllablePositionExtractor(),
    ]

    out_dir = os.path.join(data_dir, "scaffolds")
    os.makedirs(out_dir, exist_ok=True)

    # first pass, convert .xlsx files to .tsv
    for basename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, basename)
        passage_name = os.path.splitext(basename)[0]

        if basename.endswith(".xlsx") and not any(
            other.startswith(passage_name)
            and os.path.splitext(other)[1] in {".tsv", ".csv"}
            for other in os.listdir(data_dir)
        ):  # construct new TSV
            df_xlsx = pd.read_excel(filepath)

            # Replace all fields containing line breaks with space
            df = df_xlsx.replace("\n", " ", regex=True)
            df_str = df.to_csv(index=False, sep="\t", encoding="utf-8")
            # Quirks introduced by trying to read non-relational data into Pandas
            df_str = re.sub(r"Unnamed:\s\d+", "\t", df_str)
            df_str = re.sub(r"(\w+)\.\d+", r"\1", df_str)

            basename = os.path.splitext(basename)[0] + ".tsv"
            filepath = os.path.join(data_dir, basename)
            with open(filepath, "w+") as f:
                f.write(df_str)

    # second pass, build the scaffolds
    for basename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, basename)

        if os.path.isdir(filepath):
            continue

        ext = os.path.splitext(basename)[1]
        if ext == ".tsv":
            sep = "\t"
        elif ext == ".csv":
            sep = ","
        elif ext == ".xlsx":
            continue
        else:
            print(f"Skipping {filepath}, unknown extension {ext}")
            continue

        passage_name = os.path.splitext(basename)[0]
        sep = "\t" if basename.endswith(".tsv") else ","
        words, syllables = extract_words_and_syllables(filepath, sep=sep)

        constructor = ScaffoldConstructor(passage_name, words, syllables)
        constructor.register_extractors(extractors)

        df = constructor.build()
        df.to_csv(os.path.join(out_dir, f"{passage_name}-scaffold.csv"), index=False)


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print("Must pass the directory containing data files")
        exit(1)

    main(args[1])
