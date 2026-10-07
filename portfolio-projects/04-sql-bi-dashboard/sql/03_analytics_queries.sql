-- kpi_summary
SELECT COUNT(*) AS orders, COALESCE(SUM(revenue),0) AS revenue,
ROUND(AVG(revenue),0) AS avg_order_value,
ROUND(SUM(profit)*1.0/NULLIF(SUM(revenue),0),3) AS margin_pct,
COALESCE(SUM(receivables),0) AS receivables, COALESCE(SUM(overpayment),0) AS overpayments
FROM sales_order_mart;

-- monthly_sales
SELECT substr(order_date,1,7) AS month, COUNT(*) AS orders,
SUM(revenue) AS revenue, SUM(profit) AS profit,
ROUND(SUM(profit)*1.0/NULLIF(SUM(revenue),0),3) AS margin_pct
FROM sales_order_mart GROUP BY month ORDER BY month;

-- category_performance
SELECT pr.category, COUNT(DISTINCT m.order_id) AS orders,
SUM(i.line_revenue) AS revenue, SUM(i.line_revenue-i.line_cost) AS profit,
ROUND(SUM(i.line_revenue-i.line_cost)*1.0/NULLIF(SUM(i.line_revenue),0),3) AS margin_pct
FROM sales_order_mart m JOIN order_items i USING(order_id) JOIN products pr USING(product_id)
GROUP BY pr.category ORDER BY revenue DESC, pr.category;

-- receivables_by_customer
SELECT customer_name, segment, region, SUM(receivables) AS receivables,
COUNT(*) AS unpaid_orders FROM sales_order_mart WHERE receivables > 0
GROUP BY customer_id,customer_name,segment,region ORDER BY receivables DESC, customer_id LIMIT 15;

-- channel_performance
SELECT channel, COUNT(*) AS orders, SUM(revenue) AS revenue,
ROUND(AVG(revenue),0) AS avg_order_value,
RANK() OVER (ORDER BY SUM(revenue) DESC) AS revenue_rank
FROM sales_order_mart GROUP BY channel ORDER BY revenue_rank, channel;
