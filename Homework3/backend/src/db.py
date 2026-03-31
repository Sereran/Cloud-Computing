from dotenv import load_dotenv
from fastapi import HTTPException
from contextlib import contextmanager
import mysql.connector
import os
import logging
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

load_dotenv()


def get_secret(secret_id: str, project_id: str = "937961278554") -> str:
    # Fetches a secret from Secret Manager
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        logger.error(f"Failed to fetch secret {secret_id}: {e}")
        # Fallback to local .env
        return os.getenv(secret_id, "")


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": get_secret("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "cloud_homework"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

db_pool = None


def init_pool():
    global db_pool
    try:
        db_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="games_pool", pool_size=10, **DB_CONFIG
        )
        logger.info("Database connection pool initialized successfully.")
    except mysql.connector.Error as err:
        logger.error(f"Error creating connection pool: {err}")
        db_pool = None


@contextmanager
def db_session():
    """Rethrow-safe context manager for database connection management."""
    global db_pool
    if not db_pool:
        init_pool()
        if not db_pool:
            raise HTTPException(status_code=500, detail="Database connectivity error.")

    conn = None
    try:
        conn = db_pool.get_connection()
        yield conn
    except mysql.connector.Error as err:
        logger.error(f"Database error during session: {err}")
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        if conn:
            conn.close()


def close_pool():
    global db_pool
    if db_pool:
        logger.info("Closing database connection pool.")
        db_pool = None
