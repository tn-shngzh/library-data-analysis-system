import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "library_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
]

education_levels = {
    '1a': '研究生', '1b': '本科', '1c': '大专', '1d': '高中',
    '1e': '初中', '1f': '小学', '1g': '临时', '1h': '学龄前'
}
