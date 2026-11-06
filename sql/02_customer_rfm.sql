-- 建立 RFM 客户分群分析视图
CREATE OR REPLACE VIEW view_customer_rfm AS
WITH customer_rfm AS (
    -- 1. 基础聚合：计算每个客户的 Recency, Frequency, Monetary
    SELECT
        c.customer_id,
        DATEDIFF('2011-12-10', MAX(i.invoice_date)) AS recency_days,
        COUNT(DISTINCT i.invoice_no) AS frequency,
        SUM(ii.total_amount) AS monetary
    FROM customers c
    JOIN invoices i ON c.customer_id = i.customer_id
    JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
    GROUP BY c.customer_id
),
rfm_scores AS (
    -- 2. 窗口函数：按 1-5 五等分打分
    SELECT
        customer_id,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score, -- 距离现在越近分越高
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,     -- 频次越高分越高
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score       -- 金额越高分越高
    FROM customer_rfm
)
-- 3. 业务规则映射：划分客户画像分类
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN '核心高价值客户'
        WHEN r_score <= 2 AND f_score >= 4 THEN '高频流失预警客户'
        WHEN r_score >= 4 AND f_score <= 2 THEN '新进高潜客户'
        ELSE '一般维持客户'
    END AS customer_segment
FROM rfm_scores;