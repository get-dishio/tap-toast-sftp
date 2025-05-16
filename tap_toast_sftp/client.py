"""Custom client handling, including ToastSFTPStream base class."""

from __future__ import annotations

import io
import typing as t
import csv
import json
import os
from importlib import resources
from pathlib import Path

import paramiko
import logging
import time
import socket
import typing as t
import concurrent.futures
from functools import partial
from singer_sdk.streams import Stream
from singer_sdk.exceptions import ConfigValidationError, FatalAPIError, RetriableAPIError

if t.TYPE_CHECKING:
    from singer_sdk.helpers.types import Context

# Reference local JSON schema files
SCHEMAS_DIR = resources.files(__package__) / "schemas"


class SFTPClient:
    """SFTP client for connecting to Toast SFTP server."""

    def __init__(self, config: dict) -> None:
        """Initialize the SFTP client.

        Args:
            config: The tap configuration.
        """
        self.host = config["sftp_host"]
        self.username = config["sftp_username"]
        self.port = config.get("sftp_port", 22)
        self.private_key = config.get("sftp_private_key")
        self.password = config.get("sftp_password")
        self.logger = logging.getLogger("tap-toast-sftp.sftp_client")

        # Validate that either private key or password is provided
        if not self.private_key and not self.password:
            raise ConfigValidationError(
                "Either 'sftp_private_key' or 'sftp_password' must be provided"
            )

        # Normalize private key if provided
        if self.private_key:
            self.private_key = self._normalize_private_key(self.private_key)

        self._client = None

    def _normalize_private_key(self, key_str: str) -> str:
        """Normalize SSH private key by ensuring proper newlines.

        SSH keys are often stored and copied with missing or incorrect newlines.
        This method ensures the key has proper formatting with newlines.

        Args:
            key_str: The SSH private key string.

        Returns:
            Normalized SSH private key string with proper newlines.
        """
        # Handle escaped newlines (replace \\n with actual newlines)
        if "\\n" in key_str:
            self.logger.info("Converting escaped newlines in SSH key")
            key_str = key_str.replace("\\n", "\n")

        # Remove any extra whitespace at the beginning or end
        key_str = key_str.strip()

        # Check if the key has the proper BEGIN and END markers
        if "-----BEGIN" not in key_str or "-----END" not in key_str:
            self.logger.warning("SSH key appears to be missing BEGIN/END markers")
            return key_str

        # Extract the BEGIN and END lines
        begin_pattern = "-----BEGIN RSA PRIVATE KEY-----"
        end_pattern = "-----END RSA PRIVATE KEY-----"

        # Handle other key types if needed
        if begin_pattern not in key_str:
            for key_type in ["DSA", "EC", "OPENSSH", "PRIVATE KEY"]:
                test_pattern = f"-----BEGIN {key_type} PRIVATE KEY-----"
                if test_pattern in key_str:
                    begin_pattern = test_pattern
                    end_pattern = f"-----END {key_type} PRIVATE KEY-----"
                    break

        # Split the key into lines and remove any extra whitespace
        lines = [line.strip() for line in key_str.splitlines()]

        # If we already have a properly formatted key with multiple lines, just clean it up
        if len(lines) >= 3:
            return "\n".join(lines)

        # If we have a key without proper newlines, reformat it
        self.logger.info("Reformatting SSH key with missing newlines")

        # Find the begin and end markers
        begin_index = key_str.find(begin_pattern)
        end_index = key_str.find(end_pattern) + len(end_pattern)

        if begin_index < 0 or end_index <= begin_index:
            self.logger.warning("Could not find proper BEGIN/END markers in expected format")
            return key_str

        # Extract the content between markers
        key_content = key_str[begin_index:end_index]

        # Replace the begin pattern and add a newline
        formatted_key = key_content.replace(begin_pattern, begin_pattern + "\n")

        # Find the content between BEGIN and END
        content_start = formatted_key.find("\n") + 1
        content_end = formatted_key.find(end_pattern)

        if content_start > 0 and content_end > content_start:
            # Extract the middle content and clean it
            middle_content = formatted_key[content_start:content_end].strip()

            # Split the content by spaces and join with newlines
            # This handles keys where the content is all on one line with spaces
            if " " in middle_content and "\n" not in middle_content:
                parts = [p for p in middle_content.split(" ") if p]
                middle_content = "\n".join(parts)

            # Reconstruct the key with proper newlines
            formatted_key = f"{begin_pattern}\n{middle_content}\n{end_pattern}"
        else:
            # Ensure END line has a newline before it
            formatted_key = formatted_key.replace(end_pattern, "\n" + end_pattern)

        return formatted_key

    def connect(self) -> None:
        """Connect to the SFTP server with retry logic."""
        if self._client is not None:
            return

        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.host,
            "username": self.username,
            "port": self.port,
        }

        if self.private_key:
            try:
                # Create a StringIO object with the normalized key
                key_file = io.StringIO(self.private_key)

                # Try to parse the key - paramiko supports various key types
                try:
                    # First try RSA key format
                    private_key = paramiko.RSAKey.from_private_key(key_file)
                except paramiko.ssh_exception.SSHException:
                    # If RSA fails, rewind the file and try other key types
                    key_file.seek(0)
                    try:
                        # Try DSS key format
                        private_key = paramiko.DSSKey.from_private_key(key_file)
                    except paramiko.ssh_exception.SSHException:
                        # Try ECDSA key format
                        key_file.seek(0)
                        try:
                            private_key = paramiko.ECDSAKey.from_private_key(key_file)
                        except paramiko.ssh_exception.SSHException:
                            # Try Ed25519 key format
                            key_file.seek(0)
                            private_key = paramiko.Ed25519Key.from_private_key(key_file)

                connect_kwargs["pkey"] = private_key
                self.logger.info("Successfully loaded private key")

            except paramiko.ssh_exception.SSHException as e:
                self.logger.error(f"Invalid private key format: {e}")
                self.logger.error("Please check that your private key is correctly formatted with proper newlines")
                self.logger.error("Private keys should include BEGIN and END markers with proper newlines")
                raise FatalAPIError(
                    f"Invalid private key format: {e}. Please ensure your key is properly formatted with newlines."
                )
            except Exception as e:
                self.logger.error(f"Error loading private key: {e}")
                raise FatalAPIError(f"Error loading private key: {e}")
        else:
            connect_kwargs["password"] = self.password

        # Retry parameters
        max_retries = 5
        retry_delay = 2  # seconds
        retries = 0

        while retries < max_retries:
            try:
                self._client.connect(**connect_kwargs)
                self._sftp = self._client.open_sftp()
                return
            except paramiko.ssh_exception.AuthenticationException as e:
                self.logger.error(f"Authentication failed: {e}")
                raise FatalAPIError(f"Authentication failed: {e}")
            except (socket.timeout, paramiko.ssh_exception.SSHException, socket.error) as e:
                retries += 1
                if retries >= max_retries:
                    self.logger.error(f"Failed to connect to SFTP server after {max_retries} attempts: {e}")
                    raise RetriableAPIError(f"Failed to connect to SFTP server: {e}")

                self.logger.warning(f"Connection attempt {retries} failed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Exponential backoff
                retry_delay *= 2

    def disconnect(self) -> None:
        """Disconnect from the SFTP server."""
        if self._client:
            self._sftp.close()
            self._client.close()
            self._client = None

    def list_files(self, path: str) -> list[str]:
        """List files in a directory with retry logic and timeout handling.

        Args:
            path: The directory path.

        Returns:
            A list of file names.
        """
        self.connect()
        self.logger.info(f"Starting to list files in directory: {path}")

        # Retry parameters
        max_retries = 3
        retry_delay = 2  # seconds
        retries = 0

        # Set a timeout for the listdir operation
        timeout = 30  # seconds

        while retries < max_retries:
            try:
                # Use a separate thread with a timeout to prevent hanging
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._sftp.listdir, path)
                    try:
                        result = future.result(timeout=timeout)
                        self.logger.info(f"Successfully listed {len(result)} files in {path}")
                        return result
                    except concurrent.futures.TimeoutError:
                        self.logger.warning(f"Listing files in {path} timed out after {timeout} seconds")
                        # Cancel the future if possible
                        future.cancel()
                        # Try to recover the connection
                        self.disconnect()
                        self.connect()
                        retries += 1
                        if retries >= max_retries:
                            self.logger.error(f"Failed to list files in {path} after {max_retries} attempts due to timeout")
                            return []
                        self.logger.warning(f"Retrying list files (attempt {retries}) in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
            except FileNotFoundError:
                self.logger.warning(f"Directory not found: {path}")
                return []
            except (socket.timeout, paramiko.ssh_exception.SSHException, socket.error, IOError) as e:
                retries += 1
                if retries >= max_retries:
                    self.logger.error(f"Failed to list files in {path} after {max_retries} attempts: {e}")
                    return []

                self.logger.warning(f"List files attempt {retries} failed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Exponential backoff
                retry_delay *= 2
            except Exception as e:
                self.logger.error(f"Error listing files in {path}: {e}")
                return []

        # If we get here, all retries failed
        return []

    def is_directory(self, path: str) -> bool:
        """Check if a path is a directory with retry logic and timeout handling.

        Args:
            path: The path to check.

        Returns:
            True if the path is a directory, False otherwise.
        """
        self.connect()

        # Retry parameters
        max_retries = 3
        retry_delay = 2  # seconds
        retries = 0

        # Set a timeout for the stat operation
        timeout = 15  # seconds

        while retries < max_retries:
            try:
                # Use a separate thread with a timeout to prevent hanging
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(lambda: self._sftp.stat(path).st_mode & 0o40000 != 0)
                    try:
                        result = future.result(timeout=timeout)
                        return result
                    except concurrent.futures.TimeoutError:
                        self.logger.warning(f"Checking if {path} is a directory timed out after {timeout} seconds")
                        # Cancel the future if possible
                        future.cancel()
                        # Try to recover the connection
                        self.disconnect()
                        self.connect()
                        retries += 1
                        if retries >= max_retries:
                            self.logger.error(f"Failed to check if {path} is a directory after {max_retries} attempts due to timeout")
                            return False
                        self.logger.warning(f"Retrying directory check (attempt {retries}) in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
            except FileNotFoundError:
                return False
            except (socket.timeout, paramiko.ssh_exception.SSHException, socket.error, IOError) as e:
                retries += 1
                if retries >= max_retries:
                    self.logger.error(f"Failed to check if {path} is a directory after {max_retries} attempts: {e}")
                    return False

                self.logger.warning(f"Directory check attempt {retries} failed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Exponential backoff
                retry_delay *= 2
            except Exception as e:
                self.logger.error(f"Error checking if {path} is a directory: {e}")
                return False

        # If we get here, all retries failed
        return False

    def get_file_content(self, path: str) -> bytes:
        """Get the content of a file with retry logic and timeout handling.

        Args:
            path: The file path.

        Returns:
            The file content as bytes.
        """
        self.connect()
        self.logger.info(f"Starting to read file: {path}")

        # Retry parameters
        max_retries = 3
        retry_delay = 2  # seconds
        retries = 0

        # Set a timeout for the file read operation
        timeout = 60  # seconds

        while retries < max_retries:
            try:
                # Use a separate thread with a timeout to prevent hanging
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Define a function to read the file
                    def read_file():
                        with self._sftp.open(path, "rb") as f:
                            return f.read()

                    future = executor.submit(read_file)
                    try:
                        result = future.result(timeout=timeout)
                        self.logger.info(f"Successfully read {len(result)} bytes from {path}")
                        return result
                    except concurrent.futures.TimeoutError:
                        self.logger.warning(f"Reading file {path} timed out after {timeout} seconds")
                        # Cancel the future if possible
                        future.cancel()
                        # Try to recover the connection
                        self.disconnect()
                        self.connect()
                        retries += 1
                        if retries >= max_retries:
                            self.logger.error(f"Failed to read file {path} after {max_retries} attempts due to timeout")
                            return b""
                        self.logger.warning(f"Retrying file read (attempt {retries}) in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
            except FileNotFoundError:
                self.logger.warning(f"File not found: {path}")
                return b""  # Return empty bytes instead of raising an error
            except (socket.timeout, paramiko.ssh_exception.SSHException, socket.error, IOError) as e:
                retries += 1
                if retries >= max_retries:
                    self.logger.error(f"Failed to read file {path} after {max_retries} attempts: {e}")
                    return b""  # Return empty bytes instead of raising an error

                self.logger.warning(f"File read attempt {retries} failed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Exponential backoff
                retry_delay *= 2
            except Exception as e:
                self.logger.error(f"Error reading file {path}: {e}")
                return b""

        # If we get here, all retries failed
        return b""

    def __enter__(self):
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.disconnect()


class ToastSFTPStream(Stream):
    """Stream class for ToastSFTP streams."""

    def __init__(self, tap=None):
        """Initialize the stream.

        Args:
            tap: The tap instance.
        """
        super().__init__(tap=tap)
        self._sftp_client = None

    @property
    def sftp_client(self) -> SFTPClient:
        """Get the SFTP client.

        Returns:
            The SFTP client.
        """
        if self._sftp_client is None:
            self._sftp_client = SFTPClient(self.config)
        return self._sftp_client

    @property
    def locations(self) -> list[dict]:
        """Get the list of locations from the config.

        Returns:
            List of location dictionaries.
        """
        return self.config.get("locations", [])

    @property
    def schema(self) -> dict:
        """Return the schema for this stream.

        Returns:
            The schema for this stream.
        """
        schema_path = SCHEMAS_DIR / f"{self.name}.json"
        with schema_path.open("r", encoding="utf-8") as schema_file:
            return json.load(schema_file)

    def get_location_ids(self) -> list[str]:
        """Get the list of location IDs from the config.

        Returns:
            List of location ID strings.
        """
        return [location["id"] for location in self.locations]

    def get_path_for_location(self, base_path: str, location_id: str) -> str:
        """Get the file path for a specific location.

        This method can be overridden by subclasses to implement custom path formatting.

        Args:
            base_path: The base path template.
            location_id: The location ID.

        Returns:
            The formatted path for the location.
        """
        # Replace {location_id} placeholder with actual location ID
        return base_path.replace("{location_id}", location_id)

    def get_date_folders(self, location_id: str) -> list[str]:
        """Get the list of date folders for a specific location.

        Only returns the latest date folder based on folder name (expected format: YYYYMMDD).
        Optimized for performance with large numbers of folders by using a heuristic approach
        to identify date folders without checking if each item is a directory.

        Args:
            location_id: The location ID.

        Returns:
            List containing only the latest date folder name, or empty list if none found.
        """
        location_path = f"/{location_id}"
        self.logger.info(f"Finding latest date folder in {location_path}")

        try:
            with self.sftp_client as client:
                # Get all items in the location directory
                all_items = client.list_files(location_path)

                if not all_items:
                    self.logger.info(f"No items found in {location_path}")
                    return []

                # Filter potential date folders based on naming pattern (8 digits)
                # This avoids having to check if each item is a directory
                potential_date_folders = [
                    item for item in all_items
                    if item.isdigit() and len(item) == 8
                ]

                if not potential_date_folders:
                    self.logger.info(f"No potential date folders found in {location_path}")
                    return []

                # Find the latest date folder
                latest_folder = max(potential_date_folders)

                # Verify that the latest folder is actually a directory
                # We only need to check one folder instead of all of them
                latest_folder_path = f"{location_path}/{latest_folder}"
                if not client.is_directory(latest_folder_path):
                    self.logger.warning(f"Latest potential date folder {latest_folder} is not a directory")
                    return []

                self.logger.info(f"Found {len(potential_date_folders)} potential date folders. Using latest: {latest_folder}")
                return [latest_folder]  # Return a list with only the latest folder
        except Exception as e:
            self.logger.error(f"Error getting date folders for location {location_id}: {e}")
            return []

    def process_date_folder(
        self,
        location_id: str,
        date_folder: str,
        process_func: t.Callable[[str, str], t.Iterable[dict]],
    ) -> t.Iterable[dict]:
        """Process a single date folder.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.
            process_func: A function that processes the folder and yields records.

        Yields:
            Record-type dictionary objects.
        """
        self.logger.info(f"Processing date folder {date_folder} for location {location_id}")
        try:
            yield from process_func(location_id, date_folder)
        except Exception as e:
            self.logger.error(f"Error processing date folder {date_folder} for location {location_id}: {e}")

    def process_date_folders_parallel(
        self,
        location_id: str,
        process_func: t.Callable[[str, str], t.Iterable[dict]],
        max_workers: int = 4,
    ) -> t.Iterable[dict]:
        """Process date folders.

        Since we're only processing the latest date folder, this method no longer uses
        parallel processing but keeps the same interface for backward compatibility.

        Args:
            location_id: The location ID.
            process_func: A function that processes a folder and yields records.
            max_workers: Maximum number of worker threads (no longer used).

        Yields:
            Record-type dictionary objects.
        """
        date_folders = self.get_date_folders(location_id)
        if not date_folders:
            self.logger.info(f"No date folders found for location {location_id}. Skipping.")
            return  # Return an empty generator

        # We should only have one folder (the latest) due to the updated get_date_folders method
        latest_folder = date_folders[0]
        self.logger.info(f"Processing latest date folder {latest_folder} for location {location_id}")

        try:
            yield from self.process_date_folder(location_id, latest_folder, process_func)
        except Exception as e:
            self.logger.error(f"Error processing folder {latest_folder} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return

    def get_records(
        self,
        context: Context | None,
    ) -> t.Iterable[dict]:
        """Return a generator of record-type dictionary objects.

        The optional `context` argument is used to identify a specific slice of the
        stream if partitioning is required for the stream. Most implementations do not
        require partitioning and should ignore the `context` argument.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        # This is a base implementation that should be overridden by subclasses
        # to implement specific file parsing logic for each stream
        raise NotImplementedError("Subclasses must implement get_records")
