import duckdb

con = duckdb.connect("quickbite.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS raw")

for table in ["users", "restaurants", "orders", "app_events"]:
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.{table} AS
        SELECT * FROM read_csv('data/raw/{table}.csv', sample_size=-1)
    """)

print("Raw load done.")