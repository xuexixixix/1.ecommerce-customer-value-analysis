# 1. 数据清洗与描述性分析

from pathlib import Path

import pandas as pd
import numpy as np

# 1. 读取数据：将数据文件放到仓库根目录的 data/ 目录
DATA_PATH = Path("data/data.csv")
df = pd.read_csv(DATA_PATH, encoding="latin1")
print(f"原始数据维度: {df.shape}")

# 2. 清洗缺失值
df_clean = df.dropna(subset=['CustomerID']).copy()

# 3. 处理异常值
# 过滤掉退货单（数量 <= 0）和免费/错误标价商品（单价 <= 0）
df_clean = df_clean[(df_clean['Quantity'] > 0) &(df_clean['UnitPrice'] > 0)]

# 4. 新增业务指标列
# 计算单条交易明细金额 (金额 = 数量 * 单价)
df_clean['TotalAmount'] = df_clean['Quantity'] * df_clean['UnitPrice']

print(f"清洗后数据维度: {df_clean.shape}")

# 5. 查看清洗后的基本统计描述
print("\n清洗后的数值特征描述:")
print(df_clean[['Quantity', 'UnitPrice', 'TotalAmount']].describe())

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# 1. 样式设置：必须先调用 set_theme，再设置字体（否则字体会被重置）
sns.set_theme(style="whitegrid")
plt.rcParams["font.sans-serif"] = ["SimHei"]  # 正常显示中文
plt.rcParams["axes.unicode_minus"] = False  # 正常显示负号

# 2. 核心指标统计：TOP 5 国家销售额
country_sales = (
    df_clean.groupby("Country")["TotalAmount"].sum().sort_values(ascending=False)
)
print("=== TOP 5 销售额国家 (英镑) ===")
print(country_sales.head())

# 3. 统计学假设检验：英国本土 vs 海外交易明细金额对比
uk_amount = df_clean[df_clean["Country"] == "United Kingdom"]["TotalAmount"]
non_uk_amount = df_clean[df_clean["Country"] != "United Kingdom"][
    "TotalAmount"
]

# 独立样本 T 检验 (双尾检验)
t_stat, p_val = stats.ttest_ind(uk_amount, non_uk_amount, equal_var=False)

print("\n=== 统计学 T 检验结果 ===")
print(f"英国本土交易明细平均金额: £{uk_amount.mean():.2f}")
print(f"海外交易明细平均金额: £{non_uk_amount.mean():.2f}")
print(f"T 统计量: {t_stat:.4f}, p-value: {p_val:.4e}")

if p_val < 0.05:
    print(
        "结论: p-value < 0.05，拒绝原假设！海外与本土交易明细金额存在显著差异。"
    )
else:
    print("结论: 无显著差异。")

# 4. 数据可视化：绘制 TOP 10 国家销售额柱状图
plt.figure(figsize=(10, 5))
top_10_countries = country_sales.head(10)

# 修复处：显式指定 hue 并关掉图例
sns.barplot(
    x=top_10_countries.values,
    y=top_10_countries.index,
    hue=top_10_countries.index,
    legend=False,
    palette="Blues_r",
)

plt.title("Top 10 国家销售总额分布", fontsize=14)
plt.xlabel("总销售额 (£)", fontsize=12)
plt.ylabel("国家", fontsize=12)
plt.tight_layout()
plt.show()

# 2. 连接至数据库

import os

from sqlalchemy import create_engine
import pandas as pd

# 数据库连接配置：通过环境变量提供凭据，不要将密码写入代码或提交到 GitHub
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "ecommerce_db")

# 没有配置数据库密码时跳过导入，清洗和建模分析仍可继续执行。
if DB_PASSWORD:
    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # 1. 拆分并导出 Customers 表 (去重，保证 customer_id 唯一)
    df_customers = df_clean[['CustomerID', 'Country']].drop_duplicates(subset=['CustomerID'])
    df_customers.columns = ['customer_id', 'country']
    df_customers.to_sql('customers', con=engine, if_exists='append', index=False)
    print("Customers 表导入完成！")

    # 2. 拆分并导出 Invoices 表 (按 InvoiceNo 去重)
    df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
    df_invoices = df_clean[['InvoiceNo', 'InvoiceDate', 'CustomerID']].drop_duplicates(subset=['InvoiceNo'])
    df_invoices.columns = ['invoice_no', 'invoice_date', 'customer_id']
    df_invoices.to_sql('invoices', con=engine, if_exists='append', index=False)
    print("Invoices 表导入完成！")

    # 3. 导出 Invoice Items 明细表
    df_items = df_clean[['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'UnitPrice', 'TotalAmount']].copy()
    df_items.columns = ['invoice_no', 'stock_code', 'description', 'quantity', 'unit_price', 'total_amount']
    df_items.to_sql('invoice_items', con=engine, if_exists='append', index=False, chunksize=10000)
    print("Invoice_Items 明细表导入完成！")
else:
    print("未配置 MYSQL_PASSWORD，跳过 MySQL 导入步骤。")

# 3. 提取特征值，为回归分析做准备

import pandas as pd
import numpy as np

# 1. 确保时间字段格式正确，确定时间切割节点
df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
max_date = df_clean['InvoiceDate'].max()

# 以数据集最后 90 天作为预测表现期，之前的数据作为特征观察期
split_date = max_date - pd.Timedelta(days=90)

# 2. 切割数据集：观察期 (Observation Window) 与 表现期 (Performance Window)
obs_df = df_clean[df_clean['InvoiceDate'] < split_date].copy()
perf_df = df_clean[df_clean['InvoiceDate'] >= split_date].copy()

# 3. 观察期特征提取 (自变量 X)
X_features = obs_df.groupby('CustomerID').agg(
    recency=('InvoiceDate', lambda x: (split_date - x.max()).days), # 最近一次购买距观察期截止日天数
    frequency=('InvoiceNo', 'nunique'),                             # 观察期内独立订单数
    total_qty=('Quantity', 'sum'),                                  # 观察期内购买商品总量
    total_spend=('TotalAmount', 'sum')                              # 观察期内总消费金额
).reset_index()

# 修正客单价 (AOV)：使用真实的订单平均金额（总消费额 / 订单数）
X_features['avg_order_value'] = X_features['total_spend'] / X_features['frequency']

# 4. 表现期目标变量提取 (因变量 y: 未来 90 天实际总消费额)
y_target = perf_df.groupby('CustomerID')['TotalAmount'].sum().reset_index()
y_target.columns = ['CustomerID', 'future_90d_spend']

# 5. 合并特征与目标变量（观察期有行为但表现期无消费的客户，目标值填充为 0）
model_data = pd.merge(X_features, y_target, on='CustomerID', how='left')
model_data['future_90d_spend'] = model_data['future_90d_spend'].fillna(0)

# 6. 查看数据构建结果
print(f"观察期时间范围: {obs_df['InvoiceDate'].min().strftime('%Y-%m-%d')} 至 {split_date.strftime('%Y-%m-%d')}")
print(f"表现期时间范围: {split_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
print(f"有效建模客户总数: {len(model_data)}")
print("\n建模数据集前 5 行预览:")
print(model_data[['CustomerID', 'recency', 'frequency', 'total_spend', 'avg_order_value', 'future_90d_spend']].head())

# 4. 机器学习线性回归

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

# 1. 特征提取与 Log 预处理通用函数 (封装逻辑)
def extract_window_features(obs_df, perf_df, obs_end_date):
    # 提取特征 (X)
    X = obs_df.groupby('CustomerID').agg(
        recency=('InvoiceDate', lambda x: (obs_end_date - x.max()).days), # 保持线性天数
        frequency=('InvoiceNo', 'nunique'),
        total_qty=('Quantity', 'sum'),
        total_spend=('TotalAmount', 'sum')
    ).reset_index()

    # 计算真实客单价
    X['avg_order_value'] = X['total_spend'] / X['frequency']

    # 仅对长尾右偏的计数与金额特征做 log1p 压缩，保留 recency 的线性物理意义
    for col in ['frequency', 'total_qty', 'total_spend', 'avg_order_value']:
        X[col] = np.log1p(X[col])

    # 提取目标变量 (y)
    y = perf_df.groupby('CustomerID')['TotalAmount'].sum().reset_index()
    y.columns = ['CustomerID', 'future_spend']

    # 合并 X 与 y
    data = pd.merge(X, y, on='CustomerID', how='left').fillna({'future_spend': 0})
    data['future_spend_log'] = np.log1p(data['future_spend'])
    return data

# 2. 构建滑动时间窗口 (OOT 划分)
# 窗口 1（训练集）：观察期 2010.12 - 2011.06 | 表现期 2011.06 - 2011.09
obs_train = df_clean[(df_clean['InvoiceDate'] >= '2010-12-01') & (df_clean['InvoiceDate'] < '2011-06-01')]
perf_train = df_clean[(df_clean['InvoiceDate'] >= '2011-06-01') & (df_clean['InvoiceDate'] < '2011-09-01')]
train_data = extract_window_features(obs_train, perf_train, pd.to_datetime('2011-06-01'))

# 窗口 2（OOT 测试集）：观察期 2011.03 - 2011.09 | 表现期 2011.09 - 2011.12
obs_test = df_clean[(df_clean['InvoiceDate'] >= '2011-03-01') & (df_clean['InvoiceDate'] < '2011-09-01')]
perf_test = df_clean[df_clean['InvoiceDate'] >= '2011-09-01']
test_data = extract_window_features(obs_test, perf_test, pd.to_datetime('2011-09-01'))

# 3. 拟合与 OOT 验证
feature_cols = ['recency', 'frequency', 'total_qty', 'total_spend', 'avg_order_value']
X_train, y_train = train_data[feature_cols], train_data['future_spend_log']
X_test, y_test = test_data[feature_cols], test_data['future_spend_log']

# 拟合线性回归模型
model_oot = LinearRegression()
model_oot.fit(X_train, y_train)

# OOT 预测
y_pred_log = model_oot.predict(X_test)

# 评估指标计算
r2_oot = r2_score(y_test, y_pred_log)
mae_orig = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred_log))

print("=== OOT 跨时间窗口验证结果 ===")
print(f"训练集样本量: {len(train_data)} | OOT 测试集样本量: {len(test_data)}")
print(f"OOT 对数空间决定系数 ($R^2$): {r2_oot:.4f}")
print(f"OOT 真实金额平均绝对误差 (MAE): £{mae_orig:.2f}")

# 4. 特征回归系数展示
coef_df = pd.DataFrame({
    'Feature': feature_cols,
    'Coefficient': model_oot.coef_
}).sort_values(by='Coefficient', ascending=False)

print("\n=== 各特征回归系数 (权值) ===")
print(coef_df)
