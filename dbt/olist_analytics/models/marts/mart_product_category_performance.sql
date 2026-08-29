with order_items as (

    select *
    from {{ ref('fct_order_items') }}
    where order_status = 'delivered'

),

products as (

    select *
    from {{ ref('dim_products') }}

),

category_performance as (

    select
        products.product_category_name_english,
        count(*) as item_count,
        count(distinct order_items.order_id) as order_count,
        count(distinct order_items.product_id) as product_count,
        count(distinct order_items.seller_id) as seller_count,
        sum(order_items.price) as total_product_revenue,
        sum(order_items.freight_value) as total_freight_value,
        sum(order_items.total_item_value) as total_item_value,
        avg(order_items.price) as average_item_price
    from order_items
    left join products
        on order_items.product_id = products.product_id
    group by products.product_category_name_english

)

select *
from category_performance

