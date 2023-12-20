import json
import os
from datetime import timedelta, datetime, timezone

import uvicorn

from fastapi import FastAPI

from mongoengine import connect
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, JWTManager

from database.utils import create_admin_user

# Initialize Flask app
app = FastAPI()

# Set JWT key from environment variable
# try:
#     app.config["JWT_SECRET_KEY"] = os.environ["TAILFIN_JWT_KEY"]
# except KeyError:
#     app.logger.error("Please set 'TAILFIN_JWT_KEY' environment variable")
#     exit(1)

# Set JWT keys to expire after 1 hour
# app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Initialize JWT manager
# jwt = JWTManager(app)

# Connect to MongoDB
connect('tailfin')

# @app.after_request
# def refresh_expiring_jwts(response):
#     """
#     Refresh/reissue JWTs that are near expiry following each request containing a JWT
#
#     :param response: Response given by previous request
#     :return: Original response with refreshed JWT
#     """
#     try:
#         exp_timestamp = get_jwt()["exp"]
#         now = datetime.now(timezone.utc)
#         target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
#         if target_timestamp > exp_timestamp:
#             app.logger.info("Refreshing expiring JWT")
#             access_token = create_access_token(identity=get_jwt_identity())
#             data = response.get_json()
#             if type(data) is dict:
#                 data["access_token"] = access_token
#                 response.data = json.dumps(data)
#         return response
#     except (RuntimeError, KeyError):
#         # No valid JWT, return original response
#         app.logger.info("No valid JWT, cannot refresh expiry")
#         return response


if __name__ == '__main__':
    # Create default admin user if it doesn't exist
    create_admin_user()

    # Start the app
    uvicorn.run("fastapi_code:app", reload=True)
