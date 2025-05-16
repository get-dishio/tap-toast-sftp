"""Payment Details stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import CSVSFTPStream


class PaymentDetailsStream(CSVSFTPStream):
    """Stream for Toast payment details data from CSV files."""

    name = "payment_details"
    file_name = "PaymentDetails.csv"
    primary_keys = ["location_id", "date", "payment_id"]
