-- Example: Insert an allowed email
INSERT INTO allowed_google_accounts (id, email, active, created_at, updated_at)
VALUES (gen_random_uuid(), 'alice@yourcompany.com', true, now(), now());

-- Example: Insert an allowed domain
INSERT INTO allowed_google_accounts (id, domain, active, created_at, updated_at)
VALUES (gen_random_uuid(), 'yourcompany.com', true, now(), now());

-- To deactivate an account (block login):
UPDATE allowed_google_accounts SET active = false WHERE email = 'alice@yourcompany.com';
