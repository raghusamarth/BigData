from fastapi import APIRouter, HTTPException
from database import users_collection
from hashlib import sha256
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _hash(pw: str) -> str:
    return sha256(pw.encode()).hexdigest()  # preserved scheme (demo only)


@router.post("/register")
def register(username: str, password: str):
    username = (username or "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not password:
        raise HTTPException(status_code=400, detail="Password cannot be empty")
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=409, detail="Username already exists")
    users_collection.insert_one({
        "username": username,
        "password": _hash(password),
        "balance": 10000.00,
        "holdings": [],
    })
    return {"message": "User created successfully"}


@router.post("/login")
def login(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user or _hash(password) != user["password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "user_id": str(user["_id"])}


@router.get("/portfolio/{user_id}")
def portfolio(user_id: str):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")
    user = users_collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    user.pop("password", None)
    return user
