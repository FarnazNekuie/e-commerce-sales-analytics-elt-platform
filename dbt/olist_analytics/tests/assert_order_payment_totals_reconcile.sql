-- Fails when an order-level payment total in fct_orders does not reconcile
-- with its underlying staging payment records.

with expected as (

    select
        order_id,
        sum(payment_value) as expected_total_payment_value
    from {{ ref('stg_order_payments') }}
    group by order_id

),

actual as (

    select
        order_id,
        total_payment_value as actual_total_payment_value
    from {{ ref('fct_orders') }}

)

select
    expected.order_id,
    actual.actual_total_payment_value,
    expected.expected_total_payment_value
from expected
left join actual
    on expected.order_id = actual.order_id
where
    actual.order_id is null
    or abs(
        coalesce(actual.actual_total_payment_value, 0)
        - expected.expected_total_payment_value
    ) > 0.01

