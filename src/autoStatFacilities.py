import psycopg
import numpy as np
from io import StringIO
import re
'''
def fetch_dataset(step_name: str):
def graph_dataset(results: dict, stepname: str, tol_lower: float, tol_upper: float, outlier_step: int)
def prompt_window(message: str)
def in_tolerance(vin: str):
'''
AUTO_STAT_FIELDS = ('auto_door_stat_name', 'result_x', 'result_x_unit', 'result_y_lower_lim',
                    'result_y', 'result_y_upper_lim', 'result_y_unit', 'auto_door_stat_id')

X_FIELD_POSITION = 1
Y_FIELD_POSITION = 4
NAME_FIELD_POSITION = 0
'''
test_case:
A structure to help with internal referencing of data mostly. At this time it is unknown if
there will be a high performance price with this class implementation... 
'''
class test_case:
    def __init__(self, test_name, x, x_unit, 
                y_low, y, y_high, y_unit, vin):
       self.name = test_name 
       self.result_x = x
       self.result_x_unit = x_unit
       self.result_y_lower = y_low
       self.result_y = y
       self.result_y_upper = y_high
       self.result_y_unit = y_unit
       self.vehicle = vin

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
        f'vehicle: ' + str(self.vehicle) + '\n')

'''
init_test_case():
Wrapper function to make the test case instances cleaner
Strongly depends on the AUTO_STAT_FIELDS to remain the same.
'''
def init_test_case(st: tuple, vin: str) -> test_case:
    print(f'init_test_case(): ')
    print(st)
    return test_case(st[0], st[1], st[2], st[3], st[4], st[5], st[6], vin)

def parse_test_case_list(st: list):
    test_cases = []
    for i in st:
        test_cases.append(test_case(i, ))



# Matricize large selection of raw query data list
def matricize_test_cases(stats: list, test_name: str = '') -> np.array:
    assert(len(stats) > 10)
    mat = np.zeros((2, len(stats)))
    # print ('[DBG] MATRIX CHECK')
    # print(mat)
    x = 0
    y = 1
    i = 0
    if test_name == '':
        for stat in stats:
            mat[x, i] = stat[X_FIELD_POSITION]
            mat[y, i] = stat[Y_FIELD_POSITION]
            i += 1
    else:
        for stat in stats:
            if stat[NAME_FIELD_POSITION] != test_name:
                return mat
            else:
                mat[x, i] = stat[X_FIELD_POSITION]
                mat[y, i] = stat[Y_FIELD_POSITION]
                i += 1
    print ('[DBG] MATRIX CHECK 2')
    print(mat)
    return mat


'''
pull_decimal():
This is quite possibly the most unneccessary function here, as it seems data types
are actually retained by psycopg and autoparsed through to python upon the execution
of a SELECT statement. Good to know!!
'''
def pull_decimal(sql_entry: str) -> float | None: # convert the sql output string to float group
    print(f'[DBG] pull_decimal sql_entry: ')
    print(sql_entry)
    match = re.search(r'?*\d+\.\d+', sql_entry)
    if match:
        return float(match.group())
    return None

# This is where the default SQL database is set, in the future will be pulled from config file
def ezsaw_default_connect():
    return psycopg.connect(
        dbname='ezsaw3',
        user='postgres',
        password='postgres',
        host='localhost'
    )


'''
vin_fetch_outliers():
Fetches the failed results for which a given vehicles dependant variables falls out of tolerances. 
The psycopg syntax makes this rather nonobvious through no fault of it's own.
'''
def vin_fetch_outliers(vin: str, fields: tuple = AUTO_STAT_FIELDS, 
                        table1: str = 'auto_door_stats', table2: str = 'steps') -> list:
    conn = ezsaw_default_connect()
    cur = conn.cursor()

    cur.execute ('SELECT ' + ", ".join(fields) + ' FROM ' + table1 + ' JOIN ' + table2 + ' ON ' + table1 + '.auto_door_stat_id' + ' = ' + 
                table2 + '.auto_door_stat' + ' WHERE ' + table2 + '.vin = \'' + vin + '\';')  # TODO: make this function more generic

    return cur.fetchall()  # return of a tuple of the VINs occurences in the steps table

def join_stat_with_table(stat: test_case, fields: tuple = AUTO_STAT_FIELDS,
                        table: str = 'auto_door_stats', name_field: str = 'auto_door_stat_name') -> list:
    conn = ezsaw_default_connect()
    cur = conn.cursor()
    cur.execute('SELECT ' + ", ".join(fields) + ' FROM ' + table + ' WHERE ' + name_field + ' = \'' + stat.name + '\';')
    return cur.fetchall()

def results_dump(results):
    i_cnt = 0
    if results == []:
        raise ValueError("VIN not found in database") 
    else:
        # print("DEBUG: Unsorted: " + str(results))
        # print("\n\n")

        print("\n\n---------TEST_RESULTS----------")
        for i in results:
            test_results = test_case(i[0], i[1], i[2], i[3], i[4])
            i_cnt = i_cnt + 1

            print("Set #" + str(i_cnt))
            if test_results.out_of_tolerance:
                print(str(i[0]) + ": failed.")
            else:
                print(str(i[0]) + ": passed")

            print("VIN: " + str(test_results.vin) + "\n"
                  "y val: " + str(test_results.result) + "\n" 
                  "upper_lim: " + str(test_results.upper_limit) + "\n" 
                  "lower_lim: " + str(test_results.lower_limit) + "\n")

def main():
    outliers = vin_fetch_outliers('1HGCM82633A004352')
    print(outliers)
main()