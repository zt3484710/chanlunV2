# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, watchlist, stocks, chanlun_analysis

# 创建表（如果不存在）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="缠论分析平台 API", version="1.0.0", description="前后端分离架构 - Python后端")

# CORS（允许前端开发服务器访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(watchlist.router)
app.include_router(stocks.router)
app.include_router(chanlun_analysis.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "chanlun-backend"}
