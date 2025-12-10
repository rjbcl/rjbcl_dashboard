import os
import pyodbc
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------
# MSSQL ENV
# -------------------------------------------------
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# -------------------------------------------------
# POSTGRES ENV
# -------------------------------------------------
PG_NAME = os.getenv("PGNAME")
PG_USER = os.getenv("PGUSER")
PG_PASSWORD = os.getenv("PGPASSWORD")
PG_HOST = os.getenv("PGHOST")
PG_PORT = os.getenv("PGPORT")
PG_SSL = os.getenv("PGSSL", "require")


# -------------------------------------------------
# MSSQL CONNECTION
# -------------------------------------------------
def get_mssql_conn():
    """
    Returns MSSQL Database Connection  
    Uses ODBC Driver 17 or 18 depending on system.
    """
    try:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD};"
            "TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str)
        return conn

    except Exception as e:
        raise Exception(f"Failed to connect MSSQL: {e}")


# -------------------------------------------------
# POSTGRES CONNECTION
# -------------------------------------------------
def get_postgres_connection():
    """
    Returns Postgres Connection (Neon DB)
    """
    try:
        conn = psycopg2.connect(
            dbname=PG_NAME,
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
            sslmode=PG_SSL,
        )
        return conn

    except Exception as e:
        raise Exception(f"Failed to connect Postgres: {e}")
