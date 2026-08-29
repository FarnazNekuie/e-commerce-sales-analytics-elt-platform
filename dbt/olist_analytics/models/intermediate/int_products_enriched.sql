with products as (

    select *
    from {{ ref('stg_products') }}

),

category_translations as (

    select *
    from {{ ref('stg_product_category_translation') }}

),

enriched as (

    select
        products.product_id,
        products.product_category_name,
        coalesce(
            category_translations.product_category_name_english,
            'unknown'
        ) as product_category_name_english,
        products.product_name_length,
        products.product_description_length,
        products.product_photos_qty,
        products.product_weight_g,
        products.product_length_cm,
        products.product_height_cm,
        products.product_width_cm
    from products
    left join category_translations
        on products.product_category_name =
           category_translations.product_category_name

)

select *
from enriched

