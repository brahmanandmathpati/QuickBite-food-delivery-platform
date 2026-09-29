"""
QuickBite synthetic data generator.

Builds four raw tables and saves them to data/raw/:
    users        50,000 rows
    restaurants     500 rows
    orders      500,000 rows   (+1% deliberately bad rows, +a few duplicates)
    app_events 5,000,000 rows

Run from the repo root:
    python generator/generate_data.py                 # full size
    python generator/generate_data.py --scale 0.01    # tiny test run (1%)
    python generator/generate_data.py --format csv    # force CSV

Same seed -> same data every run.
"""

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
SEED = 42
N_USERS = 50_000
N_RESTAURANTS = 500
N_ORDERS = 500_000
N_EVENTS = 5_000_000

BAD_ROW_FRACTION = 0.01     # 1% bad orders (Section 6 of the requirements)
DUPLICATE_FRACTION = 0.002  # 0.2% exact duplicate orders, so staging has something to de-dup

START = pd.Timestamp("2025-01-01")
END = pd.Timestamp("2026-09-01")   # data window ends here (exclusive)

AREAS = ["Gachibowli", "Madhapur", "Banjara Hills", "Kukatpally",
         "Secunderabad", "Hitech City", "Ameerpet", "Miyapur"]

CUISINES = ["Biryani", "South Indian", "North Indian", "Chinese", "Pizza",
            "Burgers", "Desserts", "Cafe", "Healthy", "Street Food"]

NAME_WORDS_1 = ["Spice", "Royal", "Green", "Golden", "Urban", "Hyderabadi",
                "Tasty", "Fresh", "Paradise", "Bawarchi", "Masala", "Chutney"]
NAME_WORDS_2 = ["Kitchen", "House", "Point", "Corner", "Bites", "Express",
                "Dhaba", "Cafe", "Grill", "Junction", "Tiffins", "Bowl"]

# How busy each hour of the day is (index = hour 0..23). Lunch and dinner peaks.
HOUR_WEIGHTS = np.array([
    2, 1, 1, 0.5, 0.5, 0.5, 1, 2, 3, 3, 3, 4,   # 00-11
    8, 9, 6, 3, 3, 4, 5, 8, 10, 10, 7, 4,       # 12-23
], dtype=float)
HOUR_WEIGHTS /= HOUR_WEIGHTS.sum()

LATE_HOURS = [22, 23, 0, 1, 2, 3]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# 1. users
# ---------------------------------------------------------------------------
def make_users(rng, n):
    window_days = (END - START).days - 30   # nobody signs up in the last 30 days
    users = pd.DataFrame({
        "user_id": np.arange(1, n + 1),
        "signup_date": START + pd.to_timedelta(rng.integers(0, window_days, n), unit="D"),
        "city_area": rng.choice(AREAS, n),
        "device": rng.choice(["android", "ios", "web"], n, p=[0.6, 0.3, 0.1]),
    })
    return users


# ---------------------------------------------------------------------------
# 2. restaurants
# ---------------------------------------------------------------------------
def make_restaurants(rng, n):
    names = (rng.choice(NAME_WORDS_1, n).astype(object) + " "
             + rng.choice(NAME_WORDS_2, n).astype(object))
    restaurants = pd.DataFrame({
        "restaurant_id": np.arange(1, n + 1),
        # add the id so every name is unique, e.g. "Spice Kitchen #17"
        "name": names + " #" + pd.Series(np.arange(1, n + 1)).astype(str),
        "cuisine": rng.choice(CUISINES, n),
        "area": rng.choice(AREAS, n),
        # ratings 2.5-5.0, most around 4.0
        "rating": np.clip(rng.normal(4.0, 0.45, n), 2.5, 5.0).round(1),
    })
    return restaurants


# ---------------------------------------------------------------------------
# 3. orders
# ---------------------------------------------------------------------------
def make_orders(rng, n, users, restaurants):
    n_users = len(users)
    n_rest = len(restaurants)

    # Some users order a lot, most order a little (so "repeat customers" exist).
    user_weights = rng.gamma(shape=0.8, scale=1.0, size=n_users)
    user_weights /= user_weights.sum()
    user_idx = rng.choice(n_users, n, p=user_weights)

    # Popular restaurants get more orders.
    rest_weights = rng.gamma(shape=1.5, scale=1.0, size=n_rest)
    rest_weights /= rest_weights.sum()
    rest_idx = rng.choice(n_rest, n, p=rest_weights)

    user_id = users["user_id"].to_numpy()[user_idx]
    restaurant_id = restaurants["restaurant_id"].to_numpy()[rest_idx]

    # Order time: a random day between the user's signup and END,
    # then a realistic hour of day, then a random minute/second.
    signup = users["signup_date"].to_numpy()[user_idx]
    days_available = ((END - pd.to_datetime(signup)).days).to_numpy()
    day_offset = (rng.random(n) * days_available).astype(int)
    hour = rng.choice(24, n, p=HOUR_WEIGHTS)
    seconds = rng.integers(0, 3600, n)
    order_time = (pd.to_datetime(signup)
                  + pd.to_timedelta(day_offset, unit="D")
                  + pd.to_timedelta(hour, unit="h")
                  + pd.to_timedelta(seconds, unit="s"))

    # Order value in rupees: most 150-600, a long tail of big orders.
    order_value = np.round(rng.lognormal(mean=np.log(320), sigma=0.55, size=n), 2)

    # Delivery time (minutes, the ETA shown when the order is placed).
    # Late night and low-rated restaurants are slower.
    rating = restaurants["rating"].to_numpy()[rest_idx]
    is_late = np.isin(hour, LATE_HOURS)
    delivery_minutes = (rng.gamma(shape=6, scale=5.5, size=n)     # ~33 min average
                        + 6 * is_late
                        + 4 * (4.0 - rating))
    delivery_minutes = np.clip(delivery_minutes, 10, 120).round().astype(int)

    # --- Cancellation: a hidden rule the Day 4 model can learn ---------------
    # Each user has a small "flakiness" -- some users cancel more than others.
    user_flakiness = rng.normal(0, 0.6, n_users)[user_idx]

    logit = (
        -2.6
        + 0.9 * np.log(order_value / 320)          # higher value -> more cancels
        + 0.8 * is_late                            # late night -> more cancels
        + 0.04 * (delivery_minutes - 33)           # slow delivery -> more cancels
        + 0.5 * (4.0 - rating)                     # bad restaurant -> more cancels
        + user_flakiness                           # user history
    )
    p_cancel = 1 / (1 + np.exp(-logit))
    cancelled = rng.random(n) < p_cancel

    status = np.where(cancelled, "cancelled", "delivered").astype(object)
    # Orders in the last 2 hours of the window are still in progress.
    in_progress = order_time >= (END - pd.Timedelta(hours=2))
    status[np.asarray(in_progress)] = "placed"

    orders = pd.DataFrame({
        "order_id": np.arange(1, n + 1),
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "order_time": order_time,
        "order_value": order_value,
        "status": status,
        "delivery_minutes": delivery_minutes,
    })
    orders = orders.sort_values("order_time").reset_index(drop=True)
    orders["order_id"] = np.arange(1, n + 1)   # ids in time order
    return orders


# ---------------------------------------------------------------------------
# 4. app_events
# ---------------------------------------------------------------------------
def make_app_events(rng, n, users, orders):
    """
    Part A: events tied to real orders (view_menu before, place_order at,
            cancel_order after if cancelled). This lets you later ask
            "what did the user do right before cancelling?".
    Part B: random browsing events to fill up to n rows.
    """
    # Part A -- events linked to orders
    o_user = orders["user_id"].to_numpy()
    o_time = orders["order_time"].to_numpy()
    o_cancel = (orders["status"] == "cancelled").to_numpy()

    view_time = o_time - pd.to_timedelta(rng.integers(60, 900, len(orders)), unit="s").to_numpy()
    cancel_time = (o_time[o_cancel]
                   + pd.to_timedelta(rng.integers(60, 1200, o_cancel.sum()), unit="s").to_numpy())

    linked = pd.DataFrame({
        "user_id": np.concatenate([o_user, o_user, o_user[o_cancel]]),
        "event_type": (["view_menu"] * len(orders)
                       + ["place_order"] * len(orders)
                       + ["cancel_order"] * int(o_cancel.sum())),
        "event_time": np.concatenate([view_time, o_time, cancel_time]),
    })

    # Part B -- random browsing to fill the rest
    n_random = n - len(linked)
    if n_random < 0:
        raise ValueError("N_EVENTS is too small for the number of orders")

    user_idx = rng.integers(0, len(users), n_random)
    signup = pd.to_datetime(users["signup_date"].to_numpy()[user_idx])
    seconds_available = (END - signup).total_seconds().to_numpy()
    offset = (rng.random(n_random) * seconds_available).astype("int64")

    random_events = pd.DataFrame({
        "user_id": users["user_id"].to_numpy()[user_idx],
        "event_type": rng.choice(
            ["app_open", "search", "view_menu", "add_to_cart", "remove_from_cart"],
            n_random, p=[0.35, 0.20, 0.25, 0.15, 0.05]),
        "event_time": signup + pd.to_timedelta(offset, unit="s"),
    })

    events = pd.concat([linked, random_events], ignore_index=True)
    events = events.sort_values("event_time", kind="stable").reset_index(drop=True)
    events.insert(0, "event_id", np.arange(1, len(events) + 1))
    return events


# ---------------------------------------------------------------------------
# 5. Inject bad rows (Section 6: the failure we want the pipeline to catch)
# ---------------------------------------------------------------------------
def inject_bad_rows(rng, orders, fraction):
    orders = orders.copy()
    # nullable integer so user_id stays an integer column that can hold nulls
    orders["user_id"] = orders["user_id"].astype("Int64")

    n_bad = int(len(orders) * fraction)
    bad = rng.choice(orders.index, size=n_bad, replace=False)
    half = n_bad // 2
    orders.loc[bad[:half], "user_id"] = pd.NA          # null user_id
    orders.loc[bad[half:], "order_value"] *= -1        # negative order_value

    log(f"  injected {half:,} null user_id + {n_bad - half:,} negative order_value rows")
    return orders


def inject_duplicates(rng, orders, fraction):
    n_dup = int(len(orders) * fraction)
    dup_idx = rng.choice(orders.index, size=n_dup, replace=False)
    orders = pd.concat([orders, orders.loc[dup_idx]], ignore_index=True)
    log(f"  added {n_dup:,} exact duplicate order rows")
    return orders


# ---------------------------------------------------------------------------
# 6. Save
# ---------------------------------------------------------------------------
def pick_format(requested):
    if requested != "auto":
        return requested
    try:
        import pyarrow  # noqa: F401
        return "parquet"
    except ImportError:
        log("pyarrow not installed -> saving CSV instead (pip install pyarrow for Parquet)")
        return "csv"


def save(df, name, out_dir, fmt):
    path = out_dir / f"{name}.{fmt}"
    if fmt == "parquet":
        df.to_parquet(path, index=False)
    else:
        df.to_csv(path, index=False)
    log(f"  saved {path}  ({len(df):,} rows)")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate QuickBite raw data")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="multiply all row counts (e.g. 0.01 for a quick test)")
    parser.add_argument("--format", choices=["auto", "parquet", "csv"], default="auto")
    parser.add_argument("--out", default="data/raw", help="output folder")
    args = parser.parse_args()

    rng = np.random.default_rng(seed=SEED)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = pick_format(args.format)

    n_users = max(100, int(N_USERS * args.scale))
    n_rest = max(20, int(N_RESTAURANTS * args.scale))
    n_orders = max(1_000, int(N_ORDERS * args.scale))
    n_events = max(5_000, int(N_EVENTS * args.scale))

    log("1/6 users");        users = make_users(rng, n_users)
    log("2/6 restaurants");  restaurants = make_restaurants(rng, n_rest)
    log("3/6 orders");       orders = make_orders(rng, n_orders, users, restaurants)
    log(f"  cancellation rate: {(orders['status'] == 'cancelled').mean():.1%}")
    log("4/6 app_events");   app_events = make_app_events(rng, n_events, users, orders)

    log("5/6 bad rows")
    orders = inject_bad_rows(rng, orders, BAD_ROW_FRACTION)
    orders = inject_duplicates(rng, orders, DUPLICATE_FRACTION)

    log(f"6/6 saving to {out_dir}/ as {fmt}")
    save(users, "users", out_dir, fmt)
    save(restaurants, "restaurants", out_dir, fmt)
    save(orders, "orders", out_dir, fmt)
    save(app_events, "app_events", out_dir, fmt)
    log("done")


if __name__ == "__main__":
    main()
