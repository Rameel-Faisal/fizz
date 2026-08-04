
import requests
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import math

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# where logs get saved
LOG_DIR = Path("data/logs/imports")
ERROR_DIR = Path("data/logs/errors")


# ── Logging setup ─────────────────────────────────────────────────────────────

def get_log_paths(source_name: str) -> tuple:
    """
    Create timestamped log file paths for this import run.
    Returns (import_log_path, error_log_path)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    import_log = LOG_DIR / f"{source_name}_{timestamp}.log"
    error_log = ERROR_DIR / f"{source_name}_{timestamp}_errors.log"
    return import_log, error_log


def write_log(path: Path, message: str):
    """Append a line to a log file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def sanitize_row(row: dict) -> dict:
    """
    Replace NaN float values with None before sending.
    NaN is not valid JSON but None becomes null, which is valid.
    Pulled out into its own function so both post_row() and
    post_rows_bulk() can reuse the same logic.
    """
    return {
        k: (None if isinstance(v, float) and math.isnan(v) else v)
        for k, v in row.items()
    }


# ── Core single-row POST function (fixed) ─────────────────────────────────────

def post_row(table: str, row: dict) -> tuple:
    """
    Send one cleaned row to FastAPI via POST request.

    table  -> API endpoint name e.g. "fiber-types", "market-data"
    row    -> clean dict ready to POST

    Returns (success: bool, message: str)
    """
    url = f"{API_BASE_URL}/{table}"
    clean_row = sanitize_row(row)

    try:
        response = requests.post(
            url,
            json=clean_row,   # FIXED: was `json=row` — NaN values could reach the API
            timeout=10
        )

        if response.status_code == 201:
            response_data = response.json()
            created_id = next(
                (v for k, v in response_data.items() if k.endswith("_id")),
                "?"
            )
            return True, f"inserted (id: {created_id})"

        elif response.status_code == 422:
            errors = response.json().get("detail", "unknown validation error")
            return False, f"validation failed: {errors}"

        elif response.status_code == 404:
            return False, f"endpoint not found: {url}"

        else:
            return False, f"unexpected status {response.status_code}: {response.text}"

    except requests.exceptions.ConnectionError:
        return False, "connection failed — is FastAPI server running?"

    except requests.exceptions.Timeout:
        return False, "request timed out after 10 seconds"

    except Exception as e:
        return False, f"unexpected error: {str(e)}"


# ── NEW: Bulk POST function — one transaction for the whole file ─────────────

def post_rows_bulk(table: str, rows: list, source_name: str) -> dict:
    """
    Send the ENTIRE list of cleaned rows to FastAPI in a single HTTP request,
    hitting a new bulk endpoint (e.g. POST /market-data/bulk).

    The API side wraps this in one database transaction: either every row
    in the batch commits, or none of them do (rollback). This replaces the
    previous behaviour of one commit per row.

    table       -> API endpoint name e.g. "market-data"
    rows        -> list of already-cleaned dicts (post clean_row(), post
                   fiber_id resolution, post skip_categories filtering)
    source_name -> used for log file naming

    Returns summary dict with counts.
    """
    import_log, error_log = get_log_paths(source_name)
    total = len(rows)

    print()
    print(f"  Importing {total} rows to /{table}/bulk (single transaction)")
    print(f"  {'-' * 50}")

    clean_rows = [sanitize_row(row) for row in rows]
    url = f"{API_BASE_URL}/{table}/bulk"
    timestamp = datetime.now().strftime("%H:%M:%S")

    try:
        response = requests.post(url, json=clean_rows, timeout=60)
    except requests.exceptions.ConnectionError:
        message = "connection failed — is FastAPI server running?"
        write_log(import_log, f"[{timestamp}] FAILED (all {total} rows) — {message}")
        write_log(error_log, f"[{timestamp}] Bulk import failed: {message}")
        return _bulk_summary(total, 0, total, import_log, error_log)
    except requests.exceptions.Timeout:
        message = "bulk request timed out after 60 seconds"
        write_log(import_log, f"[{timestamp}] FAILED (all {total} rows) — {message}")
        write_log(error_log, f"[{timestamp}] Bulk import failed: {message}")
        return _bulk_summary(total, 0, total, import_log, error_log)

    if response.status_code == 201:
        # whole batch committed successfully
        log_line = f"[{timestamp}] SUCCESS — all {total} rows inserted in one transaction"
        print(f"  {log_line}")
        write_log(import_log, log_line)
        return _bulk_summary(total, total, 0, import_log, error_log)

    elif response.status_code == 422:
        # validation failed — API rolled back, nothing was inserted
        errors = response.json().get("detail", "unknown validation error")
        log_line = f"[{timestamp}] FAILED — batch rolled back, 0 rows inserted"
        print(f"  {log_line}")
        write_log(import_log, log_line)
        write_log(error_log, f"[{timestamp}] Validation errors:\n{json.dumps(errors, ensure_ascii=False, indent=2)}")
        return _bulk_summary(total, 0, total, import_log, error_log)

    elif response.status_code == 404:
        message = f"endpoint not found: {url} (does the /bulk route exist for this table yet?)"
        print(f"  FAILED — {message}")
        write_log(import_log, f"[{timestamp}] FAILED — {message}")
        write_log(error_log, f"[{timestamp}] {message}")
        return _bulk_summary(total, 0, total, import_log, error_log)

    else:
        message = f"unexpected status {response.status_code}: {response.text}"
        print(f"  FAILED — {message}")
        write_log(import_log, f"[{timestamp}] FAILED — {message}")
        write_log(error_log, f"[{timestamp}] {message}")
        return _bulk_summary(total, 0, total, import_log, error_log)


def _bulk_summary(total, success, failed, import_log, error_log) -> dict:
    print()
    print(f"  {'-' * 50}")
    print(f"  Results: {success} inserted  |  {failed} failed")
    print(f"  Import log: {import_log}")
    if failed > 0:
        print(f"  Error log:  {error_log}")
    print()
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "import_log": str(import_log),
        "error_log": str(error_log) if failed > 0 else None
    }

def post_rows_upsert(table: str, rows: list, source_name: str) -> dict:
    """
    Send the entire cleaned batch to /<table>/upsert instead of /<table>/bulk.
    Each row is inserted if new, or updates the matching existing row if one
    is found (based on that table's natural key). This is what makes
    re-running the same import safe — no duplicate rows on a second run.
    """
    import_log, error_log = get_log_paths(source_name)
    total = len(rows)
    print(f"\n  Upserting {total} rows to /{table}/upsert (single transaction)")
    print(f"  {'-' * 50}")

    clean_rows = [sanitize_row(row) for row in rows]
    url = f"{API_BASE_URL}/{table}/upsert"
    timestamp = datetime.now().strftime("%H:%M:%S")

    try:
        response = requests.post(url, json=clean_rows, timeout=60)
    except requests.exceptions.ConnectionError:
        message = "connection failed — is FastAPI server running?"
        write_log(import_log, f"[{timestamp}] FAILED — {message}")
        return {"total": total, "inserted": 0, "updated": 0, "failed": total,
                "import_log": str(import_log), "error_log": str(error_log)}

    if response.status_code == 200:
        result = response.json()
        log_line = (f"[{timestamp}] SUCCESS — {result['inserted']} inserted, "
                    f"{result['updated']} updated")
        print(f"  {log_line}")
        write_log(import_log, log_line)
        return {"total": total, "inserted": result["inserted"],
                "updated": result["updated"], "failed": 0,
                "import_log": str(import_log), "error_log": None}
    elif response.status_code == 400:
        detail = response.json().get("detail", "unknown error")
        write_log(import_log, f"[{timestamp}] FAILED — {detail}")
        write_log(error_log, f"[{timestamp}] {detail}")
        return {"total": total, "inserted": 0, "updated": 0, "failed": total,
                "import_log": str(import_log), "error_log": str(error_log)}
    else:
        message = f"unexpected status {response.status_code}: {response.text}"
        write_log(import_log, f"[{timestamp}] FAILED — {message}")
        return {"total": total, "inserted": 0, "updated": 0, "failed": total,
                "import_log": str(import_log), "error_log": str(error_log)}


# ── ORIGINAL per-row batch function — kept for optional manual/small imports ──

def post_rows(table: str, rows: list, source_name: str) -> dict:
    """
    Send a list of cleaned rows to FastAPI ONE AT A TIME.
    Kept for small manual imports where per-row commit is acceptable.
    For normal pipeline runs, prefer post_rows_bulk() above.
    """
    import_log, error_log = get_log_paths(source_name)

    success_count = 0
    fail_count = 0
    total = len(rows)

    print()
    print(f"  Importing {total} rows to /{table} (row-by-row)")
    print(f"  {'-' * 50}")

    for i, row in enumerate(rows, start=1):
        success, message = post_row(table, row)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if success:
            success_count += 1
            log_line = f"[{timestamp}] Row {i}/{total} — {message}"
            print(f"  {log_line}")
            write_log(import_log, log_line)
        else:
            fail_count += 1
            log_line = f"[{timestamp}] Row {i}/{total} — FAILED: {message}"
            error_line = f"[{timestamp}] Row {i} FAILED: {message}\n  Data: {json.dumps(row, ensure_ascii=False)}"
            print(f"  {log_line}")
            write_log(import_log, log_line)
            write_log(error_log, error_line)

    print()
    print(f"  {'-' * 50}")
    print(f"  Results: {success_count} inserted  |  {fail_count} failed")
    print(f"  Import log: {import_log}")
    if fail_count > 0:
        print(f"  Error log:  {error_log}")
    print()

    return {
        "total": total,
        "success": success_count,
        "failed": fail_count,
        "import_log": str(import_log),
        "error_log": str(error_log) if fail_count > 0 else None
    }


# ── Connection check ──────────────────────────────────────────────────────────

def check_connection() -> bool:
    """
    Ping the FastAPI server before starting an import.
    Gives a clear error if server is not running.
    """
    try:
        response = requests.get(API_BASE_URL, timeout=5)
        print(f"  Connected to FastAPI at {API_BASE_URL}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"  Cannot connect to FastAPI at {API_BASE_URL}")
        return False
    
    
def get_fiber_id_by_name(fiber_name: str) -> int | None:
    """
    Look up fiber_id from fiber_types table by name.
    Used when importing child tables that need fiber_id.

    "Abaca" → 6
    "Hemp"  → 7
    Returns None if not found.
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/fiber-types?limit=500",
            timeout=10
        )
        if response.status_code == 200:
            fibers = response.json()
            for fiber in fibers:
                if fiber["fiber_type_name"].lower() == fiber_name.lower():
                    return fiber["fiber_id"]
        return None
    except Exception:
        return None    