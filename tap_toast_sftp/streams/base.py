"""Base stream classes for tap-toast-sftp."""

from __future__ import annotations

import typing as t
import csv
import io
import json
import os
import pandas as pd
import concurrent.futures
from pathlib import Path
from functools import partial

from tap_toast_sftp.client import ToastSFTPStream, SCHEMAS_DIR


class CSVSFTPStream(ToastSFTPStream):
    """Base class for CSV file streams from SFTP."""

    # These should be overridden by subclasses
    name = None
    file_name = None  # The name of the file to process (e.g., "OrderDetails.csv")
    primary_keys: t.ClassVar[list[str]] = []
    replication_key = None

    # CSV parsing options
    delimiter = ","
    quotechar = '"'

    # Batch size for processing records
    batch_size = 1000

    # Maximum number of worker threads for parallel processing
    max_workers = 4

    def transform_field_name(self, field_name: str) -> str:
        """Transform field names to snake_case.

        Args:
            field_name: The original field name.

        Returns:
            The transformed field name in snake_case.
        """
        # Replace spaces and special characters with underscores
        transformed = field_name.lower().replace(' ', '_').replace('-', '_')

        # Replace special characters with descriptive names
        transformed = transformed.replace('%', 'pct').replace('#', 'num')

        # Remove question marks (e.g., "void?" becomes "void")
        transformed = transformed.replace('?', '')

        # Replace parentheses and other special characters with underscores
        transformed = transformed.replace('(', '').replace(')', '').replace('/', '_')

        # Remove any duplicate underscores
        while '__' in transformed:
            transformed = transformed.replace('__', '_')

        # Remove leading and trailing underscores
        transformed = transformed.strip('_')

        return transformed

    def process_csv_file(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process a single CSV file.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Record-type dictionary objects.
        """
        file_path = f"/{location_id}/{date_folder}/{self.file_name}"
        self.logger.info(f"Processing file {file_path} for location {location_id}, date {date_folder}")

        try:
            # Use the existing SFTP client connection
            content = self.sftp_client.get_file_content(file_path)

            # If file not found or empty, return empty generator
            if not content:
                self.logger.info(f"File {file_path} not found or empty. Skipping.")
                return

            csv_data = content.decode("utf-8")

            reader = csv.DictReader(
                io.StringIO(csv_data),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )

            # Process records in batches
            batch = []
            for row in reader:
                # Convert empty strings to None and transform field names to snake_case
                record = {
                    self.transform_field_name(k): (v if v != "" else None)
                    for k, v in row.items()
                }
                # Add location_id and date to the record
                record["location_id"] = location_id
                record["date"] = date_folder

                batch.append(record)

                # Yield batch when it reaches the batch size
                if len(batch) >= self.batch_size:
                    for record in batch:
                        yield record
                    batch = []

            # Yield any remaining records
            for record in batch:
                yield record

        except Exception as e:
            self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
            # Return empty generator instead of raising an exception
            return

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process CSV files from SFTP server for all configured locations and date folders.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        if not self.file_name:
            raise ValueError(f"Stream {self.name} must define a 'file_name' attribute")

        location_ids = self.get_location_ids()
        if not location_ids:
            self.logger.warning("No location IDs configured. No data will be extracted.")
            return

        try:
            # Establish a single SFTP connection for all file operations
            self.connect_sftp()

            for location_id in location_ids:
                # Process date folders in parallel
                yield from self.process_date_folders_parallel(
                    location_id,
                    self.process_csv_file,
                    max_workers=self.max_workers,
                )
        finally:
            # Ensure connection is closed even if an exception occurs
            self.disconnect_sftp()


class XLSSFTPStream(ToastSFTPStream):
    """Base class for Excel file streams from SFTP."""

    # These should be overridden by subclasses
    name = None
    file_name = None  # The name of the file to process (e.g., "AccountingReport.xls")
    primary_keys: t.ClassVar[list[str]] = []
    replication_key = None

    # Excel parsing options
    sheet_name = 0  # Default to first sheet

    # Batch size for processing records
    batch_size = 1000

    # Maximum number of worker threads for parallel processing
    max_workers = 4

    def process_excel_file(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process a single Excel file.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Record-type dictionary objects.
        """
        file_path = f"/{location_id}/{date_folder}/{self.file_name}"
        self.logger.info(f"Processing file {file_path} for location {location_id}, date {date_folder}")

        try:
            # Use the existing SFTP client connection
            content = self.sftp_client.get_file_content(file_path)

            # If file not found or empty, return empty generator
            if not content:
                self.logger.info(f"File {file_path} not found or empty. Skipping.")
                return

            # Create a BytesIO object from the content
            excel_data = io.BytesIO(content)

            # Read the Excel file into a pandas DataFrame
            df = pd.read_excel(excel_data, sheet_name=self.sheet_name)

            # Convert DataFrame to records
            records = df.to_dict(orient="records")

            # Process records in batches
            batch = []
            for record in records:
                # Convert NaN values to None and transform field names to snake_case
                record = {
                    self.transform_field_name(k): (None if pd.isna(v) else v)
                    for k, v in record.items()
                }
                # Add location_id and date to the record
                record["location_id"] = location_id
                record["date"] = date_folder

                batch.append(record)

                # Yield batch when it reaches the batch size
                if len(batch) >= self.batch_size:
                    for rec in batch:
                        yield rec
                    batch = []

            # Yield any remaining records
            for record in batch:
                yield record

        except Exception as e:
            self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
            # Return empty generator instead of raising an exception
            return

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process Excel files from SFTP server for all configured locations and date folders.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        if not self.file_name:
            raise ValueError(f"Stream {self.name} must define a 'file_name' attribute")

        location_ids = self.get_location_ids()
        if not location_ids:
            self.logger.warning("No location IDs configured. No data will be extracted.")
            return

        try:
            # Establish a single SFTP connection for all file operations
            self.connect_sftp()

            for location_id in location_ids:
                # Process date folders in parallel
                yield from self.process_date_folders_parallel(
                    location_id,
                    self.process_excel_file,
                    max_workers=self.max_workers,
                )
        finally:
            # Ensure connection is closed even if an exception occurs
            self.disconnect_sftp()


class JSONSFTPStream(ToastSFTPStream):
    """Base class for JSON file streams from SFTP."""

    # These should be overridden by subclasses
    name = None
    file_pattern = None  # Pattern to match JSON files (e.g., "MenuExport_*.json")
    primary_keys: t.ClassVar[list[str]] = []
    replication_key = None

    # JSON parsing options
    records_path = None  # Path to records array in JSON structure, e.g., "data.records"

    # Batch size for processing records
    batch_size = 1000

    # Maximum number of worker threads for parallel processing
    max_workers = 4

    def process_json_files(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process JSON files in a date folder.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Record-type dictionary objects.
        """
        folder_path = f"/{location_id}/{date_folder}"

        try:
            # Use the existing SFTP client connection
            # List all files in the date folder
            files = self.sftp_client.list_files(folder_path)

            # If folder doesn't exist or is empty, return empty generator
            if not files:
                self.logger.info(f"No files found in {folder_path}. Skipping.")
                return

            # Find files matching the pattern
            import fnmatch
            matching_files = [f for f in files if fnmatch.fnmatch(f, self.file_pattern)]

            if not matching_files:
                self.logger.info(f"No files matching pattern {self.file_pattern} found in {folder_path}. Skipping.")
                return

            for file_name in matching_files:
                file_path = f"{folder_path}/{file_name}"
                self.logger.info(f"Processing file {file_path} for location {location_id}, date {date_folder}")

                try:
                    content = self.sftp_client.get_file_content(file_path)

                    # If file not found or empty, skip to next file
                    if not content:
                        self.logger.info(f"File {file_path} not found or empty. Skipping.")
                        continue

                    json_data = json.loads(content.decode("utf-8"))

                    # Extract records based on records_path if provided
                    records = json_data
                    if self.records_path:
                        try:
                            for key in self.records_path.split("."):
                                records = records[key]
                        except (KeyError, TypeError):
                            self.logger.warning(f"Could not find records at path '{self.records_path}' in {file_path}. Skipping.")
                            continue

                    # Process records in batches
                    batch = []

                    # Handle both array and object responses
                    if isinstance(records, list):
                        for record in records:
                            # Add location_id and date to the record
                            record["location_id"] = location_id
                            record["date"] = date_folder

                            batch.append(record)

                            # Yield batch when it reaches the batch size
                            if len(batch) >= self.batch_size:
                                for rec in batch:
                                    yield rec
                                batch = []
                    else:
                        # Add location_id and date to the record
                        records["location_id"] = location_id
                        records["date"] = date_folder
                        yield records

                    # Yield any remaining records
                    for record in batch:
                        yield record

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
                    # Continue with next file instead of failing completely
                    continue
        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process JSON files from SFTP server for all configured locations and date folders.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        if not self.file_pattern:
            raise ValueError(f"Stream {self.name} must define a 'file_pattern' attribute")

        location_ids = self.get_location_ids()
        if not location_ids:
            self.logger.warning("No location IDs configured. No data will be extracted.")
            return

        try:
            # Establish a single SFTP connection for all file operations
            self.connect_sftp()

            for location_id in location_ids:
                # Process date folders in parallel
                yield from self.process_date_folders_parallel(
                    location_id,
                    self.process_json_files,
                    max_workers=self.max_workers,
                )
        finally:
            # Ensure connection is closed even if an exception occurs
            self.disconnect_sftp()
