#!/usr/bin/env python3
"""Comprehensive fixer for auto door test data.

Fixes:
1. Stat ID ordering to match stat_ordering.json
2. SUV missing passenger doors (driver_front/rear, passenger_front/rear)
3. Hatchback missing rear_hatch
4. Generates corrected SQL files for all locales
"""

import re
import json
import os
import random
import csv
import io

random.seed(42)

STAT_ORDERING = [
    "Striker Alignment (Sampled)",
    "Hinge Inclination (Sampled)",
    "Hinge Bind (Sampled)",
    "Hinge and Doorcheck Performance (Sampled)",
    "Door Check Performance No Cabin (Sampled)",
    "Seal Dynamics (Sampled)",
    "Static Closing Force (Sampled)",
    "Closing Energy from First Position (Sampled)",
    "Closing Energy from Full Open (Sampled)",
]

# Current order in the data (within each 9-block)
CURRENT_ORDER = [
    "Striker Alignment (Sampled)",
    "Hinge and Doorcheck Performance (Sampled)",
    "Closing Energy from First Position (Sampled)",
    "Closing Energy from Full Open (Sampled)",
    "Hinge Inclination (Sampled)",
    "Hinge Bind (Sampled)",
    "Door Check Performance No Cabin (Sampled)",
    "Static Closing Force (Sampled)",
    "Seal Dynamics (Sampled)",
]

# Per-test-type data profiles (sampled, two_var, x_unit, y_unit)
TEST_PROFILES = {
    "Striker Alignment (Sampled)": (True, True, "newtons", "mm/s"),
    "Hinge Inclination (Sampled)": (False, False, "", "degrees"),
    "Hinge Bind (Sampled)": (False, False, "", "newtons"),
    "Hinge and Doorcheck Performance (Sampled)": (True, True, "newtons", "newtons"),
    "Door Check Performance No Cabin (Sampled)": (False, False, "", "newtons"),
    "Seal Dynamics (Sampled)": (False, False, "", "newtons"),
    "Static Closing Force (Sampled)": (False, False, "", "newtons"),
    "Closing Energy from First Position (Sampled)": (False, False, "", "joules"),
    "Closing Energy from Full Open (Sampled)": (False, False, "", "joules"),
}

# Door assignments per body type
DOOR_ASSIGNMENTS = {
    "sedan":     ["driver_front", "driver_rear", "passenger_front", "passenger_rear"],
    "coupe":     ["driver_front", "passenger_front"],
    "SUV":       ["driver_front", "driver_rear", "passenger_front", "passenger_rear", "rear_hatch"],
    "pickup":    ["driver_front", "passenger_front"],
    "hatchback": ["driver_front", "driver_rear", "passenger_front", "passenger_rear", "rear_hatch"],
}

# Locale config: table/column names
LOCALE_COLUMNS = {
    "en": {
        "table": "auto_door_stats",
        "cols": ["auto_door_stat_id", "auto_door_stat_name", "sampled", "two_var",
                  "result_x", "result_x_unit", "result_y_lower_lim", "result_y",
                  "result_y_upper_lim", "result_y_unit"],
    },
    "de": {
        "table": "statistiken_tueren_fahrzeuge",
        "cols": ["id_stat_tueren_fahrzeug", "name_stat_tueren_fahrzeug", "probenahme", "zwei_variablen",
                  "ergebnis_x", "einheit_ergebnis_x", "untere_grenze_ergebnis_y", "ergebnis_y",
                  "obere_grenze_ergebnis_y", "einheit_ergebnis_y"],
    },
    "fr": {
        "table": "stats_portes_automobiles",
        "cols": ["id_stat_porte_auto", "nom_stat_porte_auto", "échantillonné", "deux_variablés",
                  "résultat_x", "unité_résultat_x", "limite_infèreure_résultat_y", "résultat_y",
                  "limite_suptère_résultat_y", "unité_résultat_y"],
    },
    "es": {
        "table": "estadísticas_puertas_vehículos",
        "cols": ["id_estadística_puerta_vehículo", "nombre_estadística_puerta_vehículo", "muestreado", "dos_variables",
                  "resultado_x", "unidad_resultado_x", "límite_inferior_resultado_y", "resultado_y",
                  "límite_superior_resultado_y", "unidad_resultado_y"],
    },
    "nl": {
        "table": "statistieken_deuren_voertuigen",
        "cols": ["id_stat_deur_voertuig", "naam_stat_deur_voertuig", "monstergroep", "twee_variabelen",
                  "resultaat_x", "eenheid_resultaat_x", "onderste_grenslimiet_resultaat_y", "resultaat_y",
                  "bovenste_grenslimiet_resultaat_y", "eenheid_resultaat_y"],
    },
}

# Door mapping for locale SQL files
DOOR_LOCALE_MAP = {
    "en": "steps",
    "de": "schritte",
    "fr": "étapes",
    "es": "pasos",
    "nl": "stappen",
}

# Steps table column names per locale
STEPS_COLUMNS = {
    "en": ("vin", "door", "fk_steps_auto_door_stats"),
    "de": ("kennzeichen", "tuerort", "fk_schritt_stat_tueren_fahrzeug"),
    "fr": ("immatriculation", "emplacement_porte", "fk_étape_stat_porte_auto"),
    "es": ("matrícula", "ubicación puerta", "fk_paso_estadística_puerta_vehículo"),
    "nl": ("kenteken", "deurlocatie", "fk_stap_stat_deur_voertuig"),
}


def load_vehicle_data(sql_file):
    """Parse vehicles from a locale SQL file."""
    with open(sql_file) as f:
        content = f.read()

    # Find the vehicles INSERT
    for loc, spec in LOCALE_COLUMNS.items():
        if spec["table"] != "auto_door_stats" and spec["table"] != "statistiken_tueren_fahrzeuge":
            # Find this locale's vehicle table name
            continue

    # Generic approach: find INSERT INTO * that has VIN-like values
    pattern = r"INSERT INTO\s+\w+\s*\([^)]+\)\s*VALUES\s*\n((?:\s*\([^;]*?\)\s*,?\s*\n?)+)\s*;"
    matches = list(re.finditer(pattern, content, re.DOTALL | re.IGNORECASE))

    vehicles = []
    vehicle_tables = {"vehicles", "fahrzeuge", "véhicules", "vehículos", "voertuigen"}

    for m in matches:
        stmt = m.group(0)
        tbl = re.match(r"INSERT INTO\s+(\w+)", stmt, re.IGNORECASE)
        if tbl and tbl.group(1).lower() in {v.lower() for v in vehicle_tables}:
            vals_block = m.group(1)
            rows = parse_sql_rows(vals_block)
            for row in rows:
                parts = parse_csv_row(row)
                if len(parts) >= 5:
                    vin = parts[0].strip().strip("'\"")
                    make = parts[1].strip().strip("'\"")
                    model = parts[2].strip().strip("'\"")
                    body = parts[3].strip().strip("'\"")
                    date = parts[4].strip().strip("'\"")
                    vehicles.append((vin, make, model, body, date))
            break

    return vehicles


def load_existing_stats(sql_file, table_name):
    """Parse stats from a locale SQL file."""
    with open(sql_file) as f:
        content = f.read()

    pattern = re.compile(
        r'INSERT INTO\s+' + re.escape(table_name) + r'\s*\([^)]+\)\s*VALUES\s*\n((?:\s*\([^;]*?\)\s*,?\s*\n?)+)\s*;',
        re.DOTALL | re.IGNORECASE
    )
    match = pattern.search(content)
    if not match:
        return None

    vals_block = match.group(1)
    rows = parse_sql_rows(vals_block)
    stats = []
    for row in rows:
        parts = parse_csv_row(row)
        if len(parts) >= 10:
            stats.append(parts)
    return stats


def parse_sql_rows(vals_block):
    """Parse rows from SQL VALUES block, handling quoted strings."""
    rows = []
    current = ""
    depth = 0
    in_quote = False
    for ch in vals_block:
        if ch == "'" and not in_quote:
            in_quote = True
            current += ch
        elif ch == "'" and in_quote:
            in_quote = False
            current += ch
        elif ch == '"' and not in_quote:
            in_quote = True
            current += ch
        elif ch == '"' and in_quote:
            in_quote = False
            current += ch
        elif ch == "(" and not in_quote:
            depth += 1
            if depth == 1:
                current = ""
                continue
            current += ch
        elif ch == ")" and not in_quote:
            depth -= 1
            if depth == 0:
                rows.append(current)
                current = ""
                continue
            current += ch
        elif ch == "," and depth == 0:
            continue
        else:
            current += ch
    return rows


def parse_csv_row(row_str):
    """Parse a CSV row handling quoted strings."""
    csv_reader = csv.reader(io.StringIO(row_str))
    return next(csv_reader)


def format_sql_value(val):
    """Format a SQL value."""
    v = val.strip()
    if v == "NULL":
        return "NULL"
    if v.lower() in ("true", "false"):
        return v.lower()
    try:
        float(v)
        return v
    except ValueError:
        pass
    inner = v
    if (inner.startswith("'") and inner.endswith("'")) or \
       (inner.startswith('"') and inner.endswith('"')):
        inner = inner[1:-1]
    inner = inner.replace("'", "''")
    return f"'{inner}'"


def format_row(parts):
    """Format parts into SQL tuple."""
    formatted = ", ".join(format_sql_value(p) for p in parts)
    return f"({formatted})"


def compute_stat_values(stat_name, is_two_var, block_number):
    """Generate realistic automotive door test values for a stat."""
    sampled, two_var, x_unit, y_unit = TEST_PROFILES[stat_name]

    if not is_two_var:
        result_x = float(block_number)
        x_unit_val = "NULL"
    else:
        x_unit_val = f"'{x_unit}'"
        # Use the block number to seed a deterministic but varied value
        random.seed(block_number * 1000 + hash(stat_name) % 10000)
        if stat_name == "Striker Alignment (Sampled)":
            result_x = round(random.uniform(150, 300), 1)
        elif stat_name == "Hinge and Doorcheck Performance (Sampled)":
            result_x = round(random.uniform(80, 300), 1)
        else:
            result_x = round(random.uniform(50, 300), 1)

    # Generate y values based on test type
    random.seed(block_number * 1000 + hash(stat_name) % 10000 + 500)

    if stat_name == "Striker Alignment (Sampled)":
        y_lower = round(random.uniform(30, 55), 1)
        y_result = round(y_lower + random.uniform(10, 40), 1)
        y_upper = round(y_result + random.uniform(10, 40), 1)
    elif stat_name == "Hinge Inclination (Sampled)":
        y_lower = round(random.uniform(0.1, 1.5), 1)
        y_result = round(y_lower + random.uniform(0.3, 2.5), 1)
        y_upper = round(y_result + random.uniform(0.5, 3.0), 1)
    elif stat_name == "Hinge Bind (Sampled)":
        y_lower = round(random.uniform(4, 18), 1)
        y_result = round(y_lower + random.uniform(4, 20), 1)
        y_upper = round(y_result + random.uniform(5, 25), 1)
    elif stat_name == "Hinge and Doorcheck Performance (Sampled)":
        y_lower = round(random.uniform(30, 80), 1)
        y_result = round(y_lower + random.uniform(15, 60), 1)
        y_upper = round(y_result + random.uniform(20, 70), 1)
    elif stat_name == "Door Check Performance No Cabin (Sampled)":
        y_lower = round(random.uniform(3, 12), 1)
        y_result = round(y_lower + random.uniform(3, 15), 1)
        y_upper = round(y_result + random.uniform(3, 18), 1)
    elif stat_name == "Seal Dynamics (Sampled)":
        y_lower = round(random.uniform(8, 25), 1)
        y_result = round(y_lower + random.uniform(8, 30), 1)
        y_upper = round(y_result + random.uniform(10, 40), 1)
    elif stat_name == "Static Closing Force (Sampled)":
        y_lower = round(random.uniform(5, 15), 1)
        y_result = round(y_lower + random.uniform(5, 20), 1)
        y_upper = round(y_result + random.uniform(5, 25), 1)
    elif stat_name == "Closing Energy from First Position (Sampled)":
        y_lower = round(random.uniform(1.5, 4.0), 1)
        y_result = round(y_lower + random.uniform(1.0, 3.5), 1)
        y_upper = round(y_result + random.uniform(1.5, 5.0), 1)
    elif stat_name == "Closing Energy from Full Open (Sampled)":
        y_lower = round(random.uniform(1.0, 3.0), 1)
        y_result = round(y_lower + random.uniform(0.5, 3.0), 1)
        y_upper = round(y_result + random.uniform(1.0, 4.0), 1)
    else:
        y_lower = round(random.uniform(2, 10), 1)
        y_result = round(y_lower + random.uniform(5, 20), 1)
        y_upper = round(y_result + random.uniform(5, 20), 1)

    return result_x, x_unit_val, y_lower, y_result, y_upper, f"'{y_unit}'"


def generate_stats(vehicles, locale):
    """Generate all stat data for a locale."""
    loc = LOCALE_COLUMNS[locale]
    stats = []
    stat_id = 1

    for vin, make, model, body, date in vehicles:
        doors = DOOR_ASSIGNMENTS[body]
        for door in doors:
            for pos, stat_name in enumerate(STAT_ORDERING):
                _, two_var = TEST_PROFILES[stat_name][0], TEST_PROFILES[stat_name][1]
                sampled, two_var_val, x_unit, y_unit = TEST_PROFILES[stat_name]
                is_two_var = two_var_val

                # For the body type's door count, compute block number
                # Block number = which (vin, door) combination this is for
                block_number = len(stats) // 9 + 1

                result_x, x_unit_str, y_lower, y_result, y_upper, y_unit_str = \
                    compute_stat_values(stat_name, is_two_var, block_number)

                sampled_str = "true" if sampled else "false"
                two_var_str = "true" if two_var_val else "false"

                row = [
                    str(stat_id),
                    f"'{stat_name}'",
                    sampled_str,
                    two_var_str,
                    str(result_x),
                    x_unit_str,
                    str(y_lower),
                    str(y_result),
                    str(y_upper),
                    y_unit_str,
                ]
                stats.append(row)
                stat_id += 1

    return stats


def generate_steps(stats, locale, vehicles):
    """Generate steps linking vehicles to stats."""
    loc_name = locale
    local_mode = locale if locale != "en" else None
    steps = []

    # Build mapping: (vin, door) → list of stat_ids
    # Stats are ordered by ID, which follows stat_ordering.json within each block
    # Each block of 9 corresponds to one (vin, door) combination

    vin_door_map = {}  # (vin, door) → list of stat_ids
    for vehicle_idx, (vin, make, model, body, date) in enumerate(vehicles):
        doors = DOOR_ASSIGNMENTS[body]
        for door in doors:
            key = (vin, door)

    # Actually, the order of stats matches the order of vehicles × doors × positions
    # So we can map directly
    stat_idx = 0
    for vin, make, model, body, date in vehicles:
        doors = DOOR_ASSIGNMENTS[body]
        for door in doors:
            for _ in range(9):
                steps.append((vin, door, stat_idx + 1))
                stat_idx += 1

    return steps


def build_sql_file(filepath, locale, locale_sql_file):
    """Build a complete SQL file for a locale."""
    # Read the original locale SQL file to get the full structure
    with open(locale_sql_file) as f:
        content = f.read()

    # Parse vehicles from the original
    vehicles = load_vehicle_data(locale_sql_file)
    print(f"  Loaded {len(vehicles)} vehicles for {locale}")

    # Generate stats
    stats = generate_stats(vehicles, locale)
    print(f"  Generated {len(stats)} stats for {locale}")

    # Generate steps
    steps = generate_steps(stats, locale, vehicles)
    print(f"  Generated {len(steps)} steps for {locale}")

    # Build the INSERT statements
    loc = LOCALE_COLUMNS[locale]
    col_list = ", ".join(loc["cols"])

    # Stats INSERT
    stats_lines = []
    for i, row in enumerate(stats):
        row_str = format_row(row)
        if i < len(stats) - 1:
            row_str += ","
        stats_lines.append(row_str)

    stats_insert = f"INSERT INTO {loc['table']} ({col_list})\nVALUES\n" + "\n".join(stats_lines) + ";"

    # Steps INSERT
    step_cols = STEPS_COLUMNS[locale]
    step_col_list = ", ".join(step_cols)
    step_lines = []
    for i, (vin, door, stat_id) in enumerate(steps):
        step_lines.append(f"('{vin}', '{door}', {stat_id})" + ("," if i < len(steps) - 1 else ""))

    steps_insert = f"INSERT INTO {DOOR_LOCALE_MAP[locale]} ({step_col_list})\nVALUES\n" + "\n".join(step_lines) + ";"

    # Now replace the INSERT blocks in the original content
    # Find and replace stats INSERT
    pattern = re.compile(
        r'INSERT INTO\s+' + re.escape(loc['table']) + r'\s*\([^)]+\)\s*VALUES\s*\n((?:\s*\([^;]*?\)\s*,?\s*\n?)+)\s*;',
        re.DOTALL | re.IGNORECASE
    )
    content = pattern.sub(stats_insert, content)

    # Find and replace steps INSERT
    pattern2 = re.compile(
        r'INSERT INTO\s+' + re.escape(DOOR_LOCALE_MAP[locale]) + r'\s*\([^)]+\)\s*VALUES\s*\n((?:\s*\([^;]*?\)\s*,?\s*\n?)+)\s*;',
        re.DOTALL | re.IGNORECASE
    )
    content = pattern2.sub(steps_insert, content)

    with open(filepath, "w") as f:
        f.write(content)

    return len(stats), len(steps)


def main():
    print("=" * 60)
    print("Comprehensive Auto Door Data Fixer")
    print("=" * 60)

    # Process each locale
    for locale, spec in LOCALE_COLUMNS.items():
        if locale == "en":
            sql_file = "db/ezsaw_tables.sql"
        else:
            sql_file = f"db/ezsaw_tables_{locale}.sql"

        print(f"\nProcessing {locale}: {sql_file}")
        n_stats, n_steps = build_sql_file(sql_file, locale, sql_file)
        print(f"  Written: {n_stats} stats, {n_steps} steps")

    # Also update insert_steps.sql
    print(f"\nProcessing: db/insert_steps.sql")
    n_stats, n_steps = build_sql_file("db/insert_steps.sql", "en", "db/insert_steps.sql")
    print(f"  Written: {n_stats} stats, {n_steps} steps")

    print("\n" + "=" * 60)
    print("Done! All files updated.")
    print("=" * 60)


if __name__ == "__main__":
    main()
