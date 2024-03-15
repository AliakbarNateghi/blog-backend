from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from .auth import get_current_user
from .database import posts_collection
from .models import Post, PostIn, User

router = APIRouter()


@router.get("/", dependencies=[Depends(get_current_user)])
def read_main():
    return {"message": "Welcome to your post!"}


@router.get("/posts", response_model=List[Post])
async def get_posts():
    posts = await posts_collection.find().to_list(1000)
    for post in posts:
        post["id"] = str(post["_id"])
    return posts


@router.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: str):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    post["id"] = str(post["_id"])
    return post


@router.post("/posts", response_model=Post)
async def create_post(post: PostIn, user: str = Depends(get_current_user)):
    new_post = {
        "title": post.title,
        "content": post.content,
        "author": {
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    result = await posts_collection.insert_one(new_post)
    new_post["id"] = str(result.inserted_id)
    return new_post


@router.put(
    "/posts/{post_id}", response_model=Post, dependencies=[Depends(get_current_user)]
)
async def update_post(post_id: str, post: PostIn):
    updated_post = await posts_collection.find_one_and_update(
        {"_id": ObjectId(post_id)},
        {"$set": {**post.dict(), "updated_at": datetime.now()}},
        return_document=ReturnDocument.AFTER,
    )
    if updated_post:
        updated_post["id"] = str(updated_post["_id"])
        return updated_post
    raise HTTPException(status_code=404, detail="Post not found")


@router.delete("/posts/{post_id}", dependencies=[Depends(get_current_user)])
async def delete_post(post_id: str):
    deleted_post = await posts_collection.delete_one({"_id": ObjectId(post_id)})
    if deleted_post:
        return {"message": "Post has been deleted successfully."}
    raise HTTPException(status_code=404, detail="Post not found")
