#!/usr/bin/env python3
"""
DEPRECATED: This script has been superseded by fix_db.py and export_fixed.py
at the project root. Kept for reference only — do not use for new work.

Generate psql insert script with interleaved stat categories.

Every 9 consecutive stat IDs span all 9 test types,
so each vehicle-door gets one of each type.
"""

import re
import random

DOOR_MAP = {
    'sedan': ['driver_front', 'driver_rear', 'passenger_front', 'passenger_rear'],
    'coupe': ['driver_front', 'passenger_front'],
    'SUV': ['trunk/hatch', 'hood'],
    'pickup': ['passenger_front', 'passenger_rear'],
    'hatchback': ['driver_front', 'driver_rear', 'passenger_front', 'passenger_rear'],
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

NUM_CATS = len(STAT_CATEGORIES)

with open('ezsaw_tables.sql') as f:
    content = f.read()

vehicles = []
for m in re.finditer(r"'([A-Z0-9]{17})',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'", content):
    vin, make, model, body, date = m.groups()
    vehicles.append((vin, body))

total_doors = sum(len(DOOR_MAP.get(b, DOOR_MAP['sedan'])) for _, b in vehicles)
total_stats_needed = total_doors * 9

print(f"Total vehicles: {len(vehicles)}")
print(f"Total vehicle-door combinations: {total_doors}")
print(f"Total stats needed: {total_stats_needed}")

rng = random.Random(42)
all_stats = []
for i in range(total_stats_needed):
    cat = STAT_CATEGORIES[i % NUM_CATS]
    name, sampled, two_var, x_unit, y_unit, x_range, y_range = cat

    if sampled:
        result_x = round(rng.uniform(*x_range), 1)
        result_x_unit = x_unit
        result_y = round(rng.uniform(*y_range), 1)
        result_y_lower = round(result_y * 0.6, 1)
        result_y_upper = round(result_y * 1.4, 1)
    else:
        sample_num = (i // NUM_CATS) + 1
        result_x = sample_num
        result_x_unit = 'NULL'
        result_y = round(rng.uniform(*y_range), 1)
        result_y_lower = round(rng.uniform(*y_range) * 0.4, 1)
        result_y_upper = round(rng.uniform(*y_range) * 1.6, 1)

    two_var_sql = 'false' if two_var is None else ('true' if two_var else 'false')
    sampled_sql = 'true' if sampled else 'false'
    x_unit_sql = 'NULL' if result_x_unit == 'NULL' else f"'{result_x_unit}'"

    all_stats.append(
        f"({i + 1}, '{name} (Sampled)', {sampled_sql}, {two_var_sql}, "
        f"{result_x}, {x_unit_sql}, {result_y_lower}, "
        f"{result_y}, {result_y_upper}, '{y_unit}')"
    )

steps = []
stat_id = 1
for vin, body in vehicles:
    doors = DOOR_MAP.get(body, DOOR_MAP['sedan'])
    for door in doors:
        for _ in range(9):
            steps.append(f"('{vin}', '{door}', {stat_id})")
            stat_id += 1

print(f"Generated {len(all_stats)} stats (interleaved by category)")
print(f"Generated {len(steps)} steps")

with open('insert_steps.sql', 'w') as f:
    f.write("-- Auto-generated: wipe + rebuild with interleaved stat categories\n")
    f.write("-- Every 9 consecutive stat IDs span all 9 test types\n\n")
    f.write("BEGIN;\n\n")

    f.write("DELETE FROM steps;\n")
    f.write("DELETE FROM auto_door_stats;\n")
    f.write("ALTER SEQUENCE auto_door_stats_auto_door_stat_id_seq RESTART WITH 1;\n\n")

    f.write("INSERT INTO auto_door_stats (\n")
    f.write("    auto_door_stat_id, auto_door_stat_name, sampled, two_var, result_x, result_x_unit,\n")
    f.write("    result_y_lower_lim, result_y, result_y_upper_lim, result_y_unit\n")
    f.write(") VALUES\n")

    for i in range(0, len(all_stats), 50):
        batch = all_stats[i:i + 50]
        f.write(",\n".join(batch))
        if i + 50 < len(all_stats):
            f.write(",\n")
        else:
            f.write(";\n\n")

    f.write("INSERT INTO steps (vin, door, fk_steps_auto_door_stats) VALUES\n")
    for i in range(0, len(steps), 50):
        batch = steps[i:i + 50]
        f.write(",\n".join(batch))
        if i + 50 < len(steps):
            f.write(",\n")
        else:
            f.write(";\n")

    f.write("\nCOMMIT;\n")

print(f"\nGenerated insert_steps.sql")
