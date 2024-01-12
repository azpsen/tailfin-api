import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.utils import create_admin_user
from routes import users, flights, auth, aircraft, img

logger = logging.getLogger("api")

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_admin_user()
    yield


# Initialize FastAPI
app = FastAPI(lifespan=lifespan)

# Allow CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

# Add subroutes
app.include_router(users.router, tags=["Users"], prefix="/users")
app.include_router(flights.router, tags=["Flights"], prefix="/flights")
app.include_router(aircraft.router, tags=["Aircraft"], prefix="/aircraft")
app.include_router(img.router, tags=["Images"], prefix="/img")
app.include_router(auth.router, tags=["Auth"], prefix="/auth")
