import json
import os
from datetime import timedelta, datetime, timezone

from flask import Flask

from mongoengine import connect
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, JWTManager

from routes.flights import flights_api
from routes.users import users_api
from routes.utils import create_admin_user

# Initialize Flask app
api = Flask(__name__)

# Register route blueprints
api.register_blueprint(users_api)
api.register_blueprint(flights_api)

# Set JWT key from environment variable
try:
    api.config["JWT_SECRET_KEY"] = os.environ["TAILFIN_DB_KEY"]
except KeyError:
    api.logger.error("Please set 'TAILFIN_DB_KEY' environment variable")
    exit(1)

# Set JWT keys to expire after 1 hour
api.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Initialize JWT manager
jwt = JWTManager(api)

# Connect to MongoDB
connect('tailfin')


@api.after_request
def refresh_expiring_jwts(response):
    """
    Refresh/reissue JWTs that are near expiry following each request containing a JWT

    :param response: Response given by previous request
    :return: Original response with refreshed JWT
    """
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            api.logger.info("Refreshing expiring JWT")
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            if type(data) is dict:
                data["access_token"] = access_token
                response.data = json.dumps(data)
        return response
    except (RuntimeError, KeyError):
        # No valid JWT, return original response
        api.logger.info("No valid JWT, cannot refresh expiry")
        return response





if __name__ == '__main__':
    # Create default admin user if it doesn't exist
    create_admin_user()

    # Start the app
    api.run()
