# 缠论分析平台

## 项目结构

```
/data/chanlun/
├── sql/
│   └── schema.sql          # MySQL 数据库结构
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── config.py       # 配置（数据库/JWT）
│   │   ├── database.py     # SQLAlchemy 连接
│   │   ├── models/         # ORM 模型
│   │   ├── schemas/        # Pydantic Schema
│   │   ├── routers/        # API 路由
│   │   └── services/       # 业务逻辑（AKShare/缠论算法）
│   ├── requirements.txt
│   └── start.sh
└── frontend/               # Vue 3 + Vite + Naive UI
    ├── src/
    │   ├── views/         # 页面组件
    │   ├── stores/         # Pinia 状态管理
    │   ├── api/            # Axios 封装
    │   └── router/         # Vue Router
    └── start.sh
```

## 快速启动

### 1. MySQL
- 数据目录: `/data/mysql`
- 连接: `mysql -u root -p'Chanlun2026!'`
- 建表: SQL 文件在 `sql/schema.sql`

### 2. 后端
```bash
cd /data/chanlun/backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8503
```

### 3. 前端
```bash
cd /data/chanlun/frontend
pnpm install
pnpm dev
```

## 端口规划

| 服务 | 端口 |
|------|------|
| 前端 (Vue Dev) | 8501 |
| 后端 (FastAPI) | 8503 |
| 旧版单体 (暂存) | 8502 |

## 数据库表

| 表名 | 说明 |
|------|------|
| users | 用户表 |
| watchlists | 股票池 |
| watchlist_stocks | 股票池股票 |
| chanlun_configs | 缠论分析配置 |

## API 概览

### 认证
- `POST /api/auth/register` 注册
- `POST /api/auth/login` 登录
- `GET /api/auth/me` 当前用户

### 股票池
- `GET /api/watchlist/` 股票池列表
- `POST /api/watchlist/` 新建股票池
- `DELETE /api/watchlist/:id` 删除
- `POST /api/watchlist/:id/stocks` 添加股票
- `DELETE /api/watchlist/:id/stocks/:sid` 移除股票

### 股票数据
- `GET /api/stocks/kline?stock_code=000001&period=daily` K线+指标
- `GET /api/stocks/quote?stock_code=000001` 实时行情
- `GET /api/stocks/macd/multi?stock_code=000001` 多周期MACD
