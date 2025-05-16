"""Menu Export child stream classes for tap-toast-sftp."""

from __future__ import annotations

import typing as t

from tap_toast_sftp.streams.base import JSONSFTPStream
from tap_toast_sftp.streams.menu_export import MenuExportStream


class MenuMenusStream(JSONSFTPStream):
    """Stream for Toast menu objects from menu export JSON files."""

    name = "menu_menus"
    parent_stream_type = MenuExportStream
    ignore_parent_replication_keys = True
    primary_keys = ["location_id", "date", "guid"]
    generate_unique_ids = True

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process menu objects from parent stream.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        parent_context = context or {}
        parent = self.parent_stream_type(self._tap, shared_sftp_client=self._sftp_client)

        for parent_record in parent.get_records(parent_context):
            # For menu_export, the parent record itself is the menu
            if not parent_record.get("guid"):
                continue

            location_id = parent_record.get("location_id")
            date = parent_record.get("date")

            # Create a copy of the parent record as the menu record
            menu = parent_record.copy()

            # Remove nested objects that will be in their own streams
            if "groups" in menu:
                del menu["groups"]

            yield menu

    def get_child_context(self, record: dict, context: t.Optional[dict]) -> dict:
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
            "menu_guid": record["guid"],
        }


class MenuGroupsStream(JSONSFTPStream):
    """Stream for Toast menu group objects from menu export JSON files."""

    name = "menu_groups"
    parent_stream_type = MenuMenusStream
    ignore_parent_replication_keys = True
    primary_keys = ["location_id", "date", "menu_guid", "guid"]
    generate_unique_ids = True

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process menu group objects from parent stream.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        parent_context = context or {}
        parent = self.parent_stream_type(self._tap, shared_sftp_client=self._sftp_client)

        for parent_record in parent.get_records(parent_context):
            if not parent_record.get("groups"):
                continue

            location_id = parent_record.get("location_id")
            date = parent_record.get("date")
            menu_guid = parent_record.get("guid")

            for group in parent_record.get("groups", []):
                if not group:
                    continue

                # Add parent context to the record
                group["location_id"] = location_id
                group["date"] = date
                group["menu_guid"] = menu_guid

                yield group

    def get_child_context(self, record: dict, context: t.Optional[dict]) -> dict:
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
            "menu_guid": record["menu_guid"],
            "group_guid": record["guid"],
        }


class MenuGroupItemsStream(JSONSFTPStream):
    """Stream for Toast menu item objects from menu export JSON files."""

    name = "menu_group_items"
    parent_stream_type = MenuGroupsStream
    ignore_parent_replication_keys = True
    primary_keys = ["location_id", "date", "menu_guid", "group_guid", "guid"]
    generate_unique_ids = True

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process menu item objects from parent stream.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        parent_context = context or {}
        parent = self.parent_stream_type(self._tap, shared_sftp_client=self._sftp_client)

        for parent_record in parent.get_records(parent_context):
            if not parent_record.get("items"):
                continue

            location_id = parent_record.get("location_id")
            date = parent_record.get("date")
            menu_guid = parent_record.get("menu_guid")
            group_guid = parent_record.get("guid")

            for item in parent_record.get("items", []):
                if not item:
                    continue

                # Add parent context to the record
                item["location_id"] = location_id
                item["date"] = date
                item["menu_guid"] = menu_guid
                item["group_guid"] = group_guid

                yield item
