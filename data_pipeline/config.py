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
        }        

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