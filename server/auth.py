from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .database import users_collection
from .models import TokenResponse, TokenData, TokenIn, User, UserAuth, UserIn, UserOut

router = APIRouter()

# openssl rand -hex 32
SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(username: str):
    user = await users_collection.find_one({"username": username})
    if user:
        return UserAuth(**user)


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_user_based_on_username(username: str):
    user = await get_user(username)
    if not user:
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user_based_on_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/api/token", response_model=TokenResponse)
async def login_for_access_token(form_data: TokenIn):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


async def create_user(user_in: UserIn):
    user = await get_user(user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    hashed_password = get_password_hash(user_in.password)
    new_user = {
        "username": user_in.username,
        "hashed_password": hashed_password,
        "email": user_in.email,
        "full_name": user_in.full_name,
    }
    result = await users_collection.insert_one(new_user)
    return {
        "id": str(result.inserted_id),
        "username": user_in.username,
        "email": str(user_in.email),
        "full_name": str(user_in.full_name),
    }


@router.post("/api/register", response_model=UserOut)
async def register(user_in: UserIn):
    return await create_user(user_in)


@router.get("/api/check-username")
async def register(username: str = Query(None)):
    user = await users_collection.find_one({"username": username})
    if user:
        return {"is_chosen": True}
    return {"is_chosen": False}
