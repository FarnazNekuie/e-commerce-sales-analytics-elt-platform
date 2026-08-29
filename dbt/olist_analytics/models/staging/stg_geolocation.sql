with source as (

    select *
    from {{ source('olist_raw', 'geolocation') }}

),

renamed as (

    select
        geolocation_zip_code_prefix,
        geolocation_lat as geolocation_latitude,
        geolocation_lng as geolocation_longitude,
        trim(geolocation_city) as geolocation_city,
        upper(trim(geolocation_state)) as geolocation_state
    from source

)

select *
from renamed

