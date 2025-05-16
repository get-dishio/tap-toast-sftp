# tap-toast-sftp

`tap-toast-sftp` is a Singer tap for extracting data from Toast POS via SFTP. This tap extracts data from various CSV, JSON, and Excel files stored in a structured directory format on a Toast SFTP server.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Supported Data Files

This tap supports extracting data from the following Toast data export files:

| Stream Name | File Name | Format | Description |
|-------------|-----------|--------|-------------|
| accounting_report | AccountingReport.xls | Excel | Accounting data export with revenue amounts for each GL code |
| all_items_report | AllItemsReport.csv | CSV | Information about all menu items |
| cash_entries | CashEntries.csv | CSV | Information about cash payments |
| check_details | CheckDetails.csv | CSV | Information about checks in orders |
| house_account_export | HouseAccountExport.csv | CSV | Information about house accounts |
| item_selection_details | ItemSelectionDetails.csv | CSV | Information about items ordered |
| kitchen_timings | KitchenTimings.csv | CSV | Information about kitchen tickets |
| menu_export | MenuExport_*.json | JSON | Information about menus |
| menu_export_v2 | MenuExportV2_*.json | JSON | Enhanced information about menus |
| modifiers_selection_details | ModifiersSelectionDetails.csv | CSV | Information about modifiers applied to items |
| order_details | OrderDetails.csv | CSV | Information about orders |
| payment_details | PaymentDetails.csv | CSV | Information about payments |
| time_entries | TimeEntries.csv | CSV | Information about employee shifts |

## SFTP Directory Structure

The tap expects the SFTP server to have a specific directory structure:

```
/
├── {location_id}/
│   ├── {date_folder}/
│   │   ├── AccountingReport.xls
│   │   ├── AllItemsReport.csv
│   │   ├── CashEntries.csv
│   │   ├── CheckDetails.csv
│   │   ├── HouseAccountExport.csv
│   │   ├── ItemSelectionDetails.csv
│   │   ├── KitchenTimings.csv
│   │   ├── MenuExport_*.json
│   │   ├── MenuExportV2_*.json
│   │   ├── ModifiersSelectionDetails.csv
│   │   ├── OrderDetails.csv
│   │   ├── PaymentDetails.csv
│   │   └── TimeEntries.csv
│   └── {another_date_folder}/
│       └── ...
└── {another_location_id}/
    └── ...
```

The tap will iterate through all configured location IDs and all date folders within each location, extracting data from the files in each date folder.

<!--

Developer TODO: Update the below as needed to correctly describe the install procedure. For instance, if you do not have a PyPI repo, or if you want users to directly install from your git repo, you can modify this step as appropriate.

## Installation

Install from PyPI:

```bash
pipx install tap-toast-sftp
```

Install from GitHub:

```bash
pipx install git+https://github.com/ORG_NAME/tap-toast-sftp.git@main
```

-->

## Configuration

### Accepted Config Options

The tap requires the following configuration options:

| Setting             | Required | Default | Description |
|---------------------|----------|---------|-------------|
| sftp_host           | True     | None    | The hostname or IP address of the SFTP server |
| sftp_username       | True     | None    | The username to authenticate with the SFTP server |
| sftp_private_key    | False    | None    | The private SSH key to authenticate with the SFTP server (either this or password is required). The key should include BEGIN and END markers with proper newlines. |
| sftp_password       | False    | None    | The password to authenticate with the SFTP server (either this or private key is required) |
| sftp_port           | False    | 22      | The port of the SFTP server |
| locations           | True     | None    | List of location IDs to extract data for, formatted as an array of objects with "id" field |

### Sample Config File

```json
{
    "sftp_host": "**************",
    "sftp_username": "***********",
    "sftp_private_key": "*********",
    "sftp_port": 22,
    "locations": [
        {"id": "201419"},
        {"id": "201420"}
    ]
}
```

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-toast-sftp --about
```

### Sample Configuration

Two sample configuration files are provided in this repository:

1. `sample_config.json` - Using password authentication
2. `sample_config_ssh_key.json` - Using SSH key authentication

You can copy one of these files and modify it with your actual credentials.

### Configure using environment variables

This Singer tap will automatically import any environment variables within the working directory's
`.env` if the `--config=ENV` is provided, such that config values will be considered if a matching
environment variable is set either in the terminal context or in the `.env` file.

Example `.env` file:
```
TAP_TOAST_SFTP_SFTP_HOST=sftp.toasttab.com
TAP_TOAST_SFTP_SFTP_USERNAME=your-username
TAP_TOAST_SFTP_SFTP_PASSWORD=your-password
TAP_TOAST_SFTP_SFTP_PORT=22
# For locations, you need to use JSON format in the environment variable
TAP_TOAST_SFTP_LOCATIONS=[{"id":"12345"},{"id":"67890"}]
TAP_TOAST_SFTP_START_DATE=2023-01-01T00:00:00Z
```

If you're using SSH key authentication with environment variables, you can format the key with literal newlines or with `\n` escape sequences.

The tap will automatically normalize the key format regardless of which approach you use.

### Source Authentication and Authorization

This tap connects to a Toast SFTP server to extract data. You need to provide either:

1. SFTP username and password, OR
2. SFTP username and private SSH key

The tap will use these credentials to authenticate with the SFTP server and download the necessary files.

### SSH Key Formatting

When using SSH key authentication, ensure your private key is properly formatted with newlines. SSH keys should:

1. Include the BEGIN and END markers
2. Have proper newlines between the BEGIN marker, key content, and END marker
3. Be properly indented

The tap includes logic to normalize SSH keys that might be missing newlines, but it's best to ensure your key is properly formatted from the start.

## Usage

You can easily run `tap-toast-sftp` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
# Show version
tap-toast-sftp --version

# Show help
tap-toast-sftp --help

# Discover mode - output catalog
tap-toast-sftp --config sample_config.json --discover > ./catalog.json

# Run the tap in sync mode
tap-toast-sftp --config sample_config.json --catalog catalog.json

# Run the tap with Poetry
poetry run tap-toast-sftp --config config.json
```

### Running with Poetry

If you're using Poetry for dependency management, you can run the tap using:

```bash
# Install dependencies
poetry install

# Run the tap in discovery mode
poetry run tap-toast-sftp --config config.json --discover

# Run the tap in sync mode
poetry run tap-toast-sftp --config config.json
```

### Output

The tap outputs data in the [Singer specification](https://github.com/singer-io/getting-started/blob/master/docs/SPEC.md) format, which can be consumed by any Singer target.

Each record will include:
- The original data from the file
- A `location_id` field with the location ID from the configuration
- A `date_folder` field with the name of the date folder

### Performance Considerations

- The tap processes date folders in parallel using multiple threads
- Records are processed in batches to improve memory efficiency
- The tap includes robust error handling with retry logic for transient errors
- Processing continues even if some files or folders fail
- The number of worker threads and batch size can be configured in the stream classes

## Developer Resources

Follow these instructions to contribute to this project.

### Initialize your Development Environment

Prerequisites:

- Python 3.9+
- [Poetry](https://python-poetry.org/)

```bash
poetry install
```

### Create and Run Tests

Create tests within the `tests` subfolder and
then run:

```bash
poetry run pytest
```

You can also test the `tap-toast-sftp` CLI interface directly using Poetry:

```bash
poetry run tap-toast-sftp --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

<!--
Developer TODO:
Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any "TODO" items listed in
the file.
-->

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-toast-sftp
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-toast-sftp --version

# OR run a test ELT pipeline:
meltano run tap-toast-sftp target-jsonl
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to
develop your own taps and targets.
