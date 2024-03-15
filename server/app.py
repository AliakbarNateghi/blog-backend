from typing import List, Optional

from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from server import auth, blog

from .models import Post

app = FastAPI()


app.include_router(blog.router)
app.include_router(auth.router)


@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017")
    app.mongodb = app.mongodb_client["aliakbar"]


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
