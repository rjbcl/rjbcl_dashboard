-- ============================================================
-- Bootstrap unmanaged external tables for KYC system
-- Safe to run multiple times (idempotent)
-- ============================================================

-- ------------------------------------------------------------
-- POLICY MASTER (External / Core mirror)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kyc_policy (
    policy_number VARCHAR(50) PRIMARY KEY,
    user_id        VARCHAR(50) NOT NULL,
    created_at     DATE NOT NULL
);

-- ------------------------------------------------------------
-- AGENT MASTER (External)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kyc_agent_info (
    agent_code   VARCHAR(50) PRIMARY KEY,
    first_name   VARCHAR(50) NOT NULL,
    last_name    VARCHAR(50) NOT NULL,
    dob          DATE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    email        VARCHAR(100),
    password     VARCHAR(50)
);

-- ------------------------------------------------------------
-- OPTIONAL: index for faster lookup
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_kyc_policy_user
ON kyc_policy(user_id);
