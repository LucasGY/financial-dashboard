-- 主机： localhost
-- 生成日期： 2026-04-18 20:25:52
-- 服务器版本： 10.3.32-MariaDB
-- PHP 版本： 8.0.23

--
-- 表的结构 `index_valuation_cleanup_backup_20260405_091245`
--

CREATE TABLE `index_valuation_cleanup_backup_20260405_091245` (
  `trade_date` date NOT NULL COMMENT '交易日期',
  `index_name` varchar(150) CHARACTER SET utf8mb4 NOT NULL COMMENT '原始指数名称，如 S&P 500 / Information Technology - SEC - PE - NTM',
  `pe_ntm` decimal(8,4) DEFAULT NULL COMMENT '未来12个月市盈率 (PE NTM)',
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp() COMMENT '最后更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
COMMIT;
