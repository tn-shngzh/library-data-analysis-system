from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.routers import auth, overview, readers, books, borrows

app = FastAPI(title="图书馆数据分析系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(overview.router)
app.include_router(readers.router)
app.include_router(books.router)
app.include_router(borrows.router)


@app.get("/")
async def root():
    return {"message": "图书馆数据分析系统 API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
