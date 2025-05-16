"""Tests for the accounting_report stream."""

import io
import os
import pandas as pd
import pytest
import logging
from unittest.mock import MagicMock, patch

from tap_toast_sftp.streams.accounting_report import AccountingReportStream


def create_sample_excel():
    """Create a sample Excel file for testing."""
    # Create the header rows
    header_rows = pd.DataFrame([
        ['Accounting Export', None, None, None, None, 'Generated 5/15/25 5:54 AM'],
        ['5/14/25 - 5/14/25', None, None, None, None, None],
        [None, None, None, None, None, None],
        ['From', 'To', 'Location', 'GL Account', 'Description', 'Amount']
    ])

    # Create sample data rows
    data_rows = pd.DataFrame([
        ['2025-05-14', '2025-05-14', 'Test Location', 1001, 'Test Description 1', 123.45],
        ['2025-05-14', '2025-05-14', 'Test Location', 1002, 'Test Description 2', 678.90]
    ])

    # Combine header and data
    full_sample = pd.concat([header_rows, data_rows], ignore_index=True)

    # Print the sample data for debugging
    print("Sample Excel data:")
    print(full_sample)

    # Save to BytesIO
    excel_buffer = io.BytesIO()
    full_sample.to_excel(excel_buffer, index=False, header=False, engine='openpyxl')
    excel_buffer.seek(0)

    # Read back the Excel file to verify it was created correctly
    excel_buffer_copy = io.BytesIO(excel_buffer.getvalue())
    df_read = pd.read_excel(excel_buffer_copy, header=None)
    print("\nExcel file read back:")
    print(df_read)

    # Test reading with header=3
    excel_buffer_copy = io.BytesIO(excel_buffer.getvalue())
    df_with_header = pd.read_excel(excel_buffer_copy, header=3)
    print("\nExcel file with header=3:")
    print(df_with_header)

    # Return to the beginning of the buffer
    excel_buffer.seek(0)
    return excel_buffer.read()


@pytest.fixture
def mock_sftp_client():
    """Create a mock SFTP client."""
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.get_file_content.return_value = create_sample_excel()
    return mock_client


def test_process_excel_file(mock_sftp_client):
    """Test processing an Excel file with the first 3 rows skipped."""
    # Set up logging to capture log messages
    logger = logging.getLogger("tap-toast-sftp")
    logger.setLevel(logging.DEBUG)

    # Create a stream handler to print log messages
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    # Create a stream instance with a mock config
    stream = AccountingReportStream(tap=MagicMock())
    stream._sftp_client = mock_sftp_client

    # Set up a mock logger for the stream
    mock_logger = MagicMock()
    stream.logger = mock_logger

    # Process the file
    location_id = "201419"
    date_folder = "20250514"

    # Add debug prints
    print("\nCalling process_excel_file...")

    # Patch the read_excel function to print its arguments
    original_read_excel = pd.read_excel

    def debug_read_excel(*args, **kwargs):
        print(f"\nread_excel called with args: {args}")
        print(f"read_excel kwargs: {kwargs}")
        result = original_read_excel(*args, **kwargs)
        print(f"read_excel result shape: {result.shape}")
        print(f"read_excel result columns: {result.columns.tolist()}")
        print(f"read_excel result:\n{result}")
        return result

    with patch('pandas.read_excel', side_effect=debug_read_excel):
        records = list(stream.process_excel_file(location_id, date_folder))

    # Print the log messages
    print("\nLog messages:")
    for call in mock_logger.info.call_args_list:
        print(f"INFO: {call[0][0]}")

    for call in mock_logger.error.call_args_list:
        print(f"ERROR: {call[0][0]}")

    print(f"\nRecords returned: {len(records)}")
    for i, record in enumerate(records):
        print(f"Record {i}: {record}")

    # Verify the results
    assert len(records) == 2

    # Check the first record
    assert records[0]["from"] == "2025-05-14"
    assert records[0]["to"] == "2025-05-14"
    assert records[0]["location"] == "Test Location"
    assert records[0]["gl_account"] == 1001
    assert records[0]["description"] == "Test Description 1"
    assert records[0]["amount"] == 123.45
    assert records[0]["location_id"] == location_id
    assert records[0]["date"] == date_folder

    # Check the second record
    assert records[1]["from"] == "2025-05-14"
    assert records[1]["to"] == "2025-05-14"
    assert records[1]["location"] == "Test Location"
    assert records[1]["gl_account"] == 1002
    assert records[1]["description"] == "Test Description 2"
    assert records[1]["amount"] == 678.90
    assert records[1]["location_id"] == location_id
    assert records[1]["date"] == date_folder
