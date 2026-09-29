import duckdb

con = duckdb.connect("quickbite.duckdb")
con.execute("CREATE SCHEMA IF NOT EXISTS mart")

con.execute("""
    CREATE OR REPLACE TABLE mart.users_dim AS
    SELECT user_id, signup_date, city_area, device FROM staging.users
""")

con.execute("""
    CREATE OR REPLACE TABLE mart.restaurants_dim AS
    SELECT restaurant_id, name, cuisine, area, rating FROM staging.restaurants
""")

con.execute("""
    CREATE OR REPLACE TABLE mart.orders_fact AS
    SELECT o.order_id, o.user_id, o.restaurant_id, o.order_time,
           o.order_value, o.status, o.delivery_minutes
    FROM staging.orders o
    JOIN mart.users_dim u ON o.user_id = u.user_id
    JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
""")

print("Marts built.")