"""Accounting Report stream class for tap-toast-sftp."""

from __future__ import annotations

import io
import pandas as pd
import typing as t

from tap_toast_sftp.streams.base import XLSSFTPStream


class AccountingReportStream(XLSSFTPStream):
    """Stream for Toast accounting report data from Excel files."""

    name = "accounting_report"
    file_name = "AccountingReport.xls"
    primary_keys = ["location_id", "date", "gl_account"]

    def transform_field_name(self, field_name: str) -> str:
        """Transform field names to snake_case.

        Args:
            field_name: The original field name.

        Returns:
            The transformed field name in snake_case.
        """
        # Replace spaces and special characters with underscores
        transformed = field_name.lower().replace(' ', '_').replace('-', '_')

        # Replace special characters with descriptive names
        transformed = transformed.replace('%', 'pct').replace('#', 'num')

        # Remove question marks (e.g., "void?" becomes "void")
        transformed = transformed.replace('?', '')

        # Replace parentheses and other special characters with underscores
        transformed = transformed.replace('(', '').replace(')', '').replace('/', '_')

        # Remove any duplicate underscores
        while '__' in transformed:
            transformed = transformed.replace('__', '_')

        # Remove leading and trailing underscores
        transformed = transformed.strip('_')

        return transformed

    def process_excel_file(self, location_id: str, date_folder: str) -> t.Iterable[dict]:
        """Process a single Excel file, skipping the first 3 rows.

        The AccountingReport.xls file has the following structure:
        - Row 1: "Accounting Export" and "Generated <date> <time>"
        - Row 2: Date range
        - Row 3: Empty row
        - Row 4: Headers (From, To, Location, GL Account, Description, Amount)
        - Row 5+: Data rows

        Args:
            location_id: The location ID.
            date_folder: The date folder name.

        Yields:
            Record-type dictionary objects.
        """
        file_path = f"/{location_id}/{date_folder}/{self.file_name}"
        self.logger.info(f"Processing file {file_path} for location {location_id}, date {date_folder}")

        try:
            with self.sftp_client as client:
                content = client.get_file_content(file_path)

                # Create a BytesIO object from the content
                excel_data = io.BytesIO(content)

                # Read the Excel file into a pandas DataFrame, skipping the first 3 rows
                # The 4th row (index 3) contains the headers
                df = pd.read_excel(excel_data, sheet_name=self.sheet_name, header=3)

                # Convert DataFrame to records
                records = df.to_dict(orient="records")

                # Process records in batches
                batch = []
                for record in records:
                    # Convert NaN values to None and transform field names to snake_case
                    transformed_record = {
                        self.transform_field_name(k): (None if pd.isna(v) else v)
                        for k, v in record.items()
                    }
                    # Add location_id and date to the record
                    transformed_record["location_id"] = location_id
                    transformed_record["date"] = date_folder

                    batch.append(transformed_record)

                    # Yield batch when it reaches the batch size
                    if len(batch) >= self.batch_size:
                        for rec in batch:
                            yield rec
                        batch = []

                # Yield any remaining records
                for record in batch:
                    yield record

        except Exception as e:
            self.logger.error(f"Error processing file {file_path} for location {location_id}, date {date_folder}: {e}")
