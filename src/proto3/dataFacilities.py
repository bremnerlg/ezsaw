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



class test_case:
    def __init__(self, step_name: str, y: float, 
    lower: float, upper: float, v: str):
       self.name = step_name
       self.result = y
       self.lower_limit = lower
       self.upper_limit = upper
       self.vin = v
       if self.result < self.lower_limit or self.result > self.upper_limit:
            self.out_of_tolerance = True
       else:
            self.out_of_tolerance = False 



def pull_decimal(sql_entry: str) -> float | None: # convert the sql output string to float group
    match = re.search(r'?*\d+\.\d+', sql_entry)
    if match:
        return float(match.group())
    return None

def vin_fetch(vin: str, fields: list, table: str) -> tuple:
    conn = psycopg.connect(
        dbname="ezsaw_proto",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    cur = conn.cursor()
    # painful reminder that for some reason I decided to put lower before upper
    cur.execute ('SELECT ' + ", ".join(fields) + ' FROM ' + table)
    return cur.fetchall()  # return of a tuple of the VINs occurences in the steps table

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
    std_fields = ['step_name', 'y', 'lower_lim', 'upper_lim', 'vin']
    results_dump(vin_fetch('1VWBT7A36EC345678', std_fields, 'steps'))
main()