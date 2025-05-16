"""Modifiers Selection Details stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class ModifiersSelectionDetailsStream(CSVSFTPStream):
    """Stream for Toast modifiers selection details data from CSV files."""

    name = "modifiers_selection_details"
    file_name = "ModifiersSelectionDetails.csv"
    primary_keys = ["location_id", "date", "modifier_id"]
