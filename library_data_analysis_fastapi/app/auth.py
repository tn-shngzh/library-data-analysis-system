import re
import uuid
import random
import base64
import io
import bcrypt
import jwt
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException, Request

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS

captcha_store = {}


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def validate_username(username: str) -> tuple:
    if not username or len(username.strip()) == 0:
        return False, "用户名不能为空"
    if len(username) < 3:
        return False, "用户名长度不能少于3个字符"
    if len(username) > 20:
        return False, "用户名长度不能超过20个字符"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "用户名只能包含字母、数字和下划线"
    return True, ""


def validate_password(password: str) -> tuple:
    if not password or len(password.strip()) == 0:
        return False, "密码不能为空"
    if len(password) < 6:
        return False, "密码长度不能少于6个字符"
    if len(password) > 50:
        return False, "密码长度不能超过50个字符"
    return True, ""


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证信息")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="无效的 token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="无效的 token")


def generate_captcha_code() -> str:
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz23456789'
    return ''.join(random.choices(chars, k=4))


def generate_captcha_image(text: str) -> str:
    width, height = 100, 46
    image = Image.new('RGB', (width, height), (241, 245, 249))
    draw = ImageDraw.Draw(image)

    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)), width=1)

    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)))

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()

    char_width = width // len(text)
    for i, char in enumerate(text):
        x = char_width * i + random.randint(5, 15)
        y = random.randint(5, 15)
        color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
        draw.text((x, y), char, fill=color, font=font)

    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


def create_captcha():
    captcha_key = str(uuid.uuid4())
    captcha_code = generate_captcha_code()
    captcha_image = generate_captcha_image(captcha_code)

    captcha_store[captcha_key] = {
        "code": captcha_code,
        "expire_time": datetime.utcnow() + timedelta(minutes=5)
    }

    now = datetime.utcnow()
    expired_keys = [k for k, v in captcha_store.items() if v["expire_time"] < now]
    for k in expired_keys:
        del captcha_store[k]

    return {"key": captcha_key, "image": captcha_image}


def verify_captcha(captcha_key: str, captcha: str):
    if not captcha_key or not captcha:
        raise HTTPException(status_code=400, detail="请输入验证码")

    captcha_data = captcha_store.get(captcha_key)
    if not captcha_data:
        raise HTTPException(status_code=400, detail="验证码已过期，请刷新")

    if captcha_data["expire_time"] < datetime.utcnow():
        del captcha_store[captcha_key]
        raise HTTPException(status_code=400, detail="验证码已过期，请刷新")

    if captcha_data["code"].lower() != captcha.lower():
        del captcha_store[captcha_key]
        raise HTTPException(status_code=400, detail="验证码错误")

    del captcha_store[captcha_key]
