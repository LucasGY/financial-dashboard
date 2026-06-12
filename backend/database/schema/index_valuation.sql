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
  `valuation_source` varchar(32) NOT NULL DEFAULT 'facset' COMMENT '估值来源：facset / proxy_adjusted',
  `is_estimated` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否为价格代理估算值',
  `raw_pe_ntm` decimal(8,4) DEFAULT NULL COMMENT '估算前的原始 FacSet PE',
  `based_on_trade_date` date DEFAULT NULL COMMENT '估算基准日期',
  `proxy_ticker` varchar(16) DEFAULT NULL COMMENT '估算使用的价格代理标的',
  `proxy_return` decimal(12,8) DEFAULT NULL COMMENT '代理标的从基准日至估算日的涨跌幅',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '最后更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指数NTM PE估值历史数据';

--
-- 表的索引 `index_valuation`
--
ALTER TABLE `index_valuation`
  ADD PRIMARY KEY (`trade_date`,`index_name`);
COMMIT;
