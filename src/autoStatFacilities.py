import psycopg
from enum import Enum
import json
import numpy as np
from io import StringIO
import re

'''
CONFIGURABLE GLOBALS FOR GENERIC SQL IMPLEMENTATION
'''
DB_CONFIG_FILE_PATH='src/db_config.JSON'
QUERY_INDICIES_FILE_PATH='src/query_indicies.JSON'
def load_db_config():
    with open(DB_CONFIG_FILE_PATH) as f:
        return json.load(f)

def query_indicies():
    with open(QUERY_INDICIES_FILE_PATH) as f:
        return json.load(f)

PGDB_CONFIG = load_db_config() # global config dictionary
PGDB_INDEX = query_indicies()
# This is where the default SQL database is set, in the future will be pulled from config file
def ezsaw_default_connect():
    return psycopg.connect(
        dbname=PGDB_CONFIG['EZ_PG_DB'],
        user=PGDB_CONFIG['EZ_PG_USER'],
        password=PGDB_CONFIG['EZ_PG_PASS'],
        host=PGDB_CONFIG['EZ_PG_HOST']
    )

'''
test_case:
A structure to help with internal referencing of data mostly. At this time it is unknown if
there will be a high performance price with this class implementation... 
'''
class door_location(Enum):
    DRIVER_FRONT = 0
    DRIVER_REAR = 1
    PASSENGER_FRONT = 2
    PASSENGER_REAR = 3
    REAR_HATCH = 4

'''
According to the definitions used in the ezsaw3 DB, a test case is comprised of a
step and auto_door_stat joined by the auto_door_stat_id.
'''
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

    def print(self):
        print(f'Test Case: ' + str(self.name) + '\n'
        f'result_x: ' + str(self.result_x) + '\n' +
        f'result_x_unit: ' + str(self.result_x_unit) + '\n' +
        f'result_y_lower: ' + str(self.result_y_lower) + '\n' +
        f'result_y: ' + str(self.result_y) + '\n' +
        f'result_y_upper: ' + str(self.result_y_upper) + '\n' +
        f'result_y_unit: ' + str(self.result_y_unit) + '\n' +
        f'vehicle: ' + str(self.vehicle) + '\n' +
        f'door location: ' + str(self.location) + '\n')

OUTLIERS_WITH_VIN_OF = f"""
SELECT * FROM {PGDB_CONFIG['EZ_JOINT_TABLE_NAME']} 
    JOIN {PGDB_CONFIG['EZ_STAT_TABLE_NAME']} 
    ON {PGDB_CONFIG['EZ_JOINT_TABLE_NAME']}.{PGDB_CONFIG['EZ_JOINT_TABLE_STAT_FK']} = 
    {PGDB_CONFIG['EZ_STAT_TABLE_NAME']}.{PGDB_CONFIG['EZ_STAT_TABLE_PK']}
    WHERE ({PGDB_CONFIG['EZ_STAT_DEPENDENT_VAR_FIELD']} <
    {PGDB_CONFIG['EZ_STAT_DEPENDENT_VAR_LOWER_LIM_FIELD']} OR
    {PGDB_CONFIG['EZ_STAT_DEPENDENT_VAR_FIELD']} >
    {PGDB_CONFIG['EZ_STAT_DEPENDENT_VAR_UPPER_LIM_FIELD']}) AND {PGDB_CONFIG['EZ_VEHICLES_PK']} = 
"""

def vin_query(vin: str, query: str=OUTLIERS_WITH_VIN_OF) -> list:
    conn = ezsaw_default_connect()

    curr = conn.cursor()
    curr.execute(query + f' \'{vin}\';')

    return curr.fetchall()

def init_test_case(raw_entry: set):
    return test_case(
        raw_entry[int(PGDB_INDEX['EZ_STAT_NAME_FIELD'])],
        raw_entry[int(PGDB_INDEX['EZ_STAT_INDEPENDENT_VAR_FIELD'])],
        raw_entry[int(PGDB_INDEX['EZ_STAT_INDEPENDENT_VAR_UNIT_FIELD'])],
        raw_entry[int(PGDB_INDEX['EZ_STAT_DEPENDENT_VAR_LOWER_LIM_FIELD'])],
        raw_entry[int(PGDB_INDEX['EZ_STAT_DEPENDENT_VAR_FIELD'])],
        raw_entry[int(PGDB_INDEX['EZ_STAT_DEPENDENT_VAR_UPPER_LIM_FIELD'])],
        raw_entry[int(PGDB_INDEX['EZ_STAT_DEPENDENT_VAR_UNIT_FIELD'])],
        raw_entry[int(PGDB_INDEX['EZ_VEHICLES_PK'])],
        raw_entry[int(PGDB_INDEX['EZ_JOINT_TABLE_DOOR_LOCATION_FIELD'])]
    )

def init_test_case_list(raw_entries: list) -> list:
    test_cases = []
    for st in raw_entries:
        test_cases.append(init_test_case(st))
    return test_cases

# Matricize large selection of raw query data list
def matricize_test_cases(stats: list)-> np.array:
    mat = np.zeros((2, len(stats)))
    # print ('[DBG] MATRIX CHECK')
    # print(mat)
    x = 0
    y = 1
    i = 0
    test_case_name = stat[0].name
    if test_case_name == '':
        for stat in stats:
            mat[x, i] = stat.result_x
            mat[y, i] = stat.result_y
            i += 1
    else:
        for stat in stats:
            if stat.name != test_case_name:
                return mat
            else:
                mat[x, i] = stat.result_x
                mat[y, i] = stat.result_y
                i += 1
    return mat

def main():
    vin_entry = input('Enter a VIN: ')
    selection = vin_query(vin_entry)
    print(selection)
    test_lists = init_test_case_list(selection)
    for i in test_lists:
        i.print()

main()