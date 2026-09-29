import duckdb

con = duckdb.connect("quickbite.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS staging")

# Catch the bad rows, put them in their own table (don't just delete them)
con.execute("""
    CREATE OR REPLACE TABLE staging.orders_quarantine AS
    SELECT * FROM raw.orders
    WHERE user_id IS NULL OR order_value < 0
""")

# Keep only good rows, remove exact duplicates
con.execute("""
    CREATE OR REPLACE TABLE staging.orders AS
    SELECT DISTINCT *
    FROM raw.orders
    WHERE user_id IS NOT NULL AND order_value >= 0
""")

con.execute("CREATE OR REPLACE TABLE staging.users AS SELECT DISTINCT * FROM raw.users")
con.execute("CREATE OR REPLACE TABLE staging.restaurants AS SELECT DISTINCT * FROM raw.restaurants")

n_bad = con.execute("SELECT COUNT(*) FROM staging.orders_quarantine").fetchone()[0]
print(f"Quarantined {n_bad} bad orders.")