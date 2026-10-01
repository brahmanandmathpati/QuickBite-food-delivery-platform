-- Q1: Orders per day
SELECT CAST(order_time AS DATE) AS order_date, COUNT(*) AS total_orders
FROM mart.orders_fact
GROUP BY order_date
ORDER BY order_date;

-- Q2: Top 10 restaurants by revenue
SELECT r.name, r.cuisine, SUM(o.order_value) AS total_revenue
FROM mart.orders_fact o
JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
WHERE o.status = 'delivered'
GROUP BY r.name, r.cuisine
ORDER BY total_revenue DESC
LIMIT 10;

-- Q3: Cancellation rate by hour of day
SELECT
    EXTRACT(HOUR FROM order_time) AS hour_of_day,
    COUNT(*) AS total_orders,
    ROUND(100.0 * SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancel_rate_pct
FROM mart.orders_fact
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Q4: Repeat customers (5+ orders)
SELECT user_id, COUNT(*) AS order_count
FROM mart.orders_fact
GROUP BY user_id
HAVING COUNT(*) >= 5
ORDER BY order_count DESC;

-- Q5: Average order value by city area
SELECT u.city_area, ROUND(AVG(o.order_value), 2) AS avg_order_value
FROM mart.orders_fact o
JOIN mart.users_dim u ON o.user_id = u.user_id
GROUP BY u.city_area
ORDER BY avg_order_value DESC;

-- Q6: Average delivery time by restaurant
-- (delivery_minutes is already stored directly in orders_fact, no need to diff timestamps)
SELECT r.name,
       ROUND(AVG(o.delivery_minutes), 1) AS avg_delivery_minutes
FROM mart.orders_fact o
JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
WHERE o.status = 'delivered'
GROUP BY r.name
ORDER BY avg_delivery_minutes ASC;

-- Q7: Orders by device type
SELECT u.device, COUNT(*) AS total_orders
FROM mart.orders_fact o
JOIN mart.users_dim u ON o.user_id = u.user_id
GROUP BY u.device
ORDER BY total_orders DESC;

-- Q8: New signups per week
SELECT DATE_TRUNC('week', signup_date) AS signup_week, COUNT(*) AS new_users
FROM mart.users_dim
GROUP BY signup_week
ORDER BY signup_week;

-- Q9: Top cuisine by number of orders
SELECT r.cuisine, COUNT(*) AS total_orders
FROM mart.orders_fact o
JOIN mart.restaurants_dim r ON o.restaurant_id = r.restaurant_id
GROUP BY r.cuisine
ORDER BY total_orders DESC;

-- Q10: Cancellation rate by city area
SELECT u.city_area,
       ROUND(100.0 * SUM(CASE WHEN o.status = 'cancelled' THEN 1 ELSE 0 END) / COUNT(*), 2) AS cancel_rate_pct
FROM mart.orders_fact o
JOIN mart.users_dim u ON o.user_id = u.user_id
GROUP BY u.city_area
ORDER BY cancel_rate_pct DESC;
