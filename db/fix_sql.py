#!/usr/bin/env python3
"""
DEPRECATED: This script has been superseded by fix_db.py and export_fixed.py
at the project root. Kept for reference only — do not use for new work.

Fix SQL files by properly regenerating auto_door_stats and steps blocks.
"""

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
        'driver_front': 'vorne_fuehrer', 'driver_rear': 'hinten_fuehrer',
        'passenger_front': 'vorne_beifahrer', 'passenger_rear': 'hinten_beifahrer',
        'rear_hatch': 'heckklappe', 'hood': 'haube',
    },
    'fr': {
        'driver_front': 'avant_driver', 'driver_rear': 'arrière_driver',
        'passenger_front': 'avant_passager', 'passenger_rear': 'arrière_passager',
        'rear_hatch': 'hayon', 'hood': 'capot',
    },
    'es': {
        'driver_front': 'delantero_conductor', 'driver_rear': 'trasero_conductor',
        'passenger_front': 'delantero_viajero', 'passenger_rear': 'trasero_viajero',
        'rear_hatch': 'maletero_trasero', 'hood': 'capó',
    },
    'nl': {
        'driver_front': 'voorste_bestuurder', 'driver_rear': 'achterste_bestuurder',
        'passenger_front': 'voorste_passagier', 'passenger_rear': 'achterste_passagier',
        'rear_hatch': 'achterklep', 'hood': 'motorkap',
    },
}

STAT_CATEGORIES = [
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


def parse_vehicles_from_lines(lines, start_line, end_line):
    """Parse vehicle entries from specific line range."""
    vehicles = []
    for line in lines[start_line:end_line]:
        m = re.match(r"\s*\('([A-Z0-9]{17})',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'", line)
        if m:
            vin, make, model, body, date = m.groups()
            vehicles.append((vin, body))
    return vehicles


def generate_auto_door_stats(num_needed, start_id=1):
    """Generate auto_door_stats entries."""
    entries = []
    rng = random.Random(42)

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


def generate_steps(vehicles, stats_start_id, locale=None, steps_per_door=9):
    """Generate step entries."""
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

    return steps


def rebuild_sql_file(locale_code, filename):
    """Rebuild a SQL file from scratch with correct structure."""
    print(f"Rebuilding {filename}...")

    # Read the original file to get the CREATE TABLE statements and vehicle data
    with open('ezsaw_tables.sql') as f:
        en_lines = f.readlines()

    # For non-English files, read the localized CREATE TABLE statements
    if locale_code:
        with open(filename) as f:
            loc_lines = f.readlines()
        # Find CREATE TABLE statements in the localized file
        create_statements = []
        for i, line in enumerate(loc_lines):
            if line.strip().startswith('CREATE '):
                create_statements.append(line)
                # Get all lines until the next CREATE or empty line
                j = i + 1
                while j < len(loc_lines) and not loc_lines[j].strip().startswith('CREATE ') and loc_lines[j].strip():
                    create_statements.append(loc_lines[j])
                    j += 1
                break
    else:
        create_statements = []
        for i, line in enumerate(en_lines):
            if line.strip().startswith('CREATE '):
                create_statements.append(line)
                j = i + 1
                while j < len(en_lines) and not en_lines[j].strip().startswith('CREATE ') and en_lines[j].strip():
                    create_statements.append(en_lines[j])
                    j += 1
                break

    # Parse vehicles from the first vehicles INSERT
    first_vehicles_start = None
    first_vehicles_end = None
    for i, line in enumerate(en_lines):
        if 'INSERT INTO vehicles' in line and first_vehicles_start is None:
            first_vehicles_start = i
        elif first_vehicles_start is not None and first_vehicles_end is None:
            if line.strip().startswith('--') or line.strip().startswith('INSERT INTO'):
                first_vehicles_end = i
                break

    original_vehicles = parse_vehicles_from_lines(en_lines, first_vehicles_start, first_vehicles_end)

    # Parse BMW/Mercedes vehicles from the second vehicles INSERT
    second_vehicles_start = None
    second_vehicles_end = None
    for i, line in enumerate(en_lines):
        if 'INSERT INTO vehicles' in line and i > first_vehicles_start:
            second_vehicles_start = i
        elif second_vehicles_start is not None and second_vehicles_end is None:
            if line.strip().startswith('--') or (line.strip().startswith('INSERT INTO') and 'vehicles' not in line):
                second_vehicles_end = i
                break

    bmw_vehicles = parse_vehicles_from_lines(en_lines, second_vehicles_start, second_vehicles_end)

    all_vehicles = original_vehicles + bmw_vehicles
    print(f"  Original vehicles: {len(original_vehicles)}")
    print(f"  BMW/Mercedes vehicles: {len(bmw_vehicles)}")
    print(f"  Total vehicles: {len(all_vehicles)}")

    # Count doors
    total_doors = sum(len(DOOR_MAP.get(b, DOOR_MAP['sedan'])) for _, b in all_vehicles)
    print(f"  Total vehicle-door combinations: {total_doors}")

    # Generate new auto_door_stats
    needed_stats = total_doors * 9
    existing_stats = 60  # 30 Striker + 30 Hinge
    new_stats_needed = needed_stats - existing_stats
    print(f"  New auto_door_stats needed: {new_stats_needed}")

    new_stats = generate_auto_door_stats(new_stats_needed, start_id=existing_stats + 1)

    # Generate steps
    en_steps = generate_steps(all_vehicles, existing_stats + 1, locale=None)
    loc_steps = generate_steps(all_vehicles, existing_stats + 1, locale=locale_code)

    # Format the SQL
    output = []

    # Add CREATE TABLE statements
    output.extend(create_statements)
    output.append("\n\n")

    # Add first vehicles INSERT (original 30)
    output.append("INSERT INTO vehicles (vin, make, model, body, manufacture_date) VALUES\n")
    for i, (vin, body) in enumerate(original_vehicles):
        # Get make/model from original SQL
        m = re.search(rf"'{vin}',\s*'([^']+)',\s*'([^']+)',\s*'{body}'", ''.join(en_lines))
        if m:
            make, model = m.group(1), m.group(2)
        else:
            make, model = 'Unknown', 'Unknown'
        comma = "," if i < len(original_vehicles) - 1 else ";"
        output.append(f"('{vin}', '{make}', '{model}', '{body}', '2021-01-01')'{comma}'\n")
    output.append("\n\n")

    # Add first auto_door_stats INSERT (original 60)
    output.append("INSERT INTO auto_door_stats (\n")
    output.append("    auto_door_stat_name, sampled, two_var, result_x, result_x_unit,\n")
    output.append("    result_y_lower_lim, result_y, result_y_upper_lim, result_y_unit\n")
    output.append(") VALUES\n")

    # Generate original 60 stats
    rng = random.Random(42)
    original_stats = []
    for i in range(60):
        cat = STAT_CATEGORIES[i % 2]  # First 2 categories
        name, sampled, two_var, x_unit, y_unit, x_range, y_range = cat
        result_x = round(rng.uniform(*x_range), 1)
        result_y = round(rng.uniform(*y_range), 1)
        result_y_lower = round(result_y * 0.6, 1)
        result_y_upper = round(result_y * 1.4, 1)
        original_stats.append(
            f"('{name} (Sampled)', true, true, {result_x}, '{x_unit}', "
            f"{result_y_lower}, {result_y}, {result_y_upper}, '{y_unit}')"
        )
    output.append(",\n".join(original_stats) + ";\n\n\n")

    # Add first steps INSERT
    output.append("INSERT INTO steps (vin, door, fk_steps_auto_door_stats) VALUES\n")
    output.append(",\n".join(en_steps) + ";\n\n\n")

    # Add second vehicles INSERT (BMW/Mercedes)
    output.append("INSERT INTO vehicles (vin, make, model, body, manufacture_date) VALUES\n")
    for i, (vin, body) in enumerate(bmw_vehicles):
        # Get make/model from original SQL
        m = re.search(rf"'{vin}',\s*'([^']+)',\s*'([^']+)',\s*'{body}'", ''.join(en_lines))
        if m:
            make, model = m.group(1), m.group(2)
        else:
            make, model = 'Unknown', 'Unknown'
        comma = "," if i < len(bmw_vehicles) - 1 else ";"
        output.append(f"('{vin}', '{make}', '{model}', '{body}', '2021-01-01')'{comma}'\n")
    output.append("\n\n")

    # Add second auto_door_stats INSERT (new entries)
    output.append("INSERT INTO auto_door_stats (\n")
    output.append("    auto_door_stat_name, sampled, two_var, result_x, result_x_unit,\n")
    output.append("    result_y_lower_lim, result_y, result_y_upper_lim, result_y_unit\n")
    output.append(") VALUES\n")
    output.append(",\n".join(new_stats) + ";\n\n\n")

    # Add second steps INSERT
    output.append("INSERT INTO steps (vin, door, fk_steps_auto_door_stats) VALUES\n")
    output.append(",\n".join(loc_steps) + ";\n")

    # Write the file
    with open(filename, 'w') as f:
        f.write("".join(output))

    print(f"  Written {filename}")


def main():
    # First rebuild English file
    rebuild_sql_file(None, 'ezsaw_tables.sql')

    # Then rebuild each localized file
    locales = [
        ('de', 'ezsaw_tables_de.sql'),
        ('fr', 'ezsaw_tables_fr.sql'),
        ('es', 'ezsaw_tables_es.sql'),
        ('nl', 'ezsaw_tables_nl.sql'),
    ]

    for locale_code, filename in locales:
        rebuild_sql_file(locale_code, filename)

    print("\nAll files rebuilt successfully!")


if __name__ == '__main__':
    main()
