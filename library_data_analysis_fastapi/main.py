from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg2
import os
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import base64
import io
import uuid
import random
import string
from PIL import Image, ImageDraw, ImageFont

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="图书馆数据分析系统")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 验证码存储（内存缓存，生产环境应使用 Redis）
captcha_store = {}


def generate_captcha_image(text: str) -> str:
    """生成验证码图片并返回 base64 编码"""
    width, height = 100, 46
    image = Image.new('RGB', (width, height), (241, 245, 249))
    draw = ImageDraw.Draw(image)

    # 绘制干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)), width=1)

    # 绘制干扰点
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(150, 200), random.randint(150, 200), random.randint(150, 200)))

    # 绘制验证码文字
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

    # 转换为 base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


def generate_captcha_code() -> str:
    """生成验证码文本"""
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz23456789'
    return ''.join(random.choices(chars, k=4))


@app.get("/api/captcha")
async def get_captcha():
    """获取验证码"""
    captcha_key = str(uuid.uuid4())
    captcha_code = generate_captcha_code()
    captcha_image = generate_captcha_image(captcha_code)

    # 存储验证码（5分钟过期）
    captcha_store[captcha_key] = {
        "code": captcha_code,
        "expire_time": datetime.utcnow() + timedelta(minutes=5)
    }

    # 清理过期验证码
    now = datetime.utcnow()
    expired_keys = [k for k, v in captcha_store.items() if v["expire_time"] < now]
    for k in expired_keys:
        del captcha_store[k]

    return {
        "key": captcha_key,
        "image": captcha_image
    }

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 数据库配置
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "library_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "GXYL2405")
}


def get_db_connection():
    """获取数据库连接"""
    conn_str = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} password={DB_CONFIG['password']}"
    return psycopg2.connect(conn_str)


def create_access_token(data: dict):
    """创建 JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@app.get("/")
async def root():
    return {"message": "图书馆数据分析系统 API"}


@app.post("/api/login")
async def login(username: str = Form(...), password: str = Form(...), captcha: str = Form(...), captcha_key: str = Form(...)):
    """登录接口"""
    # 验证验证码
    if not captcha_key or not captcha:
        raise HTTPException(status_code=400, detail="请输入验证码")
    
    captcha_data = captcha_store.get(captcha_key)
    if not captcha_data:
        raise HTTPException(status_code=400, detail="验证码已过期，请刷新")
    
    if captcha_data["expire_time"] < datetime.utcnow():
        del captcha_store[captcha_key]
        raise HTTPException(status_code=400, detail="验证码已过期，请刷新")
    
    if captcha_data["code"] != captcha.upper():
        del captcha_store[captcha_key]
        raise HTTPException(status_code=400, detail="验证码错误")
    
    # 验证成功后删除验证码（一次性使用）
    del captcha_store[captcha_key]
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 查询用户
            cur.execute(
                "SELECT id, username, password_hash, role FROM users WHERE username = %s",
                (username,)
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=401, detail="用户名或密码错误")

            user_id, db_username, password_hash, role = user

            # 验证密码（开发环境简化版）
            # 检查是否是 bcrypt 哈希
            if password_hash.startswith('$2'):
                if not pwd_context.verify(password, password_hash):
                    raise HTTPException(status_code=401, detail="用户名或密码错误")
            else:
                # 明文密码对比（仅开发测试用）
                if password != password_hash:
                    raise HTTPException(status_code=401, detail="用户名或密码错误")

            # 检查权限（只有 admin 可以登录系统）
            if role != "admin":
                raise HTTPException(status_code=403, detail="权限不足，仅管理员可登录")

            # 创建 token
            access_token = create_access_token(
                data={"sub": db_username, "role": role}
            )

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "username": db_username,
                "role": role
            }
    finally:
        conn.close()


@app.get("/api/me")
async def get_current_user(token: str):
    """获取当前用户信息"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="无效的token")
        return {"username": username, "role": role}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="无效的token")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
