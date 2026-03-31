# -*- coding: utf-8 -*-
"""股票池模型"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    stocks = relationship("WatchlistStock", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistStock(Base):
    __tablename__ = "watchlist_stocks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    watchlist_id = Column(BigInteger, ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False, index=True)
    stock_code = Column(String(20), nullable=False, index=True)
    stock_name = Column(String(50))
    added_at = Column(DateTime, server_default=func.now())

    watchlist = relationship("Watchlist", back_populates="stocks")

    __table_args__ = (UniqueConstraint("watchlist_id", "stock_code", name="uk_watchlist_stock"),)
