"""Order Details stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class OrderDetailsStream(CSVSFTPStream):
    """Stream for Toast order details data from CSV files."""

    name = "order_details"
    file_name = "OrderDetails.csv"
    primary_keys = ["location_id", "date", "order_id"]
