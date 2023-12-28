import uvicorn

from app.config import get_settings

if __name__ == '__main__':
    settings = get_settings()
    # Start the app
    uvicorn.run("app.api:app", host="0.0.0.0", port=settings.tailfin_port, reload=True)
