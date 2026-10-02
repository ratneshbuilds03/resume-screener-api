from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

client = None
db = None


async def connect_mongodb():
    global client, db
    if not settings.MONGODB_URL:
        client = None
        db = None
        return
    client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
    db = client[settings.MONGODB_DB]


async def close_mongodb():
    global client, db
    if client:
        client.close()
    client = None
    db = None


def get_mongodb():
    return db