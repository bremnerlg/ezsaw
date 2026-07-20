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


def display_test_results(edit_widget, tests, vin=None):
    """Print full query results and tolerance status for a VIN or test list."""
    if vin is not None:
        outliers = vin_query(vin)
        print("[DBG] Query Return: ")
        print(outliers)
        tests = outliers
    print("\n\n---------TEST_RESULTS----------")
    for i_cnt, row in enumerate(tests, 1):
        test_results = init_test_case(row)
        status = 'FAILED' if test_results.out_of_tolerance else 'PASSED'
        print(f"{row['test_name']}: {status}")
        print(f"Set: {i_cnt}")
        print(f"VIN: {test_results.vehicle}\n"
              f"y val: {test_results.result_y}\n"
              f"upper_lim: {test_results.result_y_upper}\n"
              f"lower_lim: {test_results.result_y_lower}\n")


def plot_stats(edit_widget):
    """Given a list of test cases, plot each one."""
    vin_selected = edit_widget.text()
    outliers = vin_query(vin_selected)
    pg.plot(title="testgraph1")
    for outlier in outliers:
        tc = init_test_case(outlier)
        print(f"Plotting: {tc.name} ({tc.result_x}, {tc.result_y})")


def dbg_print_vin_fetch(edit_widget):
    """Print raw VIN fetch output with full field arguments."""
    print(vin_query(edit_widget.text()))
