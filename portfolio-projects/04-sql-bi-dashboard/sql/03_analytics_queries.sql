-- 1. KPI по продажам и оплатам
WITH sales AS (
    SELECT
        o.order_id,
        SUM(oi.line_revenue) AS revenue,
        SUM(oi.line_revenue - oi.line_cost) AS profit,
        p.paid_amount
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN payments p ON p.order_id = o.order_id
    WHERE o.status <> 'отменен'
    GROUP BY o.order_id
)
SELECT
    COUNT(*) AS orders,
    SUM(revenue) AS revenue,
    ROUND(AVG(revenue), 0) AS avg_order_value,
    ROUND(SUM(profit) * 1.0 / SUM(revenue), 3) AS margin_pct,
    SUM(revenue - paid_amount) AS receivables
FROM sales;

-- 2. Динамика по месяцам
SELECT
    strftime('%Y-%m', o.order_date) AS month,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(oi.line_revenue) AS revenue,
    SUM(oi.line_revenue - oi.line_cost) AS profit,
    ROUND(SUM(oi.line_revenue - oi.line_cost) * 1.0 / SUM(oi.line_revenue), 3) AS margin_pct
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status <> 'отменен'
GROUP BY month
ORDER BY month;

-- 3. Категории с наибольшей выручкой
SELECT
    pr.category,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(oi.line_revenue) AS revenue,
    SUM(oi.line_revenue - oi.line_cost) AS profit,
    ROUND(SUM(oi.line_revenue - oi.line_cost) * 1.0 / SUM(oi.line_revenue), 3) AS margin_pct
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products pr ON pr.product_id = oi.product_id
WHERE o.status <> 'отменен'
GROUP BY pr.category
ORDER BY revenue DESC;

-- 4. Дебиторская задолженность по клиентам
WITH order_totals AS (
    SELECT
        o.order_id,
        o.customer_id,
        SUM(oi.line_revenue) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.status <> 'отменен'
    GROUP BY o.order_id, o.customer_id
)
SELECT
    c.customer_name,
    c.segment,
    c.region,
    SUM(ot.revenue - p.paid_amount) AS receivables,
    COUNT(*) AS unpaid_orders
FROM order_totals ot
JOIN payments p ON p.order_id = ot.order_id
JOIN customers c ON c.customer_id = ot.customer_id
WHERE ot.revenue > p.paid_amount
GROUP BY c.customer_id, c.customer_name, c.segment, c.region
ORDER BY receivables DESC
LIMIT 15;

-- 5. Рейтинг каналов продаж
SELECT
    o.channel,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(oi.line_revenue) AS revenue,
    ROUND(AVG(oi.line_revenue), 0) AS avg_line_revenue,
    RANK() OVER (ORDER BY SUM(oi.line_revenue) DESC) AS revenue_rank
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status <> 'отменен'
GROUP BY o.channel
ORDER BY revenue_rank;
