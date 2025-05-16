"""ToastSFTP tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_toast_sftp import streams
from tap_toast_sftp.client import SFTPClient


class TapToastSFTP(Tap):
    """ToastSFTP tap class."""

    name = "tap-toast-sftp"

    # Shared SFTP client for all streams
    _shared_sftp_client = None

    config_jsonschema = th.PropertiesList(
        th.Property(
            "sftp_host",
            th.StringType(nullable=False),
            required=True,
            title="SFTP Host",
            description="The hostname or IP address of the SFTP server",
        ),
        th.Property(
            "sftp_username",
            th.StringType(nullable=False),
            required=True,
            title="SFTP Username",
            description="The username to authenticate with the SFTP server",
        ),
        th.Property(
            "sftp_private_key",
            th.StringType(nullable=True),
            required=False,
            secret=True,  # Flag config as protected
            title="SFTP Private SSH Key",
            description="The private SSH key to authenticate with the SFTP server (either this or password is required)",
        ),
        th.Property(
            "sftp_password",
            th.StringType(nullable=True),
            required=False,
            secret=True,  # Flag config as protected
            title="SFTP Password",
            description="The password to authenticate with the SFTP server (either this or private key is required)",
        ),
        th.Property(
            "sftp_port",
            th.IntegerType(nullable=True),
            required=False,
            default=22,
            title="SFTP Port",
            description="The port of the SFTP server (default: 22)",
        ),
        th.Property(
            "locations",
            th.ArrayType(
                th.ObjectType(
                    th.Property(
                        "id",
                        th.StringType(nullable=False),
                        required=True,
                        description="Location ID",
                    ),
                )
            ),
            required=True,
            title="Location IDs",
            description="List of location IDs to extract data for",
        ),
        th.Property(
            "start_date",
            th.DateTimeType(nullable=True),
            description="The earliest record date to sync",
        ),
    ).to_dict()

    def get_shared_sftp_client(self):
        """Get or create a shared SFTP client for all streams.

        Returns:
            A shared SFTPClient instance.
        """
        if self._shared_sftp_client is None:
            self.logger.info("Creating shared SFTP client for all streams")
            self._shared_sftp_client = SFTPClient(self.config)
            self._shared_sftp_client.connect()
        return self._shared_sftp_client

    def discover_streams(self) -> list:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        # Get the shared SFTP client
        shared_client = self.get_shared_sftp_client()

        return [
            streams.AccountingReportStream(self, shared_sftp_client=shared_client),
            streams.AllItemsReportStream(self, shared_sftp_client=shared_client),
            streams.CashEntriesStream(self, shared_sftp_client=shared_client),
            streams.CheckDetailsStream(self, shared_sftp_client=shared_client),
            streams.HouseAccountExportStream(self, shared_sftp_client=shared_client),
            streams.ItemSelectionDetailsStream(self, shared_sftp_client=shared_client),
            streams.KitchenTimingsStream(self, shared_sftp_client=shared_client),
            streams.MenuExportStream(self, shared_sftp_client=shared_client),
            streams.MenuExportV2Stream(self, shared_sftp_client=shared_client),
            # Child streams for MenuExport
            streams.MenuMenusStream(self, shared_sftp_client=shared_client),
            streams.MenuGroupsStream(self, shared_sftp_client=shared_client),
            streams.MenuGroupItemsStream(self, shared_sftp_client=shared_client),
            # Child streams for MenuExportV2
            streams.MenuV2MenusStream(self, shared_sftp_client=shared_client),
            streams.MenuV2GroupsStream(self, shared_sftp_client=shared_client),
            streams.MenuV2ItemsStream(self, shared_sftp_client=shared_client),
            streams.MenuV2OptionGroupsStream(self, shared_sftp_client=shared_client),
            streams.MenuV2OptionItemsStream(self, shared_sftp_client=shared_client),
            streams.MenuV2PremodifierGroupsStream(self, shared_sftp_client=shared_client),
            streams.MenuV2PremodifierItemsStream(self, shared_sftp_client=shared_client),
            streams.ModifiersSelectionDetailsStream(self, shared_sftp_client=shared_client),
            streams.OrderDetailsStream(self, shared_sftp_client=shared_client),
            streams.PaymentDetailsStream(self, shared_sftp_client=shared_client),
            streams.TimeEntriesStream(self, shared_sftp_client=shared_client),
        ]

    def sync_all(self):
        """Sync all streams."""
        try:
            # Use the standard sync_all method
            super().sync_all()
        finally:
            # Clear any cached file content
            if self._shared_sftp_client:
                self.logger.info("Clearing file content cache")
                self._shared_sftp_client.clear_file_cache()

            # Ensure the shared SFTP client is closed when done
            self.close_shared_sftp_client()

    def close_shared_sftp_client(self):
        """Close the shared SFTP client if it exists."""
        if self._shared_sftp_client is not None:
            self.logger.info("Closing shared SFTP client")
            self._shared_sftp_client.disconnect()
            self._shared_sftp_client = None


if __name__ == "__main__":
    TapToastSFTP.cli()
