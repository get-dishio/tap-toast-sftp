"""Kitchen Timings stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class KitchenTimingsStream(CSVSFTPStream):
    """Stream for Toast kitchen timings data from CSV files."""

    name = "kitchen_timings"
    file_name = "KitchenTimings.csv"
    primary_keys = ["location_id", "date", "id"]
