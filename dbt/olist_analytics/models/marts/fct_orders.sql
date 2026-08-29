with orders as (

    select *
    from {{ ref('int_orders_enriched') }}

)

select
    order_id,
    customer_id,
    customer_unique_id,
    order_status,
    order_purchase_timestamp,
    order_purchase_date,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    delivery_days,
    delivery_delay_days,
    is_late_delivery,
    item_count,
    distinct_product_count,
    distinct_seller_count,
    total_product_value,
    total_freight_value,
    total_order_item_value,
    payment_record_count,
    payment_type_count,
    max_payment_installments,
    total_payment_value,
    review_count,
    average_review_score,
    minimum_review_score,
    maximum_review_score,
    latest_review_date,
    latest_review_answer_timestamp
from orders

