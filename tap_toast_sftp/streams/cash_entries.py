"""Cash Entries stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class CashEntriesStream(CSVSFTPStream):
    """Stream for Toast cash entries data from CSV files."""

    name = "cash_entries"
    file_name = "CashEntries.csv"
    primary_keys = ["location_id", "date", "entry_id"]
