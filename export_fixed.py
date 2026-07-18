#!/usr/bin/env python3
"""Export fixed English DB data to all locale SQL files.

Connects to the ezsaw3 database (which should already have been fixed by
fix_db.py or manual corrections), reads vehicle/stat/step data, and writes
fresh INSERT blocks into all 5 locale SQL files (en, de, fr, es, nl) and
insert_steps.sql.

Run this AFTER fix_db.py has regenerated the data files, or after making
direct corrections to the ezsaw3 database.
"""

import re
import decimal
import psycopg2
from datetime import date

DB_CONFIG = {
    "host": "localhost", "dbname": "ezsaw3",
    "user": "postgres", "password": "postgres",
}

LOCALE_COLUMNS = {
    "en": {"table": "auto_door_stats",
           "cols": ["auto_door_stat_id", "auto_door_stat_name", "sampled", "two_var",
                    "result_x", "result_x_unit", "result_y_lower_lim", "result_y",
                    "result_y_upper_lim", "result_y_unit"]},
    "de": {"table": "statistiken_tueren_fahrzeuge",
           "cols": ["id_stat_tueren_fahrzeug", "name_stat_tueren_fahrzeug", "probenahme", "zwei_variablen",
                    "ergebnis_x", "einheit_ergebnis_x", "untere_grenze_ergebnis_y", "ergebnis_y",
                    "obere_grenze_ergebnis_y", "einheit_ergebnis_y"]},
    "fr": {"table": "stats_portes_automobiles",
           "cols": ["id_stat_porte_auto", "nom_stat_porte_auto", "échantillonné", "deux_variablés",
                    "résultat_x", "unité_résultat_x", "limite_infèreure_résultat_y", "résultat_y",
                    "limite_suptère_résultat_y", "unité_résultat_y"]},
    "es": {"table": "estadísticas_puertas_vehículos",
           "cols": ["id_estadística_puerta_vehículo", "nombre_estadística_puerta_vehículo", "muestreado", "dos_variables",
                    "resultado_x", "unidad_resultado_x", "límite_inferior_resultado_y", "resultado_y",
                    "límite_superior_resultado_y", "unidad_resultado_y"]},
    "nl": {"table": "statistieken_deuren_voertuigen",
           "cols": ["id_stat_deur_voertuig", "naam_stat_deur_voertuig", "monstergroep", "twee_variabelen",
                    "resultaat_x", "eenheid_resultaat_x", "onderste_grenslimiet_resultaat_y", "resultaat_y",
                    "bovenste_grenslimiet_resultaat_y", "eenheid_resultaat_y"]},
}

DOOR_LOCALE_MAP = {
    "en": ("steps", "vin", "door", "fk_steps_auto_door_stats"),
    "de": ("schritte", "kennzeichen", "tuerort", "fk_schritt_stat_tueren_fahrzeug"),
    "fr": ("étapes", "immatriculation", "emplacement_porte", "fk_étape_stat_porte_auto"),
    "es": ("pasos", "matrícula", "ubicación puerta", "fk_paso_estadística_puerta_vehículo"),
    "nl": ("stappen", "kenteken", "deurlocatie", "fk_stap_stat_deur_voertuig"),
}

VEHICLE_TABLES = {
    "en": "vehicles", "de": "fahrzeuge", "fr": "véhicules", "es": "vehículos", "nl": "voertuigen",
}

DOOR_TRANSLATION = {
    "driver_front": {"en": "driver_front", "de": "vorne_fuehrer", "fr": "avant_driver",
                     "es": "delantero_conductor", "nl": "voorste_bestuurder"},
    "driver_rear": {"en": "driver_rear", "de": "hinten_fuehrer", "fr": "arrière_driver",
                    "es": "trasero_conductor", "nl": "achterste_bestuurder"},
    "passenger_front": {"en": "passenger_front", "de": "vorne_beifahrer", "fr": "avant_passager",
                        "es": "delantero_viajero", "nl": "voorste_passagier"},
    "passenger_rear": {"en": "passenger_rear", "de": "hinten_beifahrer", "fr": "arrière_passager",
                       "es": "trasero_viajero", "nl": "achterste_passagier"},
    "rear_hatch": {"en": "rear_hatch", "de": "heckklappe", "fr": "hayon",
                   "es": "maletero_trasero", "nl": "achterklep"},
    "hood": {"en": "hood", "de": "haube", "fr": "capot", "es": "capó", "nl": "motorkap"},
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def connect():
    return psycopg2.connect(**DB_CONFIG)

def fetch_all(cur, query):
    cur.execute(query)
    return cur.fetchall()


# ---------------------------------------------------------------------------
# SQL Utilities
# ---------------------------------------------------------------------------

def format_sql_value(val):
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float, decimal.Decimal)):
        v = float(val)
        if v == int(v):
            return str(int(v))
        return f"{v}"
    if isinstance(val, date):
        return f"'{val.isoformat()}'"
    escaped = str(val).replace("'", "''")
    return f"'{escaped}'"


def make_insert_block(rows, cols, table, translate_fn=None):
    """Generate an INSERT INTO ... VALUES block for a list of rows."""
    col_list = ", ".join(f'"{c}"' if (' ' in c or any(accent in c for accent in 'éíóú')) else c for c in cols)
    lines = [f"INSERT INTO {table} ({col_list}) VALUES"]
    for i, row in enumerate(rows):
        if translate_fn:
            row = translate_fn(row)
        vals = [format_sql_value(v) for v in row]
        suffix = "," if i < len(rows) - 1 else ";"
        lines.append(f"({', '.join(vals)}){suffix}")
    return "\n".join(lines)


def replace_insert_block(content, table_name, new_block):
    """Replace the INSERT block for a table in the SQL content."""
    # Try patterns with and without quoted table name, with and without newline after VALUES
    patterns = [
        re.compile(
            r'INSERT INTO\s+"?' + re.escape(table_name) + r'"?\s*\([^)]+\)\s*VALUES\s*\n((?:\s*\([^;]*?\)\s*,?\s*\n?)+)\s*;',
            re.DOTALL | re.IGNORECASE
        ),
        re.compile(
            r'INSERT INTO\s+"?' + re.escape(table_name) + r'"?\s*\([^)]+\)\s*VALUES\s*((?:\([^;]+\)\s*,?\s*)+)\s*;',
            re.DOTALL | re.IGNORECASE
        ),
    ]
    match = None
    for pat in patterns:
        match = pat.search(content)
        if match:
            break

    if not match:
        # Fallback: find "INSERT INTO" followed by the table name (possibly quoted)
        search_strs = [
            f"INSERT INTO {table_name}",
            f'INSERT INTO "{table_name}"',
        ]
        start = -1
        for s in search_strs:
            start = content.find(s)
            if start >= 0:
                break
        if start < 0:
            print(f"  WARNING: Could not find INSERT INTO {table_name}")
            return content
        end = content.find(";", start)
        end = content.find(";", end + 1)
        return content[:start] + new_block + content[end+1:]

    return content[:match.start()] + new_block + content[match.end():]


# ---------------------------------------------------------------------------
# Locale Processing
# ---------------------------------------------------------------------------

def process_locale(conn, locale, filepath, is_steps=False):
    """Process one locale SQL file."""
    print(f"\n{locale}: {filepath}")

    with open(filepath) as f:
        content = f.read()

    # Fetch data from English DB
    with conn.cursor() as cur:
        vehicles = fetch_all(cur, "SELECT vin, make, model, body, manufacture_date FROM vehicles ORDER BY vin")
        stats = fetch_all(cur,
            "SELECT auto_door_stat_id, auto_door_stat_name, sampled, two_var, "
            "result_x, result_x_unit, result_y_lower_lim, result_y, result_y_upper_lim, result_y_unit "
            "FROM auto_door_stats ORDER BY auto_door_stat_id")
        steps = fetch_all(cur,
            "SELECT vin, door, fk_steps_auto_door_stats FROM steps ORDER BY vin, door, fk_steps_auto_door_stats")

    # Vehicles
    v_table = VEHICLE_TABLES[locale]
    # Translate column names for locale
    v_trans = {
        "en": ["vin", "make", "model", "body", "manufacture_date"],
        "de": ["kennzeichen", "marke", "modell", "karosserieart", "herstellungsdatum"],
        "fr": ["immatriculation", "marque", "modèle", "type_de_carrosserie", "date_de_fabrique"],
        "es": ["matrícula", "marca", "modelo", "tipocarrocería", "fecha_fabricación"],
        "nl": ["kenteken", "merk", "model", "carrosserietype", "fabriekdatum"],
    }
    locale_v_cols = v_trans[locale]

    # Vehicle data is locale-independent — only column names differ
    v_block = make_insert_block(vehicles, locale_v_cols, v_table)
    old_content = content
    content = replace_insert_block(content, v_table, v_block)
    if content == old_content:
        # Insert before the first existing INSERT block
        insert_marker = content.find("INSERT INTO")
        if insert_marker < 0:
            content += "\n\n" + v_block + "\n"
        else:
            content = content[:insert_marker] + "\n" + v_block + "\n" + content[insert_marker:]
    print(f"  Vehicles: {len(vehicles)}")

    # Stats
    stat_config = LOCALE_COLUMNS[locale]
    stat_block = make_insert_block(stats, stat_config["cols"], stat_config["table"])
    content = replace_insert_block(content, stat_config["table"], stat_block)
    print(f"  Stats: {len(stats)}")

    # Steps
    st_table, st_vin, st_door, st_fk = DOOR_LOCALE_MAP[locale]
    st_cols = [st_vin, st_door, st_fk]

    def translate_step(row):
        vin, door_en, fk = row
        door_loc = DOOR_TRANSLATION.get(door_en, {}).get(locale, door_en)
        return (vin, door_loc, fk)

    st_block = make_insert_block(steps, st_cols, st_table, translate_step)
    content = replace_insert_block(content, st_table, st_block)
    print(f"  Steps: {len(steps)}")

    with open(filepath, "w") as f:
        f.write(content)
    print(f"  Written {len(content)} bytes")

    # If it's the English file, also write insert_steps.sql
    if locale == "en" and not is_steps:
        # For insert_steps.sql, wrap in BEGIN/COMMIT with DELETE + ALTER SEQUENCE
        steps_path = "db/insert_steps.sql"
        with open(steps_path) as f:
            steps_content = f.read()

        # Replace just the auto_door_stats INSERT
        steps_content = replace_insert_block(steps_content, stat_config["table"], stat_block)
        steps_content = replace_insert_block(steps_content, st_table, st_block)

        with open(steps_path, "w") as f:
            f.write(steps_content)
        print(f"  Steps file: {steps_path} written")


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main():
    conn = connect()
    print("Connected to ezsaw3 (fixed English DB)")

    for locale in ["en", "de", "fr", "es", "nl"]:
        if locale == "en":
            path = "db/ezsaw_tables.sql"
        else:
            path = f"db/ezsaw_tables_{locale}.sql"
        process_locale(conn, locale, path)

    print("\nDone!")

    conn.close()


if __name__ == "__main__":
    main()
