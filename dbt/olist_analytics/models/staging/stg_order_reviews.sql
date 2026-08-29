with source as (

    select *
    from {{ source('olist_raw', 'order_reviews') }}

),

renamed as (

    select
        review_id || '-' || order_id as order_review_key,
        review_id,
        order_id,
        review_score,
        trim(review_comment_title) as review_comment_title,
        trim(review_comment_message) as review_comment_message,
        review_creation_date,
        review_answer_timestamp
    from source

)

select *
from renamed

