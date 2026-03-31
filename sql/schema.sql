-- ============================================================
-- 缠论分析平台 数据库结构定义
-- 版本: v1.0.0
-- 更新: 2026-03-31
-- ============================================================

-- ----------------------------
-- 1. 用户表
-- ----------------------------
CREATE TABLE IF NOT EXISTS users (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username        VARCHAR(50)  NOT NULL UNIQUE COMMENT '用户名',
  password_hash   VARCHAR(255) NOT NULL COMMENT '密码哈希(bcrypt)',
  nickname        VARCHAR(50) COMMENT '昵称',
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ----------------------------
-- 2. 股票池表
-- ----------------------------
CREATE TABLE IF NOT EXISTS watchlists (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id     BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  name        VARCHAR(100) NOT NULL COMMENT '股票池名称',
  description TEXT COMMENT '描述',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票池';

-- ----------------------------
-- 3. 股票池股票表
-- ----------------------------
CREATE TABLE IF NOT EXISTS watchlist_stocks (
  id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  watchlist_id   BIGINT UNSIGNED NOT NULL COMMENT '股票池ID',
  stock_code     VARCHAR(20) NOT NULL COMMENT '股票代码 如 000001',
  stock_name     VARCHAR(50) COMMENT '股票名称',
  added_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_watchlist_id (watchlist_id),
  INDEX idx_stock_code (stock_code),
  UNIQUE KEY uk_watchlist_stock (watchlist_id, stock_code),
  FOREIGN KEY (watchlist_id) REFERENCES watchlists(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票池股票';

-- ----------------------------
-- 4. 缠论分析配置表
-- ----------------------------
CREATE TABLE IF NOT EXISTS chanlun_configs (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id     BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
  name        VARCHAR(100) NOT NULL COMMENT '配置名称',
  config      JSON NOT NULL COMMENT '缠论分析配置JSON',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='缠论分析配置';

-- ----------------------------
-- 字段说明
-- ----------------------------
-- users:
--   username      - 登录账号，唯一
--   password_hash - bcrypt哈希存储，不可逆
--
-- watchlists:
--   user_id       - 所属用户，实现数据隔离
--   name          - 如"我的自选"、"A股龙头"等
--
-- watchlist_stocks:
--   watchlist_id  - 所属股票池
--   stock_code    - 股票代码，6位数字
--   stock_name    - 股票名称（冗余存储，避免每次查）
--
-- chanlun_configs:
--   user_id       - 所属用户
--   config        - JSON格式，示例：
--     {
--       "periods": ["15min", "60min", "daily"],
--       "macd_show": true,
--       "macd_periods": ["daily", "weekly", "monthly"],
--       "line_type": "fenxing"  // 分型/笔/线段/中枢
--     }
