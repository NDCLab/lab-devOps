import csv
import os
import re
import string
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass
class Word:
    text: str
    clean_text: str


@dataclass
class Syllable:
    text: str
    clean_text: str
    has_punctuation: bool
    ends_sentence: bool


@dataclass
class SyllableEntry:
    word: Word
    syllables: list[Syllable]


class FeatureExtractor(ABC):
    @property
    @abstractmethod
    def feature_name(self) -> str:
        pass

    @abstractmethod
    def extract(self, syllable_directory: list[SyllableEntry]) -> list:
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
        syllable_directory = self.build_syllable_directory()

        # Create a list of all syllables and their corresponding words
        syllables = []
        cleaned_syllables = []
        words = []
        cleaned_words = []
        word_ids = []
        syllable_ids = []
        word_index = 1
        syllable_index = 1
        for entry in syllable_directory:
            for syllable in entry.syllables:
                syllables.append(syllable.text)
                cleaned_syllables.append(syllable.clean_text)
                words.append(entry.word.text)
                cleaned_words.append(entry.word.clean_text)
                # Indices (useful for unique identification)
                word_ids.append(f"{self.passage_name}_word{word_index}")
                syllable_ids.append(f"{self.passage_name}_syll{syllable_index}")
                syllable_index += 1
            word_index += 1

        # Extract features
        features = {
            extractor.feature_name: extractor.extract(syllable_directory)
            for extractor in self._extractors
        }

        # for feature, items in features.items():
        #     print(feature, len(items))

        features["syllable"] = syllables
        features["cleaned_syllable"] = cleaned_syllables
        features["word"] = words
        features["cleaned_word"] = cleaned_words
        features["word_id"] = word_ids
        features["syllable_id"] = syllable_ids

        return pd.DataFrame(features)

    def build_syllable_directory(self) -> list[SyllableEntry]:
        syllable_directory = []
        syllable_queue = self._syllables.copy()

        for word in self._words:
            current_length = 0
            cleaned_word = word.replace("-", "").lower().strip(string.punctuation)
            word_length = len(cleaned_word)

            syllable_list = []
            while syllable_queue and current_length < word_length:
                current_syllable = syllable_queue.pop(0).lower()
                cleaned_syll = current_syllable.strip(string.punctuation)
                # Check if the syllable matches the start of the remaining word
                if cleaned_word.startswith(cleaned_syll, current_length):
                    syllable_list.append(
                        Syllable(
                            current_syllable,
                            cleaned_syll,
                            current_syllable[-1] in string.punctuation,
                            current_syllable[-1] in {".", "!", "?"},
                        )
                    )
                    current_length += len(current_syllable)

            if not syllable_list:
                raise Exception(self.passage_name, word, syllable_directory)

            syllable_directory.append(
                SyllableEntry(Word(word, cleaned_word), syllable_list)
            )

        return syllable_directory


class SyllableCountExtractor(FeatureExtractor):
    feature_name = "totalWordSyllables"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        syllable_counts = []
        for entry in syllable_directory:
            count = len(entry.syllables)
            syllable_counts.extend([count] * count)
        return syllable_counts


class StartSyllableExtractor(FeatureExtractor):
    feature_name = "syllableAtWordOnset"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        syll_is_onset = []
        for entry in syllable_directory:
            count = len(entry.syllables)
            syll_is_onset += [1] + [0] * (count - 1)
        return syll_is_onset


class EndSyllableExtractor(FeatureExtractor):
    feature_name = "syllableAtWordEnd"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        syll_is_last = []
        for entry in syllable_directory:
            count = len(entry.syllables)
            syll_is_last += [0] * (count - 1) + [1]
        return syll_is_last


class PunctuationStartExtractor(FeatureExtractor):
    feature_name = "syllableAtSentenceOnset"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        syll_at_sent_start = []
        # Assume start of text is a sentence start
        prev_ends_sentence = True

        for entry in syllable_directory:
            count = len(entry.syllables)
            syll_at_sent_start += [int(prev_ends_sentence)] + [0] * (count - 1)

            prev_ends_sentence = entry.syllables[-1].ends_sentence

        return syll_at_sent_start


class PunctuationEndExtractor(FeatureExtractor):
    feature_name = "syllableAtSentenceEnd"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        syll_at_sent_end = []

        for entry in syllable_directory:
            count = len(entry.syllables)
            last_syll = entry.syllables[-1]
            syll_at_sent_end += [0] * (count - 1) + [int(last_syll.ends_sentence)]

        return syll_at_sent_end


class WordStartsSentenceExtractor(FeatureExtractor):
    feature_name = "wordAtSentenceOnset"

    def extract(self, syllable_directory):
        word_at_sent_start = []
        # Assume start of text is a sentence start
        prev_ends_sentence = True

        for entry in syllable_directory:
            count = len(entry.syllables)
            word_at_sent_start += [int(prev_ends_sentence)] * count

            prev_ends_sentence = entry.syllables[-1].ends_sentence

        return word_at_sent_start


class WordEndsSentenceExtractor(FeatureExtractor):
    feature_name = "wordAtSentenceEnd"

    def extract(self, syllable_directory):
        word_at_sent_end = []

        for entry in syllable_directory:
            count = len(entry.syllables)
            word_at_sent_end += [int(entry.syllables[-1].ends_sentence)] * count

        return word_at_sent_end


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

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        frequencies = []
        for entry in syllable_directory:
            frequency = self.word_frequencies.get(entry.word.clean_text, 0)
            frequencies.extend([frequency] * len(entry.syllables))
        return frequencies


class SyllablePositionExtractor(FeatureExtractor):
    feature_name = "syllablePosition"

    def extract(self, syllable_directory: list[SyllableEntry]) -> list[int]:
        positions = []
        for entry in syllable_directory:
            positions += range(1, len(entry.syllables) + 1)
        return positions


def extract_words_and_syllables(
    file_path: str, sep: str = "\t"
) -> tuple[list[str], list[str]]:
    words = []
    syllables = []

    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=sep)

        # Read the first row for "target text"
        first_row = next(reader, [])
        if "target text" in first_row:
            target_text_index = first_row.index("target text")
            words = [
                cell.strip()
                for cell in first_row[target_text_index + 1 :]
                if cell.strip()
            ]

        # Read the second row for "target syllables"
        second_row = next(reader, [])
        if "target syllables" in second_row:
            target_syllables_index = second_row.index("target syllables")
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
        WordStartsSentenceExtractor(),
        WordEndsSentenceExtractor(),
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
            df_str = re.sub(r"(.+?)\.\d+", r"\1", df_str)
            # Standardize text data to lower-case (syllables and words do not
            # always match capitalization in practice)
            df_str = df_str.lower()

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
