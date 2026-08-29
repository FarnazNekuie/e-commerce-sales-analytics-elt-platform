with reviews as (

    select *
    from {{ ref('stg_order_reviews') }}

),

aggregated as (

    select
        order_id,
        count(*) as review_count,
        avg(review_score) as average_review_score,
        min(review_score) as minimum_review_score,
        max(review_score) as maximum_review_score,
        max(review_creation_date) as latest_review_date,
        max(review_answer_timestamp) as latest_review_answer_timestamp
    from reviews
    group by order_id

)

select *
from aggregated

