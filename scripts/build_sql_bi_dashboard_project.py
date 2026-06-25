from __future__ import annotations

import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


ROOT = Path.cwd()
PROJECT = ROOT / "portfolio-projects" / "04-sql-bi-dashboard"
DATA = PROJECT / "data"
SQL = PROJECT / "sql"
DOCS = PROJECT / "docs"
DASHBOARD = PROJECT / "dashboard"
RESULT = PROJECT / "result"
SCREENSHOTS = PROJECT / "screenshots"
DB_PATH = DATA / "retail_sales.db"

random.seed(74)


REGIONS = ["Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск", "Краснодар"]
SEGMENTS = ["B2B", "B2C", "Партнеры"]
CHANNELS = ["сайт", "маркетплейс", "менеджер", "повторный заказ"]
PAYMENT_METHODS = ["карта", "счет", "рассрочка"]
ORDER_STATUSES = ["завершен", "в работе", "отменен"]
PAYMENT_STATUSES = ["оплачен", "частично оплачен", "просрочен", "не оплачен"]

PRODUCTS = [
    ("P001", "Ноутбук N-14", "Ноутбуки", 78000, 0.23),
    ("P002", "Монитор M-27", "Мониторы", 26500, 0.31),
    ("P003", "Клавиатура K-8", "Периферия", 6200, 0.38),
    ("P004", "Мышь MX-2", "Периферия", 3900, 0.42),
    ("P005", "Сервер S-2", "Серверы", 245000, 0.19),
    ("P006", "ИБП U-900", "Инфраструктура", 39000, 0.27),
    ("P007", "Коммутатор SW-24", "Сеть", 52000, 0.25),
    ("P008", "Маршрутизатор R-6", "Сеть", 18500, 0.34),
    ("P009", "SSD 1TB", "Комплектующие", 9800, 0.29),
    ("P010", "RAM 32GB", "Комплектующие", 12500, 0.33),
]


def ensure_dirs() -> None:
    for path in [DATA, SQL, DOCS, DASHBOARD, RESULT, SCREENSHOTS]:
        path.mkdir(parents=True, exist_ok=True)
    for keep in PROJECT.glob("**/.gitkeep"):
        keep.unlink()


def fmt_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def weighted_choice(items: list[str], weights: list[float]) -> str:
    return random.choices(items, weights=weights, k=1)[0]


def generate_customers() -> list[dict[str, object]]:
    customers = []
    for idx in range(1, 361):
        segment = weighted_choice(SEGMENTS, [0.42, 0.45, 0.13])
        customers.append(
            {
                "customer_id": f"C{idx:04d}",
                "customer_name": f"Клиент {idx:04d}",
                "segment": segment,
                "region": weighted_choice(REGIONS, [0.32, 0.18, 0.14, 0.13, 0.12, 0.11]),
                "registration_date": (date(2024, 1, 1) + timedelta(days=random.randint(0, 720))).isoformat(),
            }
        )
    return customers


def generate_orders(customers: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    orders: list[dict[str, object]] = []
    items: list[dict[str, object]] = []
    payments: list[dict[str, object]] = []
    order_id = 30001
    item_id = 1
    payment_id = 1
    start = date(2026, 1, 1)

    for day_offset in range(181):
        current_date = start + timedelta(days=day_offset)
        if current_date.weekday() >= 5:
            continue
        daily_orders = random.randint(8, 18)
        for _ in range(daily_orders):
            customer = random.choice(customers)
            channel = weighted_choice(CHANNELS, [0.36, 0.24, 0.25, 0.15])
            status = weighted_choice(ORDER_STATUSES, [0.84, 0.11, 0.05])
            discount = weighted_choice([0.00, 0.03, 0.05, 0.07, 0.10], [0.36, 0.23, 0.21, 0.13, 0.07])
            orders.append(
                {
                    "order_id": order_id,
                    "order_date": current_date.isoformat(),
                    "customer_id": customer["customer_id"],
                    "channel": channel,
                    "status": status,
                    "discount": discount,
                }
            )

            total = 0
            product_count = weighted_choice([1, 2, 3], [0.72, 0.22, 0.06])
            for product_id, product_name, category, base_price, margin in random.sample(PRODUCTS, product_count):
                qty = weighted_choice([1, 2, 3, 4], [0.64, 0.24, 0.09, 0.03])
                price = round(base_price * random.uniform(0.94, 1.08))
                line_revenue = round(price * qty * (1 - discount))
                line_cost = round(line_revenue * (1 - margin))
                total += line_revenue
                items.append(
                    {
                        "item_id": item_id,
                        "order_id": order_id,
                        "product_id": product_id,
                        "quantity": qty,
                        "unit_price": price,
                        "line_revenue": line_revenue,
                        "line_cost": line_cost,
                    }
                )
                item_id += 1

            if status == "отменен":
                payment_status = "не оплачен"
                paid_amount = 0
            else:
                payment_status = weighted_choice(PAYMENT_STATUSES, [0.76, 0.10, 0.08, 0.06])
                if payment_status == "оплачен":
                    paid_amount = total
                elif payment_status == "частично оплачен":
                    paid_amount = round(total * random.uniform(0.35, 0.75))
                elif payment_status == "просрочен":
                    paid_amount = round(total * random.uniform(0.0, 0.35))
                else:
                    paid_amount = 0
            due_date = current_date + timedelta(days=random.choice([7, 10, 14, 21]))
            payments.append(
                {
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "payment_method": weighted_choice(PAYMENT_METHODS, [0.45, 0.43, 0.12]),
                    "payment_status": payment_status,
                    "paid_amount": paid_amount,
                    "due_date": due_date.isoformat(),
                }
            )
            order_id += 1
            payment_id += 1

    return orders, items, payments


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_source_data() -> None:
    customers = generate_customers()
    products = [
        {
            "product_id": product_id,
            "product_name": product_name,
            "category": category,
            "base_price": base_price,
            "target_margin": margin,
        }
        for product_id, product_name, category, base_price, margin in PRODUCTS
    ]
    orders, items, payments = generate_orders(customers)
    write_csv(DATA / "customers.csv", customers)
    write_csv(DATA / "products.csv", products)
    write_csv(DATA / "orders.csv", orders)
    write_csv(DATA / "order_items.csv", items)
    write_csv(DATA / "payments.csv", payments)


def write_sql_files() -> None:
    (SQL / "01_schema.sql").write_text(
        """DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL,
    region TEXT NOT NULL,
    registration_date DATE NOT NULL
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    base_price INTEGER NOT NULL,
    target_margin REAL NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    discount REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    line_revenue INTEGER NOT NULL,
    line_cost INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    payment_status TEXT NOT NULL,
    paid_amount INTEGER NOT NULL,
    due_date DATE NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
""",
        encoding="utf-8",
    )

    (SQL / "02_load_data.sql").write_text(
        """.mode csv
.headers on
.import data/customers.csv customers
.import data/products.csv products
.import data/orders.csv orders
.import data/order_items.csv order_items
.import data/payments.csv payments
""",
        encoding="utf-8",
    )

    (SQL / "03_analytics_queries.sql").write_text(
        """-- 1. KPI по продажам и оплатам
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
""",
        encoding="utf-8",
    )


def build_database() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript((SQL / "01_schema.sql").read_text(encoding="utf-8"))
    for table in ["customers", "products", "orders", "order_items", "payments"]:
        with (DATA / f"{table}.csv").open(encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = [tuple(row.values()) for row in reader]
            placeholders = ", ".join(["?"] * len(reader.fieldnames or []))
            con.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
    con.commit()
    con.close()


def query_to_csv(con: sqlite3.Connection, query: str, output: Path) -> list[dict[str, object]]:
    con.row_factory = sqlite3.Row
    rows = [dict(row) for row in con.execute(query).fetchall()]
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def build_results() -> dict[str, list[dict[str, object]]]:
    con = sqlite3.connect(DB_PATH)
    queries = {
        "kpi_summary": """WITH sales AS (
    SELECT o.order_id, SUM(oi.line_revenue) AS revenue, SUM(oi.line_revenue - oi.line_cost) AS profit, p.paid_amount
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
FROM sales;""",
        "monthly_sales": """SELECT
    strftime('%Y-%m', o.order_date) AS month,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(oi.line_revenue) AS revenue,
    SUM(oi.line_revenue - oi.line_cost) AS profit,
    ROUND(SUM(oi.line_revenue - oi.line_cost) * 1.0 / SUM(oi.line_revenue), 3) AS margin_pct
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status <> 'отменен'
GROUP BY month
ORDER BY month;""",
        "category_performance": """SELECT
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
ORDER BY revenue DESC;""",
        "receivables_by_customer": """WITH order_totals AS (
    SELECT o.order_id, o.customer_id, SUM(oi.line_revenue) AS revenue
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
LIMIT 15;""",
        "channel_performance": """SELECT
    o.channel,
    COUNT(DISTINCT o.order_id) AS orders,
    SUM(oi.line_revenue) AS revenue,
    ROUND(AVG(oi.line_revenue), 0) AS avg_line_revenue,
    RANK() OVER (ORDER BY SUM(oi.line_revenue) DESC) AS revenue_rank
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status <> 'отменен'
GROUP BY o.channel
ORDER BY revenue_rank;""",
    }
    result = {name: query_to_csv(con, query, RESULT / f"{name}.csv") for name, query in queries.items()}
    con.close()
    return result


def svg_bar_chart(rows: list[dict[str, object]], label_key: str, value_key: str, x: int, y: int, width: int, color: str) -> str:
    max_value = max(float(row[value_key]) for row in rows)
    parts = []
    for idx, row in enumerate(rows[:6]):
        yy = y + idx * 42
        bar_width = float(row[value_key]) / max_value * width
        parts.append(
            f'<text x="{x - 12}" y="{yy + 22}" text-anchor="end" font-size="13" fill="#1F2937">{row[label_key]}</text>'
            f'<rect x="{x}" y="{yy}" width="{bar_width:.1f}" height="26" rx="5" fill="{color}"/>'
            f'<text x="{x + bar_width + 10:.1f}" y="{yy + 19}" font-size="12" fill="#475569">{fmt_number(float(row[value_key]))}</text>'
        )
    return "\n".join(parts)


def svg_line_chart(rows: list[dict[str, object]]) -> str:
    x0, y0, width, height = 72, 585, 650, 185
    values = [float(row["revenue"]) for row in rows]
    max_value = max(values)
    min_value = min(values)
    points = []
    labels = []
    for idx, row in enumerate(rows):
        x = x0 + idx * (width / (len(rows) - 1))
        y = y0 - ((float(row["revenue"]) - min_value) / (max_value - min_value)) * height
        points.append(f"{x:.1f},{y:.1f}")
        labels.append(f'<text x="{x:.1f}" y="{y0 + 32}" text-anchor="middle" font-size="12" fill="#64748B">{row["month"][5:]}</text>')
    circles = "".join([f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="5" fill="#1E3A5F"/>' for p in points])
    return f"""
<path d="M {x0} {y0} L {x0 + width} {y0}" stroke="#CBD5E1"/>
<polyline points="{' '.join(points)}" fill="none" stroke="#1E3A5F" stroke-width="4" stroke-linejoin="round"/>
{circles}
{''.join(labels)}
"""


def build_dashboard(results: dict[str, list[dict[str, object]]]) -> None:
    kpi = results["kpi_summary"][0]
    monthly = results["monthly_sales"]
    categories = results["category_performance"]
    receivables = results["receivables_by_customer"]
    channels = results["channel_performance"]
    top_category = categories[0]["category"]
    top_channel = channels[0]["channel"]
    cards = [
        ("Выручка", f'{fmt_number(float(kpi["revenue"]))} ₽'),
        ("Заказы", fmt_number(float(kpi["orders"]))),
        ("Средний чек", f'{fmt_number(float(kpi["avg_order_value"]))} ₽'),
        ("Маржинальность", f'{float(kpi["margin_pct"]) * 100:.1f}%'),
        ("Дебиторка", f'{fmt_number(float(kpi["receivables"]))} ₽'),
        ("Топ-категория", top_category),
    ]
    card_svg = []
    for idx, (label, value) in enumerate(cards):
        col = idx % 3
        row = idx // 3
        x = 54 + col * 300
        y = 98 + row * 115
        card_svg.append(
            f'<rect x="{x}" y="{y}" width="260" height="86" rx="10" fill="#FFFFFF" stroke="#CBD5E1"/>'
            f'<text x="{x + 18}" y="{y + 30}" font-size="13" fill="#64748B">{label}</text>'
            f'<text x="{x + 18}" y="{y + 62}" font-size="24" font-weight="750" fill="#1E3A5F">{value}</text>'
        )

    category_svg = svg_bar_chart(categories, "category", "revenue", 220, 380, 360, "#2B6CB0")
    receivables_svg = svg_bar_chart(receivables, "customer_name", "receivables", 850, 380, 260, "#C05621")
    line_svg = svg_line_chart(monthly)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="820" viewBox="0 0 1180 820">
<style>
text{{font-family:Inter,Segoe UI,Arial,sans-serif;letter-spacing:0}}
</style>
<rect width="1180" height="820" fill="#F8FAFC"/>
<text x="54" y="56" font-size="28" font-weight="800" fill="#1E3A5F">SQL + BI дашборд продаж</text>
<text x="54" y="80" font-size="14" fill="#64748B">Ключевые метрики продаж, маржинальности и дебиторской задолженности</text>
{''.join(card_svg)}
<text x="54" y="330" font-size="20" font-weight="750" fill="#1E3A5F">Выручка по категориям</text>
{category_svg}
<text x="670" y="330" font-size="20" font-weight="750" fill="#1E3A5F">Клиенты с задолженностью</text>
{receivables_svg}
<text x="54" y="535" font-size="20" font-weight="750" fill="#1E3A5F">Динамика выручки по месяцам</text>
{line_svg}
<rect x="790" y="575" width="310" height="125" rx="10" fill="#FFFFFF" stroke="#CBD5E1"/>
<text x="815" y="615" font-size="15" fill="#64748B">Канал с максимальной выручкой</text>
<text x="815" y="655" font-size="26" font-weight="750" fill="#1E3A5F">{top_channel}</text>
<text x="815" y="686" font-size="13" fill="#64748B">Используется для приоритизации BI-отчета</text>
</svg>
"""
    (SCREENSHOTS / "dashboard.svg").write_text(svg, encoding="utf-8")


def build_docs(results: dict[str, list[dict[str, object]]]) -> None:
    kpi = results["kpi_summary"][0]
    categories = results["category_performance"]
    receivables = results["receivables_by_customer"]
    channels = results["channel_performance"]
    top_category = categories[0]
    top_debt = receivables[0]
    top_channel = channels[0]

    (DOCS / "business_context.md").write_text(
        """# Бизнес-контекст

Компания продает компьютерное оборудование через сайт, маркетплейс, менеджеров и повторные заказы. Руководителю отдела продаж нужен регулярный BI-дашборд, который показывает динамику выручки, маржинальность, эффективность каналов и дебиторскую задолженность.

Задача аналитика - подготовить модель данных, написать SQL-запросы, рассчитать ключевые метрики и собрать понятный дашборд для еженедельного контроля.
""",
        encoding="utf-8",
    )
    (DOCS / "data_model.md").write_text(
        """# Модель данных

| Таблица | Назначение | Ключевые поля |
|---|---|---|
| customers | клиенты и сегменты | customer_id, segment, region |
| products | товары и категории | product_id, category, target_margin |
| orders | заказы и каналы продаж | order_id, order_date, customer_id, channel, status |
| order_items | строки заказов | item_id, order_id, product_id, quantity, line_revenue, line_cost |
| payments | оплаты и задолженность | payment_id, order_id, payment_status, paid_amount, due_date |

Связи:

- один клиент может иметь много заказов;
- один заказ может содержать несколько строк товаров;
- каждая строка заказа связана с одним продуктом;
- каждый заказ имеет запись об оплате.
""",
        encoding="utf-8",
    )
    (DOCS / "metrics.md").write_text(
        """# Метрики

| Метрика | Расчет |
|---|---|
| Выручка | сумма `line_revenue` по неотмененным заказам |
| Прибыль | `line_revenue - line_cost` |
| Маржинальность | прибыль / выручка |
| Средний чек | выручка / количество заказов |
| Дебиторская задолженность | выручка заказа - оплаченная сумма |
| Рейтинг канала | ранжирование каналов по выручке через оконную функцию |
""",
        encoding="utf-8",
    )
    (DASHBOARD / "dashboard_spec.md").write_text(
        """# Спецификация дашборда

## Целевая аудитория

Руководитель отдела продаж и коммерческий директор.

## Блоки дашборда

- KPI-карточки: выручка, заказы, средний чек, маржинальность, дебиторская задолженность, топ-категория.
- Динамика выручки по месяцам.
- Выручка по категориям.
- Клиенты с максимальной задолженностью.
- Канал продаж с максимальной выручкой.

## Решения для визуализации

- KPI вынесены в верхний ряд для быстрого чтения.
- Категории и задолженность показаны горизонтальными барами, потому что названия длинные.
- Динамика выручки показана линией по месяцам.
""",
        encoding="utf-8",
    )
    (RESULT / "insights.md").write_text(
        f"""# Аналитические выводы

## Краткий вывод

За январь-июнь 2026 года в модели отражено {fmt_number(float(kpi["orders"]))} неотмененных заказов на сумму {fmt_number(float(kpi["revenue"]))} руб. Средний чек составил {fmt_number(float(kpi["avg_order_value"]))} руб., маржинальность - {float(kpi["margin_pct"]) * 100:.1f}%, дебиторская задолженность - {fmt_number(float(kpi["receivables"]))} руб.

## Что видно по данным

- Наибольшую выручку дает категория **{top_category["category"]}**: {fmt_number(float(top_category["revenue"]))} руб.
- Канал с максимальной выручкой - **{top_channel["channel"]}**.
- Максимальная задолженность у клиента **{top_debt["customer_name"]}**: {fmt_number(float(top_debt["receivables"]))} руб.
- Для управленческого контроля важно смотреть не только выручку, но и маржинальность, задолженность и канал продаж.

## Рекомендации

1. Добавить еженедельный контроль клиентов с задолженностью выше установленного порога.
2. Отдельно отслеживать категории с высокой выручкой и маржинальностью ниже среднего уровня.
3. Использовать рейтинг каналов продаж для распределения рекламного бюджета и фокуса менеджеров.
""",
        encoding="utf-8",
    )


def build_readme(results: dict[str, list[dict[str, object]]]) -> None:
    kpi = results["kpi_summary"][0]
    top_category = results["category_performance"][0]
    top_channel = results["channel_performance"][0]
    top_debt = results["receivables_by_customer"][0]
    (PROJECT / "README.md").write_text(
        f"""# SQL + BI Dashboard

Коммерческий кейс по SQL-аналитике и подготовке BI-дашборда для контроля продаж, маржинальности и дебиторской задолженности.

В проекте использован смоделированный набор данных, отражающий типичную структуру продаж интернет-магазина компьютерного оборудования.

## Бизнес-задача

Руководителю отдела продаж нужен регулярный отчет, который отвечает на вопросы:

- сколько компания продает и как меняется выручка по месяцам;
- какие категории и каналы дают основной вклад;
- где возникает дебиторская задолженность;
- какие метрики нужно вынести на управленческий дашборд.

## Что сделано

- спроектирована SQL-модель из пяти таблиц;
- подготовлена SQLite-база данных;
- написаны SQL-запросы с JOIN, CTE, агрегациями и оконной функцией;
- рассчитаны KPI продаж, маржинальности и задолженности;
- подготовлены CSV-результаты для BI;
- собран макет управленческого дашборда.

## Управленческий дашборд

![SQL + BI дашборд](screenshots/dashboard.svg)

## Ключевые цифры

| Метрика | Значение |
|---|---:|
| Заказы | {fmt_number(float(kpi["orders"]))} |
| Выручка | {fmt_number(float(kpi["revenue"]))} руб. |
| Средний чек | {fmt_number(float(kpi["avg_order_value"]))} руб. |
| Маржинальность | {float(kpi["margin_pct"]) * 100:.1f}% |
| Дебиторская задолженность | {fmt_number(float(kpi["receivables"]))} руб. |
| Топ-категория | {top_category["category"]} |
| Топ-канал | {top_channel["channel"]} |

## Основные выводы

- Категория **{top_category["category"]}** дает максимальную выручку: {fmt_number(float(top_category["revenue"]))} руб.
- Канал **{top_channel["channel"]}** занимает первое место по выручке.
- Наибольшая задолженность у клиента **{top_debt["customer_name"]}**: {fmt_number(float(top_debt["receivables"]))} руб.
- Для руководителя важнее смотреть связку “выручка + маржинальность + задолженность”, а не только продажи.

## SQL-навыки

- проектирование реляционной модели;
- `JOIN` между заказами, товарами, клиентами и оплатами;
- `CTE` для промежуточных расчетов;
- агрегации по месяцам, категориям, каналам и клиентам;
- оконная функция `RANK()` для рейтинга каналов;
- подготовка выгрузок для BI-дашборда.

## Структура проекта

| Артефакт | Файл |
|---|---|
| Бизнес-контекст | [docs/business_context.md](docs/business_context.md) |
| Модель данных | [docs/data_model.md](docs/data_model.md) |
| Метрики | [docs/metrics.md](docs/metrics.md) |
| SQLite-база | [data/retail_sales.db](data/retail_sales.db) |
| Исходные CSV | [data](data) |
| DDL | [sql/01_schema.sql](sql/01_schema.sql) |
| Загрузка данных | [sql/02_load_data.sql](sql/02_load_data.sql) |
| Аналитические запросы | [sql/03_analytics_queries.sql](sql/03_analytics_queries.sql) |
| Спецификация дашборда | [dashboard/dashboard_spec.md](dashboard/dashboard_spec.md) |
| Итоговые выгрузки | [result](result) |
| Аналитические выводы | [result/insights.md](result/insights.md) |

## Как проверить

База уже собрана в `data/retail_sales.db`. Запросы можно выполнить в SQLite:

```sql
.open data/retail_sales.db
.read sql/03_analytics_queries.sql
```

## Формулировка для резюме

Подготовила SQL + BI кейс для контроля продаж: спроектировала модель данных, собрала SQLite-базу, написала аналитические SQL-запросы с JOIN, CTE и оконной функцией, рассчитала KPI по выручке, маржинальности и дебиторской задолженности, подготовила выгрузки и макет управленческого дашборда.
""",
        encoding="utf-8",
    )


def main() -> None:
    ensure_dirs()
    write_source_data()
    write_sql_files()
    build_database()
    results = build_results()
    build_dashboard(results)
    build_docs(results)
    build_readme(results)


if __name__ == "__main__":
    main()
