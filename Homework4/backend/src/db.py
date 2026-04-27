import pyodbc
import os
import logging
from dotenv import load_dotenv
from fastapi import HTTPException
from contextlib import contextmanager

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)

load_dotenv()

KEY_VAULT_URL = os.getenv("KEY_VAULT_URL")

# Initialize the Azure Key Vault Client
try:
    # It uses your local Azure CLI login and automatically switches to Managed Identity in the cloud
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    logger.info("Successfully connected to Azure Key Vault.")
except Exception as e:
    logger.error(f"Failed to connect to Key Vault: {e}")
    secret_client = None


def get_secret(secret_name: str) -> str:
    """Fetches a secret from Azure Key Vault, falls back to .env if needed."""
    if secret_client:
        try:
            # Reaches out to Azure to grab the secret (ex:'SQL-PASSWORD')
            retrieved_secret = secret_client.get_secret(secret_name)
            return retrieved_secret.value
        except Exception as e:
            logger.warning(f"Could not fetch {secret_name} from vault. Error: {e}")

    # Fallback for local development if the Vault connection fails
    # We replace hyphens with underscores because .env files use underscores
    env_fallback = secret_name.replace("-", "_")
    return os.getenv(env_fallback, "")


# Defines the config using those dynamic variables
DB_CONFIG = {
    "server": os.getenv("SQL_SERVER"),
    "database": os.getenv("SQL_DATABASE"),
    "username": os.getenv("SQL_USER"),
    "driver": os.getenv("SQL_DRIVER", "{ODBC Driver 17 for SQL Server}"),
    "password": get_secret("SQL-PASSWORD"),
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
