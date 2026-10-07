PRAGMA foreign_keys = ON;
DROP VIEW IF EXISTS sales_order_mart;
DROP VIEW IF EXISTS payment_totals;
DROP VIEW IF EXISTS order_totals;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL,
    region TEXT NOT NULL,
    registration_date TEXT NOT NULL
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    base_price INTEGER NOT NULL CHECK (base_price >= 0),
    target_margin REAL NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    discount REAL NOT NULL CHECK (discount BETWEEN 0 AND 1),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    line_revenue INTEGER NOT NULL CHECK (line_revenue >= 0),
    line_cost INTEGER NOT NULL CHECK (line_cost >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE payments (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    payment_status TEXT NOT NULL,
    paid_amount INTEGER NOT NULL CHECK (paid_amount >= 0),
    due_date TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

