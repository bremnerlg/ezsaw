# EZMetrology Door Analysis Wizard
A quantitative approach to automotive door troubleshooting.

## Install Instructions (Linux)
The dependencies for this program are python3 (Version 3.12.3, python3-full package is recommended on Debian systems), and postgresql (Version 16.14). In order to get Python to work correctly for this setup is recommended to setup a venv with the correct packages installed. I optionally, but strongly suggest you get [pgadmin4](https://www.pgadmin.org/download/pgadmin-4-apt/) to make your database setup relatively painless, especially if you are used to SQL Server or something of that nature.

```
sudo apt install postgresql python3-full
python3 -m venv [insert venv name]
path/to/venv/bin/pip install pandas psycopg PyQt6 pyqtgraph macropy
```

Once the needed packages are installed, you must recreate the database server on your local network using the SQL schemas in `db/` (e.g. `db/ezsaw_tables.sql`). I will not go into the specifics of how to set this up, as it is different for how each tester wants to configure his machine.

In these stages it is recommended that if you desire to work on the prototypes, you should have an IDE with a Python3 debugger such as VSCodium so you can easily reset and retrace issues as you come up.

## Build Instructions (Windows) TODO
The setup is similiar on Windows, except the mirrors for a python3 and postgresql downloads can be found [here](https://www.python.org/downloads/windows/) and [here](https://www.postgresql.org/download/windows/) respectively.

When installing Python, ensure that you select the options to include pip and venvs, as this is very important for a testing/development workflow with EZSAW. The author will try to improve upon this documentation as time and experimentation goes on, as Windows testing has not yet been done.

To install pip dependencies, you can either opt for a venv or simply install to your host machine. For Windows it doesn't matter as it does for Linux distributions, as there is little-to-no risk of package management conflict.

In powershell, execute:
```
pip install pandas numpy psycopg[binary] PyQt5 pyqtgraph
```
and you will have all of the needed Python dependencies.