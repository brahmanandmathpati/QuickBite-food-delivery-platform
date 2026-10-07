import duckdb
import pytest
from assistant.text_to_sql import ask

QUESTIONS = [
    ("How many orders are there in total?",
     "SELECT COUNT(*) FROM mart.orders_fact"),

    ("Which area has the most cancellations?",
     """SELECT u.city_area FROM mart.orders_fact o
        JOIN mart.users_dim u ON o.user_id = u.user_id
        WHERE o.status = 'cancelled'
        GROUP BY u.city_area ORDER BY COUNT(*) DESC LIMIT 1"""),

    ("What is the average order value?",
     "SELECT AVG(order_value) FROM mart.orders_fact"),

    ("Which cuisine has the most orders?",
     """SELECT r.cuisine FROM mart.orders_fact o
        JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
        GROUP BY r.cuisine ORDER BY COUNT(*) DESC LIMIT 1"""),

    ("How many users have placed 5 or more orders?",
     """SELECT COUNT(*) FROM (SELECT user_id FROM mart.orders_fact
        GROUP BY user_id HAVING COUNT(*) >= 5)"""),
]


def hand_written(sql):
    con = duckdb.connect("quickbite.duckdb", read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


@pytest.mark.parametrize("question,truth_sql", QUESTIONS)
def test_assistant_matches_hand_written_sql(question, truth_sql):
    result = ask(question)
    assert result is not None, f"Blocked: {question}"
    got = result.iloc[0, 0]
    expected = hand_written(truth_sql)[0][0]
    if isinstance(expected, float):
        assert got == pytest.approx(expected), f"{question}: {got} != {expected}"
    else:
        assert got == expected, f"{question}: {got} != {expected}"
