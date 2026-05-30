import os
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User
from app.auth.deps import create_access_token, get_current_user

router = APIRouter(tags=["auth"])

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

_oauth_states: set = set()


@router.get("/auth/github/login")
async def github_login(request: Request):
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)
    redirect_uri = str(request.base_url) + "api/auth/github/callback"
    authorize_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&scope=read:user"
    )
    return RedirectResponse(url=authorize_url)


@router.get("/auth/github/callback")
async def github_callback(code: str, state: str, db: Session = Depends(get_db)):
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    _oauth_states.discard(state)

    async with AsyncClient() as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        github_user = user_res.json()

    github_id = github_user["id"]
    username = github_user["login"]
    email = github_user.get("email") or ""
    avatar_url = github_user.get("avatar_url") or ""

    user = db.query(User).filter(User.github_id == github_id).first()
    if user:
        user.username = username
        user.email = email
        user.avatar_url = avatar_url
        user.last_login = datetime.now(timezone.utc)
    else:
        user = User(
            github_id=github_id,
            username=username,
            email=email,
            avatar_url=avatar_url,
        )
        db.add(user)
    db.commit()
    db.refresh(user)

    jwt_token = create_access_token({"sub": str(user.id), "username": user.username})
    return RedirectResponse(url=f"{FRONTEND_URL}/?token={jwt_token}")


@router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
