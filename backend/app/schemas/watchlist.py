# -*- coding: utf-8 -*-
"""股票池 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime


class WatchlistStockCreate(BaseModel):
    stock_code: str = Field(..., pattern=r"^\d{6}$")
    stock_name: str | None = None


class WatchlistStockOut(BaseModel):
    id: int
    watchlist_id: int
    stock_code: str
    stock_name: str | None
    added_at: datetime

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None


class WatchlistOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: str | None
    created_at: datetime
    stocks: list[WatchlistStockOut] = []

    class Config:
        from_attributes = True
