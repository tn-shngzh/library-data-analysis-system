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
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
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
    
    if captcha_data["code"].lower() != captcha.lower():
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


education_levels = {
    '1a': '研究生', '1b': '本科', '1c': '大专', '1d': '高中',
    '1e': '初中', '1f': '小学', '1g': '临时', '1h': '学龄前'
}


@app.get("/api/overview/stats")
async def get_overview_stats():
    """获取总览统计数据"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM mv_overview_stats")
            row = cur.fetchone()
            
            return {
                "total_readers": row[0],
                "total_borrows": row[1],
                "active_readers": row[2],
                "total_books": row[3],
                "cko_count": row[4],
                "cki_count": row[5],
                "reh_count": row[6],
                "rei_count": row[7],
                "today_visits": row[8] if row[8] else 0,
                "total_categories": row[9]
            }
    finally:
        conn.close()


@app.get("/api/overview/categories")
async def get_category_stats():
    """获取分类统计（按教育水平模拟分类）"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT el.name, COUNT(b.id) as count
                FROM borrowers b
                JOIN education_levels el ON b.degree = el.code
                GROUP BY el.name
                ORDER BY count DESC
            """)
            rows = cur.fetchall()
            total = sum(r[1] for r in rows)
            return [
                {"name": r[0], "count": r[1], "percent": round(r[1] / total * 100, 1)}
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/overview/recent-books")
async def get_recent_books():
    """获取最近借阅记录"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.action_date, c.action, b.degree
                FROM circulations c
                JOIN borrowers b ON c.borrower_id = b.id
                WHERE c.action = 'CKO'
                ORDER BY c.action_date DESC, c.action_time DESC
                LIMIT 5
            """)
            rows = cur.fetchall()
            return [
                {
                    "date": str(r[0]),
                    "action": r[1],
                    "degree": r[2]
                }
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/readers/stats")
async def get_reader_stats():
    """获取读者统计数据"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM borrowers")
            total_readers = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN 20190401 AND 20190430")
            month_active = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT borrower_id) FROM circulations WHERE action_date BETWEEN 20190401 AND 20190430 AND action = 'CKO'")
            month_borrowers = cur.fetchone()[0]

            cur.execute("SELECT AVG(borrow_count) FROM mv_reader_stats")
            avg_borrows = cur.fetchone()[0]

            return {
                "total_readers": total_readers,
                "month_active": month_active,
                "month_new": month_borrowers,
                "avg_borrows": round(avg_borrows, 1) if avg_borrows else 0
            }
    finally:
        conn.close()


@app.get("/api/readers/types")
async def get_reader_types():
    """获取读者类型分布"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT el.name, COUNT(b.id) as count
                FROM borrowers b
                JOIN education_levels el ON b.degree = el.code
                GROUP BY el.name
                ORDER BY count DESC
            """)
            rows = cur.fetchall()
            total = sum(r[1] for r in rows)
            return [
                {"name": r[0], "count": r[1], "percent": round(r[1] / total * 100, 1)}
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/readers/monthly-trend")
async def get_monthly_trend():
    """获取月度活跃趋势"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT month, active_count FROM mv_monthly_active ORDER BY month")
            rows = cur.fetchall()
            month_names = {
                201901: '1月', 201902: '2月', 201903: '3月',
                201904: '4月', 201905: '5月', 201906: '6月',
                201907: '7月', 201908: '8月', 201909: '9月',
                201910: '10月', 201911: '11月', 201912: '12月'
            }
            return [
                {"month": month_names.get(r[0], str(r[0])), "count": r[1]}
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/readers/top")
async def get_top_readers():
    """获取活跃读者排行"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rs.borrower_id, rs.borrow_count, b.degree
                FROM mv_reader_stats rs
                JOIN borrowers b ON rs.borrower_id = b.id
                ORDER BY rs.borrow_count DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            return [
                {
                    "rank": i + 1,
                    "id": r[0],
                    "borrowed": r[1],
                    "type": education_levels.get(r[2], r[2])
                }
                for i, r in enumerate(rows)
            ]
    finally:
        conn.close()


@app.get("/api/books/stats")
async def get_book_stats():
    """获取图书统计数据"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM book_categories")
            total_items = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT bib_id) FROM circulations WHERE action_date BETWEEN 20190401 AND 20190430")
            month_items = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT c.bib_id) FROM circulations c JOIN book_categories bc ON c.bib_id = bc.bib_id WHERE c.action = 'CKO'")
            borrowed_items = cur.fetchone()[0]

            borrow_rate = round(borrowed_items / total_items * 100, 1) if total_items else 0

            zero_borrow = total_items - borrowed_items if total_items > borrowed_items else 0

            return {
                "total_items": total_items,
                "month_items": month_items,
                "borrow_rate": borrow_rate,
                "zero_borrow": zero_borrow
            }
    finally:
        conn.close()


@app.get("/api/books/categories")
async def get_book_categories():
    """获取图书分类占比"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    bc.category,
                    COUNT(DISTINCT bc.bib_id) as total_items
                FROM book_categories bc
                GROUP BY bc.category
                ORDER BY total_items DESC
            """)
            rows = cur.fetchall()
            total = sum(r[1] for r in rows)
            return [
                {
                    "name": r[0],
                    "count": r[1],
                    "percent": round(r[1] / total * 100, 1) if total else 0
                }
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/books/hot")
async def get_hot_books():
    """获取热门图书排行"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bib_id, COUNT(*) as borrow_count
                FROM circulations
                WHERE action = 'CKO'
                GROUP BY bib_id
                ORDER BY borrow_count DESC
                LIMIT 10
            """)
            rows = cur.fetchall()
            return [
                {"rank": i + 1, "item_id": r[0], "borrowed": r[1]}
                for i, r in enumerate(rows)
            ]
    finally:
        conn.close()


@app.get("/api/borrows/stats")
async def get_borrow_stats():
    """获取借阅统计数据"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM mv_borrow_stats")
            row = cur.fetchone()
            
            return {
                "total_actions": row[0],
                "total_borrows": row[1],
                "total_returns": row[2],
                "total_renewals": row[3],
                "active_borrowers": row[4],
                "borrowed_books": row[5]
            }
    finally:
        conn.close()


@app.get("/api/borrows/action-stats")
async def get_action_stats():
    """获取各操作类型统计"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT action, count FROM mv_action_stats ORDER BY count DESC")
            rows = cur.fetchall()
            total = sum(r[1] for r in rows)
            action_names = {'CKO': '借出', 'CKI': '归还', 'REH': '到馆续借', 'REI': '网上续借'}
            return [
                {
                    "action": r[0],
                    "name": action_names.get(r[0], r[0]),
                    "count": r[1],
                    "percent": round(r[1] / total * 100, 1) if total else 0
                }
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/borrows/degree-stats")
async def get_degree_stats():
    """获取各读者类型借阅统计"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT degree, degree_name, count FROM mv_degree_borrow_stats ORDER BY count DESC")
            rows = cur.fetchall()
            total = sum(r[2] for r in rows)
            return [
                {
                    "code": r[0],
                    "name": r[1],
                    "count": r[2],
                    "percent": round(r[2] / total * 100, 1) if total else 0
                }
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/borrows/daily-trend")
async def get_daily_trend():
    """获取每日借阅趋势"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT action_date, count FROM mv_daily_borrow_trend")
            rows = cur.fetchall()
            return [
                {"date": str(r[0]), "count": r[1]}
                for r in rows
            ]
    finally:
        conn.close()


@app.get("/api/borrows/top-borrowers")
async def get_top_borrowers():
    """获取借阅排行TOP读者"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT borrower_id, degree, borrow_count FROM mv_top_borrowers LIMIT 15")
            rows = cur.fetchall()
            return [
                {
                    "rank": i + 1,
                    "borrower_id": r[0],
                    "degree": education_levels.get(r[1], r[1]),
                    "borrow_count": r[2]
                }
                for i, r in enumerate(rows)
            ]
    finally:
        conn.close()


@app.get("/api/borrows/top-books")
async def get_top_borrowed_books():
    """获取借阅排行TOP图书"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT bib_id, category, borrow_count FROM mv_top_books LIMIT 15")
            rows = cur.fetchall()
            return [
                {
                    "rank": i + 1,
                    "bib_id": r[0],
                    "category": r[1] if r[1] else '未知',
                    "borrow_count": r[2]
                }
                for i, r in enumerate(rows)
            ]
    finally:
        conn.close()


@app.get("/api/borrows/recent")
async def get_recent_borrows():
    """获取最近借阅记录"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.action_date, c.action_time, c.borrower_id, c.bib_id, 
                       c.action, b.degree, bc.category
                FROM circulations c
                JOIN borrowers b ON c.borrower_id = b.id
                LEFT JOIN book_categories bc ON c.bib_id = bc.bib_id
                WHERE c.action = 'CKO'
                ORDER BY c.action_date DESC, c.action_time DESC
                LIMIT 20
            """)
            rows = cur.fetchall()
            return [
                {
                    "date": str(r[0]),
                    "time": str(r[1]) if r[1] else '',
                    "borrower_id": r[2],
                    "bib_id": r[3],
                    "action": r[4],
                    "degree": education_levels.get(r[5], r[5]),
                    "category": r[6] if r[6] else '未知'
                }
                for r in rows
            ]
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
