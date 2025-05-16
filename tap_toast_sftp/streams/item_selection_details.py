"""Item Selection Details stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class ItemSelectionDetailsStream(CSVSFTPStream):
    """Stream for Toast item selection details data from CSV files."""

    name = "item_selection_details"
    file_name = "ItemSelectionDetails.csv"
    primary_keys = ["location_id", "date", "item_selection_id"]
