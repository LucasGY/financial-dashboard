-- 生成日期： 2026-04-18 20:26:31
-- 服务器版本： 10.3.32-MariaDB
-- PHP 版本： 8.0.23

--
-- 表的结构 `market_breadth`
--

CREATE TABLE `market_breadth` (
  `trade_date` date NOT NULL COMMENT '交易日期',
  `index_name` varchar(20) NOT NULL COMMENT '指数名称: SP500, NDX100',
  `above_20d_pct` decimal(5,2) DEFAULT NULL COMMENT '20日均线以上股票占比 (%)',
  `above_50d_pct` decimal(5,2) DEFAULT NULL COMMENT '50日均线以上股票占比 (%)',
  `above_200d_pct` decimal(5,2) DEFAULT NULL COMMENT '200日均线以上股票占比 (%)',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '最后更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='市场广度指标 (20d/50d/200d)';

--
-- 表的索引 `market_breadth`
--
ALTER TABLE `market_breadth`
  ADD PRIMARY KEY (`trade_date`,`index_name`);
COMMIT;
