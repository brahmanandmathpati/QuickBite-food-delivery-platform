# QuickBite — Design

## 1. What problem?
Managers can't see why orders get cancelled. QuickBite has no single view that
connects a cancelled order back to the user, restaurant, and app behavior
around it, so cancellations get investigated by gut feel instead of data.

## 2. What will I build?
Raw data → clean data → final tables → dashboard → model → AI assistant.

- **Raw**: the four source tables as they land — `users`, `restaurants`,
  `orders`, `app_events` — untouched, messy, duplicates and nulls allowed.
- **Clean**: the same tables with types fixed, duplicates removed, bad rows
  (e.g. orders with no matching user/restaurant) flagged or dropped.
- **Final tables**: analysis-ready marts, e.g. `fct_orders` (one row per
  order enriched with user and restaurant attributes) and
  `fct_order_events` (order joined to the app_events that happened around it).
- **Dashboard**: Streamlit app showing cancellation rate over time, by city
  area, by cuisine, and by restaurant, so managers can slice the problem.
- **Model**: scikit-learn classifier that predicts, at order time, the
  probability an order gets cancelled — surfaces the strongest drivers
  (restaurant rating, area, device, time of day, etc.).
- **AI assistant**: a chat layer over the mart tables so a manager can ask
  "why did cancellations spike in Koramangala last week?" in plain English.

## 3. Which tools?
Python, DuckDB (or Postgres), pytest, Streamlit, scikit-learn.

## 4. What are the 3 layers?
- **raw** = data exactly as it came, messy — direct copies of `users`,
  `restaurants`, `orders`, `app_events`.
- **staging** = cleaned — deduplicated, typed, standardized column names
  and categories (e.g. normalized `status`, `event_type`, `cuisine` values),
  orphan foreign keys resolved or dropped.
- **mart** = final tables for questions — `fct_orders`, `dim_users`,
  `dim_restaurants`, and a cancellation-focused table joining orders to the
  `app_events` in the minutes before cancellation, built to answer "why do
  orders get cancelled" directly.

### Source tables (raw layer)
| Table | Rows (approx) | Primary key | Notes |
|---|---|---|---|
| `users` | 50,000 | `user_id` | `signup_date`, `city_area`, `device` |
| `restaurants` | 500 | `restaurant_id` | `name`, `cuisine`, `area`, `rating` |
| `orders` | 500,000 | `order_id` | FK `user_id`, FK `restaurant_id`, `status` (placed/cancelled/delivered), `order_time`, `order_value`, `delivery_time` |
| `app_events` | 5,000,000 | `event_id` | FK `user_id`, `event_type`, `timestamp` |

Relationships: one `user` → many `orders` and many `app_events`; one
`restaurant` → many `orders`. See
[table diagram.png](../resources/table%20diagram.png).

## 5. What is "done"? (Definition of Done)
No requirements doc exists yet with an official checklist — this is a draft
to replace once one is written:

- [ ] Raw layer loads all four source tables unchanged, with row counts
      matching the source.
- [ ] Staging layer has no duplicate primary keys and no orphaned foreign
      keys (every order's `user_id`/`restaurant_id` resolves).
- [ ] Mart tables answer the core question: cancellation rate sliceable by
      time, city area, cuisine, and restaurant.
- [ ] pytest suite covers the raw→staging and staging→mart transforms
      (row counts, null checks, key uniqueness) and passes in CI.
- [ ] Streamlit dashboard loads from the mart layer and shows cancellation
      rate broken down by the dimensions above.
- [ ] Model predicts cancellation probability with a documented baseline
      metric (e.g. AUC) and lists its top features.
- [ ] AI assistant can answer at least 3 sample manager questions correctly
      against the mart tables.
- [ ] README documents how to run the pipeline end to end from raw data to
      dashboard.