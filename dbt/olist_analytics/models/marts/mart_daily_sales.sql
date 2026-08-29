with delivered_orders as (

    select *
    from {{ ref('fct_orders') }}
    where order_status = 'delivered'

),

daily_sales as (

    select
        order_purchase_date,
        count(*) as order_count,
        count(distinct customer_unique_id) as customer_count,
        sum(item_count) as item_count,
        sum(total_payment_value) as total_revenue,
        avg(total_payment_value) as average_order_value,
        sum(total_freight_value) as total_freight_value,
        avg(delivery_days) as average_delivery_days,
        avg(average_review_score) as average_review_score,
        count_if(is_late_delivery) as late_delivery_count
    from delivered_orders
    group by order_purchase_date

)

select *
from daily_sales

