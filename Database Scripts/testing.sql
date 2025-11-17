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
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'kyc_status_enum') THEN
        CREATE TYPE kyc_status_enum AS ENUM (
            'verified',
            'not verified',
            'pending verification',
            'not approved'
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
    KYC_status kyc_status_enum,
    password VARCHAR
);

-- Create kyc_agent_info table if not exists
CREATE TABLE IF NOT EXISTS kyc_agent_info (
    agent_code VARCHAR,
    DOB DATE,
    phone_number VARCHAR,
    name VARCHAR,
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