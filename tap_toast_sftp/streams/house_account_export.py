"""House Account Export stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class HouseAccountExportStream(CSVSFTPStream):
    """Stream for Toast house account export data from CSV files."""

    name = "house_account_export"
    file_name = "HouseAccountExport.csv"
    primary_keys = ["location_id", "date", "account_number"]
