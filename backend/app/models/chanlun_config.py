# -*- coding: utf-8 -*-
"""缠论配置模型"""
from sqlalchemy import Column, BigInteger, String, JSON, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ChanlunConfig(Base):
    __tablename__ = "chanlun_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
