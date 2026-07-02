# EZMetrology Door Analysis Wizard
A quantitative approach to automotive door troubleshooting.

## Install Instructions (Linux)
The dependencies for this program are python3 (Version 3.12.3, python3-full package is recommended on Debian systems), and postgresql (Version 16.14). In order to get Python to work correctly for this setup is recommended to setup a venv with the correct packages installed. I optionally, but strongly suggest you get pgadmin4 [https://www.pgadmin.org/download/pgadmin-4-apt/] to make your database setup relatively painless, especially if you are used to SQL Server or something of that nature.

```
sudo apt install postgresql python3-full
python3 -m venv [inser venv name]
path/to/venv/bin/pip install pandas psycopg PyQt6 pyqtgraph
```

Once the needed packages are installed, you must recreate the database server on your local network using data/pseudo_database/ezsaw_tables.pgsql. I will not go into the specifics of how to set this up, as it is different for how each tester wants to configure his machine.

In these stages it is recommended that if you desire to work on the prototypes, you should have an IDE with a Python3 debugger such as VSCodium so you can easily reset and retrace issues as you come up.

## Build Instructions (Windows) TODO
The setup is similiar on Windows, except the mirrors for a python3 and postgresql downloads can be found here [https://www.python.org/downloads/windows/] and here [https://www.pgadmin.org/download/pgadmin-4-windows/] respectively. Notice I linked pgadmin4 instead of a plain postgresql installation... this is becuase you will most probably want pgadmin if you're using postgresql in any capacity as it has a very intuitive interface for interacting with your local database servers and otherwise. 