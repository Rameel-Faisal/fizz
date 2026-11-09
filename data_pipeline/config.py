# data_pipeline/config.py
#
# Column mappings for every data source.
# Add a new entry here when a new source arrives.
# Nothing else in the pipeline needs to change.

MAPPINGS = {

    "fibers_to_fiber_types": {
        "table": "fiber-types",
        "columns": {
            "Fiber Name":   "fiber_type_name",
            "Applications": "notes",
            "Sources":      "source"
        },
        "cleaning": {
            "Fiber Name":   "extract_main_name",
            "Sources":      "nullify_no_source"
        }
    },

    "fibers_to_cultivation": {
        "table": "cultivation-data",
        "columns": {
            "Fiber Name":   "fiber_type_name",
            "Temperature":  "temperature_range",
            "Rainfall":     "water_required",
            "Sources":      "source"
        },
        "cleaning": {
            "Fiber Name":   "extract_main_name",
            "Temperature":  "strip_german_prefix",
            "Rainfall":     "extract_min_value",
            "Sources":      "nullify_no_source"
        }
    },

    "fibers_to_processing": {
        "table": "processing-methods",
        "columns": {
            "Fiber Name":          "fiber_type_name",
            "Exploration Method":  "process_type",
            "Sources":             "source"
        },
        "cleaning": {
            "Fiber Name":         "extract_main_name",
            "Exploration Method": "strip_method_prefix",
            "Sources":            "nullify_no_source"
        }
    },

    "eurostat_crop_production": {
        "table": "cultivation-data",
        "columns": {
            "geo":         "region",
            "TIME_PERIOD": "harvest_date",
            "OBS_VALUE":   "yield_amount",
            "crops":       "fiber_type_name"
        },
        "cleaning": {
            "geo":         "clean_string",
            "TIME_PERIOD": "parse_year",
            "OBS_VALUE":   "parse_number",
            "crops":       "clean_string"
        },
        "filters": {
            "strucpro": "Harvested production\xa0in EU standard humidity - thousand tonnes",
            "crops_exclude": ["Permanent crops for human consumption", "Fibre crops"]
        },
        "fiber_name_map": {
            "Hemp":         "Hanf",
            "Fibre flax":   "Flachs",
            "Cotton fibre": "Baumwolle"
        },
        "source": "Eurostat APRO_CPSH1"
    },

    # ── NEW ──────────────────────────────────────────────────────────────────
    # Source: German crop price data 2020-2024
    # File:   Crops,Flax and Hemp Price Data 2024-2020.xlsx
    # Table:  market-data
    # Notes:  Year column uses fiscal format "2023/24" → cleaned to 2023
    #         Yield and Price columns are object type → cleaned to float
    #         SGM, Value, Total output, Variable costs columns are dropped
    # ─────────────────────────────────────────────────────────────────────────
    "germany_crop_prices": {
        "table": "market-data",
        "columns": {
            "Category":     "fiber_type_name",
            "Region":       "region",
            "Year":         "year",
            "Yield dt/ha":  "demand",
            "Price €/ha":   "price"
        },
        "cleaning": {
            "Category":     "clean_string",
            "Region":       "clean_string",
            "Year":         "clean_year",
            "Yield dt/ha":  "parse_number",
            "Price €/ha":   "parse_number"
        },
        
        "fiber_name_map": {
            "Hemp":  "Hanf",
            "Flax":  "Flachs"
        },
        "skip_categories": [
        "Common wheat and spelt",
        "Durum wheat",
        "Barley",
        "Rye",
        "Grain maize"
    ],
        "fixed_fields": {               
        "country":    "Germany",
        "currency":   "EUR",
        "price_unit": "EUR/ha",
        "demand_unit": "dt/ha",
        "source":     "German Crop Price Data 2020-2024"
      }
    },
    "fao_hemp_cultivation": {
            "table": "cultivation-data",
            "columns": {
                "Area":  "country",
                "Year":  "harvest_date",
                "Value": "yield_amount",
                "Unit":  "yield_unit"
            },
            "cleaning": {
                "Area":  "clean_string",
                "Year":  "parse_year",
                "Value": "parse_number",
                "Unit":  "clean_string"
            },
            "fiber_name_map": {
                "True hemp, raw or retted": "Hanf"
            },
            "fixed_fields": {
                "source": "FAO Hemp Cultivation Data 2015-2024"
            },
            "filters": {
                "element_keep": "Yield"
            }
        },
    
"bmel_3070900": {
    "table": "cultivation-data",
    "input": {"sheet_name": "Original data", "header": None},
    "unpivot": {
        "year_column": 1,  # zero-based: B is year
        "missing_markers": ["", ".", "-", "–", "—"],
        "measurements": [
            {"source_column": 2, "fiber_type_name": "Hanf",   "measurement_type": "farm_count",     "measurement_unit": "farms"},
            {"source_column": 3, "fiber_type_name": "Hanf",   "measurement_type": "cultivated_area", "measurement_unit": "ha"},
            {"source_column": 4, "fiber_type_name": "Flachs", "measurement_type": "farm_count",     "measurement_unit": "farms"},
            {"source_column": 5, "fiber_type_name": "Flachs", "measurement_type": "cultivated_area", "measurement_unit": "ha"},
        ],
    },
    "columns": {
        "fiber_type_name":  "fiber_type_name",
        "year":             "year",
        "measurement_type": "measurement_type",
        "measurement_value": "measurement_value",
        "measurement_unit":  "measurement_unit",
    },
    "cleaning": {
        "fiber_type_name":  "clean_string",
        "year":             "parse_year",
        "measurement_type": "clean_string",
        "measurement_value": "parse_number",
        "measurement_unit":  "clean_string",
    },
    "fixed_fields": {
        "country": "Germany",
        "source": "BMEL 3070900-0000 (BLE)",
    },
    "validation": {
        "required_fields": [
            "fiber_type_name", "country", "year", "measurement_type",
            "measurement_value", "measurement_unit", "source",
        ],
        "numeric_fields": ["measurement_value"],
        "unique_fields": [
            "fiber_type_name", "country", "region", "year",
            "measurement_type", "source",
        ],
    },
},


    "bmel_3071310": {
    "table": "cultivation-data",
    "input": {
        "sheet_name": "Original data",
        "header": None,
    },
    "year_columns": {
        "header_row": 4,            # Excel row 4: years in C:P
        "category_column": 1,       # Excel column B: category name
        "category_value": "Pflanzenfasern",
        "first_year_column": 2,     # Excel column C (zero-based)
        "last_year_column": 15,     # Excel column P (zero-based)
        "fiber_type_name": "Plant fibres (BMEL aggregate)",
        "measurement_type": "cultivated_area",
        "measurement_unit": "ha",
        "original_unit": "1 000 ha",
        "value_multiplier": 1000,
        "missing_markers": ["", ".", "-", "–", "—"],
        "status_flag_map": {
            "1)": "provisional",
            "2)": "estimated",
        },
    },
    "columns": {
        "fiber_type_name": "fiber_type_name",
        "year": "year",
        "measurement_type": "measurement_type",
        "measurement_value": "measurement_value",
        "measurement_unit": "measurement_unit",
    },
    "cleaning": {
        "fiber_type_name": "clean_string",
        "year": "parse_year",
        "measurement_type": "clean_string",
        "measurement_value": "parse_number",
        "measurement_unit": "clean_string",
    },
    "fixed_fields": {
        "country": "Germany",
        "source": "BMEL 3071310-0000 (Fachagentur Nachwachsende Rohstoffe / BMLEH)",
    },
    "source_notes": [
        "Pflanzenfasern is an aggregate category, not an individual fibre crop.",
        "All source values are rounded to significant digits; rounding differences possible.",
        "2024 1) is provisional; 2025 2) is an estimate.",
        "Technical linseed oil is a different crop-use category; not fibre flax.",
        "Do not sum plant-fibre aggregate area with hemp/flax area (possible double counting).",
        "Original source: https://www.bmel-statistik.de/fileadmin/daten/3071310-0000.xlsx",
    ],
    "validation": {
        "required_fields": [
            "fiber_type_name", "country", "year", "measurement_type",
            "measurement_value", "measurement_unit", "source",
        ],
        "numeric_fields": ["measurement_value"],
        "unique_fields": [
            "fiber_type_name", "country", "region", "year", "measurement_type", "source",
        ],
    },
},


    "bmel_3070600": {
    "table": "cultivation-data",
    "input": {"sheet_name": "Original data", "header": None},
    "year_columns": {
        "series": [
            {
                "header_row": 4,             # Year headings D:S in first block
                "first_data_row": 5,
                "last_data_row": 68,
                "category_column": 0,        # Excel A (zero-based)
                "category_value": "Hanf",
                "unit_column": 2,            # Excel C
                "expected_unit": "Hektar",
                "first_year_column": 3,      # Excel D = 2010
                "last_year_column": 18,      # Excel S = 2025
                "fiber_type_name": "Hanf",
                "measurement_type": "seed_multiplication_area_total",
                "measurement_unit": "ha",
                "original_unit": "Hektar",
                "missing_markers": ["", ".", "-", "–", "—"],
            },
            {
                "header_row": 80,            # Year headings D:S in certified block
                "first_data_row": 81,
                "last_data_row": 144,
                "category_column": 0,
                "category_value": "Hanf",
                "unit_column": 2,
                "expected_unit": "Hektar",
                "first_year_column": 3,
                "last_year_column": 18,
                "fiber_type_name": "Hanf",
                "measurement_type": "seed_multiplication_area_certified",
                "measurement_unit": "ha",
                "original_unit": "Hektar",
                "missing_markers": ["", ".", "-", "–", "—"],
            },
        ],
    },
    "columns": {
        "fiber_type_name": "fiber_type_name",
        "year": "year",
        "measurement_type": "measurement_type",
        "measurement_value": "measurement_value",
        "measurement_unit": "measurement_unit",
    },
    "cleaning": {
        "fiber_type_name": "clean_string",
        "year": "parse_year",
        "measurement_type": "clean_string",
        "measurement_value": "parse_number",
        "measurement_unit": "clean_string",
    },
    "fixed_fields": {
        "country": "Germany",
        "source": "BMEL 3070600-0000 (Bundessortenamt / BMLEH)",
    },
    "source_notes": [
        "Both series are successfully field-inspected seed multiplication areas.",
        "Total series includes basic + certified seed; certified-only is a subset, including Z2.",
        "Do not add the two series: doing so would double-count certified hectares.",
        "Footnote 3) on Hanf: Außer für Zierzwecke (excluding ornamental purposes).",
        "Lein is not automatically fibre flax; exclude pending scientific crop/use clarification.",
        "A dash is a source missing/suppression symbol, never automatically zero.",
        "Source: https://www.bmel-statistik.de/fileadmin/daten/3070600-0000.xlsx",
    ],
    "cross_checks": [
        {
            "type": "subset_lte_total",
            "subset_measurement_type": "seed_multiplication_area_certified",
            "total_measurement_type": "seed_multiplication_area_total",
            "group_by": ["fiber_type_name", "country", "region", "year", "source"],
        }
    ],
    "validation": {
        "required_fields": [
            "fiber_type_name", "country", "year", "measurement_type",
            "measurement_value", "measurement_unit", "source",
        ],
        "numeric_fields": ["measurement_value"],
        "unique_fields": [
            "fiber_type_name", "country", "region", "year", "measurement_type", "source",
        ],
    },
},
"bmel_3070500_context": {
    "table": "context-only",  # Deliberately NOT a FIZZ API endpoint/table
    "import_policy": "CONTEXT_ONLY_NEVER_IMPORT_WITH_CURRENT_SEVEN_TABLE_SCHEMA",
    "input": {"sheet_name": "Original data", "header": None},
    "row_sections": {
        "series": [
            {
                "section_heading_row": 5,
                "section_heading_value": "1 000 ha",
                "first_data_row": 6,
                "last_data_row": 40,
                "first_year": 1991,
                "last_year": 2025,
                "year_column": 1,             # Excel B
                "value_column": 9,            # Excel J
                "original_column": "Ackerland insgesamt",
                "category_name": "Total arable land (BMEL context)",
                "measurement_type": "total_arable_area",
                "measurement_unit": "ha",
                "original_unit": "1 000 ha",
                "value_multiplier": 1000,
            },
            {
                "section_heading_row": 5,
                "section_heading_value": "1 000 ha",
                "first_data_row": 6,
                "last_data_row": 40,
                "first_year": 1991,
                "last_year": 2025,
                "year_column": 1,
                "value_column": 6,            # Excel G
                "original_column": "Handelsgewächse 4)",
                "category_name": "Industrial/commercial crops (BMEL context)",
                "measurement_type": "industrial_crop_area",
                "measurement_unit": "ha",
                "original_unit": "1 000 ha",
                "value_multiplier": 1000,
            },
            {
                "section_heading_row": 41,
                "section_heading_value": "Anteil in %",
                "first_data_row": 42,
                "last_data_row": 76,
                "first_year": 1991,
                "last_year": 2025,
                "year_column": 1,
                "value_column": 6,
                "original_column": "Handelsgewächse / Anteil in %",
                "category_name": "Industrial/commercial crops (BMEL context)",
                "measurement_type": "industrial_crop_share",
                "measurement_unit": "%",
                "original_unit": "%",
                "value_multiplier": 1,
            },
        ],
    },
    "columns": {
        "category_name": "category_name",
        "year": "year",
        "measurement_type": "measurement_type",
        "measurement_value": "measurement_value",
        "measurement_unit": "measurement_unit",
    },
    "cleaning": {
        "category_name": "clean_string",
        "year": "parse_year",
        "measurement_type": "clean_string",
        "measurement_value": "parse_number",
        "measurement_unit": "clean_string",
    },
    "fixed_fields": {
        "country": "Germany",
        "source": "BMEL 3070500-0000 (Destatis GENESIS 41271-0003 / BMLEH)",
    },
    "source_notes": [
        "Handelsgewächse is a mixed industrial/commercial crop group that includes non-fibre crops. NOT hemp or flax area.",
        "Source area is labelled 1 000 ha; factor 1000 used to convert to hectares for normal rows.",
        "The simplified review workbook's 2004 and 2005 area cells appear to use a different scale; these are quarantined, not silently corrected.",
        "Percent-share series is a reported source figure, not market share/demand.",
        "Methodology changed in 2010. Comparisons between 2010 onward and earlier data are limited.",
        "Source footnote 4) includes oil crops, hops, tobacco, herbs, hemp, flax, kenaf, miscanthus and other commercial crops.",
        "Official source requires verification: https://www.bmel-statistik.de/fileadmin/daten/3070500-0000.xlsx",
    ],
    "validation": {
        "required_fields": ["category_name", "country", "year", "measurement_type", "measurement_value", "measurement_unit", "source"],
        "numeric_fields": ["measurement_value"],
        "unique_fields": ["category_name", "country", "year", "measurement_type", "source"],
        # Review thresholds, NOT substitutions or estimates. Flag rather than fix.
        "value_bounds_by_metric": {
            "total_arable_area": {"min": 0, "max": 20000000},
            "industrial_crop_area": {"min": 0, "max": 20000000},
            "industrial_crop_share": {"min": 0, "max": 100},
        },
    },
},
"bmel_3071610_context": {
    "table": "context-only",
    "import_policy": "CONTEXT_ONLY_NEVER_IMPORT_WITH_CURRENT_SEVEN_TABLE_SCHEMA",
    "input": {"sheet_name": "Original data", "header": None},
    "row_sections": {
        "series": [
            {
                "section_heading_row": 5, "section_heading_column": 2,
                "section_heading_value": "Zahl",
                "first_data_row": 7, "last_data_row": 37,
                "first_year": 1994, "last_year": 2024,
                "year_column": 1, "value_column": 2,
                "original_column": "Betriebe / Zahl",
                "category_name": "Organic agriculture (Germany, BMEL context)",
                "measurement_type": "organic_farm_count", "measurement_unit": "farms",
                "original_unit": "farms", "value_multiplier": 1,
                "value_number_format": "space_grouped",
                "allow_year_footnotes": True,
                "year_status_map": {"3)": "2010 survey-threshold change: comparability with earlier years is limited"},
            },
            {
                "section_heading_row": 5, "section_heading_column": 3,
                "section_heading_value": "Anteil in % 2)",
                "first_data_row": 7, "last_data_row": 37,
                "first_year": 1994, "last_year": 2024,
                "year_column": 1, "value_column": 3,
                "original_column": "Betriebe / Anteil in % 2)",
                "category_name": "Organic agriculture (Germany, BMEL context)",
                "measurement_type": "organic_farm_share", "measurement_unit": "%",
                "original_unit": "%", "value_multiplier": 1,
                "allow_year_footnotes": True,
                "year_status_map": {"3)": "2010 survey-threshold change: comparability with earlier years is limited"},
            },
            {
                "section_heading_row": 5, "section_heading_column": 4,
                "section_heading_value": "ha",
                "first_data_row": 7, "last_data_row": 37,
                "first_year": 1994, "last_year": 2024,
                "year_column": 1, "value_column": 4,
                "original_column": "LF / zusammen / ha",
                "category_name": "Organic agriculture (Germany, BMEL context)",
                "measurement_type": "organic_agricultural_area", "measurement_unit": "ha",
                "original_unit": "ha", "value_multiplier": 1,
                "value_number_format": "space_grouped",
                "allow_year_footnotes": True,
                "year_status_map": {"3)": "2010 survey-threshold change: comparability with earlier years is limited"},
            },
            {
                "section_heading_row": 5, "section_heading_column": 5,
                "section_heading_value": "Anteil in % 2)",
                "first_data_row": 7, "last_data_row": 37,
                "first_year": 1994, "last_year": 2024,
                "year_column": 1, "value_column": 5,
                "original_column": "LF / Anteil in % 2)",
                "category_name": "Organic agriculture (Germany, BMEL context)",
                "measurement_type": "organic_area_share", "measurement_unit": "%",
                "original_unit": "%", "value_multiplier": 1,
                "allow_year_footnotes": True,
                "year_status_map": {"3)": "2010 survey-threshold change: comparability with earlier years is limited"},
            },
            {
                "section_heading_row": 5, "section_heading_column": 6,
                "section_heading_value": "ha",
                "first_data_row": 7, "last_data_row": 37,
                "first_year": 1994, "last_year": 2024,
                "year_column": 1, "value_column": 6,
                "original_column": "LF / je Betrieb / ha",
                "category_name": "Organic agriculture (Germany, BMEL context)",
                "measurement_type": "organic_area_per_farm", "measurement_unit": "ha/farm",
                "original_unit": "ha/farm", "value_multiplier": 1,
                "allow_year_footnotes": True,
                "year_status_map": {"3)": "2010 survey-threshold change: comparability with earlier years is limited"},
            },
        ],
    },
    "columns": {
        "category_name": "category_name",
        "year": "year",
        "measurement_type": "measurement_type",
        "measurement_value": "measurement_value",
        "measurement_unit": "measurement_unit",
    },
    "cleaning": {
        "category_name": "clean_string",
        "year": "parse_year",
        "measurement_type": "clean_string",
        "measurement_value": "parse_number",
        "measurement_unit": "clean_string",
    },
    "fixed_fields": {
        "country": "Germany",
        "source": "BMEL 3071610-0000 (BLE / BMLEH)",
    },
    "source_notes": [
        "Organic agriculture nationwide; these observations are NOT hemp/flax/plant-fibre-specific.",
        "Year-end stock: observations refer to 31 December of each reporting year.",
        "Until 1999, enterprise counts covered farms with plant production; from 2000, livestock farms included.",
        "2010 3) denotes a survey-threshold change; comparison with previous years is limited.",
        "Farm share denominator: all agricultural enterprises with utilised agricultural area.",
        "Area share denominator: total utilised agricultural area (LF).",
        "Source records reported percentages as 14.1, not 0.141; retain percentage-point scale.",
        "2018 area (1 498 027) and 2010 farm count (21 942) have space-grouped thousands.",
        "Keep the source's reported average ha/farm; don't recalculate to replace it.",
        "Original source: https://www.bmel-statistik.de/fileadmin/daten/3071610-0000.xlsx",
        "Verify source against official file before using in a database or public chart.",
    ],
    "validation": {
        "required_fields": ["category_name", "country", "year", "measurement_type", "measurement_value", "measurement_unit", "source"],
        "numeric_fields": ["measurement_value"],
        "integer_measurement_types": ["organic_farm_count"],
        "unique_fields": ["category_name", "country", "year", "measurement_type", "source"],
        "value_bounds_by_metric": {
            "organic_farm_count": {"min": 0, "max": 1000000},
            "organic_farm_share": {"min": 0, "max": 100},
            "organic_agricultural_area": {"min": 0, "max": 25000000},
            "organic_area_share": {"min": 0, "max": 100},
            "organic_area_per_farm": {"min": 0, "max": 10000},
        },
    },
},

}




def get_mapping(source_name: str) -> dict:
    if source_name not in MAPPINGS:
        available = list(MAPPINGS.keys())
        raise ValueError(
            f"Source '{source_name}' not found in config.\n"
            f"Available sources: {available}"
        )
    return MAPPINGS[source_name]


def list_sources() -> list:
    return list(MAPPINGS.keys())