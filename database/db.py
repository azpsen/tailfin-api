import logging

import motor.motor_asyncio

from app.config import get_settings, Settings

logger = logging.getLogger("api")

settings: Settings = get_settings()

# Connect to MongoDB instance
mongo_str = f"mongodb://{settings.db_user}:{settings.db_pwd}@{settings.db_uri}:{settings.db_port}?authSource={settings.db_name}"

client = motor.motor_asyncio.AsyncIOMotorClient(mongo_str)
db_client = client[settings.db_name]

# Test db connection
try:
    client.admin.command("ping")
    logger.info("Pinged MongoDB deployment. Successfully connected to MongoDB.")
except Exception as e:
    logger.error(e)

# Get db collections
user_collection = db_client["user"]
flight_collection = db_client["flight"]
aircraft_collection = db_client["aircraft"]
token_collection = db_client["token_blacklist"]
