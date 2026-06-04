import secrets

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.core.roles import Role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginIn, RegisterIn, TokenOut

router = APIRouter()
settings = get_settings()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.post("/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=Role.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email, "role": user.role.value}


@router.post("/login", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # Swagger "username" field = your email
    user = db.scalar(select(User).where(User.email == form_data.username))
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user.id), user.role.value)
    return TokenOut(access_token=token)


@router.get("/oauth/google/start")
async def oauth_google_start(request: Request):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured")
    if not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=400, detail="GOOGLE_REDIRECT_URI is not configured")

    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    return await oauth.google.authorize_redirect(
        request,
        settings.GOOGLE_REDIRECT_URI,
        state=state,
    )


@router.get("/oauth/google/callback")
async def oauth_google_callback(request: Request, db: Session = Depends(get_db)):
    state = request.query_params.get("state")
    saved_state = request.session.get("oauth_state")
    if not state or state != saved_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        user_info = await oauth.google.userinfo(token=token)

    email = user_info.get("email")
    sub = user_info.get("sub")
    if not email or not sub:
        raise HTTPException(status_code=400, detail="Invalid Google userinfo")

    user = db.scalar(select(User).where(User.email == email))
    if not user:
        role = Role.SUPERADMIN if settings.SUPERADMIN_EMAIL == email else Role.USER
        user = User(
            email=email,
            oauth_provider="google",
            oauth_sub=sub,
            role=role,
            hashed_password=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.oauth_sub:
        user.oauth_provider = "google"
        user.oauth_sub = sub
        db.commit()

    jwt_token = create_access_token(str(user.id), user.role.value)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}")