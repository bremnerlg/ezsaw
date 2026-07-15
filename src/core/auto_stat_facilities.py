import psycopg
from enum import Enum
import json
import numpy as np
from pathlib import Path

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / 'config'
DB_CONFIG_FILE_PATH = _CONFIG_DIR / 'db_config.json'

def load_db_config():
    with open(DB_CONFIG_FILE_PATH) as f:
        return json.load(f)

PGDB_CONFIG = load_db_config()

def ezsaw_default_connect():
    return psycopg.connect(
        dbname=PGDB_CONFIG['EZ_PG_DB'],
        user=PGDB_CONFIG['EZ_PG_USER'],
        password=PGDB_CONFIG['EZ_PG_PASS'],
        host=PGDB_CONFIG['EZ_PG_HOST']
    )

class door_location(Enum):
    DRIVER_FRONT = 'driver_front'
    DRIVER_REAR = 'driver_rear'
    PASSENGER_FRONT = 'passenger_front'
    PASSENGER_REAR = 'passenger_rear'
    REAR_HATCH = 'trunk/hatch'
    HOOD = 'hood'

class test_case:
    def __init__(self, test_name, x, x_unit,
                 y_low, y, y_high, y_unit, vin, dl):
        self.vehicle = vin
        self.location = dl
        self.name = test_name
        self.result_x = x
        self.result_x_unit = x_unit
        self.result_y_lower = y_low
        self.result_y = y
        self.result_y_upper = y_high
        self.result_y_unit = y_unit

        if self.result_y < self.result_y_lower or self.result_y > self.result_y_upper:
            self.out_of_tolerance = True
        else:
            self.out_of_tolerance = False

    def describe(self):
        print(
            f'Test Case: {self.name}\n'
            f'result_x: {self.result_x}\n'
            f'result_x_unit: {self.result_x_unit}\n'
            f'result_y_lower: {self.result_y_lower}\n'
            f'result_y: {self.result_y}\n'
            f'result_y_upper: {self.result_y_upper}\n'
            f'result_y_unit: {self.result_y_unit}\n'
            f'vehicle: {self.vehicle}\n'
            f'door location: {self.location}\n'
        )


def build_outlier_query(config):
    joint   = config['EZ_JOINT_TABLE_NAME']
    stat    = config['EZ_STAT_TABLE_NAME']
    fk      = config['EZ_JOINT_TABLE_STAT_FK']
    stat_pk = config['EZ_STAT_TABLE_PK']
    vin_pk  = config['EZ_VEHICLES_PK']
    door    = config['EZ_JOINT_TABLE_DOOR_LOCATION_FIELD']
    name    = config['EZ_STAT_NAME_FIELD']
    x       = config['EZ_STAT_INDEPENDENT_VAR_FIELD']
    x_unit  = config['EZ_STAT_INDEPENDENT_VAR_UNIT_FIELD']
    y_low   = config['EZ_STAT_DEPENDENT_VAR_LOWER_LIM_FIELD']
    y       = config['EZ_STAT_DEPENDENT_VAR_FIELD']
    y_high  = config['EZ_STAT_DEPENDENT_VAR_UPPER_LIM_FIELD']
    y_unit  = config['EZ_STAT_DEPENDENT_VAR_UNIT_FIELD']

    return f"""
    SELECT
        {joint}.{door}   AS door_location,
        {stat}.{name}    AS test_name,
        {stat}.{x}       AS result_x,
        {stat}.{x_unit}  AS result_x_unit,
        {stat}.{y_low}   AS result_y_lower_lim,
        {stat}.{y}       AS result_y,
        {stat}.{y_high}  AS result_y_upper_lim,
        {stat}.{y_unit}  AS result_y_unit,
        {joint}.{vin_pk} AS vin
    FROM {joint}
    JOIN {stat} ON {joint}.{fk} = {stat}.{stat_pk}
    WHERE ({stat}.{y} < {stat}.{y_low} OR {stat}.{y} > {stat}.{y_high})
    AND {joint}.{vin_pk} = %s
    """


def vin_query(vin, config=None):
    if config is None:
        config = PGDB_CONFIG
    query = build_outlier_query(config)
    conn = ezsaw_default_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(query, (vin,))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def build_stat_family_query(config):
    joint   = config['EZ_JOINT_TABLE_NAME']
    stat    = config['EZ_STAT_TABLE_NAME']
    fk      = config['EZ_JOINT_TABLE_STAT_FK']
    stat_pk = config['EZ_STAT_TABLE_PK']
    vin_pk  = config['EZ_VEHICLES_PK']
    door    = config['EZ_JOINT_TABLE_DOOR_LOCATION_FIELD']
    name    = config['EZ_STAT_NAME_FIELD']
    x       = config['EZ_STAT_INDEPENDENT_VAR_FIELD']
    x_unit  = config['EZ_STAT_INDEPENDENT_VAR_UNIT_FIELD']
    y_low   = config['EZ_STAT_DEPENDENT_VAR_LOWER_LIM_FIELD']
    y       = config['EZ_STAT_DEPENDENT_VAR_FIELD']
    y_high  = config['EZ_STAT_DEPENDENT_VAR_UPPER_LIM_FIELD']
    y_unit  = config['EZ_STAT_DEPENDENT_VAR_UNIT_FIELD']

    return f"""
    SELECT
        {joint}.{door}   AS door_location,
        {stat}.{name}    AS test_name,
        {stat}.{x}       AS result_x,
        {stat}.{x_unit}  AS result_x_unit,
        {stat}.{y_low}   AS result_y_lower_lim,
        {stat}.{y}       AS result_y,
        {stat}.{y_high}  AS result_y_upper_lim,
        {stat}.{y_unit}  AS result_y_unit,
        {joint}.{vin_pk} AS vin
    FROM {joint}
    JOIN {stat} ON {joint}.{fk} = {stat}.{stat_pk}
    WHERE {stat}.{name} = %s
    AND {joint}.{door} = %s
    """


def fetch_stat_family(test_name, door_location, config=None):
    if config is None:
        config = PGDB_CONFIG
    query = build_stat_family_query(config)
    conn = ezsaw_default_connect()
    try:
        with conn.cursor() as cur:
            cur.execute(query, (test_name, door_location))
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def init_test_case(row):
    return test_case(
        row['test_name'],
        row['result_x'],
        row['result_x_unit'],
        row['result_y_lower_lim'],
        row['result_y'],
        row['result_y_upper_lim'],
        row['result_y_unit'],
        row['vin'],
        row['door_location']
    )


def init_test_case_list(raw_entries):
    return [init_test_case(entry) for entry in raw_entries]


def matricize_test_cases(stats):
    if not stats:
        return np.zeros((2, 0))

    mat = np.zeros((2, len(stats)))
    test_case_name = stats[0].name
    i = 0

    if test_case_name == '':
        for stat in stats:
            mat[0, i] = stat.result_x
            mat[1, i] = stat.result_y
            i += 1
    else:
        for stat in stats:
            if stat.name != test_case_name:
                break
            mat[0, i] = stat.result_x
            mat[1, i] = stat.result_y
            i += 1

    return mat[:, :i]


def main():
    vin_entry = input('Enter a VIN: ').strip()
    if not vin_entry:
        print('No VIN entered.')
        return

    selection = vin_query(vin_entry)
    if not selection:
        print(f'No outlier results found for VIN: {vin_entry}')
        return

    test_cases = init_test_case_list(selection)
    print(f'\nFound {len(test_cases)} outlier(s) for VIN {vin_entry}:\n')
    for tc in test_cases:
        tc.describe()


if __name__ == '__main__':
    main()
