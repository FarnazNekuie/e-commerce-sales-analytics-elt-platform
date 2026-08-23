SELECT
    'orders_without_customer' AS check_name,
    COUNT(*) AS failed_rows
FROM olist.orders AS o
LEFT JOIN olist.customers AS c
    ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL

UNION ALL

SELECT
    'items_without_order',
    COUNT(*)
FROM olist.order_items AS oi
LEFT JOIN olist.orders AS o
    ON oi.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

SELECT
    'items_without_product',
    COUNT(*)
FROM olist.order_items AS oi
LEFT JOIN olist.products AS p
    ON oi.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL

SELECT
    'items_without_seller',
    COUNT(*)
FROM olist.order_items AS oi
LEFT JOIN olist.sellers AS s
    ON oi.seller_id = s.seller_id
WHERE s.seller_id IS NULL

UNION ALL

SELECT
    'payments_without_order',
    COUNT(*)
FROM olist.order_payments AS op
LEFT JOIN olist.orders AS o
    ON op.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

SELECT
    'reviews_without_order',
    COUNT(*)
FROM olist.order_reviews AS r
LEFT JOIN olist.orders AS o
    ON r.order_id = o.order_id
WHERE o.order_id IS NULL

UNION ALL

SELECT
    'invalid_review_scores',
    COUNT(*)
FROM olist.order_reviews
WHERE review_score NOT BETWEEN 1 AND 5

UNION ALL

SELECT
    'negative_item_prices',
    COUNT(*)
FROM olist.order_items
WHERE price < 0 OR freight_value < 0

UNION ALL

SELECT
    'negative_payment_values',
    COUNT(*)
FROM olist.order_payments
WHERE payment_value < 0

ORDER BY check_name;


