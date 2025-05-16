"""Menu Export V2 child stream classes for tap-toast-sftp."""

from __future__ import annotations

import typing as t

from tap_toast_sftp.streams.base import JSONSFTPStream
from tap_toast_sftp.streams.menu_export import MenuExportV2Stream


class MenuV2MenusStream(JSONSFTPStream):
    """Stream for Toast menu objects from menu export V2 JSON files."""

    name = "menu_v2_menus"
    parent_stream_type = MenuExportV2Stream
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
            if not parent_record.get("menus"):
                continue

            location_id = parent_record.get("location_id")
            date = parent_record.get("date")
            menu_export_guid = parent_record.get("guid")

            for menu in parent_record.get("menus", []):
                if not menu:
                    continue

                # Add parent context to the record
                menu["location_id"] = location_id
                menu["date"] = date
                menu["menu_export_guid"] = menu_export_guid

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


class MenuV2GroupsStream(JSONSFTPStream):
    """Stream for Toast menu group objects from menu export V2 JSON files."""

    name = "menu_v2_groups"
    parent_stream_type = MenuV2MenusStream
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


class MenuV2ItemsStream(JSONSFTPStream):
    """Stream for Toast menu item objects from menu export V2 JSON files."""

    name = "menu_v2_items"
    parent_stream_type = MenuV2GroupsStream
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
            "group_guid": record["group_guid"],
            "item_guid": record["guid"],
        }


class MenuV2OptionGroupsStream(JSONSFTPStream):
    """Stream for Toast menu option group objects from menu export V2 JSON files."""

    name = "menu_v2_option_groups"
    parent_stream_type = MenuV2ItemsStream
    ignore_parent_replication_keys = True
    primary_keys = ["location_id", "date", "menu_guid", "group_guid", "item_guid", "guid"]
    generate_unique_ids = True

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process menu option group objects from parent stream.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        parent_context = context or {}
        parent = self.parent_stream_type(self._tap, shared_sftp_client=self._sftp_client)

        for parent_record in parent.get_records(parent_context):
            if not parent_record.get("optionGroups"):
                continue

            location_id = parent_record.get("location_id")
            date = parent_record.get("date")
            menu_guid = parent_record.get("menu_guid")
            group_guid = parent_record.get("group_guid")
            item_guid = parent_record.get("guid")

            for option_group in parent_record.get("optionGroups", []):
                if not option_group:
                    continue

                # Add parent context to the record
                option_group["location_id"] = location_id
                option_group["date"] = date
                option_group["menu_guid"] = menu_guid
                option_group["group_guid"] = group_guid
                option_group["item_guid"] = item_guid

                yield option_group

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
            "group_guid": record["group_guid"],
            "item_guid": record["item_guid"],
            "option_group_guid": record["guid"],
        }


class MenuV2OptionItemsStream(JSONSFTPStream):
    """Stream for Toast menu option item objects from menu export V2 JSON files."""

    name = "menu_v2_option_items"
    parent_stream_type = MenuV2OptionGroupsStream
    ignore_parent_replication_keys = True
    primary_keys = ["location_id", "date", "menu_guid", "group_guid", "item_guid", "option_group_guid", "guid"]
    generate_unique_ids = True

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process menu option item objects from parent stream.

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
            group_guid = parent_record.get("group_guid")
            item_guid = parent_record.get("item_guid")
            option_group_guid = parent_record.get("guid")

            for option_item in parent_record.get("items", []):
                if not option_item:
                    continue

                # Add parent context to the record
                option_item["location_id"] = location_id
                option_item["date"] = date
                option_item["menu_guid"] = menu_guid
                option_item["group_guid"] = group_guid
                option_item["item_guid"] = item_guid
                option_item["option_group_guid"] = option_group_guid

                yield option_item


class MenuV2PremodifierGroupsStream(JSONSFTPStream):
    """Stream for Toast premodifier group objects from menu export V2 JSON files."""

    name = "menu_v2_premodifier_groups"
    parent_stream_type = MenuExportV2Stream
    ignore_parent_replication_keys = True
    primary_keys = ["location_id", "date", "menu_export_guid", "guid"]
    generate_unique_ids = True

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process premodifier group objects from parent stream.

        Args:
            context: Stream partition or context dictionary.

        Yields:
            Record-type dictionary objects.
        """
        parent_context = context or {}
        parent = self.parent_stream_type(self._tap, shared_sftp_client=self._sftp_client)

        for parent_record in parent.get_records(parent_context):
            if not parent_record.get("premodifierGroups"):
                continue

            location_id = parent_record.get("location_id")
            date = parent_record.get("date")
            menu_export_guid = parent_record.get("guid")

            for premodifier_group in parent_record.get("premodifierGroups", []):
                if not premodifier_group:
                    continue

                # Add parent context to the record
                premodifier_group["location_id"] = location_id
                premodifier_group["date"] = date
                premodifier_group["menu_export_guid"] = menu_export_guid

                yield premodifier_group

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
            "menu_export_guid": record["menu_export_guid"],
            "premodifier_group_guid": record["guid"],
        }


class MenuV2PremodifierItemsStream(JSONSFTPStream):
    """Stream for Toast premodifier item objects from menu export V2 JSON files."""

    name = "menu_v2_premodifier_items"
    parent_stream_type = MenuV2PremodifierGroupsStream
    ignore_parent_replication_keys = True
    primary_keys = ["location_id", "date", "menu_export_guid", "premodifier_group_guid", "guid"]
    generate_unique_ids = True

    def get_records(
        self,
        context: t.Optional[dict] = None,
    ) -> t.Iterable[dict]:
        """Process premodifier item objects from parent stream.

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
            menu_export_guid = parent_record.get("menu_export_guid")
            premodifier_group_guid = parent_record.get("guid")

            for premodifier_item in parent_record.get("items", []):
                if not premodifier_item:
                    continue

                # Add parent context to the record
                premodifier_item["location_id"] = location_id
                premodifier_item["date"] = date
                premodifier_item["menu_export_guid"] = menu_export_guid
                premodifier_item["premodifier_group_guid"] = premodifier_group_guid

                yield premodifier_item
