"""Tests standard tap features using the built-in SDK tests library."""

import datetime

from singer_sdk.testing import get_tap_test_class

from tap_toast_sftp.tap import TapToastSFTP

SAMPLE_CONFIG = {
    "sftp_host": "sftp.toasttab.com",
    "sftp_username": "test-username",
    "sftp_password": "test-password",
    "locations": [{"id": "12345"}, {"id": "67890"}],
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
}


# Run standard built-in tap tests from the SDK:
TestTapToastSFTP = get_tap_test_class(
    tap_class=TapToastSFTP,
    config=SAMPLE_CONFIG,
)


# TODO: Create additional tests as appropriate for your tap.
