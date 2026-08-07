# syllable_analysis

`syllable_analysis` is a Python package for processing READ-style speech coding data at the syllable level. It takes raw participant Excel files and passage templates, builds passage scaffolds, aligns coded syllables to scaffold features, labels disfluencies and errors, writes processed CSV outputs, computes summary statistics, creates timestamping sheets, and performs a separate recall-analysis pass.

The package is designed to be run as a command-line program through the module entrypoint in `syllable_analysis/__main__.py`.

## What this folder contains

This package is the full processing pipeline. The main responsibilities are split across a few modules:

- `__main__.py` defines the CLI and the overall execution order.
- `scaffolds.py` builds passage scaffolds from template spreadsheets and produces scaffold word-match summaries.
- `syllable_match/` parses raw coded Excel files, creates derived fields, labels deviations, matches hesitation/error/duplication spans, and writes processed passage CSVs.
- `error_analysis/` performs recall-period analysis and writes recall summary CSV files.
- `timestamping.py` creates timestamping sheets from the processed syllable-level CSVs.
- `utils.py` contains directory discovery helpers, file-name parsing, template discovery, and a few shared utilities.

## End-to-end pipeline

When you run the package in normal mode, the processing order is:

1. Build scaffolds from the coding template directory.
2. Process each accepted participant and each reconciled passage file.
3. Label and match hesitations, errors, and duplications on a syllable-by-syllable basis.
4. Write detailed processed CSVs for each passage.
5. Compute passage-level and overall summary statistics.
6. Analyze recall-period data and write recall-analysis CSV outputs.
7. Generate timestamping sheets for the processed passages.

That order is implemented directly in `syllable_analysis/__main__.py`.

## Command-line interface

The package is intended to be run with:

```bash
python -m syllable_analysis INPUT_DIR CODING_TEMPLATE_DIR OUTPUT_DIR
```

### Required arguments

- `input_dir`: Directory containing participant folders.
- `coding_template_dir`: Directory containing blank template spreadsheets used to build scaffolds.
- `output_dir`: Parent directory where timestamped run folders will be created.

### Optional flags

- `-t`, `--timestamp-only`: Skip the main processing pipeline and generate timestamp sheets using the most recent run in `output_dir`.
- `-o`, `--old-matching`: Use the older syllable matching implementation instead of the alternate matching logic.
- `--accepted_subjects SUBJ1 SUBJ2 ...`: Limit processing to the listed participant IDs in `sub-###` format.

## Input layout

The code expects participant folders inside `input_dir` whose names start with `sub-`.

Inside each participant folder, `syllable_analysis/utils.py` looks for a subdirectory ending in `_reconciled` and then loads the `.xlsx` files inside it as passage files.

The passage file name is parsed by `extract_passage_name()`, which expects a name that matches this general pattern:

```text
sub-<digits>_<passage_name>...reconciled....xlsx
```

If a passage file does not match that naming pattern, the processing step raises an error.

## Output layout

Each normal run creates a timestamped subdirectory under `output_dir`, for example:

```text
OUTPUT_DIR/
  20260717_1430-data/
    scaffolds/
    processed_passages/
    recall_analysis/
    timestamp/
    master-statistics.csv
```

The exact timestamp format is `YYYYMMDD_HHMM-data`.

### Scaffold outputs

`scaffolds.py` builds one scaffold CSV per template passage and also writes a word-match summary file named `word_matching_statistics.txt` into the scaffold output directory.

The scaffold directory is created at:

```text
OUTPUT_DIR/<run>/scaffolds/
```

### Processed passage outputs

`syllable_match/__init__.py` writes processed results under:

```text
OUTPUT_DIR/<run>/processed_passages/<participant_id>/
```

For each passage, the code writes:

- `<passage_name>_all-cols.csv`: the full syllable-level dataframe, including scaffold columns, raw coded fields, derived indicators, and match metadata.
- `<passage_name>.csv`: a reduced CSV containing only the fields listed in `syllable_match/fields.py`.
- `<participant_id>-passage-counts.csv`: participant-level summary statistics produced by `error_analysis/__init__.py`.

### Summary statistics

The summary stage writes:

- `master-statistics.csv` in the run root.

This file contains per-passage means plus overall mean and standard deviation rows.

### Recall analysis outputs

The recall-analysis stage writes CSV files into:

```text
OUTPUT_DIR/<run>/recall_analysis/
```

These are timestamped CSV exports for recall period 1 and recall period 2 analysis.

### Timestamping outputs

The timestamping stage writes per-participant timestamp sheets under:

```text
OUTPUT_DIR/<run>/timestamp/<participant_id>/
```

These sheets are generated from the `processed_passages/*_all-cols.csv` files.

## What scaffolds are

Scaffolds are the template-based passage baselines built from the template spreadsheets in `coding_template_dir`.

`scaffolds.py` uses a fixed set of feature extractors to derive scaffold features such as:

- beginning and end of passage markers
- word-boundary markers for syllables
- punctuation context before and after words
- word frequency
- part-of-speech

The scaffolds are written before participant passages are processed so the later matching logic can align raw coded syllables with the appropriate passage structure.

The scaffold build step also summarizes word-match performance by reporting how many scaffold words are direct matches, lemmatized matches, stemmed matches, or unmatched.

## How raw passage files are parsed

The raw Excel passage files are handled by `syllable_match/parsing/__init__.py`.

The parser:

1. Reads the Excel file.
2. Renames the first two columns to `Category` and `Item`.
3. Extracts rows corresponding to error, disfluency, outcome, and correction categories.
4. Converts coded values into numeric per-syllable feature columns.
5. Reconstructs the passage text and target syllable list.
6. Aligns syllables to words and assigns sequential `WordID` and `SyllableID` values.
7. Derives higher-level indicator columns used later by the labeling and matching logic.

### Main derived fields

The parser and preprocessing step produce many of the columns consumed by later stages, including:

- `any-error`
- `any-disfluency`
- `any-deviation`
- `correction-syll`
- `hesitation-disfluency`
- `duplication`
- `duplication-word`
- `duplication-phrase`
- before/after window indicators for each of the above

These are built in `preprocess_fields()` by taking logical unions across the relevant raw error/disfluency columns and by computing a rolling window indicator around each syllable.

## Matching and labeling

The participant processing stage in `syllable_match/__init__.py` combines the scaffold with the parsed passage data and then applies three labeling/matching passes:

1. Hesitations
2. Errors
3. Duplications

Each pass has a labeling step and a matching step.

The labeling step marks the relevant start/end/match fields in the dataframe. The matching step attempts to pair the current participant syllable span against a corresponding scaffold or comparison span.

The CLI flag `--old-matching` switches between the older matching implementation and the alternate matching implementation provided by the package.

The exact matching logic lives under `syllable_match/labels/` and `syllable_match/matching/`.

## Processed CSV schema

The reduced CSV written for each passage contains the fields listed in `syllable_match/fields.py`.

Those fields are the core derived indicators used downstream for summary stats and timestamping. They include:

- general deviation indicators
- error indicators
- disfluency indicators
- hesitation start/end/match fields
- error start/end/match fields
- duplication start/end/match fields
- comparison fields for matched spans

The `_all-cols.csv` file contains those columns plus the raw coded columns and the scaffold-derived fields.

## Summary statistics

`syllable_match/stats.py` computes passage statistics for each processed sheet.

For each passage, it counts things like:

- syllables
- words
- inserted and omitted syllables without word errors
- word substitutions and approximations
- raw error/disfluency counts per error type
- word-level and correction-level counts
- match completeness for high-error, low-error, and hesitation spans

The summary stage aggregates those results by passage name and then adds overall mean and standard deviation rows.

## Recall analysis

`error_analysis/analyze.py` provides a separate analysis path for recall data.

### Recall period 1

The first recall period expects an Excel file in the participant folder whose name matches the recall-period-1 pattern used by `analyze_recall_periods()`.

For each recalled passage, the code:

- normalizes the input column names to `tp`, `tp2`, and `os`
- matches recalled target passages against the participant’s processed passage files
- computes passage-wide counts for errors, disfluencies, and syllables
- computes per-syllable and per-word rates
- records whether each passage was recalled

### Recall period 2

The second recall period expects a text file in the participant folder.

For each recalled phrase, the code:

- normalizes punctuation and spacing
- compares the phrase against each processed passage’s cleaned text
- finds every occurrence of the phrase in that passage
- extracts the exact phrase span and a surrounding window of five syllables on each side
- counts deviations inside the phrase and inside the wider five-syllable window
- stores passage-level and phrase-level summary metadata for each occurrence

### Important caveats

The current recall-analysis code is fragile and should be treated carefully. As written, it contains implementation issues that can prevent it from running cleanly without fixes, including malformed f-strings and a no-op column cleanup step. The README documents the intended behavior of the module, but the code should be validated before relying on its outputs.

## Timestamping sheets

`timestamping.py` converts processed syllable CSVs into timestamping sheets.

For each syllable row, it marks whether the row is:

- a hesitation
- an error
- a comparison row for hesitation or error matching

It then adds a `MarkLocation` column so timestamping can target onset or offset positions depending on the type of event.

The output sheet includes a `Duplicate` marker for rows that share a `SyllableID`, and a blank `Timestamp` column intended for later manual or downstream annotation.

## Known limitations and assumptions

The implementation makes a number of strict assumptions:

- Participant directories must start with `sub-`.
- Passage files must live under a `_reconciled` directory.
- Passage filenames must follow the regex-based naming convention used by `extract_passage_name()`.
- `--timestamp-only` assumes there is already at least one prior run in `output_dir` and simply chooses the lexicographically latest directory name.
- The recall-analysis module is currently brittle and should be checked before use.
- Some internal helper logic is written for a specific dataset layout and is not a general-purpose speech coding framework.

## Practical usage notes

If you are working with a new dataset, verify the following before running the pipeline:

1. Participant folders are named correctly.
2. The reconciled passage `.xlsx` files are in the expected location.
3. The coding templates contain the target text and target syllables rows required by the scaffold builder.
4. The output directory exists and is writable.

If you want to regenerate only timestamp sheets from the most recent run, use `--timestamp-only`.

If you want to compare the older and alternate matching behavior, run once with `--old-matching` and once without it, then compare the contents of the generated `processed_passages` outputs.