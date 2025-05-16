"""Sales stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class SalesStream(CSVSFTPStream):
    """Stream for Toast sales data from CSV files."""

    name = "sales"
    path_template = "/exports/{location_id}/sales.csv"  # Template with location_id placeholder
    primary_keys = ["order_id", "location_id"]
    replication_key = "order_date"
