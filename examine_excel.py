import pandas as pd
import sys
import io
import os

# Read the Excel file
file_path = 'sample_sftp/201419/20250514/AccountingReport.xls'
print(f"Reading file: {file_path}")

# Read all data to see the structure
df_all = pd.read_excel(file_path, header=None)
print("\nFirst 10 rows of the file (with no header):")
print(df_all.head(10))

# Now read with header at row 3 (0-indexed, so this is the 4th row)
df_with_header = pd.read_excel(file_path, header=3)
print("\nData with header at row 4:")
print(df_with_header.head(10))

# Print column names
print("\nColumn names:")
print(df_with_header.columns.tolist())

# Check if there's data after the header row
print("\nTotal rows in the file:", len(df_all))
print("Total rows with header at row 4:", len(df_with_header))

# Create a sample dataframe with the same structure but with some data
# This will help us test the implementation
sample_data = {
    'From': ['2025-05-14'],
    'To': ['2025-05-14'],
    'Location': ['Test Location'],
    'GL Account': [1001],
    'Description': ['Test Description'],
    'Amount': [123.45]
}
sample_df = pd.DataFrame(sample_data)

print("\nSample data for testing:")
print(sample_df)

# Let's just work with the dataframe directly since we're having issues with Excel writing
# Create a dataframe that simulates what we would get after reading the Excel file with header at row 3
sample_df_with_header = pd.DataFrame({
    'From': ['2025-05-14'],
    'To': ['2025-05-14'],
    'Location': ['Test Location'],
    'GL Account': [1001],
    'Description': ['Test Description'],
    'Amount': [123.45]
})

print("\nSimulated dataframe with header at row 3:")
print(sample_df_with_header)

# Test the transform_field_name function similar to what's in the base.py file
def transform_field_name(field_name):
    """Transform field names to snake_case."""
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

# Transform the column names
transformed_columns = {col: transform_field_name(col) for col in sample_df_with_header.columns}
print("\nTransformed column names:")
print(transformed_columns)

# Apply the transformation to the dataframe
sample_df_with_header.rename(columns=transformed_columns, inplace=True)
print("\nDataframe with transformed column names:")
print(sample_df_with_header)
