# -*- coding: utf-8 -*-
"""缠论配置 Schema"""
from pydantic import BaseModel
from datetime import datetime


class ChanlunConfigCreate(BaseModel):
    name: str
    config: dict


class ChanlunConfigOut(BaseModel):
    id: int
    user_id: int
    name: str
    config: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
