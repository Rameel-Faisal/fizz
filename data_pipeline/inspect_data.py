# data_pipeline/inspect_data.py
# PURPOSE: Profile raw data BEFORE touching the database.
# RUN WITH: python -m data_pipeline.inspect_data

import pandas as pd

RAW_FILE = "data/raw/cleaned_fibers_data.xlsx"

def inspect_file(path: str) -> None:
    print("=" * 60)
    print(f"PROFILING: {path}")
    print("=" * 60)

    xl = pd.ExcelFile(path)
    print(f"\nSheets found: {xl.sheet_names}\n")

    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)

        print(f"\n{'─' * 60}")
        print(f"SHEET: '{sheet}'")
        print(f"  Rows: {df.shape[0]}  |  Columns: {df.shape[1]}")

        print("\n  Column names and types:")
        for col, dtype in df.dtypes.items():
            print(f"    {col:<35} {str(dtype)}")

        missing = df.isnull().sum()
        missing_cols = missing[missing > 0]
        if missing_cols.empty:
            print("\n  Missing values: none")
        else:
            print("\n  Missing values:")
            for col, count in missing_cols.items():
                pct = (count / len(df)) * 100
                print(f"    {col:<35} {count} missing ({pct:.1f}%)")

        print("\n  First 3 rows:")
        print(df.head(3).to_string(index=False))

    print("\n" + "=" * 60)
    print("DONE")

if __name__ == "__main__":
    inspect_file(RAW_FILE)
    