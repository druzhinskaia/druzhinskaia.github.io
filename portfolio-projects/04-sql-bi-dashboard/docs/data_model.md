# Модель данных

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
