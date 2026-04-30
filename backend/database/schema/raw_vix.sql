-- 生成日期： 2026-04-18 20:27:08
-- 服务器版本： 10.3.32-MariaDB
-- PHP 版本： 8.0.23

--
-- 表的结构 `raw_vix`
--

CREATE TABLE `raw_vix` (
  `trade_date` date NOT NULL COMMENT '交易日期',
  `vix_close` decimal(5,2) DEFAULT NULL COMMENT 'VIX 收盘价',
  `vvix_close` decimal(5,2) DEFAULT NULL COMMENT 'VVIX 收盘价',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '最后更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='VIX与VVIX波动率原始数据';

--
-- 表的索引 `raw_vix`
--
ALTER TABLE `raw_vix`
  ADD PRIMARY KEY (`trade_date`);
COMMIT;
