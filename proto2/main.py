import psycopg

def vin_fetch(vin_name: str):
    conn = psycopg.connect("dbname=learning_db user=postgres") # if database is upgrade eventually this will have to be changed accordingly.
    cur = conn.cursor()

    cur.execute ("SELECT vin FROM steps WHERE vin=" + user_in)
    return cur.fetchone()



def main():
    jls_extract_var = "Enter a vehicle VIN number: "
    user_in = str(input(jls_extract_var))
    print(vin_fetch(user_in))

main()