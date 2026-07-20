#!/usr/bin/env python3
"""
DEPRECATED: This script has been superseded by fix_db.py and export_fixed.py
at the project root. Kept for reference only — do not use for new work.

Generate SQL INSERT statements for auto_door_stats and steps tables.

For each vehicle-door combination, assigns 9 consecutive auto_door_stats IDs
using sequential chunking. Adds new auto_door_stats entries as needed.
"""
import warnings
warnings.warn(
    "db/generate_steps.py is deprecated — use fix_db.py or export_fixed.py instead",
    DeprecationWarning, stacklevel=2,
)

import re
import random

# Door configurations per body type
DOOR_MAP = {
    'sedan': ['driver_front', 'driver_rear', 'passenger_front', 'passenger_rear'],
    'coupe': ['driver_front', 'passenger_front'],
    'SUV': ['rear_hatch', 'hood'],
    'pickup': ['passenger_front', 'passenger_rear'],
    'hatchback': ['driver_front', 'driver_rear', 'passenger_front', 'passenger_rear'],
}

# Localized door names
DOOR_LOCALES = {
    'de': {
        'driver_front': 'vorne_fuehrer',
        'driver_rear': 'hinten_fuehrer',
        'passenger_front': 'vorne_beifahrer',
        'passenger_rear': 'hinten_beifahrer',
        'rear_hatch': 'heckklappe',
        'hood': 'haube',
    },
    'fr': {
        'driver_front': 'avant_driver',
        'driver_rear': 'arrière_driver',
        'passenger_front': 'avant_passager',
        'passenger_rear': 'arrière_passager',
        'rear_hatch': 'hayon',
        'hood': 'capot',
    },
    'es': {
        'driver_front': 'delantero_conductor',
        'driver_rear': 'trasero_conductor',
        'passenger_front': 'delantero_viajero',
        'passenger_rear': 'trasero_viajero',
        'rear_hatch': 'maletero_trasero',
        'hood': 'capó',
    },
    'nl': {
        'driver_front': 'voorste_bestuurder',
        'driver_rear': 'achterste_bestuurder',
        'passenger_front': 'voorste_passagier',
        'passenger_rear': 'achterste_passagier',
        'rear_hatch': 'achterklep',
        'hood': 'motorkap',
    },
}

# Stat categories with their properties
STAT_CATEGORIES = [
    # (name, sampled, two_var, x_unit, y_unit, x_range, y_range)
    ('Striker Alignment', True, True, 'newtons', 'mm/s', (150, 300), (50, 200)),
    ('Hinge and Doorcheck Performance', True, True, 'joules', 'mm/s', (100, 300), (40, 180)),
    ('Closing Energy from First Position', False, None, None, 'joules', (1, 100), (1, 9)),
    ('Closing Energy from Full Open', False, None, None, 'joules', (1, 100), (1, 9)),
    ('Hinge Inclination', False, None, None, 'degrees', (1, 100), (0, 15)),
    ('Hinge Bind', False, None, None, 'newtons', (1, 100), (0, 50)),
    ('Door Check Performance No Cabin', False, None, None, 'newtons', (1, 100), (0, 30)),
    ('Static Closing Force', False, None, None, 'newtons', (1, 100), (5, 40)),
    ('Seal Dynamics', False, None, None, 'newtons', (1, 100), (10, 60)),
]


def parse_vehicles(sql_content):
    """Parse vehicle entries from SQL content."""
    vehicles = []
    for m in re.finditer(
        r"'([A-Z0-9]{17})',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'",
        sql_content,
    ):
        vin, make, model, body, date = m.groups()
        vehicles.append((vin, body))
    return vehicles


def generate_auto_door_stats(num_needed, start_id=1):
    """Generate auto_door_stats entries."""
    entries = []
    rng = random.Random(42)  # Deterministic for reproducibility

    for i in range(num_needed):
        cat = STAT_CATEGORIES[i % len(STAT_CATEGORIES)]
        name, sampled, two_var, x_unit, y_unit, x_range, y_range = cat

        if sampled:
            result_x = round(rng.uniform(*x_range), 1)
            result_x_unit = x_unit
            result_y = round(rng.uniform(*y_range), 1)
            result_y_lower = round(result_y * 0.6, 1)
            result_y_upper = round(result_y * 1.4, 1)
        else:
            sample_num = (i // len(STAT_CATEGORIES)) + 1
            result_x = sample_num
            result_x_unit = 'NULL'
            result_y = round(rng.uniform(*y_range), 1)
            result_y_lower = round(rng.uniform(*y_range) * 0.4, 1)
            result_y_upper = round(rng.uniform(*y_range) * 1.6, 1)

        if two_var is None:
            two_var_sql = 'false'
        else:
            two_var_sql = 'true' if two_var else 'false'

        sampled_sql = 'true' if sampled else 'false'

        if result_x_unit == 'NULL':
            x_unit_sql = 'NULL'
        else:
            x_unit_sql = f"'{result_x_unit}'"

        entries.append(
            f"('{name} (Sampled)', {sampled_sql}, {two_var_sql}, "
            f"{result_x}, {x_unit_sql}, {result_y_lower}, "
            f"{result_y}, {result_y_upper}, '{y_unit}')"
        )

    return entries


def generate_steps(vehicles, stats_start_id, steps_per_door=9):
    """Generate step entries mapping each vehicle-door to sequential stat chunks."""
    steps = []
    stat_id = stats_start_id

    for vin, body in vehicles:
        doors = DOOR_MAP.get(body, DOOR_MAP['sedan'])
        for door in doors:
            for _ in range(steps_per_door):
                steps.append(f"('{vin}', '{door}', {stat_id})")
                stat_id += 1

    return steps, stat_id


def generate_steps_by_locale(vehicles, stats_start_id, locale, steps_per_door=9):
    """Generate step entries with localized door names."""
    door_names = DOOR_LOCALES.get(locale, {})
    steps = []
    stat_id = stats_start_id

    for vin, body in vehicles:
        doors = DOOR_MAP.get(body, DOOR_MAP['sedan'])
        for door in doors:
            local_door = door_names.get(door, door)
            for _ in range(steps_per_door):
                steps.append(f"('{vin}', '{local_door}', {stat_id})")
                stat_id += 1

    return steps, stat_id


def format_insert(table, columns, values, batch_size=50):
    """Format INSERT statement with batching."""
    lines = [f"INSERT INTO {table} ({columns}) VALUES"]
    for i in range(0, len(values), batch_size):
        batch = values[i:i + batch_size]
        lines.append(",\n".join(batch) + ";")
        if i + batch_size < len(values):
            lines.append(f"INSERT INTO {table} ({columns}) VALUES")
    return "\n".join(lines)


def main():
    # Parse English SQL to get vehicles
    with open('ezsaw_tables.sql') as f:
        en_content = f.read()

    vehicles = parse_vehicles(en_content)
    print(f"Parsed {len(vehicles)} vehicles")

    # Calculate how many auto_door_stats we need
    total_doors = sum(len(DOOR_MAP.get(v[1], DOOR_MAP['sedan'])) for v in vehicles)
    needed_stats = total_doors * 9
    print(f"Total vehicle-door combinations: {total_doors}")
    print(f"Needed auto_door_stats: {needed_stats}")

    # Count existing stats (Striker=30, Hinge=30, Closing Energy First=400)
    existing_stats = 460
    print(f"Existing auto_door_stats: {existing_stats}")
    new_stats_needed = needed_stats - existing_stats
    print(f"New auto_door_stats to add: {new_stats_needed}")

    # Generate new auto_door_stats entries
    new_stats = generate_auto_door_stats(new_stats_needed, start_id=existing_stats + 1)
    print(f"Generated {len(new_stats)} new auto_door_stats entries")

    # Generate steps for English
    en_steps, _ = generate_steps(vehicles, existing_stats + 1)
    print(f"Generated {len(en_steps)} step entries")

    # Verify: each vehicle should have exactly 9 steps per door
    from collections import Counter
    vin_counts = Counter()
    for vin, body in vehicles:
        doors = DOOR_MAP.get(body, DOOR_MAP['sedan'])
        vin_counts[vin] = len(doors) * 9
    print(f"Expected steps: {sum(vin_counts.values())}")
    print(f"Generated steps: {len(en_steps)}")

    # Now update each SQL file
    locales = {
        'en': ('ezsaw_tables.sql', None),
        'de': ('ezsaw_tables_de.sql', 'de'),
        'fr': ('ezsaw_tables_fr.sql', 'fr'),
        'es': ('ezsaw_tables_es.sql', 'es'),
        'nl': ('ezsaw_tables_nl.sql', 'nl'),
    }

    for locale, (filename, locale_code) in locales.items():
        print(f"\nProcessing {filename}...")

        with open(filename) as f:
            content = f.read()

        # Find the second auto_door_stats INSERT (the one after BMW/Mercedes vehicles)
        # It starts after the second vehicles INSERT
        second_vehicles_pos = content.find("INSERT INTO", content.find("INSERT INTO") + 1)
        second_vehicles_pos = content.find("\n", second_vehicles_pos) + 1

        # Find the auto_door_stats INSERT after that
        stats_pos = content.find("INSERT INTO", second_vehicles_pos)
        stats_end = content.find(";", stats_pos) + 1

        # Find the steps INSERT after the auto_door_stats
        steps_pos = content.find("INSERT INTO", stats_end)
        steps_end = content.find(";", steps_pos) + 1

        # Find the auto_door_stats column list
        stats_header_end = content.find(") VALUES", stats_pos)
        stats_header = content[stats_pos:stats_header_end + 9]

        # Generate steps for this locale
        if locale_code:
            locale_steps, _ = generate_steps_by_locale(vehicles, existing_stats + 1, locale_code)
        else:
            locale_steps, _ = generate_steps(vehicles, existing_stats + 1)

        # Format the new stats INSERT
        stats_values = ",\n".join(new_stats) + ";"
        new_stats_insert = f"{stats_header}\n{stats_values}"

        # Format the new steps INSERT
        steps_header = content[steps_pos:content.find(") VALUES", steps_pos) + 9]
        steps_values = ",\n".join(locale_steps) + ";"
        new_steps_insert = f"{steps_header}\n{steps_values}"

        # Replace the old stats and steps blocks
        new_content = (
            content[:stats_pos]
            + new_stats_insert
            + "\n\n"
            + new_steps_insert
            + "\n"
            + content[steps_end:]
        )

        with open(filename, 'w') as f:
            f.write(new_content)

        print(f"  Updated {filename}")

    # Generate psql script for local databases
    print("\nGenerating psql insert script...")
    generate_psql_script(vehicles, existing_stats, new_stats, locales)

    print("\nDone!")


def generate_psql_script(vehicles, existing_stats, new_stats, locales):
    """Generate a psql script to insert data into local databases."""
    with open('insert_steps.sql', 'w') as f:
        f.write("-- Auto-generated script to insert missing steps data\n")
        f.write("-- Run against each locale's database\n\n")

        # Insert new auto_door_stats
        f.write("INSERT INTO auto_door_stats (\n")
        f.write("    auto_door_stat_name, sampled, two_var, result_x, result_x_unit,\n")
        f.write("    result_y_lower_lim, result_y, result_y_upper_lim, result_y_unit\n")
        f.write(") VALUES\n")
        f.write(",\n".join(new_stats) + ";\n\n")

        # Insert steps for English
        en_steps, _ = generate_steps(vehicles, existing_stats + 1)
        f.write("INSERT INTO steps (vin, door, fk_steps_auto_door_stats) VALUES\n")
        f.write(",\n".join(en_steps) + ";\n")

    print(f"Generated insert_steps.sql with {len(new_stats)} new stats + {len(en_steps)} steps")


if __name__ == '__main__':
    main()
