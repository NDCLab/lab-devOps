import json
import os
import subprocess
from typing import Type

import pandas as pd
import pytest

from .base_cases import (
    TestCase,
    _TestCaseRegistry,
)
from .eeg_cases import (
    EEGDataFileVHDRMismatchTestCase,
    EEGDataFileVMRKMismatchTestCase,
    EEGMarkerFileVHDRMismatchTestCase,
)
from .exception_cases import (
    DeviationAndNoDataErrorTestCase,
    DeviationAndNoDataFilesErrorTestCase,
    DeviationFilePreventsErrorWithExtraFilesTestCase,
    DeviationFileWithBadNamesTestCase,
    DeviationFileWithFolderMismatchTestCase,
    DeviationFileWithValidNamesTestCase,
    IssueFileTestCase,
    MissingIdentifierNoDataTestCase,
    MissingIdentifierWithoutNoDataTestCase,
    NoDataAdditionalFilesTestCase,
)
from .misc_cases import (
    BaseTestCase,
    DataDictionaryHasChangesTestCase,
    EmptyFileTestCase,
    ExpectedFileMissingTestCase,
    ExtraFilesInFolderTestCase,
    InsufficientFilesTestCase,
    MissingTaskFromDataDictionaryTestCase,
    MultipleTasksFromCombinationRowTestCase,
    PendingFilesCsvCreatedTestCase,
)
from .misplaced_cases import (
    FolderRunSuffixMismatchTestCase,
    FolderSessionSuffixMismatchTestCase,
    FolderSubjectMismatchTestCase,
    FolderVariableMismatchTestCase,
)
from .naming_cases import (
    InvalidEventSuffixTestCase,
    InvalidExtensionTestCase,
    InvalidRunSuffixTestCase,
    InvalidSessionSuffixTestCase,
    InvalidSubjectNumberTestCase,
    InvalidVariableNameTestCase,
    MissingEventSuffixTestCase,
    MissingExtensionTestCase,
    MissingRunSuffixTestCase,
    MissingSessionSuffixTestCase,
    MissingSubjectNumberTestCase,
    MissingVariableNameTestCase,
)
from .psychopy_cases import PsychopyFileIDMismatchTestCase
from .qa_cases import (
    PendingQAFileTestCase,
    QAChecklistCreatedTestCase,
    QAChecklistEntryTestCase,
    QAEmptyDirectoriesAreDeletedTestCase,
    QAPassAddedToValidatedFileRecordTestCase,
    QAPassMovedToCheckedTestCase,
    QAPassRemovedFromChecklistTestCase,
)
from .tracker_cases import (
    BaseUpdateTrackerTestCase,
    BBSDataOneDeviationFileTestCase,
    BBSDataZeroIncorrectDataTestCase,
    BBSDataZeroMissingDataTestCase,
    BBSDataZeroMissingDatatypeFolderTestCase,
    BBSDataZeroNoDataFileTestCase,
    DeviationCheckedUpdateTrackerTestCase,
    DeviationNoCheckedUpdateTrackerTestCase,
    DuplicateREDCapColumnsTestCase,
)

BASE_SUBJECT_ID = TestCase.BASE_SUBJECT_ID


def create_base_subject(basedir):
    base_subdir = os.path.join(basedir, TestCase.BASE_SUBJECT_SUBDIR)
    os.makedirs(base_subdir)

    # add metadata file
    metadata = {
        "description": "Unmodified test data.",
        "subject": f"sub-{BASE_SUBJECT_ID}",
    }
    with open(os.path.join(base_subdir, "metadata.json"), "w") as f:
        json.dump(metadata, f)

    # -- set up standard files --
    # (stored in "checked order": sub/ses/dtype)

    checked_data_dir = os.path.join(
        base_subdir, "sourcedata", "checked", f"sub-{BASE_SUBJECT_ID}"
    )
    os.makedirs(checked_data_dir)

    ses_runs = [("s1", "r1"), ("s2", "r1"), ("s3", "r1")]

    datatypes = set()
    # set up files in checked directory
    for ses, run in ses_runs:
        # set up session/run directory
        sr_dir = os.path.join(checked_data_dir, f"{ses}_{run}")
        os.makedirs(sr_dir)

        # set up psychopy data

        datatypes.add("psychopy")
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

        datatypes.add("eeg")
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

        datatypes.add("audacity")
        audacity_dir = os.path.join(sr_dir, "audacity")
        os.makedirs(audacity_dir)

        audacity_zip_gpg = f"sub-{BASE_SUBJECT_ID}_all_audacity_{ses}_{run}_e1.zip.gpg"
        with open(os.path.join(audacity_dir, audacity_zip_gpg), "w") as f:
            f.write("audacity data")

        # set up zoom data

        datatypes.add("zoom")
        zoom_dir = os.path.join(sr_dir, "zoom")
        os.makedirs(zoom_dir)

        zoom_zip_gpg = f"sub-{BASE_SUBJECT_ID}_all_zoom_{ses}_{run}_e1.zip.gpg"
        with open(os.path.join(zoom_dir, zoom_zip_gpg), "w") as f:
            f.write("zoom data")

        # set up digi data

        datatypes.add("digi")
        digi_dir = os.path.join(sr_dir, "digi")
        os.makedirs(digi_dir)

        digi_zip_gpg = f"sub-{BASE_SUBJECT_ID}_all_digi_{ses}_{run}_e1.zip.gpg"
        with open(os.path.join(digi_dir, digi_zip_gpg), "w") as f:
            f.write("digi data")

    # copy checked directory files to raw directory
    raw_data_dir = os.path.join(base_subdir, "sourcedata", "raw")
    os.makedirs(raw_data_dir)
    for ses, run in ses_runs:
        ses_run = f"{ses}_{run}"
        for dtype in datatypes:
            dtype_dir = os.path.join(raw_data_dir, ses_run, dtype)
            os.makedirs(dtype_dir)
            src_path = os.path.join(checked_data_dir, ses_run, dtype)
            dest_path = os.path.join(dtype_dir, f"sub-{BASE_SUBJECT_ID}")
            subprocess.check_call(["cp", "-r", src_path, dest_path])

    # -- set up sourcedata/pending-qa/ directory --

    pending_qa_dir = os.path.join(base_subdir, "sourcedata", "pending-qa")
    os.makedirs(pending_qa_dir)

    # set up empty QA checklist

    checklist_path = os.path.join(pending_qa_dir, "qa-checklist.csv")
    mock_checklist = pd.DataFrame(
        columns=[
            "datetime",
            "user",
            "identifier",
            "identifierDetails",
            "qa",
            "localMove",
        ]
    )
    mock_checklist.to_csv(checklist_path, index=False)

    # -- set up data-monitoring/ directory --

    data_monitoring_dir = os.path.join(base_subdir, "data-monitoring")
    os.makedirs(data_monitoring_dir)

    # set up validated file record
    validated_files_path = os.path.join(
        data_monitoring_dir, "validated-file-record.csv"
    )
    validated_files = pd.DataFrame(
        columns=[
            "datetime",
            "user",
            "identifier",
            "identifierDetails",
        ]
    )
    validated_files.to_csv(validated_files_path, index=False)

    # set up pending/ directory and files

    pending_dir = os.path.join(data_monitoring_dir, "pending")
    os.makedirs(pending_dir)

    timestamp = "2024-01-01_12-30"

    pending_files_path = os.path.join(pending_dir, f"pending-files-{timestamp}.csv")
    pending_files = pd.DataFrame(
        columns=[
            "datetime",
            "user",
            "passRaw",
            "identifier",
            "identifierDetails",
            "errorType",
            "errorDetails",
        ]
    )
    pending_files.to_csv(pending_files_path, index=False)

    pending_errors_path = os.path.join(pending_dir, f"pending-errors-{timestamp}.csv")
    pending_errors = pd.DataFrame(
        columns=[
            "datetime",
            "user",
            "identifier",
            "identifierDetails",
            "errorType",
            "errorDetails",
        ]
    )
    pending_errors.to_csv(pending_errors_path, index=False)

    # set up data dictionary and "latest" data dictionary

    dd_dir = os.path.join(data_monitoring_dir, "data-dictionary")
    os.makedirs(dd_dir)

    dd_path = os.path.join(dd_dir, "central-tracker_datadict.csv")
    latest_dd_path = os.path.join(dd_dir, "central-tracker_datadict_latest.csv")
    mock_dd = [
        {
            "variable": "id",
            "dataType": "id",
            "description": "Participant ID",
            "detail": "The participant ID is specific to this study, and is auto-assigned by REDCap.",
            "allowedSuffix": "NA",
            "measureUnit": "Integer",
            "allowedValues": "[3000000,3009999],[3080000,3089999],[3090000,3099999]",
            "valueInfo": "One ID per participant (eligible and ineligible)",
            "provenance": f'file: "{TestCase.BASE_SUBJECT_SUBDIR}consent"; variable: "record_id"',
            "expectedFileExt": "NA",
        },
        {
            "variable": "consent",
            "dataType": "consent",
            "description": "Participant consent status",
            "detail": 'When data is transferred from raw to checked, value of 1 is assigned based on the value of "consent_complete" or "consentes_complete" == "2"(indicating participant consented), otherwise 0.',
            "allowedSuffix": "NA",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": f'file: "{TestCase.BASE_SUBJECT_SUBDIR}consent"; variable: ""',
            "expectedFileExt": "NA",
        },
        {
            "variable": "assent",
            "dataType": "assent",
            "description": "Participant assent status",
            "detail": 'When data is transferred from raw to checked, value of 1 is assigned based on the value of "assent_complete"=="2" (indicating participant assented), otherwise 0.',
            "allowedSuffix": "NA",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": f'file: "{TestCase.BASE_SUBJECT_SUBDIR}consent"; variable: ""',
            "expectedFileExt": "NA",
        },
        {
            "variable": "arrow-alert-v1-1_psychopy",
            "dataType": "psychopy",
            "description": "arrow-alert-v1-1_psychopy task status",
            "detail": 'When data is transferred from raw to checked, value of 1 is assigned if "arrow-alert-v1-1" file exists, otherwise 0.',
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": "direct-psychopy",
            "expectedFileExt": ".psydat, .csv, .log",
        },
        {
            "variable": "arrow-alert-v1-2_psychopy",
            "dataType": "psychopy",
            "description": "arrow-alert-v1-2_psychopy task status",
            "detail": 'When data is transferred from raw to checked, value of 1 is assigned if "arrow-alert-v1-2" file exists, otherwise 0.',
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": "direct-psychopy",
            "expectedFileExt": ".psydat, .csv, .log",
        },
        {
            "variable": "arrow-alert_psychopy",
            "dataType": "combination",
            "description": "arrow-alert_psychopy task status",
            "detail": "When updatetracker is run, value of 1 is assigned if either of the variables specificed for a given allowedSuffix = 1, otherwise a value of 0 is assigned.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": 'variables: "arrow-alert-v1-1_psychopy","arrow-alert-v1-2_psychopy"',
            "expectedFileExt": "NA",
        },
        {
            "variable": "all_audacity",
            "dataType": "audacity",
            "description": "Audacity data status",
            "detail": "When hallMonitor is run, value of 1 is assigned if data already exists in checked, otherwise 0.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": "direct-audacity",
            "expectedFileExt": ".zip.gpg",
        },
        {
            "variable": "all_zoom",
            "dataType": "zoom",
            "description": "Zoom data status",
            "detail": "When hallMonitor is run, value of 1 is assigned if data already exists in checked, otherwise 0.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": "direct-zoom",
            "expectedFileExt": ".zip.gpg",
        },
        {
            "variable": "all_eeg",
            "dataType": "eeg",
            "description": "Brain Vision EEG data status",
            "detail": "When data is transferred from raw to checked, value of 1 is assigned if data exists, otherwise 0.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": "direct-eeg",
            "expectedFileExt": ".eeg, .vmrk, .vhdr",
        },
        {
            "variable": "all_digi",
            "dataType": "digi",
            "description": "Digi data status",
            "detail": "When hallMonitor is run, value of 1 is assigned if data already exists in checked, otherwise 0.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": "direct-digi",
            "expectedFileExt": ".zip.gpg",
        },
        {
            "variable": "iqs_status",
            "dataType": "visit_status",
            "description": "Status of participant's IQS visit (attended vs not attended)",
            "detail": "Value of 1 is assigned if the participant attended the IQS visit, otherwise 0.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, participant has not attended IQS | 1, participant has attended IQS",
            "provenance": 'file: "iqsclinician"; variable: "iqsclchecklist"',
            "expectedFileExt": "NA",
        },
        {
            "variable": "bbs_status",
            "dataType": "visit_status",
            "description": "Status of participant's BBS visit (attended vs not attended)",
            "detail": "Value of 1 is assigned if the participant attended the BBS visit, otherwise 0.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, participant has not attended BBS | 1, participant has attended BBS",
            "provenance": 'file: "bbsra"; variable: "bbsradebrief"; id: "bbsratrk_acid"',
            "expectedFileExt": "NA",
        },
        {
            "variable": "iqs_data",
            "dataType": "visit_data",
            "description": "Status of participant's IQS data (present on HPC or not)",
            "detail": "Value of 1 is assigned if IQS data exists, otherwise 0.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, IQS data does not exist | 1, IQS data exists",
            "provenance": 'file: "iqsclinician"',
            "expectedFileExt": "NA",
        },
        {
            "variable": "bbs_data",
            "dataType": "visit_data",
            "description": "Status of participant's BBS data (present on HPC or not)",
            "detail": "Value of 1 is assigned if all BBS data exists, otherwise 0.",
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, At least some BBS data does not exist | 1, All BBS data exists",
            "provenance": 'variables: "arrow-alert_psychopy","all_audacity","all_zoom","all_eeg","all_digi"',
            "expectedFileExt": "NA",
        },
        {
            "variable": "abq",
            "dataType": "redcap_data",
            "description": "ABQ questionnaire status",
            "detail": 'When data is transferred from raw to checked, value of 1 is assigned based on the value of "{questionnaire name}_complete"!=NULL (indicating participant began questionnaire), otherwise 0.',
            "allowedSuffix": "s1_r1_e1, s2_r1_e1, s3_r1_e1",
            "measureUnit": "Logical",
            "allowedValues": "NA, 0, 1",
            "valueInfo": "NA, status unknown | 0, no data exists | 1, data exists",
            "provenance": 'file: "bbschild"; variable: ""',
            "expectedFileExt": "NA",
        },
    ]
    mock_dd = pd.DataFrame(mock_dd)
    mock_dd.to_csv(dd_path, index=False)
    mock_dd.to_csv(latest_dd_path, index=False)

    # set up minimum necessary REDCaps

    redcap_dir = os.path.join(base_subdir, "sourcedata", "checked", "redcap")
    os.makedirs(redcap_dir)

    # basic "consent" REDCap (not associated with a ses/run)
    rc_consent_path = os.path.join(redcap_dir, build_base_rc_name("consent"))
    consent_row = {
        "record_id": TestCase.BASE_SUBJECT_ID,
        # English variables
        "consent_complete": 2,
        "assent_complete": 2,
        # Spanish variables
        "consentes_complete": 2,
        "assentes_complete": 2,
    }
    consent_df = pd.DataFrame([consent_row])
    consent_df.to_csv(rc_consent_path, index=False)

    # set up identical REDCap files for all session/run combinations,
    # with appropriate substitutions to file content and names
    for ses, run in ses_runs:
        # basic "iqsclinician" REDCap
        rc_iqsclinician_path = os.path.join(
            redcap_dir, build_base_rc_name("iqsclinician", ses, run)
        )
        iqsclinician_row = {
            "record_id": TestCase.BASE_SUBJECT_ID,
            f"iqsclchecklist_{ses}_{run}_e1_complete": 2,
        }
        iqsclinician_df = pd.DataFrame([iqsclinician_row])
        iqsclinician_df.to_csv(rc_iqsclinician_path, index=False)

        # basic "bbsRA" REDCap
        rc_bbsra_path = os.path.join(redcap_dir, build_base_rc_name("bbsRA", ses, run))
        bbsra_row = {
            "record_id": 1,
            f"bbsradebrief_{ses}_{run}_e1_complete": 2,
            f"bbsratrk_acid_{ses}_{run}_e1": TestCase.BASE_SUBJECT_ID,
        }
        bbsra_df = pd.DataFrame([bbsra_row])
        bbsra_df.to_csv(rc_bbsra_path, index=False)

        # basic "bbschild" REDCap
        rc_bbschild_path = os.path.join(
            redcap_dir, build_base_rc_name("bbschild", ses, run)
        )
        bbschild_row = {
            "record_id": TestCase.BASE_SUBJECT_ID,
            f"abq_{ses}_{run}_e1_complete": 2,
        }
        bbschild_df = pd.DataFrame([bbschild_row])
        bbschild_df.to_csv(rc_bbschild_path, index=False)

    # set up empty central tracker

    # handle record_id, consent, and assent variables separately
    tracker_cols = {"id", "consent", "assent"}

    var_df = mock_dd[~mock_dd["variable"].isin(tracker_cols)]
    for _, row in var_df.iterrows():
        variable = str(row["variable"])
        suffixes = str(row["allowedSuffix"]).split(",")
        for suffix in suffixes:
            tracker_cols.add(f"{variable}_{suffix.strip()}")

    case_name = os.path.basename(TestCase.BASE_SUBJECT_SUBDIR)
    tracker_path = os.path.join(data_monitoring_dir, f"central-tracker_{case_name}.csv")

    tracker_df = pd.DataFrame(columns=list(tracker_cols))
    tracker_df.to_csv(tracker_path, index=False)


def build_base_rc_name(rc_stem: str, ses: str = "", run: str = ""):
    RC_TIMESTAMP = "2024-01-01_1230"
    return f"{TestCase.BASE_SUBJECT_SUBDIR}{rc_stem}{ses}{run}_DATA_{RC_TIMESTAMP}.csv"


def create_registry():
    basedir = os.path.dirname(__file__)
    basedir = os.path.join(basedir, ".test_output")
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
    registry = _TestCaseRegistry(basedir)
    tests: list[Type[TestCase]] = [
        BaseTestCase,
        BaseUpdateTrackerTestCase,
        BBSDataOneDeviationFileTestCase,
        BBSDataZeroIncorrectDataTestCase,
        BBSDataZeroMissingDataTestCase,
        BBSDataZeroMissingDatatypeFolderTestCase,
        BBSDataZeroNoDataFileTestCase,
        DataDictionaryHasChangesTestCase,
        DeviationAndNoDataErrorTestCase,
        DeviationAndNoDataFilesErrorTestCase,
        DeviationCheckedUpdateTrackerTestCase,
        DeviationFilePreventsErrorWithExtraFilesTestCase,
        DeviationFileWithBadNamesTestCase,
        DeviationFileWithFolderMismatchTestCase,
        DeviationFileWithValidNamesTestCase,
        DeviationNoCheckedUpdateTrackerTestCase,
        DuplicateREDCapColumnsTestCase,
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
        MissingIdentifierNoDataTestCase,
        MissingIdentifierWithoutNoDataTestCase,
        MissingRunSuffixTestCase,
        MissingSessionSuffixTestCase,
        MissingSubjectNumberTestCase,
        MissingTaskFromDataDictionaryTestCase,
        MissingVariableNameTestCase,
        MultipleTasksFromCombinationRowTestCase,
        NoDataAdditionalFilesTestCase,
        PendingFilesCsvCreatedTestCase,
        PendingQAFileTestCase,
        PsychopyFileIDMismatchTestCase,
        QAChecklistCreatedTestCase,
        QAChecklistEntryTestCase,
        QAEmptyDirectoriesAreDeletedTestCase,
        QAPassAddedToValidatedFileRecordTestCase,
        QAPassMovedToCheckedTestCase,
        QAPassRemovedFromChecklistTestCase,
    ]
    registry.add_cases(tests)
    return registry


registry = create_registry()
registry.generate_all()
tests = registry.get_cases()


# run each test separately using a pytest harness
@pytest.mark.parametrize("test_case", tests, ids=lambda t: t.case_name)
def test_validate_test_cases(test_case) -> None:
    test_case.validate()
