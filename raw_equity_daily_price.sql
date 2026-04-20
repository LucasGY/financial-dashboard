-- 股票/ETF 回测原始价格表

CREATE TABLE IF NOT EXISTS `raw_equity_daily_price` (
  `instrument_id` bigint unsigned NOT NULL,
  `trade_date` date NOT NULL COMMENT '交易日',
  `adj_close_price` decimal(20,6) DEFAULT NULL COMMENT '供应商复权收盘价',
  `source_system` varchar(32) NOT NULL DEFAULT 'yfinance',
  `source_ticker` varchar(32) NOT NULL COMMENT '供应商原始 ticker',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`instrument_id`, `trade_date`),
  KEY `idx_raw_equity_daily_price_trade_date` (`trade_date`),
  CONSTRAINT `fk_raw_equity_daily_price_instrument`
    FOREIGN KEY (`instrument_id`) REFERENCES `dim_instrument` (`instrument_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票与ETF回测原始价格数据';
