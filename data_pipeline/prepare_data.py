from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from data_pipeline.config import get_mapping
from data_pipeline.transform import clean_row

CULTIVATION_ORDER = [
    'fiber_type_name', 'country', 'region', 'year', 'soil_type',
    'farming_method', 'measurement_type', 'measurement_value',
    'measurement_unit', 'source',
]
SUPPORTED_FILTERS = {'strucpro', 'crops_exclude', 'element_keep'}


def _plain(value: Any) -> Any:
    """Make a pandas/numpy value safe for CSV and JSON."""
    if value is None:
        return None
    if isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, 'item'):
        try:
            return _plain(value.item())
        except (AttributeError, TypeError, ValueError):
            pass
    return str(value)


def _read_rows(path: Path, mapping: dict) -> list[tuple[int, dict]]:
    """Returns (Excel/CSV row number, values) without editing the input."""
    source_options = mapping.get('input', {})
    sheet = source_options.get('sheet_name', 0)
    header = source_options.get('header', 0)
    if path.suffix.lower() == '.csv':
        try:
            frame = pd.read_csv(path, header=header, keep_default_na=False,
                                dtype=object, encoding='utf-8-sig')
        except UnicodeDecodeError:
            frame = pd.read_csv(path, header=header, keep_default_na=False,
                                dtype=object, encoding='latin-1')
    elif path.suffix.lower() in {'.xlsx', '.xls'}:
        frame = pd.read_excel(path, sheet_name=sheet, header=header,
                              keep_default_na=False, dtype=object)
    else:
        raise ValueError(f'Unsupported input extension: {path.suffix}')
    if frame.empty:
        raise ValueError('No input rows found; verify sheet name and header.')
    if frame.columns.duplicated().any():
        raise ValueError('Duplicate column names in source; fix the sheet/header config.')
    # User's current inspector/importer use pandas; this follows the same convention.
    # For header=None, the first row is physical row 1; for header=0, row 1 is a header.
    row_start = 1 if header is None else int(header) + 2
    return [(row_start + i, {k: _plain(v) for k, v in record.items()})
            for i, record in enumerate(frame.to_dict(orient='records'))]


def _get_column(row: dict, selector: Any) -> Any:
    """Column selector is a zero-based index with header=None, or a header name."""
    if isinstance(selector, int):
        return row.get(selector)
    return row.get(selector)


def _year(value: Any) -> int | None:
    if value is None or str(value).strip() in {'', '.', '-', '–', '—'}:
        return None
    try:
        y = float(str(value).strip())
    except (ValueError, TypeError):
        return None
    if not math.isfinite(y) or y != int(y):
        return None
    return int(y) if 1900 <= int(y) <= 2100 else None


def _missing(value: Any, markers: list[str]) -> bool:
    return value is None or str(value).strip().lower() in {
        s.strip().lower() for s in markers
    }


def _flatten(rows: list[tuple[int, dict]], mapping: dict, exceptions: list[dict]) -> list[tuple[int, dict]]:
    """Config-driven wide-to-long reshaping for BMEL-style statistical tables."""
    options = mapping.get('unpivot')
    if not options:
        return rows
    year_col = options['year_column']
    metrics = options['measurements']
    missing_markers = options.get('missing_markers', ['', '.', '-', '–', '—'])
    result = []
    observations = 0
    for physical_row, row in rows:
        year = _year(_get_column(row, year_col))
        if year is None:
            # Headings and footnotes are not numeric year rows.
            continue
        observations += 1
        for spec in metrics:
            raw_value = _get_column(row, spec['source_column'])
            if _missing(raw_value, missing_markers):
                exceptions.append({
                    'row': physical_row, 'type': 'missing_source_value',
                    'fiber': spec['fiber_type_name'], 'year': year,
                    'metric': spec['measurement_type'],
                    'raw_value': str(raw_value),
                    'reason': 'Not reported; never convert to zero. Check source footnote.',
                })
                continue
            result.append((physical_row, {
                'fiber_type_name': spec['fiber_type_name'],
                'year': year,
                'measurement_type': spec['measurement_type'],
                'measurement_value': raw_value,
                'measurement_unit': spec['measurement_unit'],
            }))
    if observations == 0:
        raise ValueError('No year rows found. Check input sheet and unpivot.year_column.')
    return result


def _year_from_header(value: Any) -> tuple[int | None, str]:
    """Read spreadsheet year headers such as 2024, '2024 1)', '2025 2)'."""
    raw = str(value).strip()
    match = re.fullmatch(r'(\d{4})(?:\s+(.*))?', raw)
    if not match:
        return None, ''
    year = int(match.group(1))
    if not 1900 <= year <= 2100:
        return None, ''
    return year, (match.group(2) or '').strip()


def _flatten_year_columns(rows: list[tuple[int, dict]], mapping: dict,
                          exceptions: list[dict]) -> tuple[list[tuple[int, dict]], dict]:
    """Turn wide year columns into observations, optionally across many sections.

    Single-series format (year_columns with category_value, header_row, etc.)
    stays compatible with v2. A new year_columns.series list handles distinct
    sections (such as seed total and certified-only), without hardcoding BMEL.
    Each series can specify first_data_row/last_data_row to disambiguate repeated
    category names and validate an expected_unit in a unit_column.
    """
    cfg = mapping['year_columns']
    multi = 'series' in cfg
    specs = cfg['series'] if multi else [cfg]
    if not isinstance(specs, list) or not specs:
        raise ValueError('year_columns.series must be a nonempty list')

    observations: list[tuple[int, dict]] = []
    all_series_info: list[dict] = []

    for series_index, spec in enumerate(specs, start=1):
        hdr_num = int(spec['header_row'])  # physical Excel row (1-based)
        header_row = next((row for n, row in rows if n == hdr_num), None)
        if header_row is None:
            raise ValueError(f'Series {series_index}: year header row {hdr_num} not found')
        target = str(spec['category_value']).strip().casefold()
        cat_col = spec['category_column']
        first_data_row = int(spec.get('first_data_row', hdr_num + 1))
        last_data_row = int(spec.get('last_data_row', max(n for n, _ in rows)))
        if last_data_row < first_data_row:
            raise ValueError(f'Series {series_index}: invalid data row range')
        matches = [(n, row) for n, row in rows
                   if first_data_row <= n <= last_data_row
                   and str(_get_column(row, cat_col) or '').strip().casefold() == target]
        if len(matches) != 1:
            raise ValueError(f'Series {series_index}: expected exactly one '
                             f'{spec["category_value"]!r} row in Excel rows '
                             f'{first_data_row}–{last_data_row}, found {len(matches)}')
        physical_row, category_row = matches[0]
        if 'unit_column' in spec and 'expected_unit' in spec:
            unit = str(_get_column(category_row, spec['unit_column']) or '').strip()
            if unit.casefold() != str(spec['expected_unit']).strip().casefold():
                raise ValueError(f'Series {series_index}: expected unit '
                                 f'{spec["expected_unit"]!r}, got {unit!r}')

        start = int(spec['first_year_column'])
        end = int(spec['last_year_column'])
        if end < start:
            raise ValueError(f'Series {series_index}: invalid year-column range')
        missing_markers = spec.get('missing_markers',
                                   cfg.get('missing_markers', ['', '.', '-', '–', '—']))
        status_map = spec.get('status_flag_map', cfg.get('status_flag_map', {}))
        series_flags, years_seen = {}, set()
        before = len(observations)
        missing_count = 0

        for col in range(start, end + 1):
            year, raw_flag = _year_from_header(_get_column(header_row, col))
            if year is None:
                raise ValueError(f'Series {series_index}: invalid year heading in '
                                 f'Excel column {col+1}: {_get_column(header_row, col)!r}')
            if year in years_seen:
                raise ValueError(f'Series {series_index}: duplicate year {year}')
            years_seen.add(year)
            if raw_flag:
                if raw_flag not in status_map:
                    raise ValueError(f'Series {series_index}: unrecognized year flag '
                                     f'{raw_flag!r} in {year}')
                series_flags[str(year)] = {'marker': raw_flag, 'meaning': status_map[raw_flag]}
            raw_value = _get_column(category_row, col)
            if _missing(raw_value, missing_markers):
                missing_count += 1
                exceptions.append({
                    'row': physical_row, 'type': 'missing_source_value',
                    'year': year, 'fiber': spec['fiber_type_name'],
                    'metric': spec['measurement_type'], 'raw_value': str(raw_value),
                    'reason': 'Not reported; not zero. Preserve original source symbol.',
                })
                continue
            observations.append((physical_row, {
                'fiber_type_name': spec['fiber_type_name'],
                'year': year,
                'measurement_type': spec['measurement_type'],
                'measurement_value': raw_value,
                'measurement_unit': spec['measurement_unit'],
                '__fizz_value_multiplier': spec.get('value_multiplier',
                                                     cfg.get('value_multiplier', 1)),
            }))
        all_series_info.append({
            'original_category': spec['category_value'],
            'measurement_type': spec['measurement_type'],
            'source_row_number': physical_row,
            'original_unit': spec.get('original_unit', cfg.get('original_unit')),
            'conversion_multiplier': spec.get('value_multiplier', cfg.get('value_multiplier', 1)),
            'year_statuses': series_flags,
            'years_found': sorted(years_seen),
            'prepared_candidate_rows': len(observations) - before,
            'missing_observations': missing_count,
        })

    if multi:
        metadata = {'series': all_series_info, 'source_notes': mapping.get('source_notes', [])}
    else:
        # Preserve the report shape from v2 for the earlier 3071310 mapping.
        info = all_series_info[0]
        metadata = {
            'original_category': info['original_category'],
            'original_unit': info['original_unit'],
            'conversion_multiplier': info['conversion_multiplier'],
            'year_statuses': info['year_statuses'],
            'source_notes': mapping.get('source_notes', []),
            'source_row_number': info['source_row_number'],
        }
    return observations, metadata




def _normalize_space_grouped_number(value: Any) -> Any:
    """Normalize valid space-grouped numeric strings only when explicitly configured.

    E.g. '21 942' -> '21942', '1\u00a0498\u00a0027' -> '1498027'.
    A malformed grouping is rejected, never silently converted to a missing value.
    """
    if not isinstance(value, str):
        return value
    raw = value.strip()
    if not re.search(r'[ \u00a0\u202f]', raw):
        return raw
    # Do not confuse spaces in a number with a decimal separator.
    if not re.fullmatch(r'[+-]?\d{1,3}(?:[ \u00a0\u202f]\d{3})+(?:[.,]\d+)?', raw):
        raise ValueError(f'Invalid space-grouped numeric value: {value!r}')
    return re.sub(r'[ \u00a0\u202f]', '', raw)


def _flatten_row_sections(rows: list[tuple[int, dict]], mapping: dict,
                          exceptions: list[dict]) -> tuple[list[tuple[int, dict]], dict]:
    """Generic year-in-rows extraction from specified physical table sections.

    A single source may have an area block and a percent block, both with
    their own units and value multipliers. All definitions live in config.py.
    No assumptions about BMEL or fibre categories are made in this function.
    """
    cfg = mapping['row_sections']
    specs = cfg.get('series', [])
    if not isinstance(specs, list) or not specs:
        raise ValueError('row_sections.series must be a nonempty list')
    row_by_number = dict(rows)
    out: list[tuple[int, dict]] = []
    series_info = []
    for index, spec in enumerate(specs, 1):
        start = int(spec['first_data_row'])
        stop = int(spec['last_data_row'])
        if stop < start:
            raise ValueError(f'Row series {index}: invalid row range')
        # Guard against accidentally reading the wrong sheet or shifted rows.
        if 'section_heading_row' in spec:
            heading_row = int(spec['section_heading_row'])
            heading = row_by_number.get(heading_row)
            if heading is None:
                raise ValueError(f'Row series {index}: section heading row missing')
            cell = str(_get_column(heading, spec.get('section_heading_column', 0)) or '').strip()
            if cell != str(spec['section_heading_value']).strip():
                raise ValueError(f'Row series {index}: expected section heading '
                                 f'{spec["section_heading_value"]!r} in row '
                                 f'{heading_row}, got {cell!r}')
        seen_years = set()
        present = 0
        skipped_missing = 0
        year_statuses = {}
        for physical_row in range(start, stop + 1):
            row = row_by_number.get(physical_row)
            if row is None:
                raise ValueError(f'Row series {index}: missing source row {physical_row}')
            raw_year = _get_column(row, spec['year_column'])
            if spec.get('allow_year_footnotes', False):
                year, marker = _year_from_header(raw_year)
                if marker:
                    defined_flags = spec.get('year_status_map', {})
                    if marker not in defined_flags:
                        raise ValueError(f'Row series {index}: unknown year footnote '
                                         f'{marker!r} in Excel row {physical_row}')
                    year_statuses[str(year)] = {'marker': marker, 'meaning': defined_flags[marker]}
            else:
                year = _year(raw_year)
            if year is None:
                raise ValueError(f'Row series {index}: missing/invalid year in Excel row {physical_row}')
            if year in seen_years:
                raise ValueError(f'Row series {index}: duplicate year {year}')
            seen_years.add(year)
            raw_value = _get_column(row, spec['value_column'])
            if _missing(raw_value, spec.get('missing_markers', ['', '.', '-', '–', '—'])):
                skipped_missing += 1
                exceptions.append({
                    'row': physical_row, 'type': 'missing_source_value',
                    'year': year, 'category_name': spec['category_name'],
                    'metric': spec['measurement_type'], 'raw_value': str(raw_value),
                    'reason': 'Source value is missing; do not replace with zero.',
                })
                continue
            # A source may use spaces as thousands separators (e.g. '21 942').
            # This is opt-in so other source-specific number formats stay unchanged.
            if spec.get('value_number_format') == 'space_grouped':
                raw_value = _normalize_space_grouped_number(raw_value)
            elif spec.get('value_number_format', 'standard') != 'standard':
                raise ValueError(f'Unknown value_number_format: {spec.get("value_number_format")!r}')
            out.append((physical_row, {
                'category_name': spec['category_name'],
                'year': year,
                'measurement_type': spec['measurement_type'],
                'measurement_value': raw_value,
                'measurement_unit': spec['measurement_unit'],
                '__fizz_value_multiplier': spec.get('value_multiplier', 1),
            }))
            present += 1
        expected_start, expected_end = spec.get('first_year'), spec.get('last_year')
        if expected_start is not None and min(seen_years) != int(expected_start):
            raise ValueError(f'Row series {index}: unexpected first year {min(seen_years)}')
        if expected_end is not None and max(seen_years) != int(expected_end):
            raise ValueError(f'Row series {index}: unexpected last year {max(seen_years)}')
        series_info.append({
            'original_column': spec.get('original_column'),
            'category_name': spec['category_name'],
            'measurement_type': spec['measurement_type'],
            'original_unit': spec.get('original_unit'),
            'converted_unit': spec['measurement_unit'],
            'conversion_multiplier': spec.get('value_multiplier', 1),
            'source_row_range': [start, stop],
            'years': sorted(seen_years),
            'candidates': present,
            'missing': skipped_missing,
            'year_statuses': year_statuses,
            'value_number_format': spec.get('value_number_format', 'standard'),
        })
    if not out:
        raise ValueError('No observations found in row sections')
    return out, {'series': series_info, 'source_notes': mapping.get('source_notes', [])}

def _filter_reason(row: dict, rules: dict) -> str | None:
    if 'strucpro' in rules and row.get('strucpro') != rules['strucpro']:
        return 'strucpro not selected'
    if 'element_keep' in rules and row.get('Element', row.get('element')) != rules['element_keep']:
        return 'element not selected'
    if row.get('crops') in rules.get('crops_exclude', []):
        return 'crop category excluded'
    return None


def _normalize_record(row: dict, mapping: dict) -> tuple[dict | None, str | None]:
    out = clean_row(row, mapping['columns'], mapping.get('cleaning', {}))
    if not isinstance(out, dict):
        raise ValueError('transform.clean_row() must return a dict')
    # Resolve only the *name*. Actual numeric fiber_id lookup happens at import time.
    if 'fiber_type_name' in out:
        name = out['fiber_type_name']
        if name in mapping.get('skip_categories', []):
            return None, 'fiber/category explicitly excluded'
        mapped_name = mapping.get('fiber_name_map', {}).get(name, name)
        if mapped_name is None:
            return None, 'fiber name deliberately excluded by fiber_name_map'
        out['fiber_type_name'] = mapped_name
    # Applies to both row-sections and year-columns, using the source config.
    factor = row.get('__fizz_value_multiplier',
                     mapping.get('year_columns', {}).get('value_multiplier', 1))
    if factor != 1:
        value = out.get('measurement_value')
        if value is not None:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError('measurement_value is not finite before unit conversion')
            out['measurement_value'] = number * float(factor)
    for field, value in mapping.get('fixed_fields', {}).items():
        out.setdefault(field, value)
    if mapping.get('source') and 'source' not in out:
        out['source'] = mapping['source']
    return {key: _plain(val) for key, val in out.items()}, None


def _validate(row: dict, mapping: dict) -> str | None:
    validation = mapping.get('validation', {})
    for field in validation.get('required_fields', []):
        val = row.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ''):
            return f'missing required field {field}'
    for field in validation.get('numeric_fields', []):
        val = row.get(field)
        if val is None:
            continue
        try:
            number = float(val)
        except (ValueError, TypeError):
            return f'{field} is not numeric: {val!r}'
        if not math.isfinite(number):
            return f'{field} is not finite'
    # Configurable physical plausibility limits. Outliers are quarantined,
    # never silently rescaled or adjusted. Use scientifically approved bounds.
    bounds = validation.get('value_bounds_by_metric', {}).get(row.get('measurement_type'))
    if bounds:
        try:
            number = float(row['measurement_value'])
        except (ValueError, TypeError, KeyError):
            return 'measurement_value is not numeric for range validation'
        if 'min' in bounds and number < float(bounds['min']):
            return f'{row.get("measurement_type")} below approved lower bound ({bounds["min"]})'
        if 'max' in bounds and number > float(bounds['max']):
            return f'{row.get("measurement_type")} exceeds review threshold ({bounds["max"]})'
    # Optional generic exact-integer checks for count-type measurements.
    if row.get('measurement_type') in validation.get('integer_measurement_types', []):
        try:
            number = float(row.get('measurement_value'))
        except (ValueError, TypeError):
            return f'{row.get("measurement_type")} must be numeric integer'
        if not math.isfinite(number) or number < 0 or not number.is_integer():
            return f'{row.get("measurement_type")} must be a nonnegative whole number'
    # Dataset-specific scientific rules, rather than general guesses.
    if mapping.get('table') == 'cultivation-data':
        if row.get('measurement_type') == 'farm_count' and row.get('measurement_value') is not None:
            try:
                n = float(row['measurement_value'])
                if n < 0 or not n.is_integer():
                    return 'farm_count must be a nonnegative whole number'
            except (ValueError, TypeError):
                return 'farm_count must be numeric'
        if row.get('measurement_unit') == 'ha' and row.get('measurement_value') is not None:
            if float(row['measurement_value']) < 0:
                return 'area in hectares cannot be negative'
    return None


def _cross_measurement_warnings(records: list[dict], mapping: dict) -> list[dict]:
    """Config-driven cross-row scientific checks; warn without changing source values.

    Example: one metric is a subset of another, so its area should not exceed
    the total. Flag suspect observations for human review; never auto-correct.
    """
    warnings: list[dict] = []
    for rule in mapping.get('cross_checks', []):
        if rule.get('type') != 'subset_lte_total':
            raise ValueError(f'Unknown cross-check type: {rule.get("type")!r}')
        group_by = rule.get('group_by', ['fiber_type_name', 'country', 'region', 'year', 'source'])
        subset = rule['subset_measurement_type']
        total = rule['total_measurement_type']
        tolerance = float(rule.get('tolerance', 0))
        indexed: dict[tuple, dict[str, dict]] = {}
        for record in records:
            key = tuple(str(record.get(field)) for field in group_by)
            indexed.setdefault(key, {})[str(record.get('measurement_type'))] = record
        for key, group in indexed.items():
            if subset in group and total in group:
                a = float(group[subset]['measurement_value'])
                b = float(group[total]['measurement_value'])
                if a > b + tolerance:
                    warnings.append({
                        'type': 'subset_exceeds_total', 'group': dict(zip(group_by, key)),
                        'subset_measurement_type': subset,
                        'subset_value': a,
                        'total_measurement_type': total,
                        'total_value': b,
                        'unit': group[subset].get('measurement_unit'),
                        'reason': 'Subset exceeds total; verify source and scope before import.',
                    })
    return warnings


def prepare(filepath: str | Path, source_name: str, out: str | Path) -> dict:
    path, destination = Path(filepath), Path(out)
    if not path.is_file():
        raise FileNotFoundError(f'Input file not found: {path}')
    if path.resolve() == destination.resolve():
        raise ValueError('Output cannot overwrite the original input file.')
    if destination.suffix.lower() != '.csv':
        raise ValueError('Output must be a .csv file')
    mapping = get_mapping(source_name)
    filter_rules = mapping.get('filters', {})
    unknown_filters = set(filter_rules) - SUPPORTED_FILTERS
    if unknown_filters:
        raise ValueError(f'Unsupported filter keys: {sorted(unknown_filters)}')
    if 'columns' not in mapping or not mapping['columns']:
        raise ValueError('Mapping must define columns')
    if destination.exists():
        raise FileExistsError(f'Output already exists: {destination}; choose a new filename')

    original_rows = _read_rows(path, mapping)
    exceptions: list[dict] = []
    modes = [name for name in ('year_columns', 'unpivot', 'row_sections') if name in mapping]
    if len(modes) > 1:
        raise ValueError(f'Choose one reshaping mode, not {modes!r}')
    source_metadata = {}
    if 'year_columns' in mapping:
        source_rows, source_metadata = _flatten_year_columns(original_rows, mapping, exceptions)
    elif 'row_sections' in mapping:
        source_rows, source_metadata = _flatten_row_sections(original_rows, mapping, exceptions)
    else:
        source_rows = _flatten(original_rows, mapping, exceptions)
    accepted, seen = [], set()
    counts = Counter()
    keys = mapping.get('validation', {}).get('unique_fields', [])
    for src_row, raw in source_rows:
        reason = _filter_reason(raw, filter_rules)
        if reason:
            counts['filtered'] += 1
            exceptions.append({'row': src_row, 'type': 'filtered', 'reason': reason})
            continue
        try:
            cleaned, skip = _normalize_record(raw, mapping)
            if skip:
                counts['filtered'] += 1
                exceptions.append({'row': src_row, 'type': 'filtered', 'reason': skip})
                continue
            reason = _validate(cleaned, mapping)
            if reason:
                raise ValueError(reason)
            if keys:
                key = tuple(str(cleaned.get(k)) for k in keys)
                if key in seen:
                    raise ValueError(f'duplicate observation for {keys}: {key}')
                seen.add(key)
            accepted.append(cleaned)
        except (ValueError, KeyError, TypeError) as exc:
            counts['rejected'] += 1
            exceptions.append({
                'row': src_row, 'type': 'rejected', 'reason': str(exc),
                'raw_values': {str(k): _plain(v) for k, v in raw.items()},
            })

    scientific_warnings = _cross_measurement_warnings(accepted, mapping)

    header = []
    if mapping.get('table') == 'cultivation-data':
        header += CULTIVATION_ORDER
    else:
        header += list(mapping['columns'].values())
    header += list(mapping.get('fixed_fields', {}))
    if mapping.get('source'):
        header.append('source')
    header += [k for row in accepted for k in row]
    header = list(dict.fromkeys(header))  # stable, deduplicated column order
    if not accepted:
        raise ValueError('No valid cleaned rows. Inspect mapping and source report assumptions.')

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header, extrasaction='raise')
        writer.writeheader()
        writer.writerows(accepted)

    report = {
        'status': ('PREVIEW_WITH_REJECTIONS_NOT_IMPORT_APPROVED' if counts['rejected']
                   else 'PREVIEW_WITH_WARNINGS_NOT_IMPORT_APPROVED' if scientific_warnings
                   else 'PREVIEW_ONLY_NOT_IMPORT_APPROVED'),
        'import_policy': mapping.get('import_policy', 'requires_separate approval and API verification'),
        'import_eligible': False,
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'input_file': str(path),
        'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_config': source_name,
        'target_table': mapping['table'],
        'source_metadata': source_metadata,
        'config_mapping_fields': list(mapping['columns'].values()),
        'raw_rows_read': len(original_rows),
        'candidate_measurement_rows': len(source_rows),
        'prepared_rows': len(accepted),
        'missing_observations': sum(x['type'] == 'missing_source_value' for x in exceptions),
        'filtered_rows': counts['filtered'],
        'rejected_rows': counts['rejected'],
        'exceptions': exceptions,
        'scientific_warnings': scientific_warnings,
        'output_csv': str(destination),
        'api_called': False,
        'database_written': False,
    }
    report_path = destination.with_name(destination.stem + '_report.json')
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Input physical data rows: {len(original_rows)}')
    print(f'Candidate observations: {len(source_rows)} | Cleaned: {len(accepted)}')
    print(f"Missing: {report['missing_observations']} | Filtered: {counts['filtered']} | Rejected: {counts['rejected']}")
    print(f'Preview CSV: {destination}\nValidation report: {report_path}')
    print('No API requests or database writes were made.')
    if counts['rejected']:
        print('WARNING: rejected records require review before import.')
    if scientific_warnings:
        print(f'WARNING: {len(scientific_warnings)} scientific cross-check(s) need review before import.')
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description='Offline FIZZ source preparation')
    parser.add_argument('--file', required=True, help='Source .csv/.xlsx/.xls')
    parser.add_argument('--source', required=True, help='Key from config.py MAPPINGS')
    parser.add_argument('--out', required=True, help='Output CSV path (must not exist)')
    args = parser.parse_args()
    try:
        prepare(args.file, args.source, args.out)
    except (OSError, ValueError, KeyError, ImportError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    main()
