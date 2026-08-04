import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_pipeline.api_client import check_connection, post_rows_upsert, get_fiber_id_by_name

import argparse
from pathlib import Path


# ── Action: inspect ───────────────────────────────────────────────────────────

def action_inspect(filepath: str):
    from data_pipeline.inspect_data import inspect
    inspect(filepath)


# ── Action: list-sources ──────────────────────────────────────────────────────

def action_list_sources():
    from data_pipeline.config import list_sources
    sources = list_sources()

    print()
    print("  Configured sources in data_pipeline/config.py:")
    print(f"  {'─' * 40}")
    for source in sources:
        print(f"  → {source}")
    print()


# ── Helper: apply filters ─────────────────────────────────────────────────────

def apply_filters(raw_rows: list, mapping: dict) -> list:
    """
    Filter rows based on config filters before cleaning.
    Removes rows that don't match the required values.
    """
    filters = mapping.get("filters", {})

    if not filters:
        return raw_rows  # no filters defined — return all rows

    filtered = []
    skipped = 0

    strucpro_filter = filters.get("strucpro")
    crops_exclude = filters.get("crops_exclude", [])

    for row in raw_rows:

        # filter by strucpro — only keep matching measurement type
        if strucpro_filter:
            row_strucpro = row.get("strucpro", "")
            if row_strucpro != strucpro_filter:
                skipped += 1
                continue

        # skip excluded crop categories
        row_crop = row.get("crops", "")
        if row_crop in crops_exclude:
            skipped += 1
            continue

        # skip rows with no value
        if row.get("OBS_VALUE") is None:
            skipped += 1
            continue

        filtered.append(row)

    print(f"  Rows after filtering: {len(filtered)} kept, {skipped} skipped")
    return filtered


# ── Helper: move to processed ─────────────────────────────────────────────────

def move_to_processed(filepath: str):
    source = Path(filepath)
    destination = Path("data/processed") / source.name
    try:
        source.rename(destination)
        print(f"  📁 File moved to data/processed/{source.name}")
    except Exception as e:
        print(f"  ⚠ Could not move file to processed: {e}")


# ── Action: import ────────────────────────────────────────────────────────────

def action_import(filepath: str, source_name: str):
    from data_pipeline.api_client import check_connection, post_rows_upsert, get_fiber_id_by_name
    from data_pipeline.config import get_mapping
    from data_pipeline.transform import clean_row
    from data_pipeline.sources.import_excel import load_and_map

    print()
    print("=" * 60)
    print("  FIZZ DATA PIPELINE")
    print("=" * 60)
    print(f"  File:   {filepath}")
    print(f"  Source: {source_name}")

    # ── Step 1: check FastAPI is running ──────────────────────
    print()
    print("  Step 1 — Checking FastAPI connection...")
    connected = check_connection()
    if not connected:
        print()
        print("  ❌ Import cancelled — start FastAPI first:")
        print("     uvicorn app.main:app --reload")
        sys.exit(1)

    # ── Step 2: get mapping from config ───────────────────────
    print()
    print("  Step 2 — Loading column mapping from config...")
    try:
        mapping = get_mapping(source_name)
    except ValueError as e:
        print(f"  ❌ {e}")
        sys.exit(1)

    table = mapping["table"]
    column_mapping = mapping["columns"]
    cleaning_rules = mapping.get("cleaning", {})
    fiber_name_map = mapping.get("fiber_name_map", {})
    skip_categories = mapping.get("skip_categories", [])
    config_source = mapping.get("source")

    print(f"  Target table: /{table}")
    print(f"  Columns mapped: {len(column_mapping)}")

    # ── Step 3: load file ─────────────────────────────────────
    print()
    print("  Step 3 — Loading and cleaning file...")
    try:
        raw_rows = load_and_map(filepath)
    except Exception as e:
        print(f"  ❌ Failed to load file: {e}")
        sys.exit(1)

    # apply filters from config before cleaning
    raw_rows = apply_filters(raw_rows, mapping)

    # ── Step 4: clean every row ───────────────────────────────
    clean_rows = []
    skipped = 0

    for i, row in enumerate(raw_rows, start=1):
        try:
            cleaned = clean_row(row, column_mapping, cleaning_rules)

            # if row has fiber_type_name but no fiber_id
            # look up the fiber_id automatically
            if "fiber_type_name" in cleaned and "fiber_id" not in cleaned:

                fiber_name = cleaned.pop("fiber_type_name")
                cleaned.pop("scientific_name", None)

                # skip non-fiber categories defined in config
                if fiber_name in skip_categories:
                    skipped += 1
                    continue

                # apply fiber name map if one exists in config
                # e.g. "Hemp" → "Hanf" for Eurostat data

                if fiber_name in fiber_name_map:
                    fiber_name = fiber_name_map[fiber_name]
                    # if mapped to None — skip this row entirely
                    if fiber_name is None:
                        skipped += 1
                        continue

                # look up fiber_id from fiber_types table
                fiber_id = get_fiber_id_by_name(fiber_name)

                if fiber_id:
                    cleaned["fiber_id"] = fiber_id
                else:
                    print(f"  ⚠ Row {i} skipped — '{fiber_name}' not found in fiber_types table")
                    skipped += 1
                    continue

            # inject all fixed fields from config
            fixed_fields = mapping.get("fixed_fields", {})
            for field, value in fixed_fields.items():
                if field not in cleaned:
                    cleaned[field] = value

            clean_rows.append(cleaned)

        except Exception as e:
            print(f"  ⚠ Row {i} skipped during cleaning: {e}")
            skipped += 1

    print(f"  Rows loaded:   {len(raw_rows)}")
    print(f"  Rows cleaned:  {len(clean_rows)}")
    print(f"  Rows skipped:  {skipped}")

    if not clean_rows:
        print()
        print("  ❌ No rows to import after cleaning.")
        sys.exit(1)

    # ── Step 5: post to FastAPI (UPSERT — insert new, update existing) ───────
    print()
    print("  Step 4 — Upserting to FastAPI...")
    summary = post_rows_upsert(
        table=table,
        rows=clean_rows,
        source_name=source_name
    )

    # ── Step 6: move file to processed ────────────────────────
    if summary["failed"] == 0:
        move_to_processed(filepath)

    # ── Final summary ─────────────────────────────────────────
    print("=" * 60)
    print("  IMPORT COMPLETE")
    print(f"  Total:     {summary['total']}")
    print(f"  Inserted:  {summary['inserted']} ✅")
    print(f"  Updated:   {summary['updated']} 🔄")
    print(f"  Failed:    {summary['failed']} ❌")
    if summary["error_log"]:
        print(f"  Errors:    {summary['error_log']}")
    print("=" * 60)
    print()


# ── Argument parser ───────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Fizz Data Pipeline",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["inspect", "import", "list-sources"],
        help=(
            "inspect      → profile a raw file\n"
            "import       → import a file into PostgreSQL\n"
            "list-sources → show all configured source names"
        )
    )
    parser.add_argument(
        "--file",
        help="Path to the raw file"
    )
    parser.add_argument(
        "--source",
        help="Source name from config.py"
    )
    return parser.parse_args()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    if args.action == "inspect":
        if not args.file:
            print("ERROR: --file is required for inspect")
            sys.exit(1)
        action_inspect(args.file)

    elif args.action == "list-sources":
        action_list_sources()

    elif args.action == "import":
        if not args.file:
            print("ERROR: --file is required for import")
            sys.exit(1)
        if not args.source:
            print("ERROR: --source is required for import")
            print("Run this to see available sources:")
            print("python -m data_pipeline.run_pipeline --action list-sources")
            sys.exit(1)
        action_import(args.file, args.source)


if __name__ == "__main__":
    main()