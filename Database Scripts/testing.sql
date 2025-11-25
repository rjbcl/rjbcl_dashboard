-- Create database only if it doesn't exist (run manually if needed)
-- CREATE DATABASE KYC_testing;

-- Connect to the database before running the rest
-- \c KYC_testing;

-- Show current user and database
SELECT current_user, current_database();

-- List existing tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

-- Create ENUM type only if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'kyc_statuses') THEN
        CREATE TYPE kyc_statuses AS ENUM (
            'Not Initiated',
            'Incomplete',
            'Pending',
            'Verified',
            'Rejected'
        );
    END IF;
END$$;

-- Create kyc_user_info table if not exists
CREATE TABLE IF NOT EXISTS kyc_user_info (
    policy_number VARCHAR,
    DOB DATE,
    Name VARCHAR,
    User_ID VARCHAR,
    User_email VARCHAR,
    Citizenship_number VARCHAR,
    Phone_number VARCHAR,
    Address VARCHAR,
    KYC_status kyc_statuses,
    password VARCHAR
);

-- Create kyc_agent_info table if not exists
CREATE TABLE IF NOT EXISTS kyc_agent_info (
    agent_code VARCHAR UNIQUE PRIMARY KEY,
    first_name VARCHAR,
    last_name VARCHAR,
    DOB DATE,
    phone_number VARCHAR,
    email VARCHAR,
    password VARCHAR
);


-- Insert dummy users only if table is empty
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM kyc_user_info) THEN
        INSERT INTO kyc_user_info (
            policy_number, DOB, Name, User_ID, User_email,
            Citizenship_number, Phone_number, Address,
            KYC_status, password
        ) VALUES
        ('POL123456', '1990-05-15', 'Aarav Sharma', 'USR001', 'aarav@example.com', '1234567890', '9800000001', 'Kathmandu', 'verified', 'pass@123'),
        ('POL234567', '1985-08-22', 'Sita Thapa', 'USR002', 'sita@example.com', '9876543210', '9800000002', 'Pokhara', 'pending verification', 'sita#456'),
        ('POL345678', '1992-12-01', 'Bikash Rai', 'USR003', 'bikash@example.com', '1122334455', '9800000003', 'Lalitpur', 'not verified', 'bikash789');
    END IF;
END$$;

-- Insert dummy agents only if table is empty
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM kyc_agent_info) THEN
        INSERT INTO kyc_agent_info (
            agent_code, DOB, phone_number, name, password
        ) VALUES
        ('AG001', '1988-03-12', '9801000001', 'Ramesh Karki', 'ram@123'),
        ('AG002', '1991-07-25', '9801000002', 'Sunita Lama', 'sunita456'),
        ('AG003', '1985-11-08', '9801000003', 'Dipesh Shrestha', 'dipesh789');
    END IF;
END$$;

-- Show data from both tables
SELECT * FROM kyc_user_info;
SELECT * FROM kyc_agent_info;



--=============POLICY TABLE=================
REATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create kyc_status_table
CREATE TABLE kyc_status_table (
    kyc_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_number kyc_user_info(policy_number),
    User_ID VARCHAR REFERENCES kyc_user_info(User_ID),
    KYC_status kyc_statuses
);

DROP TABLE IF EXISTS kyc_agent_info;
DROP TABLE IF EXISTS kyc_user_info;

-- ******************* CREATE TABLE  kyc_user_info *******************
CREATE TABLE kyc_user_info (
    row_id SERIAL PRIMARY KEY,
    user_ID VARCHAR UNIQUE,  
    dob DATE,
    first_name VARCHAR,
    last_name VARCHAR,
    user_email VARCHAR,
    citizenship_number VARCHAR,
    phone_number VARCHAR,
    address VARCHAR,
    password VARCHAR
);



--- Adding 3 Dummy data into the user info table
INSERT INTO kyc_user_info (
    user_ID, dob, first_name, last_name, user_email,
    citizenship_number, phone_number, address, password
) VALUES
('USR001', '1990-01-01', 'Aarav', 'Shrestha', 'aarav@example.com', '01-90-12345', '9800000001', 'Kathmandu', 'pass123'),
('USR002', '1985-05-15', 'Bina', 'Rai', 'bina@example.com', '05-85-54321', '9800000002', 'Lalitpur', 'pass456'),
('USR003', '1992-09-20', 'Chirag', 'Gurung', 'chirag@example.com', '09-92-67890', '9800000003', 'Bhaktapur', 'pass789');



-- ******************* CREATE TABLE kyc_policy *******************
CREATE TABLE kyc_policy (
    policy_number VARCHAR PRIMARY KEY,
    user_ID VARCHAR REFERENCES kyc_user_info(user_ID),
    created_at DATE DEFAULT CURRENT_DATE
);


INSERT INTO kyc_policy (policy_number, user_ID, created_at) VALUES
('POL001', 'USR001', '2025-01-10'),
('POL002', 'USR002', '2025-02-15'),
('POL003', 'USR003', '2025-03-20'),
('POL004', 'USR001', '2025-03-20');



SELECT * from kyc_agent_info
SELECT * from kyc_user_info
SELECT * from kyc_policy
