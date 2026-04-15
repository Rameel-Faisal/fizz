# data_pipeline/transform.py
#
# Shared cleaning functions for all data sources.
# Each function takes a raw value and returns a clean value.
# Used by import_excel.py when processing each row.

import re
from typing import Optional


# ── Core cleaning functions ───────────────────────────────────────────────────

def nullify_no_source(value) -> Optional[str]:
    """
    Convert placeholder source strings to None.

    "No source provided" → None
    "N/A"               → None
    "-"                 → None
    ""                  → None
    Any real value      → returned as is
    """
    if value is None:
        return None

    cleaned = str(value).strip()

    null_values = [
        "no source provided",
        "n/a",
        "na",
        "-",
        "--",
        "none",
        "not available",
        "unknown",
        ""
    ]

    if cleaned.lower() in null_values:
        return None

    return cleaned


def extract_main_name(value) -> dict:
    """
    Split a fiber name that contains both common name
    and scientific/local name in brackets.

    "Abaca (Manilahanf)"      → {"fiber_type_name": "Abaca",
                                  "scientific_name": "Manilahanf"}

    "Baumwolle (Gossypium)"   → {"fiber_type_name": "Baumwolle",
                                  "scientific_name": "Gossypium"}

    "Hemp"                    → {"fiber_type_name": "Hemp",
                                  "scientific_name": None}
    """
    if value is None:
        return {"fiber_type_name": None, "scientific_name": None}

    value = str(value).strip()

    # check if there is something in brackets
    match = re.match(r"^(.+?)\s*\((.+?)\)$", value)

    if match:
        main_name = match.group(1).strip()
        bracketed = match.group(2).strip()
        return {
            "fiber_type_name": main_name,
            "scientific_name": bracketed
        }

    # no brackets — just return the name as is
    return {
        "fiber_type_name": value,
        "scientific_name": None
    }


def strip_german_prefix(value) -> Optional[str]:
    """
    Strip German label prefixes from temperature and rainfall values.

    "Temperaturprofil: 20-25 °C"       → "20-25 °C"
    "Niederschlagsmengen: 1800-2500 mm" → "1800-2500 mm"
    "Rainfall: 1000 mm"                 → "1000 mm"

    Works by removing everything before and including the first colon.
    """
    if value is None:
        return None

    value = str(value).strip()

    if ":" in value:
        # take everything after the first colon
        after_colon = value.split(":", 1)[1].strip()
        return after_colon if after_colon else None

    return value


def strip_method_prefix(value) -> Optional[str]:
    """
    Strip the "Method: " prefix from processing method values.

    "Method: mechanischer Aufschluss"  → "mechanischer Aufschluss"
    "Method: Mechanischer Aufschluss"  → "Mechanischer Aufschluss"
    "mechanischer Aufschluss"          → "mechanischer Aufschluss"
    """
    if value is None:
        return None

    value = str(value).strip()

    # remove "Method: " prefix case insensitive
    if value.lower().startswith("method:"):
        return value[7:].strip()

    return value


def clean_string(value) -> Optional[str]:
    """
    Basic string cleaning used on all text fields.

    Strips whitespace, fixes encoding artifacts,
    returns None for empty strings.
    """
    if value is None:
        return None

    cleaned = str(value).strip()

    # fix common encoding artifacts from German files
    cleaned = cleaned.replace("\xa0", " ")  # non-breaking space
    cleaned = cleaned.replace("\u200b", "")  # zero width space

    return cleaned if cleaned else None


def parse_number(value) -> Optional[float]:
    """
    Convert string numbers to float.
    Handles German number format (comma as decimal separator).

    "1.200,50"  → 1200.50   (German format)
    "1200.50"   → 1200.50   (English format)
    "1200"      → 1200.0
    "N/A"       → None
    ""          → None
    """
    if value is None:
        return None

    value = str(value).strip()

    if not value or value.lower() in ["n/a", "na", "-", "none"]:
        return None

    # detect German format: has both dot and comma
    # German: 1.200,50 (dot = thousands, comma = decimal)
    if "," in value and "." in value:
        # remove thousand separators (dots) then replace comma with dot
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        # only comma — treat as decimal separator
        value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        return None


# ── Cleaning dispatcher ───────────────────────────────────────────────────────

# Maps cleaning rule names (used in config.py) to actual functions
CLEANING_FUNCTIONS = {
    "extract_main_name":    extract_main_name,
    "strip_german_prefix":  strip_german_prefix,
    "strip_method_prefix":  strip_method_prefix,
    "nullify_no_source":    nullify_no_source,
    "clean_string":         clean_string,
    "parse_number":         parse_number,
}


def apply_cleaning(value, rule: str):
    """
    Apply a named cleaning rule to a value.
    Used by import_excel.py when processing each row.

    value  → the raw cell value from the file
    rule   → the cleaning rule name from config.py
    """
    if rule not in CLEANING_FUNCTIONS:
        raise ValueError(
            f"Unknown cleaning rule: '{rule}'\n"
            f"Available rules: {list(CLEANING_FUNCTIONS.keys())}"
        )

    return CLEANING_FUNCTIONS[rule](value)


def clean_row(row: dict, column_mapping: dict, cleaning_rules: dict) -> dict:
    """
    Process one raw row from a file into a clean API-ready dict.

    row             → raw row from pandas (column names from file)
    column_mapping  → maps file columns to API fields (from config.py)
    cleaning_rules  → maps file columns to cleaning functions (from config.py)

    Returns a clean dict ready to POST to FastAPI.
    """
    cleaned = {}

    for file_col, api_field in column_mapping.items():

        # get raw value from the row
        raw_value = row.get(file_col)

        # apply cleaning rule if one exists for this column
        if file_col in cleaning_rules:
            rule = cleaning_rules[file_col]
            result = apply_cleaning(raw_value, rule)

            # extract_main_name returns a dict with two fields
            # handle this special case
            if isinstance(result, dict):
                cleaned.update(result)
            else:
                cleaned[api_field] = result

        else:
            # no cleaning rule — just clean whitespace
            cleaned[api_field] = clean_string(raw_value)

    return cleaned