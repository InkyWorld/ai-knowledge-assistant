CREATE ROLE assistant_ro LOGIN PASSWORD 'change-me';
GRANT CONNECT ON DATABASE assistant TO assistant_ro;
GRANT USAGE ON SCHEMA public TO assistant_ro;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM assistant_ro;
GRANT SELECT ON documents TO assistant_ro;
ALTER ROLE assistant_ro SET default_transaction_read_only = on;
ALTER ROLE assistant_ro SET statement_timeout = '5s';