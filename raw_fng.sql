-- 生成日期： 2026-04-18 20:26:55
-- 服务器版本： 10.3.32-MariaDB
-- PHP 版本： 8.0.23

--
-- 表的结构 `raw_fng`
--

CREATE TABLE `raw_fng` (
  `trade_date` date NOT NULL COMMENT '交易日期',
  `fng_value` int(11) DEFAULT NULL COMMENT 'CNN恐贪指数 (0-100)',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '最后更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='CNN恐贪指数原始数据';

--
-- 表的索引 `raw_fng`
--
ALTER TABLE `raw_fng`
  ADD PRIMARY KEY (`trade_date`);
COMMIT;
