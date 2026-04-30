-- 生成日期： 2026-04-18 20:20:08
-- 服务器版本： 10.3.32-MariaDB
-- PHP 版本： 8.0.23

--
-- 表的结构 `index_valuation`
--
CREATE TABLE `index_valuation` (
  `trade_date` date NOT NULL COMMENT '交易日期',
  `index_name` varchar(150) NOT NULL COMMENT '原始指数名称，如 S&P 500 / Information Technology - SEC - PE - NTM',
  `pe_ntm` decimal(8,4) DEFAULT NULL COMMENT '未来12个月市盈率 (PE NTM)',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '最后更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指数NTM PE估值历史数据';

--
-- 表的索引 `index_valuation`
--
ALTER TABLE `index_valuation`
  ADD PRIMARY KEY (`trade_date`,`index_name`);
COMMIT;