from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.mydatabase


users_collection = db["users"]
posts_collection = db["posts"]
