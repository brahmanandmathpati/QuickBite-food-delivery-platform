SELECT DATE(order_time) AS order_date, COUNT(*) AS num_orders
FROM mart.orders_fact
GROUP BY order_date
ORDER BY order_date;