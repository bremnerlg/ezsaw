#!/usr/bin/env python3
"""
DEPRECATED: This script has been superseded by fix_db.py and export_fixed.py
at the project root. Kept for reference only — do not use for new work.

Insert new auto_door_stats and steps data into SQL locale files.

Uses interleaved stat categories so every 9 consecutive IDs
span all 9 test types.
"""

import re
import random

DOOR_MAP = {
    'sedan': ['driver_front', 'driver_rear', 'passenger_front', 'passenger_rear'],
    'coupe': ['driver_front', 'passenger_front'],
    'SUV': ['rear_hatch', 'hood'],
    'pickup': ['passenger_front', 'passenger_rear'],
    'hatchback': ['driver_front', 'driver_rear', 'passenger_front', 'passenger_rear'],
}

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

LOCALIZED_TABLES = {
    'de': {
        'auto_door_stats': 'statistiken_tueren_fahrzeuge',
        'auto_door_stat_name': 'name_stat_tueren_fahrzeug',
        'sampled': 'probenahme',
        'two_var': 'zwei_variablen',
        'result_x': 'ergebnis_x',
        'result_x_unit': 'einheit_ergebnis_x',
        'result_y_lower_lim': 'untere_grenze_ergebnis_y',
        'result_y': 'ergebnis_y',
        'result_y_upper_lim': 'obere_grenze_ergebnis_y',
        'result_y_unit': 'einheit_ergebnis_y',
        'steps': 'schritte',
        'vin': 'kennzeichen',
        'door': 'tuerort',
        'fk_steps_auto_door_stats': 'fk_schritt_stat_tueren_fahrzeug',
    },
    'fr': {
        'auto_door_stats': 'stats_portes_automobiles',
        'auto_door_stat_name': 'nom_stat_porte_vehicule',
        'sampled': 'preleve',
        'two_var': 'deux_variables',
        'result_x': 'resultat_x',
        'result_x_unit': 'unite_resultat_x',
        'result_y_lower_lim': 'limite_inferieure_resultat_y',
        'result_y': 'resultat_y',
        'result_y_upper_lim': 'limite_superieure_resultat_y',
        'result_y_unit': 'unite_resultat_y',
        'steps': 'étapes',
        'vin': 'immatriculation',
        'door': 'emplacement_porte',
        'fk_steps_auto_door_stats': 'fk_étape_stat_porte_auto',
    },
    'es': {
        'auto_door_stats': 'estadísticas_puertas_vehículos',
        'auto_door_stat_name': 'nombre_estadística_puerta_vehículo',
        'sampled': 'muestreado',
        'two_var': 'dos_variables',
        'result_x': 'resultado_x',
        'result_x_unit': 'unidad_resultado_x',
        'result_y_lower_lim': 'límite_inferior_resultado_y',
        'result_y': 'resultado_y',
        'result_y_upper_lim': 'límite_superior_resultado_y',
        'result_y_unit': 'unidad_resultado_y',
        'steps': 'pasos',
        'vin': 'matrícula',
        'door': 'ubicación puerta',
        'fk_steps_auto_door_stats': 'fk_paso_estadística_puerta_vehículo',
    },
    'nl': {
        'auto_door_stats': 'statistieken_deuren_voertuigen',
        'auto_door_stat_name': 'naam_statistiek_deur_voertuig',
        'sampled': 'bemonsterd',
        'two_var': 'twee_variabelen',
        'result_x': 'resultaat_x',
        'result_x_unit': 'eenheid_resultaat_x',
        'result_y_lower_lim': 'ondergrens_resultaat_y',
        'result_y': 'resultaat_y',
        'result_y_upper_lim': 'bovengrens_resultaat_y',
        'result_y_unit': 'eenheid_resultaat_y',
        'steps': 'stappen',
        'vin': 'kenteken',
        'door': 'deurlocatie',
        'fk_steps_auto_door_stats': 'fk_stap_stat_deur_voertuig',
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

NUM_CATS = len(STAT_CATEGORIES)


def find_inserts(lines):
    """Find all INSERT INTO statements and their approximate ranges."""
    inserts = []
    for i, line in enumerate(lines):
        if line.strip().startswith('INSERT INTO'):
            inserts.append(i)
    return inserts


def parse_vehicles(lines, start, end):
    vehicles = []
    for line in lines[start:end + 1]:
        m = re.match(r"\s*\('([A-Z0-9]{17})',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'", line)
        if m:
            vehicles.append((m.group(1), m.group(4)))
    return vehicles


def find_block_end(lines, start):
    """Find the end of an INSERT block by looking for a line ending with ';'."""
    for i in range(start + 1, len(lines)):
        if lines[i].rstrip().endswith(';'):
            return i
    return len(lines) - 1


def generate_all_stats(total_needed):
    rng = random.Random(42)
    stats = []
    for i in range(total_needed):
        cat = STAT_CATEGORIES[i % NUM_CATS]
        name, sampled, two_var, x_unit, y_unit, x_range, y_range = cat
        if sampled:
            result_x = round(rng.uniform(*x_range), 1)
            result_x_unit = x_unit
            result_y = round(rng.uniform(*y_range), 1)
            result_y_lower = round(result_y * 0.6, 1)
            result_y_upper = round(result_y * 1.4, 1)
        else:
            result_x = (i // NUM_CATS) + 1
            result_x_unit = 'NULL'
            result_y = round(rng.uniform(*y_range), 1)
            result_y_lower = round(rng.uniform(*y_range) * 0.4, 1)
            result_y_upper = round(rng.uniform(*y_range) * 1.6, 1)
        two_var_sql = 'false' if two_var is None else ('true' if two_var else 'false')
        sampled_sql = 'true' if sampled else 'false'
        x_unit_sql = 'NULL' if result_x_unit == 'NULL' else f"'{result_x_unit}'"
        stats.append(
            f"({i + 1}, '{name} (Sampled)', {sampled_sql}, {two_var_sql}, "
            f"{result_x}, {x_unit_sql}, {result_y_lower}, "
            f"{result_y}, {result_y_upper}, '{y_unit}')"
        )
    return stats


def generate_steps(vehicles, locale=None):
    door_names = DOOR_LOCALES.get(locale, {})
    steps = []
    stat_id = 1
    for vin, body in vehicles:
        doors = DOOR_MAP.get(body, DOOR_MAP['sedan'])
        for door in doors:
            local_door = door_names.get(door, door)
            for _ in range(9):
                steps.append(f"('{vin}', '{local_door}', {stat_id})")
                stat_id += 1
    return steps


def process_file(filename, locale_code=None):
    print(f"\nProcessing {filename}...")
    with open(filename) as f:
        lines = f.readlines()

    insert_lines = find_inserts(lines)
    print(f"  INSERT lines at: {[l+1 for l in insert_lines]}")

    # Block 1: first vehicles INSERT
    b1_start = insert_lines[0]
    b1_end = find_block_end(lines, b1_start)
    # Block 4: second vehicles INSERT
    b4_start = insert_lines[3]
    b4_end = find_block_end(lines, b4_start)

    orig_vehicles = parse_vehicles(lines, b1_start, b1_end)
    bmw_vehicles = parse_vehicles(lines, b4_start, b4_end)
    all_vehicles = orig_vehicles + bmw_vehicles
    total_doors = sum(len(DOOR_MAP.get(b, DOOR_MAP['sedan'])) for _, b in all_vehicles)
    total_stats = total_doors * 9

    print(f"  Vehicles: {len(all_vehicles)}, Doors: {total_doors}, Stats needed: {total_stats}")

    all_stats = generate_all_stats(total_stats)
    all_steps = generate_steps(all_vehicles, locale_code)

    loc = LOCALIZED_TABLES.get(locale_code, {})
    st = loc.get('auto_door_stats', 'auto_door_stats')
    sn = loc.get('auto_door_stat_name', 'auto_door_stat_name')
    ss = loc.get('sampled', 'sampled')
    sv = loc.get('two_var', 'two_var')
    sx = loc.get('result_x', 'result_x')
    sxu = loc.get('result_x_unit', 'result_x_unit')
    syl = loc.get('result_y_lower_lim', 'result_y_lower_lim')
    sy = loc.get('result_y', 'result_y')
    syu = loc.get('result_y_upper_lim', 'result_y_upper_lim')
    syun = loc.get('result_y_unit', 'result_y_unit')
    tbl_steps = loc.get('steps', 'steps')
    v_col = loc.get('vin', 'vin')
    d_col = loc.get('door', 'door')
    fk_col = loc.get('fk_steps_auto_door_stats', 'fk_steps_auto_door_stats')
    if ' ' in d_col:
        d_col = f'"{d_col}"'

    # Keep: CREATE TABLEs + first vehicles INSERT (block 1)
    # Replace: everything after block 1 (old stats + steps + second vehicles + old data)
    b1_start = insert_lines[0]
    new_lines = lines[:b1_start]

    # Write all interleaved stats
    new_lines.append(f"INSERT INTO {st} (\n")
    new_lines.append(f"    auto_door_stat_id, {sn}, {ss}, {sv}, {sx}, {sxu},\n")
    new_lines.append(f"    {syl}, {sy}, {syu}, {syun}\n")
    new_lines.append(") VALUES\n")

    for i in range(0, len(all_stats), 50):
        batch = all_stats[i:i+50]
        new_lines.append(",\n".join(batch))
        new_lines.append(",\n" if i + 50 < len(all_stats) else ";\n\n\n")

    # Write all steps
    new_lines.append(f"INSERT INTO {tbl_steps} ({v_col}, {d_col}, {fk_col}) VALUES\n")
    for i in range(0, len(all_steps), 50):
        batch = all_steps[i:i+50]
        new_lines.append(",\n".join(batch))
        new_lines.append(",\n" if i + 50 < len(all_steps) else ";\n")

    with open(filename, 'w') as f:
        f.writelines(new_lines)
    print(f"  Written {len(new_lines)} lines")


def main():
    process_file('ezsaw_tables.sql', None)
    for code, fn in [('de', 'ezsaw_tables_de.sql'), ('fr', 'ezsaw_tables_fr.sql'),
                      ('es', 'ezsaw_tables_es.sql'), ('nl', 'ezsaw_tables_nl.sql')]:
        process_file(fn, code)
    print("\nDone!")


if __name__ == '__main__':
    main()
