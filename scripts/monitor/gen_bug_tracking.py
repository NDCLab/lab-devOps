import os
from typing import Type

import pandas as pd
import pytest
from test_cases import (
    DeviationAndNoDataErrorTestCase,
    DeviationAndNoDataFilesErrorTestCase,
    DeviationFilePreventsErrorWithExtraFilesTestCase,
    DeviationFileWithBadNamesTestCase,
    DeviationFileWithFolderMismatchTestCase,
    DeviationFileWithValidNamesTestCase,
    EEGDataFileVHDRMismatchTestCase,
    EEGDataFileVMRKMismatchTestCase,
    EEGMarkerFileVHDRMismatchTestCase,
    EmptyFileTestCase,
    ExpectedFileMissingTestCase,
    ExtraFilesInFolderTestCase,
    FolderRunSuffixMismatchTestCase,
    FolderSessionSuffixMismatchTestCase,
    FolderSubjectMismatchTestCase,
    FolderVariableMismatchTestCase,
    InsufficientFilesTestCase,
    InvalidEventSuffixTestCase,
    InvalidExtensionTestCase,
    InvalidRunSuffixTestCase,
    InvalidSessionSuffixTestCase,
    InvalidSubjectNumberTestCase,
    InvalidVariableNameTestCase,
    IssueFileTestCase,
    MissingEventSuffixTestCase,
    MissingExtensionTestCase,
    MissingRunSuffixTestCase,
    MissingSessionSuffixTestCase,
    MissingSubjectNumberTestCase,
    MissingVariableNameTestCase,
    MultipleTasksFromCombinationRowTestCase,
    NoDataAdditionalFilesTestCase,
    PsychopyFileIDMismatchTestCase,
    TestCase,
    TestCaseRegistry,
)

BASE_SUBJECT_ID = TestCase.BASE_SUBJECT_ID


def create_base_subject(basedir):
    base_subdir = os.path.join(basedir, TestCase.BASE_SUBJECT_SUBDIR)
    os.makedirs(base_subdir)

    # -- set up standard files --
    # (stored in "checked order": sub/ses/dtype)

    ses_runs = [("s1", "r1"), ("s2", "r1"), ("s3", "r1")]

    for ses, run in ses_runs:
        # set up session/run directory
        sr_dir = os.path.join(base_subdir, f"{ses}_{run}")
        os.makedirs(sr_dir)

        # set up psychopy data

        psychopy_dir = os.path.join(sr_dir, "psychopy")
        os.makedirs(psychopy_dir)

        psychopy_var = "arrow-alert-v1-1_psychopy"
        psychopy_base = f"sub-{BASE_SUBJECT_ID}_{psychopy_var}_{ses}_{run}_e1"

        psychopy_log = psychopy_base + ".log"
        psychopy_psydat = psychopy_base + ".psydat"
        for filename in {psychopy_log, psychopy_psydat}:
            with open(os.path.join(psychopy_dir, filename), "w") as f:
                f.write("psychopy data")

        psychopy_csv = psychopy_base + ".csv"
        csv_data = [{"id": BASE_SUBJECT_ID}]  # ID in CSV matches subject ID
        df = pd.DataFrame(csv_data)
        df.to_csv(os.path.join(psychopy_dir, psychopy_csv), index=False)

        # set up eeg data

        eeg_dir = os.path.join(sr_dir, "eeg")
        os.makedirs(eeg_dir)

        eeg_var = "all_eeg"
        eeg_base = f"sub-{BASE_SUBJECT_ID}_{eeg_var}_{ses}_{run}_e1"

        eeg_data = eeg_base + ".eeg"
        eeg_vhdr = eeg_base + ".vhdr"
        eeg_vmrk = eeg_base + ".vmrk"

        with open(os.path.join(eeg_dir, eeg_data), "w") as f:
            f.write("eeg data")

        # match .vmrk and .eeg files
        with open(os.path.join(eeg_dir, eeg_vhdr), "w") as f:
            vhdr_lines = [
                f"MarkerFile={eeg_vmrk}",
                f"DataFile={eeg_data}",
            ]
            f.write("\n".join(vhdr_lines))

        # just match .eeg file
        with open(os.path.join(eeg_dir, eeg_vmrk), "w") as f:
            f.write(f"DataFile={eeg_data}")

        # set up audacity data

        audacity_dir = os.path.join(sr_dir, "audacity")
        os.makedirs(audacity_dir)

        audacity_zip_gpg = f"sub-{BASE_SUBJECT_ID}_all_audacity_{ses}_{run}_e1.zip.gig"
        with open(os.path.join(audacity_dir, audacity_zip_gpg), "w") as f:
            f.write("audacity data")

        # set up zoom data

        zoom_dir = os.path.join(sr_dir, "zoom")
        os.makedirs(zoom_dir)

        zoom_zip_gpg = f"sub-{BASE_SUBJECT_ID}_all_zoom_{ses}_{run}_e1.zip.gig"
        with open(os.path.join(zoom_dir, zoom_zip_gpg), "w") as f:
            f.write("zoom data")

        # set up digi data

        digi_dir = os.path.join(sr_dir, "digi")
        os.makedirs(digi_dir)

        digi_zip_gpg = f"sub-{BASE_SUBJECT_ID}_all_digi_{ses}_{run}_e1.zip.gig"
        with open(os.path.join(digi_dir, digi_zip_gpg), "w") as f:
            f.write("digi data")


def create_tests():
    basedir = "test_output"
    if os.path.exists(basedir):
        # clear directory before running tests
        for root, dirs, files in os.walk(basedir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    os.makedirs(basedir, exist_ok=True)

    # one-time setup for the base subject
    create_base_subject(basedir)

    # set up test cases
    registry = TestCaseRegistry(basedir)
    tests: list[Type[TestCase]] = [
        DeviationAndNoDataErrorTestCase,
        DeviationAndNoDataFilesErrorTestCase,
        DeviationFilePreventsErrorWithExtraFilesTestCase,
        DeviationFileWithBadNamesTestCase,
        DeviationFileWithFolderMismatchTestCase,
        DeviationFileWithValidNamesTestCase,
        EEGDataFileVHDRMismatchTestCase,
        EEGDataFileVMRKMismatchTestCase,
        EEGMarkerFileVHDRMismatchTestCase,
        EmptyFileTestCase,
        ExpectedFileMissingTestCase,
        ExtraFilesInFolderTestCase,
        FolderRunSuffixMismatchTestCase,
        FolderSessionSuffixMismatchTestCase,
        FolderSubjectMismatchTestCase,
        FolderVariableMismatchTestCase,
        InsufficientFilesTestCase,
        InvalidEventSuffixTestCase,
        InvalidExtensionTestCase,
        InvalidRunSuffixTestCase,
        InvalidSessionSuffixTestCase,
        InvalidSubjectNumberTestCase,
        InvalidVariableNameTestCase,
        IssueFileTestCase,
        MissingEventSuffixTestCase,
        MissingExtensionTestCase,
        MissingRunSuffixTestCase,
        MissingSessionSuffixTestCase,
        MissingSubjectNumberTestCase,
        MissingVariableNameTestCase,
        MultipleTasksFromCombinationRowTestCase,
        NoDataAdditionalFilesTestCase,
        PsychopyFileIDMismatchTestCase,
    ]
    registry.add_cases(tests)
    registry.generate_all()
    return registry


registry = create_tests()
tests = registry.get_cases()


# run each test separately using a pytest harness
@pytest.mark.parametrize("test_case", tests)
def test_validate_test_cases(test_case):
    test_case.validate()
