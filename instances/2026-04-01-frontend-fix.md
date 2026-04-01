---
instance_id: 2026-04-01-frontend-fix
title: "缠论前端5个问题修复 + 三层MACD"
status: pending
current_step: 2
created_at: 2026-04-01T03:50:00Z
updated_at: 2026-04-01T03:55:00Z
owner: 涛哥
---

# 缠论前端修复 + 三层MACD

## 需求确认（已完成）

| # | 问题 | 方案 |
|---|------|------|
| 1 | 点击分析同时调用日/周/月三周期 | 默认只查日线，切换周期再触发请求 |
| 2 | limit=240 规则没生效，日线从2020年开始 | 修复 limit 参数传递 |
| 3 | 刷新/日期/赋权变更后不重请求 | watch 变更自动重请求 |
| 4 | 底部 loading 图标一直存在 | 请求完成关闭 loading |
| 5 | 中枢/笔/线段/趋势/分型参照旧缠论样式 | 参考 `bak/chanlun/` 旧版 Plotly 样式 |
| **6（新增）** | **三层 MACD** | **同时展示：15分钟 MACD + 60分钟 MACD + 日线 MACD** |

## 参考文件

- **旧版缠论样式**：`/root/.openclaw/workspace/projects/bak/chanlun/`（包含 Streamlit+Plotly 的笔/线段/中枢/分型样式）
- **新版前端**：`/root/.openclaw/workspace/projects/chanlun/frontend/`（Vue 前端）
- **新版后端**：`/root/.openclaw/workspace/projects/chanlun/backend/`（FastAPI）

## 三层 MACD 详细说明

涛哥要求：三层 MACD（参照旧版 MACD 样式）

| 层级 | 周期 | 说明 |
|------|------|------|
| 第1层 | 15分钟 | 15分钟K线 + 15分钟MACD |
| 第2层 | 60分钟 | 60分钟K线 + 60分钟MACD |
| 第3层 | 日线 | 日线K线 + 日线MACD |

图表布局（四图纵向排列）：
1. 15分钟：K线 + 成交量 + 15分钟MACD
2. 60分钟：K线 + 成交量 + 60分钟MACD
3. 日线：K线 + 成交量 + 日线MACD
4. （可选）原有缠论笔线段叠加

注意：进入页面默认加载日线（K线 + 日线MACD），15分钟/60分钟MACD根据用户切换加载。

## 步骤状态

| 步骤 | 状态 | 产出 |
|------|------|------|
| requirement | ✅ 完成 | 需求已确认 |
| split | ✅ 完成 | 6个任务已拆分 |
| develop | ⬜ 进行中 | — |
| review | ⬜ 待审核 | — |
| deliver | ⬜ 待交付 | — |

## 任务清单

| ID | 任务 | 状态 |
|----|------|------|
| T1 | 修复周期请求逻辑：默认只查日线，切换再请求 | ⬜ |
| T2 | 修复 limit=240 参数生效 | ⬜ |
| T3 | 刷新/日期/赋权变更后自动重请求 | ⬜ |
| T4 | Loading 图标正确关闭 | ⬜ |
| T5 | 笔/线段/中枢/分型样式参照旧版 Plotly | ⬜ |
| T6 | 三层 MACD（15分钟/60分钟/日线）| ⬜ |
