with order_items as (

    select *
    from {{ ref('stg_order_items') }}

),

orders as (

    select *
    from {{ ref('stg_orders') }}

),

customers as (

    select *
    from {{ ref('stg_customers') }}

),

products as (

    select *
    from {{ ref('int_products_enriched') }}

),

sellers as (

    select *
    from {{ ref('stg_sellers') }}

),

enriched as (

    select
        order_items.order_item_key,
        order_items.order_id,
        order_items.order_item_id,

        orders.customer_id,
        customers.customer_unique_id,
        customers.customer_city,
        customers.customer_state,

        order_items.product_id,
        products.product_category_name,
        products.product_category_name_english,

        order_items.seller_id,
        sellers.seller_city,
        sellers.seller_state,

        orders.order_status,
        orders.order_purchase_timestamp,
        orders.order_approved_at,
        orders.order_delivered_carrier_date,
        orders.order_delivered_customer_date,
        orders.order_estimated_delivery_date,

        order_items.shipping_limit_date,
        order_items.price,
        order_items.freight_value,
        order_items.price + order_items.freight_value
            as total_item_value

    from order_items
    left join orders
        on order_items.order_id = orders.order_id
    left join customers
        on orders.customer_id = customers.customer_id
    left join products
        on order_items.product_id = products.product_id
    left join sellers
        on order_items.seller_id = sellers.seller_id

)

select *
from enriched

