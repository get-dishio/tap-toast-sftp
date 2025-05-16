"""Menu items stream class for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import JSONSFTPStream


class MenuItemsStream(JSONSFTPStream):
    """Stream for Toast menu items from JSON files."""

    name = "menu_items"
    path_template = "/exports/{location_id}/menu_items.json"  # Template with location_id placeholder
    primary_keys = ["item_id", "location_id"]
    records_path = "items"  # Example path to records in JSON structure
