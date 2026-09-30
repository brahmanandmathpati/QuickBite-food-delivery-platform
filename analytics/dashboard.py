import duckdb
import streamlit as st

con = duckdb.connect("quickbite.duckdb")

st.subheader("Orders per Day")
orders_per_day = con.execute("""
    SELECT CAST(order_time AS DATE) AS order_date, COUNT(*) AS total_orders
    FROM mart.orders_fact
    GROUP BY order_date
    ORDER BY order_date
""").df()
st.line_chart(orders_per_day.set_index("order_date"))

st.subheader("Top 10 Restaurants by Revenue")
top_restaurants = con.execute("""
    SELECT r.name, SUM(o.order_value) AS total_revenue
    FROM mart.orders_fact o
    JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
    WHERE o.status = 'delivered'
    GROUP BY r.name
    ORDER BY total_revenue DESC LIMIT 10
""").df()
st.bar_chart(top_restaurants.set_index("name"))

st.subheader("Cancellation Rate by Hour of Day")
cancel_by_hour = con.execute("""
    SELECT EXTRACT(HOUR FROM order_time) AS hour_of_day,
           ROUND(100.0 * SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancel_rate_pct
    FROM mart.orders_fact
    GROUP BY hour_of_day ORDER BY hour_of_day
""").df()
st.line_chart(cancel_by_hour.set_index("hour_of_day"))

st.subheader("Repeat Customers (5+ orders)")
repeat_customers = con.execute("""
    SELECT user_id, COUNT(*) AS order_count
    FROM mart.orders_fact
    GROUP BY user_id HAVING COUNT(*) >= 5
    ORDER BY order_count DESC
""").df()
st.dataframe(repeat_customers)