with orders as (

    select *
    from {{ ref('stg_orders') }}

),

customers as (

    select *
    from {{ ref('stg_customers') }}

),

order_items as (

    select *
    from {{ ref('int_order_items_aggregated') }}

),

payments as (

    select *
    from {{ ref('int_order_payments_aggregated') }}

),

reviews as (

    select *
    from {{ ref('int_order_reviews_aggregated') }}

),

enriched as (

    select
        orders.order_id,
        orders.customer_id,
        customers.customer_unique_id,
        customers.customer_city,
        customers.customer_state,

        orders.order_status,
        orders.order_purchase_timestamp,
        cast(orders.order_purchase_timestamp as date)
            as order_purchase_date,
        orders.order_approved_at,
        orders.order_delivered_carrier_date,
        orders.order_delivered_customer_date,
        orders.order_estimated_delivery_date,

        datediff(
            'day',
            orders.order_purchase_timestamp,
            orders.order_delivered_customer_date
        ) as delivery_days,

        datediff(
            'day',
            orders.order_estimated_delivery_date,
            orders.order_delivered_customer_date
        ) as delivery_delay_days,

        case
            when orders.order_delivered_customer_date is null then null
            when orders.order_delivered_customer_date
                > orders.order_estimated_delivery_date then true
            else false
        end as is_late_delivery,

        coalesce(order_items.item_count, 0) as item_count,
        coalesce(order_items.distinct_product_count, 0)
            as distinct_product_count,
        coalesce(order_items.distinct_seller_count, 0)
            as distinct_seller_count,
        coalesce(order_items.total_product_value, 0)
            as total_product_value,
        coalesce(order_items.total_freight_value, 0)
            as total_freight_value,
        coalesce(order_items.total_order_item_value, 0)
            as total_order_item_value,

        coalesce(payments.payment_record_count, 0)
            as payment_record_count,
        coalesce(payments.payment_type_count, 0)
            as payment_type_count,
        coalesce(payments.max_payment_installments, 0)
            as max_payment_installments,
        coalesce(payments.total_payment_value, 0)
            as total_payment_value,

        reviews.review_count,
        reviews.average_review_score,
        reviews.minimum_review_score,
        reviews.maximum_review_score,
        reviews.latest_review_date,
        reviews.latest_review_answer_timestamp

    from orders
    left join customers
        on orders.customer_id = customers.customer_id
    left join order_items
        on orders.order_id = order_items.order_id
    left join payments
        on orders.order_id = payments.order_id
    left join reviews
        on orders.order_id = reviews.order_id

)

select *
from enriched

