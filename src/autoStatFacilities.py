import psycopg
import pandas as pd
from io import StringIO
import re
'''
def fetch_dataset(step_name: str):
def graph_dataset(results: dict, stepname: str, tol_lower: float, tol_upper: float, outlier_step: int)
def prompt_window(message: str)
def in_tolerance(vin: str):
'''

AUTO_STAT_FIELDS = ('auto_door_stat_name', 'result_x', 'result_x_unit', 'result_y_lower_lim',
                    'result_y', 'result_y_upper_lim', 'result_y_unit', 'vin')

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

'''
vin_fetch_outliers():
Fetches the failed results for which a given vehicles dependant variables falls out of tolerances. 
The psycopg syntax makes this rather nonobvious through no fault of it's own.
'''
def vin_fetch_outliers(vin: str, fields: tuple = AUTO_STAT_FIELDS, 
                        table1: str = 'auto_door_stats', table2: str = 'steps') -> list:

    conn = psycopg.connect( # eventually the JSON will be where the db server config is pulled from
        dbname="ezsaw3",    # Probably will be done by means of helper function(s)
        user="postgres",
        password="postgres",
        host="localhost"
    )

    cur = conn.cursor()
    # painful reminder that for some reason I decided to put lower before upper
    cur.execute ('SELECT ' + ", ".join(fields) + ' FROM ' + table1 + ' JOIN ' + table2 + ' ON ' + table1 + '.auto_door_stat_id' + ' = ' + 
                table2 + '.auto_door_stat' + ' WHERE ' + table2 + '.vin = \'' + vin + '\';') 

    return cur.fetchall()  # return of a tuple of the VINs occurences in the steps table

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
       self.result_x_unit = unit_x 
       self.result_y_lower = y_low
       self.result_y = y
       self.result_y_upper = y_high
       self.result_y_unit = y_unit
       self.vehicle = vin

       if self.result_y < self.result_y_lower or self.result_y > self.result_y_upper:
            self.out_of_tolerance = True
       else:
            self.out_of_tolerance = False 

'''
init_test_case():
Wrapper function to make the test case instances cleaner
Strongly depends on the AUTO_STAT_FIELDS to remain the same.
'''
def init_test_case(st: tuple, vin: str) -> test_case:
    return test_case(st[0], st[1], st[2], st[3], st[4], st[5], st[6], vin)

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

'''
def main():
    std_fields = ['auto_door_stat_name', 'result_x', 'result_x_unit', 'result_y_lower_lim', 'result_y', 
        'result_y_upper_lim', 'result_y_unit' ]
    results_dump(vin_fetch('1VWBT7A36EC345678', std_fields, 'steps'))
main()
'''