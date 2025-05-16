"""ToastSFTP tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

# TODO: Import your custom stream types here:
from tap_toast_sftp import streams


class TapToastSFTP(Tap):
    """ToastSFTP tap class."""

    name = "tap-toast-sftp"

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

    def discover_streams(self) -> list:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.AccountingReportStream(self),
            streams.AllItemsReportStream(self),
            streams.CashEntriesStream(self),
            streams.CheckDetailsStream(self),
            streams.HouseAccountExportStream(self),
            streams.ItemSelectionDetailsStream(self),
            streams.KitchenTimingsStream(self),
            streams.MenuExportStream(self),
            streams.MenuExportV2Stream(self),
            streams.ModifiersSelectionDetailsStream(self),
            streams.OrderDetailsStream(self),
            streams.PaymentDetailsStream(self),
            streams.TimeEntriesStream(self),
        ]


if __name__ == "__main__":
    TapToastSFTP.cli()
