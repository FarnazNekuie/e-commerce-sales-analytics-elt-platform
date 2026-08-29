with order_items as (

    select *
    from {{ ref('int_order_items_enriched') }}

),

aggregated as (

    select
        order_id,
        count(*) as item_count,
        count(distinct product_id) as distinct_product_count,
        count(distinct seller_id) as distinct_seller_count,
        sum(price) as total_product_value,
        sum(freight_value) as total_freight_value,
        sum(total_item_value) as total_order_item_value
    from order_items
    group by order_id

)

select *
from aggregated

