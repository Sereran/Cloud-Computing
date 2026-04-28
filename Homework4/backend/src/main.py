import logging
import json
# import google.cloud.logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.router import router
from src import db

# conectam aplicatia la google cloud logging
# client = google.cloud.logging.Client()
# client.setup_logging()


class CloudLoggingFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        return json.dumps(log_entry)


# configuram noul logger
handler = logging.StreamHandler()
handler.setFormatter(CloudLoggingFormatter())

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("aplicatia a pornit si se conecteaza la baza de date")
    db.init_pool()
    yield
    logger.info("aplicatia se inchide")


app = FastAPI(title="Cloud Homework", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://kind-pond-05f3ad403.7.azurestaticapps.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
