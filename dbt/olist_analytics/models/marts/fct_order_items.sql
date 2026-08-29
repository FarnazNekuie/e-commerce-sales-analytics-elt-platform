with order_items as (

    select *
    from {{ ref('int_order_items_enriched') }}

)

select
    order_item_key,
    order_id,
    order_item_id,
    customer_id,
    customer_unique_id,
    product_id,
    seller_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    shipping_limit_date,
    price,
    freight_value,
    total_item_value
from order_items

