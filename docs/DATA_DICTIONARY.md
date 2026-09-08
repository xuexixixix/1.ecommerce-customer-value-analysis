# 数据字典

数据集：Kaggle [Ecommerce Data](https://www.kaggle.com/datasets/carrie1/ecommerce-data)

| 原始字段      | 含义         | 在项目中的用途                             |
| ------------- | ------------ | ----------------------------------------|
| `InvoiceNo`   | 订单编号     | 订单去重、订单数量和 Frequency 计算        |
| `StockCode`   | 商品编号     | 订单明细和商品分析                        |
| `Description` | 商品描述     | 订单明细展示                              |
| `Quantity`    | 商品数量     | 销量和客户购买量计算                       |
| `InvoiceDate` | 订单日期     | 时间分析、Recency 和 OOT 切分              |
| `UnitPrice`   | 商品单价     | 订单金额计算                               |
| `CustomerID`  | 客户编号     | 客户关联、RFM 和预测建模                   |
| `Country`     | 客户所在国家 | 国家销售额和英国/海外对比                   |
| `TotalAmount` | 订单明细金额 | 项目新增字段，等于 `Quantity * UnitPrice`  |


## 清洗口径

- 删除 `CustomerID` 缺失记录。
- 删除 `Quantity <= 0` 的记录。
- 删除 `UnitPrice <= 0` 的记录。
- `TotalAmount` 在清洗后计算，不属于原始字段。

## 客户特征

- `recency`：观察窗口结束日至客户最近一次购买的天数，数值越小表示越近期购买。
- `frequency`：观察窗口内的独立订单数。
- `total_qty`：观察窗口内购买商品总数量。
- `total_spend`：观察窗口内历史消费金额。
- `avg_order_value`：历史消费金额除以独立订单数。
- `future_spend`：表现窗口内客户实际消费金额。
