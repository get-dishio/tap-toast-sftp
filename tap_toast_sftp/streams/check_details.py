"""Check Details stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class CheckDetailsStream(CSVSFTPStream):
    """Stream for Toast check details data from CSV files."""

    name = "check_details"
    file_name = "CheckDetails.csv"
    primary_keys = ["location_id", "date", "check_id"]
