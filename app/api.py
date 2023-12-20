import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from mongoengine import connect

from app.config import get_settings
from database.utils import create_admin_user
from routes import users, flights

logger = logging.getLogger("api")

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.DEBUG)


async def connect_to_db():
    # Connect to MongoDB
    settings = get_settings()
    try:
        connected = connect(settings.db_name, host=settings.db_uri, username=settings.db_user,
                            password=settings.db_pwd, authentication_source=settings.db_name)
        if connected:
            logging.info("Connected to database %s", settings.db_name)
            # Create default admin user if it doesn't exist
            create_admin_user()
    except ConnectionError:
        logger.error("Failed to connect to MongoDB")
        raise ConnectionError


# Initialize FastAPI
app = FastAPI()
app.include_router(users.router)
app.include_router(flights.router)


@app.on_event("startup")
async def startup():
    await connect_to_db()
