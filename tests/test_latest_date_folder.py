"""Tests for the latest date folder functionality."""

import unittest
from unittest.mock import patch, MagicMock
from tap_toast_sftp.client import ToastSFTPStream, SFTPClient


class MockToastSFTPStream(ToastSFTPStream):
    """Mock ToastSFTPStream class for testing."""

    name = "mock_stream"  # Required by the parent class

    @property
    def schema(self):
        """Return a mock schema."""
        return {"type": "object", "properties": {}}

    def get_records(self, context=None):
        """Mock implementation of get_records."""
        return []


class TestLatestDateFolder(unittest.TestCase):
    """Test cases for the latest date folder functionality."""

    def setUp(self):
        """Set up test cases."""
        # Create a mock tap with config
        mock_tap = MagicMock()
        mock_tap.config = {
            "sftp_host": "test-host",
            "sftp_username": "test-user",
            "sftp_password": "test-password",
            "locations": [{"id": "123456"}]
        }

        # Initialize the stream with the mock tap
        self.stream = MockToastSFTPStream(tap=mock_tap)
        self.stream.logger = MagicMock()
        self.stream._sftp_client = MagicMock()

    @patch('tap_toast_sftp.client.SFTPClient')
    def test_get_date_folders_returns_latest(self, mock_client_class):
        """Test that get_date_folders returns only the latest date folder."""
        # Mock the SFTP client
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        # Mock the list_files method to return a list of date folders and some non-date folders
        mock_client.list_files.return_value = ["20241116", "20250506", "20250514", "not_a_date", "123456"]

        # Mock the is_directory method to return True for all folders
        mock_client.is_directory.return_value = True

        # Set the mock client on the stream
        self.stream._sftp_client = mock_client

        # Call the method
        result = self.stream.get_date_folders("123456")

        # Assert that only the latest folder is returned
        self.assertEqual(result, ["20250514"])

        # Assert that the log message indicates we're using the latest folder
        self.stream.logger.info.assert_any_call("Found 3 potential date folders. Using latest: 20250514")

    @patch('tap_toast_sftp.client.SFTPClient')
    def test_get_date_folders_empty(self, mock_client_class):
        """Test that get_date_folders returns an empty list when no folders are found."""
        # Mock the SFTP client
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        # Mock the list_files method to return an empty list
        mock_client.list_files.return_value = []

        # Set the mock client on the stream
        self.stream._sftp_client = mock_client

        # Call the method
        result = self.stream.get_date_folders("123456")

        # Assert that an empty list is returned
        self.assertEqual(result, [])

        # Assert that the log message indicates no folders were found
        self.stream.logger.info.assert_any_call("No items found in /123456")

    @patch('tap_toast_sftp.client.SFTPClient')
    def test_get_date_folders_filters_non_date_folders(self, mock_client_class):
        """Test that get_date_folders correctly filters out non-date folders."""
        # Mock the SFTP client
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        # Mock the list_files method to return a mix of date and non-date folders
        mock_client.list_files.return_value = ["not_a_date", "text", "123", "20250514"]

        # Set up the is_directory method to return True for all folders
        mock_client.is_directory.return_value = True

        # Set the mock client on the stream
        self.stream._sftp_client = mock_client

        # Call the method
        result = self.stream.get_date_folders("123456")

        # Assert that only the date folder is returned
        self.assertEqual(result, ["20250514"])

        # Assert that the log message indicates we found only one date folder
        self.stream.logger.info.assert_any_call("Found 1 potential date folders. Using latest: 20250514")

    @patch('tap_toast_sftp.client.SFTPClient')
    def test_process_date_folders_parallel(self, mock_client_class):
        """Test that process_date_folders_parallel processes only the latest folder."""
        # Mock the SFTP client
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        # Create a mock tap with config
        mock_tap = MagicMock()
        mock_tap.config = {
            "sftp_host": "test-host",
            "sftp_username": "test-user",
            "sftp_password": "test-password",
            "locations": [{"id": "123456"}]
        }

        # Create a mock stream with a mocked get_date_folders method
        stream = MockToastSFTPStream(tap=mock_tap)
        stream.logger = MagicMock()
        stream.get_date_folders = MagicMock(return_value=["20250514"])
        stream.process_date_folder = MagicMock(return_value=iter([{"record": "data"}]))

        # Mock process function
        process_func = MagicMock()

        # Call the method
        result = list(stream.process_date_folders_parallel("123456", process_func))

        # Assert that the result contains the expected record
        self.assertEqual(result, [{"record": "data"}])

        # Assert that process_date_folder was called with the latest folder
        stream.process_date_folder.assert_called_once_with("123456", "20250514", process_func)

        # Assert that the log message indicates we're processing the latest folder
        stream.logger.info.assert_any_call("Processing latest date folder 20250514 for location 123456")


if __name__ == "__main__":
    unittest.main()
