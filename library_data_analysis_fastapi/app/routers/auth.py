from fastapi import APIRouter, Form, HTTPException, Depends, Request
from datetime import datetime
import jwt

from app.database import get_db
from app.auth import (
    hash_password, verify_password, validate_username, validate_password,
    create_access_token, create_captcha, verify_captcha, revoke_token, get_current_user
)
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api", tags=["认证"])


@router.get("/captcha")
async def get_captcha():
    return create_captcha()


@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...), conn=Depends(get_db)):
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    is_valid, error_msg = validate_password(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="该用户名已被注册，请选择其他用户名")

            cur.execute("SELECT MAX(id) FROM users")
            max_id = cur.fetchone()[0]
            new_id = (max_id + 1) if max_id else 1

            password_hash = hash_password(password)

            cur.execute(
                "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (%s, %s, %s, %s, %s)",
                (new_id, username, password_hash, 'user', datetime.utcnow())
            )
            conn.commit()

            return {
                "message": "注册成功",
                "user_id": new_id,
                "username": username
            }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败，请稍后重试: {str(e)}")


@router.post("/login")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    captcha: str = Form(...),
    captcha_key: str = Form(...),
    conn=Depends(get_db)
):
    verify_captcha(captcha_key, captcha)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (username,)
        )
        user = cur.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        user_id, db_username, password_hash, role = user

        if not verify_password(password, password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        system = "library" if role != "admin" else "analysis"

        access_token = create_access_token(
            data={"sub": db_username, "role": role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": db_username,
            "role": role,
            "system": system
        }


@router.get("/me")
async def get_current_user_info(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的token")
        return {"username": username, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="无效的token")


@router.post("/logout")
async def logout(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        revoke_token(token)
    return {"message": "注销成功"}
