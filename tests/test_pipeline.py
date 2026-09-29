import duckdb

def get_con():
    return duckdb.connect("quickbite.duckdb")

def test_no_duplicate_order_ids():
    con = get_con()
    n = con.execute("""
        SELECT COUNT(*) FROM (
            SELECT order_id, COUNT(*) c FROM mart.orders_fact
            GROUP BY order_id HAVING c > 1
        )
    """).fetchone()[0]
    assert n == 0, f"Found {n} duplicate order_ids"

def test_no_negative_prices():
    con = get_con()
    n = con.execute("SELECT COUNT(*) FROM mart.orders_fact WHERE order_value < 0").fetchone()[0]
    assert n == 0, f"Found {n} negative order_value rows"

def test_every_order_has_valid_user():
    con = get_con()
    n = con.execute("""
        SELECT COUNT(*) FROM mart.orders_fact o
        LEFT JOIN mart.users_dim u ON o.user_id = u.user_id
        WHERE u.user_id IS NULL
    """).fetchone()[0]
    assert n == 0, f"Found {n} orders with no matching user"