# FIZZ Database Schema

## fiber_types

| Column | Type | Nullable | Key / change |
|---|---|---|---|
| fiber_id | Integer | NO | PK; auto increment |
| fiber_type_name | String(100) | NO | Unique |
| scientific_name | String(150) | YES |  |
| notes | Text | YES |  |
| created_at | DateTime | auto |  |
| updated_at | DateTime | auto |  |

## fiber_quality

| Column | Type | Nullable | Key / change |
|---|---|---|---|
| quality_id | Integer | NO | PK |
| fiber_id | Integer | NO | FK → fiber_types.fiber_id |
| tensile_strength | Numeric(12,2) | YES |  |
| fiber_length | Numeric(12,2) | YES |  |
| purity_level | Numeric(5,2) | YES |  |
| moisture_content | Numeric(5,2) | YES |  |
| elasticity | Numeric(5,2) | YES |  |
| quality_grade | String(10) | YES |  |
| testing_date | Date | YES |  |
| source | Text | YES |  |
| created_at | DateTime | auto |  |
| updated_at | DateTime | auto |  |

## cultivation_data

| Column | Type | Nullable | Key / change |
|---|---|---|---|
| cultivation_id | Integer | NO | PK |
| fiber_id | Integer | NO | FK → fiber_types.fiber_id |
| country | String(100) | YES |  |
| region | String(100) | YES |  |
| year | Integer | YES | Renamed from harvest_date |
| soil_type | String(50) | YES |  |
| farming_method | String(50) | YES |  |
| measurement_type | String(50) | NO | Added |
| measurement_value | Numeric(12,2) | NO | Added |
| measurement_unit | String(20) | NO | Added |
| source | Text | YES |  |
| created_at | DateTime | auto |  |
| updated_at | DateTime | auto |  |

**Why the three added columns:** `measurement_type` identifies what is measured, `measurement_value` stores the number, and `measurement_unit` stores its unit. Each row holds one measurement. This supports different cultivation measurements without adding a column for every new source. Yield and water requirements use these fields instead of separate measurement columns.

## processing_methods

| Column | Type | Nullable | Key / change |
|---|---|---|---|
| processing_id | Integer | NO | PK |
| fiber_id | Integer | NO | FK → fiber_types.fiber_id |
| process_type | String(500) | YES |  |
| energy_required | Numeric(12,2) | YES |  |
| chemicals_used | Text | YES |  |
| source | Text | YES |  |
| created_at | DateTime | auto |  |
| updated_at | DateTime | auto |  |

## sustainability_metrics

| Column | Type | Nullable | Key / change |
|---|---|---|---|
| sustainability_id | Integer | NO | PK |
| fiber_id | Integer | NO | FK → fiber_types.fiber_id |
| year | Integer | YES |  |
| co2_emissions | Numeric(12,2) | YES |  |
| water_usage | Numeric(12,2) | YES |  |
| energy_consumption | Numeric(12,2) | YES |  |
| source | Text | YES |  |
| created_at | DateTime | auto |  |
| updated_at | DateTime | auto |  |

## market_data

| Column | Type | Nullable | Key / change |
|---|---|---|---|
| market_id | Integer | NO | PK |
| fiber_id | Integer | NO | FK → fiber_types.fiber_id |
| industry | String(80) | YES |  |
| year | Integer | YES |  |
| country | String(100) | YES |  |
| region | String(100) | YES |  |
| demand | Numeric(12,2) | YES |  |
| demand_unit | String(20) | YES |  |
| price | Numeric(12,2) | YES |  |
| price_unit | String(20) | YES |  |
| currency | String(10) | YES |  |
| source | Text | YES |  |
| created_at | DateTime | auto |  |
| updated_at | DateTime | auto |  |

## products

| Column | Type | Nullable | Key / change |
|---|---|---|---|
| product_id | Integer | NO | PK |
| product_name | String(100) | NO |  |
| fiber_id | Integer | NO | FK → fiber_types.fiber_id |
| product_category | String(50) | YES |  |
| product_type | String(50) | YES |  |
| quality_required | Integer | YES | FK → fiber_quality.quality_id |
| description | Text | YES |  |
| created_at | DateTime | auto |  |
| updated_at | DateTime | auto |  |

## Keys and table relationships

- **Primary key (PK):** uniquely identifies each row in its table and cannot be null.
- **Foreign key (FK):** references an existing row in another table.
- **Unique:** prevents duplicate values, such as duplicate fibre names.
- **Nullable:** YES allows an empty value; NO requires a value. `auto` marks timestamps managed by the application.

| Dependent column (FK) | Referenced column (PK) | Relationship |
|---|---|---|
| fiber_quality.fiber_id | fiber_types.fiber_id | One fibre can have many fiber_quality records. |
| cultivation_data.fiber_id | fiber_types.fiber_id | One fibre can have many cultivation_data records. |
| processing_methods.fiber_id | fiber_types.fiber_id | One fibre can have many processing_methods records. |
| sustainability_metrics.fiber_id | fiber_types.fiber_id | One fibre can have many sustainability_metrics records. |
| market_data.fiber_id | fiber_types.fiber_id | One fibre can have many market_data records. |
| products.fiber_id | fiber_types.fiber_id | One fibre can have many products records. |
| products.quality_required | fiber_quality.quality_id | One quality record can be referenced by many products; this reference is optional. |

`fiber_types` is the parent table for all six other tables. `products` also depends on `fiber_quality` when `quality_required` is populated.
