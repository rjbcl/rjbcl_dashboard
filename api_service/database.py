import os
import pyodbc
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

print("Loading env from:", ENV_PATH)
load_dotenv(dotenv_path=ENV_PATH)

print("DB_SERVER =", os.getenv("DB_SERVER"))
print("DB_NAME =", os.getenv("DB_NAME"))

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
    """
    DB_PORT = os.getenv("DB_PORT", "1433")

    for v, n in [
        (DB_SERVER, "DB_SERVER"),
        (DB_NAME, "DB_NAME"),
        (DB_USER, "DB_USER"),
        (DB_PASSWORD, "DB_PASSWORD"),
    ]:
        if not v:
            raise RuntimeError(f"Missing required env variable: {n}")

    try:
        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str, timeout=5)

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
