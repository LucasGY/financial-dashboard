-- 回测证券主数据表

CREATE TABLE IF NOT EXISTS `dim_instrument` (
  `instrument_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `ticker` varchar(16) NOT NULL COMMENT '标准证券代码，例如 SPY / AAPL',
  `name` varchar(128) DEFAULT NULL COMMENT '证券名称，可后续补齐',
  `asset_type` varchar(32) NOT NULL DEFAULT 'EQUITY' COMMENT 'EQUITY / ETF',
  `currency_code` char(3) NOT NULL DEFAULT 'USD',
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`instrument_id`),
  UNIQUE KEY `uk_dim_instrument_ticker` (`ticker`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='回测证券主数据';
