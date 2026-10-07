import re
import time
import duckdb
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # loads GEMINI_API_KEY from .env (gitignored)

DB_PATH = "quickbite.duckdb"
MODEL = "gemini-3.8-flash"

SCHEMA = """
Tables (DuckDB, schema 'mart'):

mart.orders_fact(order_id, user_id, restaurant_id, order_time TIMESTAMP,
                 order_value, status, delivery_time)
  - status is one of: 'placed', 'cancelled', 'delivered'

mart.users_dim(user_id, signup_date, city_area, device)
  - device is one of: 'android', 'ios', 'web'

mart.restaurants_dim(restaurant_id, name, cuisine, area, rating)

Rules:
- "area" means the user's city_area unless the question says restaurant area.
- Join orders_fact to the dimension tables using the id columns.
- Always write mart.table_name in full.
"""

SYSTEM_PROMPT = f"""You write DuckDB SQL for a food-delivery database.
{SCHEMA}
Return ONLY one SELECT query. No explanation, no markdown, no semicolon at the end."""

_client = None


def get_client():
    # created on first use so importing this module doesn't require GEMINI_API_KEY
    global _client
    if _client is None:
        _client = genai.Client()  # reads GEMINI_API_KEY from your environment
    return _client


def generate_sql(question: str) -> str:
    client = get_client()
    last_error = None
    for attempt in range(1, 5):  # try up to 4 times
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0,
                    max_output_tokens=4000,
                ),
            )
            sql = response.text.strip()
            sql = re.sub(r"^```(?:sql)?|```$", "", sql, flags=re.MULTILINE).strip()
            return sql.rstrip(";")
        except Exception as e:
            last_error = e
            wait = attempt * 5
            print(f"Attempt {attempt} failed ({type(e).__name__}). Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"Gemini is not responding after 4 tries: {last_error}")


BLOCKED_WORDS = ["insert", "update", "delete", "drop", "alter", "create",
                 "attach", "copy", "pragma", "truncate", "replace"]


def is_safe(sql: str) -> bool:
    lowered = sql.lower().strip()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False
    if ";" in lowered:
        return False
    return not any(re.search(rf"\b{w}\b", lowered) for w in BLOCKED_WORDS)


def run_query(sql: str):
    # read_only=True is the real safety lock: writes are impossible
    con = duckdb.connect(DB_PATH, read_only=True)
    try:
        return con.execute(sql).df()
    finally:
        con.close()


def ask(question: str):
    sql = generate_sql(question)
    print("SQL:", sql)
    if not is_safe(sql):
        print("Blocked: this query is not a safe read-only SELECT.")
        return None
    return run_query(sql)


if __name__ == "__main__":
    while True:
        q = input("\nAsk a question (or type 'quit'): ")
        if q.strip().lower() == "quit":
            break
        result = ask(q)
        if result is not None:
            print(result)
