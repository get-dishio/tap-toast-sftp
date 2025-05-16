"""All Items Report stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class AllItemsReportStream(CSVSFTPStream):
    """Stream for Toast all items report data from CSV files."""

    name = "all_items_report"
    file_name = "AllItemsReport.csv"
    primary_keys = ["location_id", "date", "item_id"]
