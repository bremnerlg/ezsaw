"""
Debug and diagnostic tools for EZSAW.

These functions operate on PyQt5 widget instances and the current
database API (vin_query, init_test_case from auto_stat_facilities).
"""

import pyqtgraph as pg
from src.core.auto_stat_facilities import vin_query, init_test_case


def display_failed_graphs(edit_widget):
    """Print query results and flag outliers that exceed tolerance."""
    vin_selected = edit_widget.text()
    outliers = vin_query(vin_selected)
    print('[DBG] Query Return: ')
    print(outliers)
    for row in outliers:
        test_results = init_test_case(row)
        if test_results.out_of_tolerance:
            # TODO: fetch the full results for that stat name
            # TODO: graph the full results
            # TODO: paint vin_selected a different colour than the rest
            pass


def display_related_stats(edit_widget, tests):
    """
    Given a specific stat, display all other stats that are
    within that stat case.
    """
    vin_selected = edit_widget.text()
    outliers = vin_query(vin_selected)
    for outlier in outliers:
        stat = init_test_case(outlier)
        print(stat.name)
    print("\n\n---------TEST_RESULTS----------")
    i_cnt = 0
    for row in tests:
        test_results = init_test_case(row)
        i_cnt = i_cnt + 1

        if test_results.out_of_tolerance:
            print(str(row['test_name']) + ': FAILED.')
        else:
            print(str(row['test_name']) + ': PASSED')
        print("Set: " + str(i_cnt))
        print("VIN: " + str(test_results.vehicle) + "\n"
              "y val: " + str(test_results.result_y) + "\n"
              "upper_lim: " + str(test_results.result_y_upper) + "\n"
              "lower_lim: " + str(test_results.result_y_lower) + "\n")


def plot_stats(edit_widget):
    """Given a list of test cases, plot each one."""
    vin_selected = edit_widget.text()
    outliers = vin_query(vin_selected)
    pg.plot(title="testgraph1")
    for outlier in outliers:
        init_test_case(outlier)


def display_entry_table(edit_widget, vin):
    """Print full query results and tolerance status for a VIN."""
    outliers = vin_query(vin)
    print("[DBG] Query Return: ")
    print(outliers)
    print("\n\n---------TEST_RESULTS----------")
    i_cnt = 0
    for row in outliers:
        test_results = init_test_case(row)
        i_cnt = i_cnt + 1

        if test_results.out_of_tolerance:
            print(str(row['test_name']) + ': FAILED.')
        else:
            print(str(row['test_name']) + ': PASSED')
        print("Set: " + str(i_cnt))
        print("VIN: " + str(test_results.vehicle) + "\n"
              "y val: " + str(test_results.result_y) + "\n"
              "upper_lim: " + str(test_results.result_y_upper) + "\n"
              "lower_lim: " + str(test_results.result_y_lower) + "\n")


def dbg_print_vin_fetch(edit_widget):
    """Print raw VIN fetch output with full field arguments."""
    print(vin_query(edit_widget.text()))
