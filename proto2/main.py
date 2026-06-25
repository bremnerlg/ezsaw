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
    def __init__(self, y: float, upper: float, lower: float):
       self.result = y
       self.upper_limit = upper
       self.lower_limit = lower
       if self.result < self.lower_limit or self.result > self.upper_limit:
            self.out_of_tolerance = True
       else:
            self.out_of_tolerance = False 



def pull_decimal(sql_entry: str) -> float | None: # convert the sql output string to float group
    match = re.search(r'?*\d+\.\d+', sql_entry)
    if match:
        return float(match.group())
    return None



def vin_fetch(vin: str) -> list: # return is of form ((y1, lower1, upper1), (y2, lower2, upper2), ...)
    conn = psycopg.connect(
        dbname="ezsaw_proto",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    cur = conn.cursor()
    # painful reminder that for some reason I decided to put lower before upper
    cur.execute ("SELECT y, upper_lim, lower_lim, step_name FROM steps WHERE vin = '" + vin + "'")
    return cur.fetchall()  # return of a tuple of the VINs occurences in the steps table



def main():
    user_in = str(input("Enter a VIN: "))

    i_cnt = 0
    results = vin_fetch(user_in)
    if results == []:
        raise ValueError("VIN not found in database") 
    else:
        # print("DEBUG: Unsorted: " + str(results))
        # print("\n\n")

        print("\n\n---------TEST_RESULTS----------")
        print("Vehicle: " + user_in)
        for i in results:
            test_results = test_case(i[0], i[1], i[2]) # assign a test case with y, upper_lim, lower_lim
            i_cnt = i_cnt + 1

            if test_results.out_of_tolerance:
                print(str(i[3]) + ": failed.")
            else:
                print(str(i[3]) + ": passed")

            print("Set " + str(i_cnt))
            print("y val: " + str(test_results.result) + "\n" 
                  "upper_lim: " + str(test_results.upper_limit) + "\n" 
                  "lower_lim: " + str(test_results.lower_limit) + "\n")
main()