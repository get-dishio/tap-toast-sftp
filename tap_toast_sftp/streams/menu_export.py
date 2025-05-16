"""Menu Export stream classes for tap-toast-sftp."""

from __future__ import annotations

from tap_toast_sftp.streams.base import JSONSFTPStream


class MenuExportStream(JSONSFTPStream):
    """Stream for Toast menu export data from JSON files."""

    name = "menu_export"
    file_pattern = "MenuExport_*.json"
    primary_keys = ["location_id", "date"]
    generate_unique_ids = True

    def process_json_files(self, location_id, date_folder, folder_path):
        """Process JSON files in the given folder.

        This overrides the base implementation to handle the list format of MenuExport files.

        Args:
            location_id: The location ID.
            date_folder: The date folder name.
            folder_path: The path to the folder containing the files.

        Yields:
            Record-type dictionary objects.
        """
        try:
            # Get list of files matching the pattern
            file_paths = self._sftp_client.list_files(folder_path, self.file_pattern)

            for file_path in file_paths:
                try:
                    # Get file content
                    json_data = self._sftp_client.get_json_file(file_path)

                    # Handle list format (MenuExport files contain a list of menus)
                    if isinstance(json_data, list):
                        for menu in json_data:
                            # Add location_id and date to the record
                            menu["location_id"] = location_id
                            menu["date"] = date_folder

                            # Validate primary keys before yielding
                            if self.validate_primary_keys(menu):
                                yield menu
                    else:
                        # Handle object format (single menu)
                        json_data["location_id"] = location_id
                        json_data["date"] = date_folder

                        # Validate primary keys before yielding
                        if self.validate_primary_keys(json_data):
                            yield json_data

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
                    # Continue with next file instead of failing completely
                    continue
        except Exception as e:
            self.logger.error(f"Error processing folder {folder_path} for location {location_id}: {e}")
            # Return empty generator instead of raising an exception
            return

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
