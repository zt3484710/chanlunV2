# -*- coding: utf-8 -*-
"""股票数据路由"""
from fastapi import APIRouter, Depends, Query
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.stock_data import get_kline_data, get_realtime_quote, get_stock_info
from app.services.chanlun_analysis import get_kline_with_indicators, get_multi_period_macd

router = APIRouter(prefix="/api/stocks", tags=["股票数据"])


@router.get("/kline")
def get_kline(
    stock_code: str = Query(..., description="股票代码，如 000001"),
    period: str = Query("daily", description="周期: 15min/60min/daily/weekly/monthly"),
    adjust: str = Query("qfq", description="复权: qfq/hfq"),
    limit: int = Query(240, description="K线数量限制，默认240"),
    current_user: User = Depends(get_current_user),
):
    return get_kline_with_indicators(stock_code, period, adjust, limit)


@router.get("/quote")
def get_quote(
    stock_code: str = Query(..., description="股票代码"),
    current_user: User = Depends(get_current_user),
):
    return get_realtime_quote(stock_code)


@router.get("/info")
def get_info(
    stock_code: str = Query(..., description="股票代码"),
    current_user: User = Depends(get_current_user),
):
    return get_stock_info(stock_code)


@router.get("/macd/multi")
def get_macd_multi(
    stock_code: str = Query(..., description="股票代码"),
    current_user: User = Depends(get_current_user),
):
    return get_multi_period_macd(stock_code)
