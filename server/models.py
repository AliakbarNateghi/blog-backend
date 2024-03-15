from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    # disabled: Optional[bool] = None


class UserOut(User):
    id: str


class UserAuth(User):
    hashed_password: str


class UserIn(User):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class TokenIn(BaseModel):
    username: str
    password: str


class PostBase(BaseModel):
    title: str
    content: str
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, title="The time the blog post was created"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now, title="The time the blog post was last updated"
    )


class Post(PostBase):
    id: str
    author: User = Field(..., title="The author of the blog post")


class PostIn(BaseModel):
    title: str
    content: str


class PostOut(PostBase):
    id: str
    author: str
