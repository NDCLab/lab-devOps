# HallMonitor 2.0

The `hallmonitor` module is designed to ensure data integrity within the [NDCLab's](https://www.ndclab.com/) datasets. It validates files within raw and checked directories against a central tracker and data dictionary, performing checks for expected files, naming conventions, and handling exceptions such as `no-data.txt` and `deviation.txt` files. The module logs errors for missing, extra, or misnamed files, runs special checks for data types like EEG and Psychopy, and prepares valid files for QA.

## Features

- **Data Validation**: Validates the presence and correctness of files in raw and checked directories.
- **Error Logging**: Logs detailed information about missing, extra, or misnamed files.
- **Special Data Checks**: Performs specific checks for data types like EEG and Psychopy.
- **QA Preparation**: Prepares valid files for quality assurance checks.
- **Central Tracker Update**: Updates a central tracker with the status of validated files.

## Building with Singularity
To build `hallmonitor`, you'll need:
* [Singularity](https://github.com/sylabs/singularity/blob/main/INSTALL.md) — Install via your preferred method (e.g. package manager or from source).
* `make` utility — Required to run the build script:
    * **Linux**: Typically preinstalled.
    * **macOS**: Install via [Homebrew](https://formulae.brew.sh/formula/make).
    * **Windows**: Use [WSL (Windows Subsystem for Linux)](https://learn.microsoft.com/en-us/windows/wsl/install), which includes access to standard Linux tooling like `make` and can run Singularity if installed within the WSL environment.

Once you have Singularity installed, navigate to the root directory of this project (the directory containing `pyproject.toml`) and run:
```sh
make
```

> **Windows users**: You can either run the `make` command directly from within WSL, or run the included `build.bat` from **Command Prompt**. This will automatically invoke the build inside WSL:
> ```bat
> build.bat
> ```
> To clean old builds from **Command Prompt**, use:
> ```bat
> clean.bat
> ```

This will build a Singularity container in the `build/` directory. The build process typically takes about a minute, depending on your system. The container will be named based on the version in `pyproject.toml` (e.g., `build/hm2_0-1-0.sif` for version 0.1.0).

To remove old builds from the `build/` directory, run:
```sh
make clean
```

> **Note:** As part of the build process, Singularity will run `pytest` on the `hallmonitor` module. Any failed tests will cause the build to exit with error.

To run `hallmonitor` from within a Singularity container, simply execute:
```sh
singularity run build/image_name.sif dataset [OPTIONS]
```

## Testing

To run the test suite locally, execute `./test.sh` from the root `hallMonitor2` directory. This will run all tests and generate an HTML report in the `reports/` directory.

The script will also attempt to open the report automatically in your default browser. If that doesn't work, you can manually open the report by pasting the full file path (e.g., `/home/ndc/reports/test-20250520_153000.html`) into your browser’s address bar.

## Usage

To use the `hallmonitor` module, you need to ensure that the module is installed and accessible from your Python environment. You can achieve this by installing the module using `pip` and then running the script from any directory.

First, navigate to the root directory of the `hallmonitor` module and install it:

```sh
pip install .
```

After installation, you can run the `hallmonitor` script from any directory by using the following command:

```sh
python -m hallmonitor [dataset-path] [options]
```

### Options

- `-c, --child-data`: Indicates that the dataset includes child data.
- `-l, --legacy-exceptions`: Use legacy exception file behavior (deviation.txt and no-data.txt do not include identifier name).
- `-n, --no-color`: Disable color in output, useful for logging or plain-text environments.
- `--no-qa`: Skip the QA (quality assurance) step of the pipeline.
- `-o, --output`: Specify a file path for logger output (defaults to a timestamped file in data-monitoring/logs/).
- `--checked-only`: Only run data validation for data in sourcedata/checked/.
- `--raw-only`: Only run data validation for data in sourcedata/raw/.
- `-v, --verbose`: Print additional debugging information to the console.
- `-q, --quiet`: Do not print any information to the console.
- `-r, --replace`: Replace all REDCap columns with the passed values.
- `-m, --map`: Remap the names of specified REDCap columns.

## Example

To validate a dataset located at `/path/to/dataset` and log the output to a specific file, use:

```sh
python -m hallmonitor /path/to/dataset -o /path/to/logfile.log
```
