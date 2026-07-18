"""
Database query layer for EZSAW.

Provides functions to query PostgreSQL for door check outlier results,
vehicle lookups, and stat family data. All queries use parameterized
inputs and quoted identifiers for safety.
"""

import atexit
import json
import os
from pathlib import Path

import numpy as np

try:
    import psycopg
    HAS_PSYCOPG = True
except ImportError:
    HAS_PSYCOPG = False

try:
    from psycopg_pool import ConnectionPool
    HAS_PSYCOPG_POOL = True
except ImportError:
    HAS_PSYCOPG_POOL = False

# ---------------------------------------------------------------------------
# Config & connection
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / 'config'
DB_CONFIG_FILE_PATH = _CONFIG_DIR / 'db_config.json'


def load_db_config():
    """Load the default db_config.json from the config directory."""
    try:
        with open(DB_CONFIG_FILE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


# Default config loaded at import time; individual functions accept overrides.
PGDB_CONFIG = load_db_config()

# ---------------------------------------------------------------------------
# Connection pool (psycopg_pool with fallback)
# ---------------------------------------------------------------------------

_POOL = None


def _get_pool():
    """Lazily initialise a psycopg_pool.ConnectionPool.

    Env vars are resolved once at pool creation time.  If ``psycopg_pool`` is
    not installed, returns ``None`` and every call falls back to a direct
    connection.
    """
    global _POOL
    if _POOL is None and HAS_PSYCOPG_POOL:
        config = PGDB_CONFIG
        try:
            _POOL = ConnectionPool(
                conninfo=(
                    f"dbname={os.environ.get('EZ_PG_DB') or config['EZ_PG_DB']} "
                    f"user={os.environ.get('EZ_PG_USER') or config['EZ_PG_USER']} "
                    f"password={os.environ.get('EZ_PG_PASS') or config['EZ_PG_PASS']} "
                    f"host={os.environ.get('EZ_PG_HOST') or config['EZ_PG_HOST']} "
                    f"port={os.environ.get('EZ_PG_PORT') or config.get('EZ_PG_PORT', 5432)}"
                ),
                min_size=1,
                max_size=4,
            )
            atexit.register(_POOL.close)
        except Exception:
            pass
    return _POOL


def _return_conn(conn):
    """Return a connection to the pool, or close it if no pool is active."""
    pool = _get_pool()
    if pool is not None and not conn.closed:
        pool.putconn(conn)
    elif HAS_PSYCOPG and not conn.closed:
        conn.close()


def ezsaw_default_connect(config=None):
    """Return a DB connection from the pool (or a fresh one if pool is off).

    DB credentials are resolved in order of precedence:
      1. Environment variables (EZ_PG_DB, EZ_PG_USER, EZ_PG_PASS, EZ_PG_HOST, EZ_PG_PORT)
      2. Config file values
    """
    if config is None:
        config = PGDB_CONFIG
    pool = _get_pool()
    if pool is not None:
        return pool.getconn()
    return psycopg.connect(
        dbname=os.environ.get('EZ_PG_DB') or config['EZ_PG_DB'],
        user=os.environ.get('EZ_PG_USER') or config['EZ_PG_USER'],
        password=os.environ.get('EZ_PG_PASS') or config['EZ_PG_PASS'],
        host=os.environ.get('EZ_PG_HOST') or config['EZ_PG_HOST'],
        port=os.environ.get('EZ_PG_PORT') or config.get('EZ_PG_PORT', 5432)
    )


def _quote_identifier(name):
    """Wrap an SQL identifier in double-quotes for safe use in queries."""
    return f'"{name}"'


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class test_case:
    """Represents a single door check measurement with tolerance bounds."""

    def __init__(self, test_name, x, x_unit,
                 y_low, y, y_high, y_unit, vin, door_location,
                 make=None, model=None, mandate=None):
        self.vehicle = vin
        self.location = door_location
        self.name = test_name
        self.result_x = x
        self.result_x_unit = x_unit
        self.result_y_lower = y_low
        self.result_y = y
        self.result_y_upper = y_high
        self.result_y_unit = y_unit
        self.make = make
        self.model = model
        self.mandate = mandate

        self.out_of_tolerance = (
            self.result_y < self.result_y_lower
            or self.result_y > self.result_y_upper
        )


# ---------------------------------------------------------------------------
# Constructors / conversion
# ---------------------------------------------------------------------------

def init_test_case(row):
    """Convert a raw query result dict into a test_case instance."""
    return test_case(
        row['test_name'],
        row['result_x'],
        row['result_x_unit'],
        row['result_y_lower_lim'],
        row['result_y'],
        row['result_y_upper_lim'],
        row['result_y_unit'],
        row['vin'],
        row['door_location'],
        make=row.get('make'),
        model=row.get('model'),
        mandate=row.get('manufacture_date'),
    )


def init_test_case_list(raw_entries):
    """Convert a list of raw query result dicts into test_case instances."""
    return [init_test_case(entry) for entry in raw_entries]


def matricize_test_cases(stats):
    """Convert a list of test_case objects into a (2, n) numpy matrix
    of [result_x, result_y] values for plotting.

    If the first entry has a non-empty name, only consecutive entries
    matching that name are included. If the name is empty, all entries
    are included.
    """
    if stats is None:
        return np.zeros((2, 0))

    if not stats:
        return np.zeros((2, 0))

    matrix = np.zeros((2, len(stats)))
    target_name = stats[0].name
    col_idx = 0

    if target_name == '':
        for stat in stats:
            matrix[0, col_idx] = stat.result_x if stat.result_x is not None else np.nan
            matrix[1, col_idx] = stat.result_y if stat.result_y is not None else np.nan
            col_idx += 1
    else:
        for stat in stats:
            if stat.name != target_name:
                break
            matrix[0, col_idx] = stat.result_x if stat.result_x is not None else np.nan
            matrix[1, col_idx] = stat.result_y if stat.result_y is not None else np.nan
            col_idx += 1

    return matrix[:, :col_idx]


# ---------------------------------------------------------------------------
# SQL query builders
# ---------------------------------------------------------------------------

def _select_columns(joint, stat):
    """Return the shared SELECT column list for outlier queries."""
    return f"""
        {joint}.door        AS door_location,
        {stat}.name         AS test_name,
        {stat}.x            AS result_x,
        {stat}.x_unit       AS result_x_unit,
        {stat}.y_lower      AS result_y_lower_lim,
        {stat}.y            AS result_y,
        {stat}.y_upper      AS result_y_upper_lim,
        {stat}.y_unit       AS result_y_unit,
        {joint}.vin         AS vin
    """


def build_outlier_query(config):
    """Build a query that finds all outlier rows for a single VIN.

    Returns rows where the dependent variable (y) is outside tolerance bounds.
    """
    joint = _quote_identifier(config['EZ_JOINT_TABLE_NAME'])
    stat = _quote_identifier(config['EZ_STAT_TABLE_NAME'])
    fk = _quote_identifier(config['EZ_JOINT_TABLE_STAT_FK'])
    pk = _quote_identifier(config['EZ_STAT_TABLE_PK'])
    vin = _quote_identifier(config['EZ_VEHICLES_PK'])
    door = _quote_identifier(config['EZ_JOINT_TABLE_DOOR_LOCATION_FIELD'])
    name = _quote_identifier(config['EZ_STAT_NAME_FIELD'])
    x = _quote_identifier(config['EZ_STAT_INDEPENDENT_VAR_FIELD'])
    x_unit = _quote_identifier(config['EZ_STAT_INDEPENDENT_VAR_UNIT_FIELD'])
    y_lower = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_LOWER_LIM_FIELD'])
    y = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_FIELD'])
    y_upper = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_UPPER_LIM_FIELD'])
    y_unit = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_UNIT_FIELD'])
    vehicles = _quote_identifier(config['EZ_VEHICLES_TABLE_NAME'])
    make = _quote_identifier(config['EZ_VEHICLES_MAKE_FIELD'])
    model = _quote_identifier(config['EZ_VEHICLES_MODEL_FIELD'])
    man_date = _quote_identifier(config['EZ_VEHICLES_MAN_DATE_FIELD'])

    return f"""
    SELECT
        {joint}.{door}   AS door_location,
        {stat}.{name}    AS test_name,
        {stat}.{x}       AS result_x,
        {stat}.{x_unit}  AS result_x_unit,
        {stat}.{y_lower} AS result_y_lower_lim,
        {stat}.{y}       AS result_y,
        {stat}.{y_upper} AS result_y_upper_lim,
        {stat}.{y_unit}  AS result_y_unit,
        {joint}.{vin}    AS vin,
        {vehicles}.{make}  AS make,
        {vehicles}.{model} AS model,
        {vehicles}.{man_date} AS manufacture_date
    FROM {joint}
    JOIN {stat} ON {joint}.{fk} = {stat}.{pk}
    JOIN {vehicles} ON {joint}.{vin} = {vehicles}.{vin}
    WHERE ({stat}.{y} < {stat}.{y_lower} OR {stat}.{y} > {stat}.{y_upper})
    AND {joint}.{vin} = %s
    """


def vin_query(vin, config=None):
    """Query outlier results for a specific VIN."""
    if config is None:
        config = PGDB_CONFIG
    query = build_outlier_query(config)
    conn = ezsaw_default_connect(config)
    try:
        with conn.cursor() as cur:
            cur.execute(query, (vin,))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        _return_conn(conn)


def build_outlier_query_by_vehicle(config):
    """Build a query that finds outlier rows for a make/model/year combination.

    Joins the vehicles table to filter by make, model, and manufacture year.
    """
    joint = _quote_identifier(config['EZ_JOINT_TABLE_NAME'])
    stat = _quote_identifier(config['EZ_STAT_TABLE_NAME'])
    fk = _quote_identifier(config['EZ_JOINT_TABLE_STAT_FK'])
    pk = _quote_identifier(config['EZ_STAT_TABLE_PK'])
    vin = _quote_identifier(config['EZ_VEHICLES_PK'])
    door = _quote_identifier(config['EZ_JOINT_TABLE_DOOR_LOCATION_FIELD'])
    name = _quote_identifier(config['EZ_STAT_NAME_FIELD'])
    x = _quote_identifier(config['EZ_STAT_INDEPENDENT_VAR_FIELD'])
    x_unit = _quote_identifier(config['EZ_STAT_INDEPENDENT_VAR_UNIT_FIELD'])
    y_lower = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_LOWER_LIM_FIELD'])
    y = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_FIELD'])
    y_upper = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_UPPER_LIM_FIELD'])
    y_unit = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_UNIT_FIELD'])
    vehicles = _quote_identifier(config['EZ_VEHICLES_TABLE_NAME'])
    make = _quote_identifier(config['EZ_VEHICLES_MAKE_FIELD'])
    model = _quote_identifier(config['EZ_VEHICLES_MODEL_FIELD'])
    date = _quote_identifier(config['EZ_VEHICLES_MAN_DATE_FIELD'])

    return f"""
    SELECT
        {joint}.{door}   AS door_location,
        {stat}.{name}    AS test_name,
        {stat}.{x}       AS result_x,
        {stat}.{x_unit}  AS result_x_unit,
        {stat}.{y_lower} AS result_y_lower_lim,
        {stat}.{y}       AS result_y,
        {stat}.{y_upper} AS result_y_upper_lim,
        {stat}.{y_unit}  AS result_y_unit,
        {joint}.{vin}    AS vin,
        {vehicles}.{make}  AS make,
        {vehicles}.{model} AS model,
        {vehicles}.{date}  AS manufacture_date
    FROM {joint}
    JOIN {stat} ON {joint}.{fk} = {stat}.{pk}
    JOIN {vehicles} ON {joint}.{vin} = {vehicles}.{vin}
    WHERE ({stat}.{y} < {stat}.{y_lower} OR {stat}.{y} > {stat}.{y_upper})
    AND {vehicles}.{make} = %s
    AND {vehicles}.{model} = %s
    AND EXTRACT(YEAR FROM {vehicles}.{date})::int = %s
    """


def vehicle_query(make, model, year, config=None):
    """Query outlier results for a specific make/model/year."""
    if config is None:
        config = PGDB_CONFIG
    query = build_outlier_query_by_vehicle(config)
    conn = ezsaw_default_connect(config)
    try:
        with conn.cursor() as cur:
            cur.execute(query, (make, model, year))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        _return_conn(conn)


def build_stat_family_query(config):
    """Build a query that fetches all measurements for a specific test name
    and door location (the "family" of related stats for a scatter plot)."""
    joint = _quote_identifier(config['EZ_JOINT_TABLE_NAME'])
    stat = _quote_identifier(config['EZ_STAT_TABLE_NAME'])
    fk = _quote_identifier(config['EZ_JOINT_TABLE_STAT_FK'])
    pk = _quote_identifier(config['EZ_STAT_TABLE_PK'])
    vin = _quote_identifier(config['EZ_VEHICLES_PK'])
    door = _quote_identifier(config['EZ_JOINT_TABLE_DOOR_LOCATION_FIELD'])
    name = _quote_identifier(config['EZ_STAT_NAME_FIELD'])
    x = _quote_identifier(config['EZ_STAT_INDEPENDENT_VAR_FIELD'])
    x_unit = _quote_identifier(config['EZ_STAT_INDEPENDENT_VAR_UNIT_FIELD'])
    y_lower = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_LOWER_LIM_FIELD'])
    y = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_FIELD'])
    y_upper = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_UPPER_LIM_FIELD'])
    y_unit = _quote_identifier(config['EZ_STAT_DEPENDENT_VAR_UNIT_FIELD'])

    return f"""
    SELECT
        {joint}.{door}   AS door_location,
        {stat}.{name}    AS test_name,
        {stat}.{x}       AS result_x,
        {stat}.{x_unit}  AS result_x_unit,
        {stat}.{y_lower} AS result_y_lower_lim,
        {stat}.{y}       AS result_y,
        {stat}.{y_upper} AS result_y_upper_lim,
        {stat}.{y_unit}  AS result_y_unit,
        {joint}.{vin}    AS vin
    FROM {joint}
    JOIN {stat} ON {joint}.{fk} = {stat}.{pk}
    WHERE {stat}.{name} = %s
    AND {joint}.{door} = %s
    """


def fetch_stat_family(test_name, door_location, config=None):
    """Fetch the full measurement family for a given test name and door."""
    if config is None:
        config = PGDB_CONFIG
    query = build_stat_family_query(config)
    conn = ezsaw_default_connect(config)
    try:
        with conn.cursor() as cur:
            cur.execute(query, (test_name, door_location))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        _return_conn(conn)


# ---------------------------------------------------------------------------
# Vehicle lookups (for make/model/year cascading dropdowns)
# ---------------------------------------------------------------------------

def fetch_makes(config=None):
    """Return a sorted list of distinct vehicle makes."""
    if config is None:
        config = PGDB_CONFIG
    table = _quote_identifier(config['EZ_VEHICLES_TABLE_NAME'])
    make_col = _quote_identifier(config['EZ_VEHICLES_MAKE_FIELD'])
    conn = ezsaw_default_connect(config)
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT DISTINCT {make_col} FROM {table} ORDER BY {make_col}")
            return [row[0] for row in cur.fetchall()]
    finally:
        _return_conn(conn)


def fetch_models(make, config=None):
    """Return a sorted list of distinct models for a given make."""
    if config is None:
        config = PGDB_CONFIG
    table = _quote_identifier(config['EZ_VEHICLES_TABLE_NAME'])
    make_col = _quote_identifier(config['EZ_VEHICLES_MAKE_FIELD'])
    model_col = _quote_identifier(config['EZ_VEHICLES_MODEL_FIELD'])
    conn = ezsaw_default_connect(config)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT DISTINCT {model_col} FROM {table} WHERE {make_col} = %s ORDER BY {model_col}",
                (make,),
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        _return_conn(conn)


def fetch_years(make, model, config=None):
    """Return a sorted list of distinct manufacture years for a make/model."""
    if config is None:
        config = PGDB_CONFIG
    table = _quote_identifier(config['EZ_VEHICLES_TABLE_NAME'])
    make_col = _quote_identifier(config['EZ_VEHICLES_MAKE_FIELD'])
    model_col = _quote_identifier(config['EZ_VEHICLES_MODEL_FIELD'])
    date_col = _quote_identifier(config['EZ_VEHICLES_MAN_DATE_FIELD'])
    conn = ezsaw_default_connect(config)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT DISTINCT EXTRACT(YEAR FROM {date_col})::int FROM {table} "
                f"WHERE {make_col} = %s AND {model_col} = %s ORDER BY 1",
                (make, model),
            )
            return [row[0] for row in cur.fetchall()]
    finally:
        _return_conn(conn)


# ---------------------------------------------------------------------------
# Stat ordering (JSON-driven traversal)
# ---------------------------------------------------------------------------

_STAT_ORDERING_PATH = Path(__file__).resolve().parent.parent.parent / 'config' / 'stat_ordering.json'


def load_stat_ordering():
    """Load the stat_ordering.json config. Returns default structure if
    the file is missing or corrupt."""
    try:
        with open(_STAT_ORDERING_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {'default_order': 'alphabetical', 'branches': []}


def apply_stat_ordering(stats):
    """Reorder a list of test_case objects according to stat_ordering.json.

    For each branch rule, if the set of stat names in the current selection
    is a superset of the branch's match list, the stats are reordered to
    match the branch's order. Unknown names are appended at the end in
    alphabetical order. Falls back to alphabetical if no branch matches.
    """
    if not stats:
        return stats

    ordering = load_stat_ordering()
    stat_names = [s.name for s in stats]
    name_set = set(stat_names)

    # Try to find a matching branch
    for branch in ordering.get('branches', []):
        match_set = set(branch['match'])
        if match_set.issubset(name_set):
            ordered = []
            remaining = {s.name for s in stats}
            for name in branch['order']:
                if name in remaining:
                    ordered.extend(s for s in stats if s.name == name)
                    remaining.discard(name)
            # Append any names not in the branch order, sorted alphabetically
            for name in sorted(remaining):
                ordered.extend(s for s in stats if s.name == name)
            return ordered

    # Default: alphabetical by name
    return sorted(stats, key=lambda s: s.name)



