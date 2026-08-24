DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'fivetran_user'
    ) THEN
        CREATE ROLE fivetran_user LOGIN;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE neondb TO fivetran_user;

GRANT USAGE ON SCHEMA olist TO fivetran_user;

GRANT SELECT
ON ALL TABLES IN SCHEMA olist
TO fivetran_user;

ALTER DEFAULT PRIVILEGES
IN SCHEMA olist
GRANT SELECT ON TABLES TO fivetran_user;


