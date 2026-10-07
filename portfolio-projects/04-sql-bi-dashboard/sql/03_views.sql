-- Aggregate each one-to-many relation BEFORE joining: one row per order.
CREATE VIEW order_totals AS
SELECT order_id, SUM(line_revenue) AS revenue, SUM(line_cost) AS cost,
       SUM(line_revenue-line_cost) AS profit
FROM order_items GROUP BY order_id;
CREATE VIEW payment_totals AS
SELECT order_id, SUM(paid_amount) AS paid_amount, MIN(due_date) AS due_date,
       COUNT(*) AS payment_records
FROM payments GROUP BY order_id;
CREATE VIEW sales_order_mart AS
SELECT o.*, c.customer_name, c.segment, c.region,
       COALESCE(t.revenue,0) AS revenue, COALESCE(t.cost,0) AS cost,
       COALESCE(t.profit,0) AS profit, COALESCE(p.paid_amount,0) AS paid_amount,
       MAX(COALESCE(t.revenue,0)-COALESCE(p.paid_amount,0),0) AS receivables,
       MAX(COALESCE(p.paid_amount,0)-COALESCE(t.revenue,0),0) AS overpayment,
       p.due_date, COALESCE(p.payment_records,0) AS payment_records
FROM orders o JOIN customers c USING(customer_id)
LEFT JOIN order_totals t USING(order_id)
LEFT JOIN payment_totals p USING(order_id)
WHERE o.status <> 'отменен';
