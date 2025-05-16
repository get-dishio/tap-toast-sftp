"""Menu Export stream classes for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import JSONSFTPStream


class MenuExportStream(JSONSFTPStream):
    """Stream for Toast menu export data from JSON files."""

    name = "menu_export"
    file_pattern = "MenuExport_*.json"
    primary_keys = ["location_id", "date"]
    generate_unique_ids = True

    def get_child_context(self, record: dict, context: dict = None) -> dict:
        """Return a context dictionary for child streams.

        Args:
            record: The current record.
            context: The parent stream's context.

        Returns:
            A context dictionary for child streams.
        """
        return {
            "location_id": record["location_id"],
            "date": record["date"],
            "menu_guid": record.get("guid", ""),
        }


class MenuExportV2Stream(JSONSFTPStream):
    """Stream for Toast menu export V2 data from JSON files."""

    name = "menu_export_v2"
    file_pattern = "MenuExportV2_*.json"
    primary_keys = ["location_id", "date"]
    generate_unique_ids = True

    def get_child_context(self, record: dict, context: dict = None) -> dict:
        """Return a context dictionary for child streams.

        Args:
            record: The current record.
            context: The parent stream's context.

        Returns:
            A context dictionary for child streams.
        """
        return {
            "location_id": record["location_id"],
            "date": record["date"],
            "menu_export_guid": record.get("guid", ""),
        }
