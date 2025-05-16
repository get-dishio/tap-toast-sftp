"""Time Entries stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class TimeEntriesStream(CSVSFTPStream):
    """Stream for Toast time entries data from CSV files."""

    name = "time_entries"
    file_name = "TimeEntries.csv"
    primary_keys = ["location_id", "date", "id"]
