"""
Debug and diagnostic tools extracted from main.py.

These functions were originally methods on the intro_form class.
They reference the older API (vin_fetch_outliers, self.edit.text())
and are preserved here for reference and future debugging use.
"""

import pyqtgraph as pg
from src.core.auto_stat_facilities import init_test_case


def display_failed_graphs(vin_fetch_outliers, edit_widget):
    """Print query results and flag outliers that exceed tolerance."""
    vin_selected = edit_widget.text()
    outliers = vin_fetch_outliers(vin_selected)
    print('[DBG] Query Return: ')
    print(outliers)
    for i in outliers:
        test_results = init_test_case(i, vin_selected)
        if test_results.out_of_tolerance:
            # TODO: fetch the full results for that stat name
            # TODO: graph the full results
            # TODO: paint vin_selected a different colour than the rest
            pass


def display_related_stats(vin_fetch_outliers, edit_widget, tests):
    """
    Given a specific stat, display all other stats that are
    within that stat case.
    """
    vin_selected = edit_widget.text()
    outliers = vin_fetch_outliers(vin_selected)
    for outlier in outliers:
        stat = init_test_case(outlier, vin_selected)
        related_stats = stat  # join_stat_with_table(stat) -- old API
        print(related_stats)
    print("\n\n---------TEST_RESULTS----------")
    i_cnt = 0
    for i in tests:
        test_results = init_test_case(i, vin_selected)
        i_cnt = i_cnt + 1

        if test_results.out_of_tolerance:
            print(str(i[0]) + ': FAILED.')
        else:
            print(str(i[0]) + ': PASSED')
        print("Set: " + str(i_cnt))
        print("VIN: " + str(test_results.vehicle) + "\n"
              "y val: " + str(test_results.result_y) + "\n"
              "upper_lim: " + str(test_results.result_y_upper) + "\n"
              "lower_lim: " + str(test_results.result_y_lower) + "\n")


def plot_stats(vin_fetch_outliers, edit_widget):
    """Given a list of test cases, plot each one."""
    vin_selected = edit_widget.text()
    outliers = vin_fetch_outliers(vin_selected)
    stats_graph = pg.plot(title="testgraph1")
    for outlier in outliers:
        stat = init_test_case(outlier, vin_selected)
        # stat_graph(stat)  -- old API, function not defined
        pass


def display_entry_table(vin_fetch_outliers, edit_widget, vin):
    """Print full query results and tolerance status for a VIN."""
    vin_selected = edit_widget.text()
    outliers = vin_fetch_outliers(vin)
    print("[DBG] Query Return: ")
    print(outliers)
    print("\n\n---------TEST_RESULTS----------")
    i_cnt = 0
    for i in outliers:
        test_results = init_test_case(i, vin_selected)
        i_cnt = i_cnt + 1

        if test_results.out_of_tolerance:
            print(str(i[0]) + ': FAILED.')
        else:
            print(str(i[0]) + ': PASSED')
        print("Set: " + str(i_cnt))
        print("VIN: " + str(test_results.vehicle) + "\n"
              "y val: " + str(test_results.result_y) + "\n"
              "upper_lim: " + str(test_results.result_y_upper) + "\n"
              "lower_lim: " + str(test_results.result_y_lower) + "\n")


def dbg_print_vin_fetch(vin_fetch_outliers, edit_widget):
    """Print raw VIN fetch output with full field arguments."""
    # AUTO_STAT_FIELDS, 'auto_door_stats', 'steps' -- old API args
    print(vin_fetch_outliers(edit_widget.text()))
