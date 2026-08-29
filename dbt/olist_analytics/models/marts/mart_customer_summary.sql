with orders as (

    select *
    from {{ ref('fct_orders') }}

),

customer_summary as (

    select
        customer_unique_id,
        min(order_purchase_date) as first_order_date,
        max(order_purchase_date) as latest_order_date,
        count(*) as total_order_count,
        count_if(order_status = 'delivered') as delivered_order_count,
        sum(
            case
                when order_status = 'delivered'
                    then total_payment_value
                else 0
            end
        ) as lifetime_revenue,
        avg(
            case
                when order_status = 'delivered'
                    then total_payment_value
            end
        ) as average_delivered_order_value,
        avg(average_review_score) as average_review_score,
        count_if(is_late_delivery) as late_delivery_count
    from orders
    group by customer_unique_id

)

select *
from customer_summary

