import os
from app.main import app

if __name__ == "__main__":
    import uvicorn
    env = os.getenv("FLASK_ENV","development")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=env == "development"
    )