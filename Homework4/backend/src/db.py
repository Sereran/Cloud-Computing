import pyodbc
import os
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
from contextlib import contextmanager
# from google.cloud import secretmanager

logger = logging.getLogger(__name__)

load_dotenv()

# def get_secret(secret_id: str, project_id: str = "937961278554") -> str:
#     # Fetches a secret from Secret Manager
#     try:
#         client = secretmanager.SecretManagerServiceClient()
#         name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
#         response = client.access_secret_version(request={"name": name})
#         return response.payload.data.decode("UTF-8").strip()
#     except Exception as e:
#         logger.error(f"Failed to fetch secret {secret_id}: {e}")
#         # Fallback to local .env
#         return os.getenv(secret_id, "")
# 
# 
# # Extract the user first so we can use it for logic
# db_user = os.getenv("DB_USER", "root")

# Determine which secret to fetch based on the user
# if db_user == "mariailade":
#     secret_name = "DB_PASSWORD_MARIA"
# elif db_user == "petrubraha":
#     secret_name = "DB_PASSWORD_PETRU"
# elif db_user == "public":
#     secret_name = "DB_PASSWORD_PUBLIC"
# else:
#     # Default fallback using mariailade's password
#     secret_name = "DB_PASSWORD"

# Defines the config using those dynamic variables
DB_CONFIG = {
    "server": os.getenv("SQL_SERVER"),
    "database": os.getenv("SQL_DATABASE"),
    "username": os.getenv("SQL_USER"),
    "password": os.getenv("SQL_PASSWORD"),
    "driver": os.getenv("SQL_DRIVER"),
}

def get_conn_str() -> str:
    return (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        "Authentication=ActiveDirectoryPassword"
    )


def init_pool():
    try:
        conn_str = get_conn_str()
        conn = pyodbc.connect(conn_str)
        conn.close()
        logger.info("Database connectivity verified.")
    except Exception as err:
        logger.error(f"Error connecting to database: {err}")


@contextmanager
def db_session():
    """Rethrow-safe context manager for database connection management."""
    conn = None
    try:
        conn_str = get_conn_str()
        conn = pyodbc.connect(conn_str)
        yield conn
    except Exception as err:
        logger.error(f"Database error during session: {err}")
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        if conn:
            conn.close()
