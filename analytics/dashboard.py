import duckdb
import streamlit as st

st.set_page_config(page_title="QuickBite KPI Dashboard", layout="wide")
st.title("QuickBite Analytics Dashboard")

con = duckdb.connect("quickbite.duckdb", read_only=True)

st.subheader("1. Orders per Day")
df1 = con.execute("""
    SELECT CAST(order_time AS DATE) AS order_date, COUNT(*) AS total_orders
    FROM mart.orders_fact GROUP BY order_date ORDER BY order_date
""").df()
st.line_chart(df1.set_index("order_date"))

st.subheader("2. Top 10 Restaurants by Revenue")
df2 = con.execute("""
    SELECT r.name, SUM(o.order_value) AS total_revenue
    FROM mart.orders_fact o JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
    WHERE o.status = 'delivered' GROUP BY r.name ORDER BY total_revenue DESC LIMIT 10
""").df()
st.bar_chart(df2.set_index("name"))

st.subheader("3. Cancellation Rate by Hour")
df3 = con.execute("""
    SELECT EXTRACT(HOUR FROM order_time) AS hour_of_day,
           ROUND(100.0 * SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancel_rate_pct
    FROM mart.orders_fact GROUP BY hour_of_day ORDER BY hour_of_day
""").df()
st.line_chart(df3.set_index("hour_of_day"))

st.subheader("4. Repeat Customers (5+ orders)")
df4 = con.execute("""
    SELECT user_id, COUNT(*) AS order_count
    FROM mart.orders_fact GROUP BY user_id HAVING COUNT(*) >= 5 ORDER BY order_count DESC
""").df()
st.dataframe(df4)

st.subheader("5. Avg Order Value by City Area")
df5 = con.execute("""
    SELECT u.city_area, ROUND(AVG(o.order_value), 2) AS avg_order_value
    FROM mart.orders_fact o JOIN mart.users_dim u ON o.user_id = u.user_id
    GROUP BY u.city_area ORDER BY avg_order_value DESC
""").df()
st.bar_chart(df5.set_index("city_area"))

st.subheader("6. Avg Delivery Time by Restaurant")
df6 = con.execute("""
    SELECT r.name, ROUND(AVG(o.delivery_minutes), 1) AS avg_delivery_minutes
    FROM mart.orders_fact o JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
    WHERE o.status = 'delivered' GROUP BY r.name ORDER BY avg_delivery_minutes ASC
""").df()
st.dataframe(df6)

st.subheader("7. Orders by Device Type")
df7 = con.execute("""
    SELECT u.device, COUNT(*) AS total_orders
    FROM mart.orders_fact o JOIN mart.users_dim u ON o.user_id = u.user_id
    GROUP BY u.device ORDER BY total_orders DESC
""").df()
st.bar_chart(df7.set_index("device"))

st.subheader("8. New Signups per Week")
df8 = con.execute("""
    SELECT DATE_TRUNC('week', signup_date) AS signup_week, COUNT(*) AS new_users
    FROM mart.users_dim GROUP BY signup_week ORDER BY signup_week
""").df()
st.line_chart(df8.set_index("signup_week"))

st.subheader("9. Top Cuisine by Orders")
df9 = con.execute("""
    SELECT r.cuisine, COUNT(*) AS total_orders
    FROM mart.orders_fact o JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
    GROUP BY r.cuisine ORDER BY total_orders DESC
""").df()
st.bar_chart(df9.set_index("cuisine"))

st.subheader("10. Cancellation Rate by City Area")
df10 = con.execute("""
    SELECT u.city_area,
           ROUND(100.0 * SUM(CASE WHEN o.status='cancelled' THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancel_rate_pct
    FROM mart.orders_fact o JOIN mart.users_dim u ON o.user_id = u.user_id
    GROUP BY u.city_area ORDER BY cancel_rate_pct DESC
""").df()
st.bar_chart(df10.set_index("city_area"))
