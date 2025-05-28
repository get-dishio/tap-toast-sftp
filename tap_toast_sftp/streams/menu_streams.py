"""Flattened Menu stream classes for tap-toast-sftp.

These streams provide a simplified, flat structure for Menu data instead of the complex
parent/child relationship approach. Each stream reads directly from the JSON files and
includes all necessary parent context in each record.
"""

from __future__ import annotations

import typing as t
import fnmatch
import hashlib
import json

from tap_toast_sftp.streams.base import JSONSFTPStream


class MenuMenusStream(JSONSFTPStream):
    """Stream for Toast menu objects from menu export JSON files.

    This stream extracts all menu records as flat objects, handling both
    MenuExport (array format) and MenuExportV2 (object format) files.
    """

    name = "menu_menus"
    file_pattern = "MenuExport*.json"  # Matches both MenuExport_*.json and MenuExportV2_*.json
    primary_keys = ["location_id", "date", "guid"]
    generate_unique_ids = True

    def process_json_files(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process JSON files in the given folder.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Menu record dictionaries.
        """
        folder_path = f"{location_id}/{date_folder}"

        try:
            # Get list of files in the folder
            files = self._sftp_client.list_files(folder_path)

            # Filter files that match our pattern
            matching_files = [f for f in files if fnmatch.fnmatch(f, self.file_pattern)]

            if not matching_files:
                self.logger.info(f"No files matching pattern '{self.file_pattern}' found in {folder_path}")
                return

            record_count = 0
            for file_name in matching_files:
                file_path = f"{folder_path}/{file_name}"
                try:
                    # Get file content
                    json_data = json.loads(self._sftp_client.get_file_content(file_path).decode("utf-8"))

                    # Extract menus based on file format
                    menus = []
                    if isinstance(json_data, list):
                        # MenuExport format - array of menus
                        menus = json_data
                    elif isinstance(json_data, dict) and 'menus' in json_data:
                        # MenuExportV2 format - object with menus array
                        menus = json_data.get('menus', [])
                    else:
                        self.logger.warning(f"Unknown format in file {file_path}")
                        continue

                    # Process each menu
                    for menu in menus:
                        if not isinstance(menu, dict) or not menu.get("guid"):
                            continue

                        # Create a copy of the menu record
                        menu_record = menu.copy()

                        # Add location_id and date to the record
                        menu_record["location_id"] = location_id
                        menu_record["date"] = date_folder

                        # Remove nested objects that will be in their own streams
                        if "groups" in menu_record:
                            del menu_record["groups"]

                        # Validate primary keys before yielding
                        if self.validate_primary_keys(menu_record):
                            record_count += 1
                            yield menu_record

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
                    # Continue with next file instead of failing completely
                    continue

            self.logger.info(f"Processed {record_count} menu records for location {location_id}, date {date_folder}")

        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return


class MenuGroupsStream(JSONSFTPStream):
    """Stream for Toast menu group objects from menu export JSON files.

    This stream extracts all menu group records with parent menu context.
    """

    name = "menu_groups"
    file_pattern = "MenuExport*.json"
    primary_keys = ["location_id", "date", "menu_guid", "guid"]
    generate_unique_ids = True

    def process_json_files(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process JSON files in the given folder.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Menu group record dictionaries with parent menu context.
        """
        folder_path = f"{location_id}/{date_folder}"

        try:
            # Get list of files in the folder
            files = self._sftp_client.list_files(folder_path)

            # Filter files that match our pattern
            matching_files = [f for f in files if fnmatch.fnmatch(f, self.file_pattern)]

            if not matching_files:
                self.logger.info(f"No files matching pattern '{self.file_pattern}' found in {folder_path}")
                return

            record_count = 0
            for file_name in matching_files:
                file_path = f"{folder_path}/{file_name}"
                try:
                    # Get file content
                    json_data = json.loads(self._sftp_client.get_file_content(file_path).decode("utf-8"))

                    # Extract menus based on file format
                    menus = []
                    if isinstance(json_data, list):
                        # MenuExport format - array of menus
                        menus = json_data
                    elif isinstance(json_data, dict) and 'menus' in json_data:
                        # MenuExportV2 format - object with menus array
                        menus = json_data.get('menus', [])
                    else:
                        self.logger.warning(f"Unknown format in file {file_path}")
                        continue

                    # Process each menu and its groups
                    for menu in menus:
                        if not isinstance(menu, dict) or not menu.get("guid"):
                            continue

                        menu_guid = menu["guid"]

                        for group in menu.get("groups", []):
                            if not isinstance(group, dict) or not group.get("guid"):
                                continue

                            # Create a copy of the group record
                            group_record = group.copy()

                            # Add parent context
                            group_record["location_id"] = location_id
                            group_record["date"] = date_folder
                            group_record["menu_guid"] = menu_guid

                            # Remove nested objects that will be in their own streams
                            if "items" in group_record:
                                del group_record["items"]
                            if "subgroups" in group_record:
                                del group_record["subgroups"]

                            # Validate primary keys before yielding
                            if self.validate_primary_keys(group_record):
                                record_count += 1
                                yield group_record

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
                    # Continue with next file instead of failing completely
                    continue

            self.logger.info(f"Processed {record_count} group records for location {location_id}, date {date_folder}")

        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return


class MenuItemsStream(JSONSFTPStream):
    """Stream for Toast menu item objects from menu export JSON files.

    This stream extracts all menu item records with full parent context.
    """

    name = "menu_items"
    file_pattern = "MenuExport*.json"
    primary_keys = ["location_id", "date", "menu_guid", "group_guid", "guid"]
    generate_unique_ids = True

    def process_json_files(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process JSON files in the given folder.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Menu item record dictionaries with full parent context.
        """
        folder_path = f"{location_id}/{date_folder}"

        try:
            # Get list of files in the folder
            files = self._sftp_client.list_files(folder_path)

            # Filter files that match our pattern
            matching_files = [f for f in files if fnmatch.fnmatch(f, self.file_pattern)]

            if not matching_files:
                self.logger.info(f"No files matching pattern '{self.file_pattern}' found in {folder_path}")
                return

            record_count = 0
            for file_name in matching_files:
                file_path = f"{folder_path}/{file_name}"
                try:
                    # Get file content
                    json_data = json.loads(self._sftp_client.get_file_content(file_path).decode("utf-8"))

                    # Extract menus based on file format
                    menus = []
                    if isinstance(json_data, list):
                        # MenuExport format - array of menus
                        menus = json_data
                    elif isinstance(json_data, dict) and 'menus' in json_data:
                        # MenuExportV2 format - object with menus array
                        menus = json_data.get('menus', [])
                    else:
                        self.logger.warning(f"Unknown format in file {file_path}")
                        continue

                    # Process each menu, group, and item
                    for menu in menus:
                        if not isinstance(menu, dict) or not menu.get("guid"):
                            continue

                        menu_guid = menu["guid"]

                        for group in menu.get("groups", []):
                            if not isinstance(group, dict) or not group.get("guid"):
                                continue

                            group_guid = group["guid"]

                            for item in group.get("items", []):
                                if not isinstance(item, dict) or not item.get("guid"):
                                    continue

                                # Create a copy of the item record
                                item_record = item.copy()

                                # Add parent context
                                item_record["location_id"] = location_id
                                item_record["date"] = date_folder
                                item_record["menu_guid"] = menu_guid
                                item_record["group_guid"] = group_guid

                                # Remove nested objects that will be in their own streams
                                if "optionGroups" in item_record:
                                    del item_record["optionGroups"]
                                if "prices" in item_record:
                                    del item_record["prices"]

                                # Validate primary keys before yielding
                                if self.validate_primary_keys(item_record):
                                    record_count += 1
                                    yield item_record

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
                    # Continue with next file instead of failing completely
                    continue

            self.logger.info(f"Processed {record_count} item records for location {location_id}, date {date_folder}")

        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return


class MenuOptionGroupsStream(JSONSFTPStream):
    """Stream for Toast menu option group objects from menu export JSON files.

    This stream extracts all option group records with full parent context.
    """

    name = "menu_option_groups"
    file_pattern = "MenuExport*.json"
    primary_keys = ["location_id", "date", "menu_guid", "group_guid", "item_guid", "guid"]
    generate_unique_ids = True

    def process_json_files(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process JSON files in the given folder.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Option group record dictionaries with full parent context.
        """
        folder_path = f"{location_id}/{date_folder}"

        try:
            # Get list of files in the folder
            files = self._sftp_client.list_files(folder_path)

            # Filter files that match our pattern
            matching_files = [f for f in files if fnmatch.fnmatch(f, self.file_pattern)]

            if not matching_files:
                self.logger.info(f"No files matching pattern '{self.file_pattern}' found in {folder_path}")
                return

            record_count = 0
            for file_name in matching_files:
                file_path = f"{folder_path}/{file_name}"
                try:
                    # Get file content
                    json_data = json.loads(self._sftp_client.get_file_content(file_path).decode("utf-8"))

                    # Extract menus based on file format
                    menus = []
                    if isinstance(json_data, list):
                        # MenuExport format - array of menus
                        menus = json_data
                    elif isinstance(json_data, dict) and 'menus' in json_data:
                        # MenuExportV2 format - object with menus array
                        menus = json_data.get('menus', [])
                    else:
                        self.logger.warning(f"Unknown format in file {file_path}")
                        continue

                    # Process each menu, group, item, and option group
                    for menu in menus:
                        if not isinstance(menu, dict) or not menu.get("guid"):
                            continue

                        menu_guid = menu["guid"]

                        for group in menu.get("groups", []):
                            if not isinstance(group, dict) or not group.get("guid"):
                                continue

                            group_guid = group["guid"]

                            for item in group.get("items", []):
                                if not isinstance(item, dict) or not item.get("guid"):
                                    continue

                                item_guid = item["guid"]

                                for option_group in item.get("optionGroups", []):
                                    if not isinstance(option_group, dict) or not option_group.get("guid"):
                                        continue

                                    # Create a copy of the option group record
                                    option_group_record = option_group.copy()

                                    # Add parent context
                                    option_group_record["location_id"] = location_id
                                    option_group_record["date"] = date_folder
                                    option_group_record["menu_guid"] = menu_guid
                                    option_group_record["group_guid"] = group_guid
                                    option_group_record["item_guid"] = item_guid

                                    # Remove nested objects that will be in their own streams
                                    if "items" in option_group_record:
                                        del option_group_record["items"]

                                    # Validate primary keys before yielding
                                    if self.validate_primary_keys(option_group_record):
                                        record_count += 1
                                        yield option_group_record

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
                    # Continue with next file instead of failing completely
                    continue

            self.logger.info(f"Processed {record_count} option group records for location {location_id}, date {date_folder}")

        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return


class MenuOptionItemsStream(JSONSFTPStream):
    """Stream for Toast menu option item objects from menu export JSON files.

    This stream extracts all option item records with full parent context.
    """

    name = "menu_option_items"
    file_pattern = "MenuExport*.json"
    primary_keys = ["location_id", "date", "menu_guid", "group_guid", "item_guid", "option_group_guid", "guid"]
    generate_unique_ids = True

    def process_json_files(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process JSON files in the given folder.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Option item record dictionaries with full parent context.
        """
        folder_path = f"{location_id}/{date_folder}"

        try:
            # Get list of files in the folder
            files = self._sftp_client.list_files(folder_path)

            # Filter files that match our pattern
            matching_files = [f for f in files if fnmatch.fnmatch(f, self.file_pattern)]

            if not matching_files:
                self.logger.info(f"No files matching pattern '{self.file_pattern}' found in {folder_path}")
                return

            record_count = 0
            for file_name in matching_files:
                file_path = f"{folder_path}/{file_name}"
                try:
                    # Get file content
                    json_data = json.loads(self._sftp_client.get_file_content(file_path).decode("utf-8"))

                    # Extract menus based on file format
                    menus = []
                    if isinstance(json_data, list):
                        # MenuExport format - array of menus
                        menus = json_data
                    elif isinstance(json_data, dict) and 'menus' in json_data:
                        # MenuExportV2 format - object with menus array
                        menus = json_data.get('menus', [])
                    else:
                        self.logger.warning(f"Unknown format in file {file_path}")
                        continue

                    # Process each menu, group, item, option group, and option item
                    for menu in menus:
                        if not isinstance(menu, dict) or not menu.get("guid"):
                            continue

                        menu_guid = menu["guid"]

                        for group in menu.get("groups", []):
                            if not isinstance(group, dict) or not group.get("guid"):
                                continue

                            group_guid = group["guid"]

                            for item in group.get("items", []):
                                if not isinstance(item, dict) or not item.get("guid"):
                                    continue

                                item_guid = item["guid"]

                                for option_group in item.get("optionGroups", []):
                                    if not isinstance(option_group, dict) or not option_group.get("guid"):
                                        continue

                                    option_group_guid = option_group["guid"]

                                    for option_item in option_group.get("items", []):
                                        if not isinstance(option_item, dict) or not option_item.get("guid"):
                                            continue

                                        # Create a copy of the option item record
                                        option_item_record = option_item.copy()

                                        # Add parent context
                                        option_item_record["location_id"] = location_id
                                        option_item_record["date"] = date_folder
                                        option_item_record["menu_guid"] = menu_guid
                                        option_item_record["group_guid"] = group_guid
                                        option_item_record["item_guid"] = item_guid
                                        option_item_record["option_group_guid"] = option_group_guid

                                        # Remove nested objects (option items can have their own optionGroups)
                                        if "optionGroups" in option_item_record:
                                            del option_item_record["optionGroups"]

                                        # Validate primary keys before yielding
                                        if self.validate_primary_keys(option_item_record):
                                            record_count += 1
                                            yield option_item_record

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
                    # Continue with next file instead of failing completely
                    continue

            self.logger.info(f"Processed {record_count} option item records for location {location_id}, date {date_folder}")

        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return


class MenuPricesStream(JSONSFTPStream):
    """Stream for Toast menu item price objects from menu export JSON files.

    This stream extracts all price records with full parent context.
    """

    name = "menu_prices"
    file_pattern = "MenuExport*.json"
    primary_keys = ["location_id", "date", "menu_guid", "group_guid", "item_guid", "price_id"]
    generate_unique_ids = True

    def process_json_files(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process JSON files in the given folder.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Price record dictionaries with full parent context.
        """
        folder_path = f"{location_id}/{date_folder}"

        try:
            # Get list of files in the folder
            files = self._sftp_client.list_files(folder_path)

            # Filter files that match our pattern
            matching_files = [f for f in files if fnmatch.fnmatch(f, self.file_pattern)]

            if not matching_files:
                self.logger.info(f"No files matching pattern '{self.file_pattern}' found in {folder_path}")
                return

            record_count = 0
            for file_name in matching_files:
                file_path = f"{folder_path}/{file_name}"
                try:
                    # Get file content
                    json_data = json.loads(self._sftp_client.get_file_content(file_path).decode("utf-8"))

                    # Extract menus based on file format
                    menus = []
                    if isinstance(json_data, list):
                        # MenuExport format - array of menus
                        menus = json_data
                    elif isinstance(json_data, dict) and 'menus' in json_data:
                        # MenuExportV2 format - object with menus array
                        menus = json_data.get('menus', [])
                    else:
                        self.logger.warning(f"Unknown format in file {file_path}")
                        continue

                    # Process each menu, group, item, and price
                    for menu in menus:
                        if not isinstance(menu, dict) or not menu.get("guid"):
                            continue

                        menu_guid = menu["guid"]

                        for group in menu.get("groups", []):
                            if not isinstance(group, dict) or not group.get("guid"):
                                continue

                            group_guid = group["guid"]

                            for item in group.get("items", []):
                                if not isinstance(item, dict) or not item.get("guid"):
                                    continue

                                item_guid = item["guid"]

                                for price_index, price in enumerate(item.get("prices", [])):
                                    if not isinstance(price, dict):
                                        continue

                                    # Create a copy of the price record
                                    price_record = price.copy()

                                    # Add parent context
                                    price_record["location_id"] = location_id
                                    price_record["date"] = date_folder
                                    price_record["menu_guid"] = menu_guid
                                    price_record["group_guid"] = group_guid
                                    price_record["item_guid"] = item_guid

                                    # Generate a unique price_id since prices don't have their own guid
                                    # Use a combination of item_guid and price_index
                                    price_id = f"{item_guid}_{price_index}"
                                    if "guid" in price_record:
                                        price_id = price_record["guid"]
                                    elif "id" in price_record:
                                        price_id = str(price_record["id"])
                                    else:
                                        # Create a hash-based ID from the price data
                                        price_data = f"{item_guid}_{price_index}_{price.get('amount', '')}_{price.get('currency', '')}"
                                        price_id = hashlib.md5(price_data.encode()).hexdigest()[:16]

                                    price_record["price_id"] = price_id

                                    # Validate primary keys before yielding
                                    if self.validate_primary_keys(price_record):
                                        record_count += 1
                                        yield price_record

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
                    # Continue with next file instead of failing completely
                    continue

            self.logger.info(f"Processed {record_count} price records for location {location_id}, date {date_folder}")

        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return
