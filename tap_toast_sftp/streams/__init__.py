"""Stream classes for tap-toast-sftp."""

from tap_toast_sftp.streams.base import CSVSFTPStream, JSONSFTPStream, XLSSFTPStream
from tap_toast_sftp.streams.accounting_report import AccountingReportStream
from tap_toast_sftp.streams.all_items_report import AllItemsReportStream
from tap_toast_sftp.streams.cash_entries import CashEntriesStream
from tap_toast_sftp.streams.check_details import CheckDetailsStream
from tap_toast_sftp.streams.house_account_export import HouseAccountExportStream
from tap_toast_sftp.streams.item_selection_details import ItemSelectionDetailsStream
from tap_toast_sftp.streams.kitchen_timings import KitchenTimingsStream
from tap_toast_sftp.streams.menu_export import MenuExportStream, MenuExportV2Stream
from tap_toast_sftp.streams.modifiers_selection_details import ModifiersSelectionDetailsStream
from tap_toast_sftp.streams.order_details import OrderDetailsStream
from tap_toast_sftp.streams.payment_details import PaymentDetailsStream
from tap_toast_sftp.streams.time_entries import TimeEntriesStream

__all__ = [
    "CSVSFTPStream",
    "JSONSFTPStream",
    "XLSSFTPStream",
    "AccountingReportStream",
    "AllItemsReportStream",
    "CashEntriesStream",
    "CheckDetailsStream",
    "HouseAccountExportStream",
    "ItemSelectionDetailsStream",
    "KitchenTimingsStream",
    "MenuExportStream",
    "MenuExportV2Stream",
    "ModifiersSelectionDetailsStream",
    "OrderDetailsStream",
    "PaymentDetailsStream",
    "TimeEntriesStream",
]
