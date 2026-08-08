# SG Builder Brief

> **Reusable context for AI models and new contributors.**
> Last updated: 2026-07-27 | Version: 4.2.2 Beta (MATLAB-aligned stats + DB rebuild)

**IMPORTANT:** Any AI agent working on this project MUST update BRIEF.md AND CHANGELOG.md (in docs/) as it goes to avoid stale context accumulating and ensure needed context is always present. Delete sections that are no longer relevant; add new ones as discoveries are made.

---

## What This Project Is

Schema grapher is a desktop application for **statistical analysis and troubleshooting**. It helps quality engineers quickly identify and analyze measurements that fell **out of tolerance** — (e.g. statistical anomalies in how vehicle doors close, seal, align, and perform.)

The end user is an automotive quality engineer. They enter a vehicle (by make/model/year or VIN) and a door location, and SG walks them through a series of scatter plots showing where that vehicle's door measurements deviated from the expected tolerance bounds. Each plot represents a different test (e.g., "Closing Energy", "Hinge Inclination", "Striker Alignment"), and the user can navigate through them sequentially.

**GUI Layout:** Left sidebar (270px fixed) contains all controls — VIN input, OR divider, vehicle dropdowns, door list, and action buttons. Main area is the pyqtgraph plot. This follows the industry-standard pattern used by JMP, Minitab, and other statistical analysis tools. Buttons remain disabled (greyed out) until a door is selected, enforcing the prerequisite workflow.

---

## Architecture Overview

```
SG/
├── config/                  # All configuration lives here (JSON)
│   ├── db_config.json       # Default DB connection + column mappings
│   ├── db_config_*.json     # Per-locale DB configs (de, fr, es, nl)
│   ├── locale_en.json       # English UI strings (35 keys)
│   ├── locale_*.json        # Translations for DE, FR, ES, NL
│   ├── stat_ordering.json   # Branch-based graph traversal order rules
│   └── user_prefs.json      # Persists user's language + DB selection
├── src/
│   ├── main.py              # PyQt5 GUI (intro_form class, ~830 lines, sidebar layout)
│   └── core/
│       ├── auto_stat_facilities.py  # DB queries, data model, stat ordering (~426 lines)
│       ├── locale.py                # Locale/DB config loading (~189 lines)
│       └── __init__.py              # Public re-exports
├── tests/
│   ├── conftest.py          # Autouse fixture resetting prefs per test
│   ├── test_unit.py         # Unit tests (model, queries, locale, stat ordering)
│   ├── test_widgets.py      # Widget tests (UI state, navigation, plotting)
│   └── test_stress.py       # Stress tests (1000-case plotting, edge cases)
├── db/                      # SQL schema + helper scripts for PostgreSQL setup
│   ├── SG_tables*.sql    # Schema + bulk INSERT data (one per locale)
│   ├── fix_sql.py           # DEPRECATED — has door bugs
│   ├── gen_psql.py          # DEPRECATED — has door bugs
│   ├── generate_steps.py    # DEPRECATED — has door bugs
│   ├── insert_data.py       # DEPRECATED — has door + column bugs
│   ├── insert_steps.sql     # Steps INSERT (used for SG DB)
│   ├── sql_fix.sql          # SQL fix script (applied to SG3)
│   └── backup/              # Pre-fix SQL file backups
├── fix_db.py                # Comprehensive fixer (DB-side, applied to SG3)
├── export_fixed.py          # Active exporter from fixed DB to all SQL files
├── data/
│   ├── logo/                # Company logo for the UI header
│   └── pseudo_database/     # Test/pseudo database files
```

**Tech stack:** Python 3.12, PyQt5, pyqtgraph, numpy, psycopg2/psycopg3, PostgreSQL 16+

---

## Live Databases

| DB | Language | Source SQL | Rows (veh/stats/steps) | Notes |
|----|----------|-----------|----------------------|-------|
| `SG` | English | `SG_tables.sql` | 1030 / 38205 / 38205 | MATLAB-aligned stats, 84.5% in-tol |
| `SG_de` | German | `SG_tables_de.sql` | 1030 / 38205 / 38205 | MATLAB-aligned stats |
| `SG_es` | Spanish | `SG_tables_es.sql` | 1030 / 38205 / 38205 | MATLAB-aligned stats |
| `SG_fr` | French | `SG_tables_fr.sql` | 1030 / 38205 / 38205 | MATLAB-aligned stats |
| `SG_nl` | Dutch | `SG_tables_nl.sql` | 1030 / 38205 / 38205 | MATLAB-aligned stats |

---

## How the Data Model Works

The database stores door check measurement results across three logical layers:

1. **Vehicles** — VIN, make, model, body type, manufacture date
2. **Stats** (auto_door_stats) — 38205 individual measurement results with x/y values and tolerance bounds (lower limit, upper limit). Every 9 consecutive IDs span all 9 test types.
3. **Steps** (joint table) — Links stats to vehicles, includes door location

**Door assignments per body type:**
- sedan: driver_front, driver_rear, passenger_front, passenger_rear (4 doors)
- coupe: driver_front, passenger_front (2 doors)
- SUV: driver_front, driver_rear, passenger_front, passenger_rear, rear_hatch, hood (6 doors)
- pickup: driver_front, passenger_front (2 doors)
- hatchback: driver_front, driver_rear, passenger_front, passenger_rear, rear_hatch (5 doors)

An **outlier** is any measurement where result_y falls outside tolerance bounds. A **stat family** is all measurements sharing the same test name and door location across all vehicles.

---

## The Configurability System

The entire DB schema is abstracted through `config/db_config*.json`. No column names or table names are hardcoded in Python — they're referenced through config keys. This means the same codebase works against different DB schemas by swapping the config file, and each locale can point to a different database.
---

## Known Issues & Future Work

1. ~~**Connection pooling** — Every DB query opens a new TCP connection. With 1000 outliers, this means 1000 round-trips. `psycopg_pool` would fix this.~~ **RESOLVED**: `psycopg_pool.ConnectionPool` added to `auto_stat_facilities.py` with lazy init and direct-connection fallback.
2. ~~**Credentials in plaintext** — `db_config*.json` contains `postgres/postgres`. Should use env vars before public release.~~ **RESOLVED**: Env vars (`EZ_PG_DB`, `EZ_PG_USER`, `EZ_PG_PASS`, `EZ_PG_HOST`, `EZ_PG_PORT`) now override config file values in both `auto_stat_facilities.py` and `locale.py`.
3. ~~**Unused config keys** — `EZ_VEHICLES_BODY_TYPE_FIELD`, `EZ_STAT_SAMPLED_FIELD`, `EZ_STAT_TWO_VAR_FIELD` are defined but never referenced in code.~~ **RESOLVED**: Documented as reserved for future use via `_note` field in each `db_config*.json`.
4. **`db/insert_data.py` has translation errors** — French column names are wrong (e.g., uses `nom_stat_porte_vehicule` instead of `nom_stat_porte_auto`). Dutch column names also wrong. Script should not be used.
5. **`db/fix_sql.py` is broken** — Has syntax error, uses wrong door mappings, hardcodes dates. Should not be used.
6. **Missing CHECK constraints in locale SQL files** — The English `SG_tables.sql` has 5 CHECK constraints (`ck_vin_format`, `ck_manufacture_date_not_null`, `ck_sampled_not_null`, `ck_result_x_unit_not_null`, `ck_result_y_not_null`) that are absent from all 4 locale SQL files (`_de`, `_es`, `_fr`, `_nl`). Should be added for schema parity.

---

## File Map (for quick reference)

| File | Purpose | Notes |
|------|---------|-------|
| `src/main.py` | PyQt5 GUI | `intro_form` (QMainWindow), plotting, navigation, dropdowns, on-plot annotations |
| `src/core/auto_stat_facilities.py` | DB query layer + stat ordering | `vin_query`, `vehicle_query`, `fetch_stat_family`, `test_case` (+make/model/mandate), `matricize_test_cases`, `apply_stat_ordering` |
| `src/core/locale.py` | Locale/config system | `load_locale_strings`, `load_db_config_for_locale`, `translate_test_name`, `get_supported_db_configs` |
| `src/core/__init__.py` | Public API re-exports | All of the above |
| `tests/` | Test suite | pytest with offscreen Qt rendering; DB calls mocked |
| `config/db_config.json` | Default EN DB config | Points to `SG3` DB |
| `config/db_config_de.json` | German DB config | Points to `SG_de` DB |
| `config/db_config_fr.json` | French DB config | Points to `SG_fr` DB |
| `config/db_config_es.json` | Spanish DB config | Points to `SG_es` DB |
| `config/db_config_nl.json` | Dutch DB config | Points to `SG_nl` DB |
| `config/stat_ordering.json` | Graph traversal order | Branch rules for reordering outlier stats |
| `db/SG_tables.sql` | EN schema + data | 1030 vehicles, 38205 stats, 38205 steps |
| `db/SG_tables_de.sql` | DE schema + data | Translated table/column names |
| `db/SG_tables_fr.sql` | FR schema + data | Uses `véhicules`, `stats_portes_automobiles`, `étapes` |
| `db/SG_tables_es.sql` | ES schema + data | Uses `vehículos`, `estadísticas_puertas_vehículos`, `pasos` |
| `db/SG_tables_nl.sql` | NL schema + data | Uses `voertuigen`, `statistieken_deuren_voertuigen`, `stappen` |
| `db/insert_steps.sql` | Interleaved steps | BEGIN/DELETE/ALTER/INSERT/COMMIT for SG DB |
| `db/sql_fix.sql` | DB-side fix script | Reorders stat IDs, adds missing doors |
| `export_fixed.py` | Active export script | Reads SG3 DB, writes all SQL files |
| `fix_db.py` | DB-side fixer | Python equivalent of sql_fix.sql |
| `db/introduce_outliers.sql` | Outlier injection | Pushes ~10% of result_y outside tolerance bounds |

---

## Running Tests

```bash
cd SG
./venvs/test/bin/python -m pytest tests/ -v
```

Requires PyQt5, pyqtgraph, numpy, psycopg. Tests cannot run without these dependencies installed.

---

## Project Conventions

- **Class naming:** `test_case` and `intro_form` are classes using snake_case (legacy convention)
- **Config keys:** Prefixed with `EZ_` (e.g., `EZ_PG_DB`, `EZ_STAT_NAME_FIELD`)
- **Locale keys:** Same `EZ_` prefix (e.g., `EZ_BTN_QUERY`, `EZ_STATUS_READY`)
- **Private functions:** Prefixed with `_` (e.g., `_quote_identifier`, `_update_door_availability`)
- **Module-level state:** `_LOCALE`, `_APP_CONFIG`, `DOOR_LOCATIONS` are set at import time from user_prefs.json
- **Error handling:** DB failures surface to the status bar; corrupt JSON falls back to defaults
- **Test approach:** pytest-qt with offscreen rendering; all DB calls mocked in widget tests
