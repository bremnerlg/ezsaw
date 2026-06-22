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
    def __init__(self, result: float, upper_limit: float, lower_limit: float, ):
        self.__result = result
        self.__upper_limit = upper_limit 
        self.__lower_limit = lower_limit
        if result < lower_limit or result > upper_limit:
            self.__out_of_tolerance = True
            



def pull_decimal(sql_entry: str) -> float | None: # convert the sql output string to float
    match = re.search(r'?*\d+\.\d+', sql_entry)
    if match:
        return float(match.group())
    return None

def find_outliers()

def in_tolerance(y, upper, lower) -> bool:
    if float(y) > float(upper) or float(y) < (lower):
        return False
    return True

def vin_fetch(vin: str) -> tuple: # return is of form ((y1, lower1, upper1), (y2, lower2, upper2), ...)
    conn = psycopg.connect(
        dbname="learning_db",
        user="postgres",
        password="postgres",
        host="localhost"
    )
    cur = conn.cursor()

    cur.execute ("SELECT y, lower, upper FROM steps WHERE vin = '" + vin + "'")
    return cur.fetchall()  # return of a tuple of the VINs occurences in the steps table


def main():
    user_in = str(input("Enter a VIN: "))

    results = vin_fetch(user_in)
    if results == None:
        raise ValueError("VIN not found in database") 
    else:
        print("All results:")
        print(results)
        print("First result")
        print(results[0][0])
main()