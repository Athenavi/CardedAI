# FastBlog 支付系统

## 概述

FastBlog支付系统是一个综合性的支付解决方案，支持多种支付方式：

1. **传统支付网关**: Stripe, PayPal, 支付宝, 微信支付
2. **加密货币支付**: BTC, ETH, USDT, USDC等
3. **x402微支付协议**: 用于微支付场景
4. **NFT门票验证**: NFT持有者内容解锁
5. **税务计算**: VAT/GST自动计算
6. **合规性**: GDPR, PCI DSS合规检查

## 架构

```
shared/services/payment/
├── __init__.py              # 统一支付服务入口
├── payment_gateway.py       # 传统支付网关
├── crypto_payment.py        # 加密货币支付
├── tax_compliance.py        # 税务和合规性
└── order_management.py      # 订单管理
```

## API端点

### 传统支付

- `POST /api/v1/payment/create-order` - 创建订单
- `POST /api/v1/payment/pay/{order_id}` - 处理支付
- `GET /api/v1/payment/order/{order_id}` - 查询订单
- `POST /api/v1/payment/refund/{order_id}` - 退款

### 加密货币支付

- `POST /api/v1/payment/crypto/create` - 创建加密货币支付
- `GET /api/v1/payment/crypto/status/{order_id}` - 检查支付状态

### x402微支付

- `POST /api/v1/payment/x402/channel/create` - 创建支付通道
- `POST /api/v1/payment/x402/payment` - 处理微支付

### NFT验证

- `POST /api/v1/payment/nft/verify` - 验证NFT所有权

### 税务计算

- `POST /api/v1/payment/tax/calculate` - 计算税务
- `GET /api/v1/payment/compliance/check` - 检查合规性

### 购物车

- `POST /api/v1/payment/cart/add` - 添加到购物车
- `GET /api/v1/payment/cart` - 获取购物车
- `POST /api/v1/payment/cart/checkout` - 结算

### 订单管理

- `POST /api/v1/payment/order/create` - 创建订单
- `GET /api/v1/payment/orders` - 获取订单列表
- `POST /api/v1/payment/order/{order_id}/cancel` - 取消订单

## 使用示例

### 创建订单并支付

```python
# 1. 创建订单
response = await client.post("/api/v1/payment/order/create", json={
    "items": [
        {
            "product_id": 1,
            "product_name": "Premium Article",
            "quantity": 1,
            "unit_price": 9.99
        }
    ],
    "currency": "USD"
})

order_id = response.json()["data"]["order"]["order_id"]

# 2. 使用Stripe支付
response = await client.post(f"/api/v1/payment/pay/{order_id}", json={
    "success_url": "https://example.com/success",
    "cancel_url": "https://example.com/cancel"
})

# 3. 或使用加密货币支付
response = await client.post("/api/v1/payment/crypto/create", json={
    "order_id": order_id,
    "blockchain": "ethereum",
    "token_symbol": "ETH"
})
```

### 购物车流程

```python
# 1. 添加到购物车
await client.post("/api/v1/payment/cart/add", json={
    "product_id": 1,
    "product_name": "Article",
    "unit_price": 9.99,
    "quantity": 2
})

# 2. 查看购物车
cart = await client.get("/api/v1/payment/cart")

# 3. 结算
order = await client.post("/api/v1/payment/cart/checkout", json={
    "currency": "USD",
    "shipping_address": {...},
    "billing_address": {...}
})
```

### 税务计算

```python
# 计算VAT
response = await client.post("/api/v1/payment/tax/calculate", json={
    "amount": 100.0,
    "country_code": "DE",
    "has_vat_number": True,
    "vat_number": "DE123456789"
})

# 返回:
# {
#     "subtotal": 100.0,
#     "tax_rate": 0.0,  # B2B免税
#     "tax_amount": 0.0,
#     "total": 100.0,
#     "exemption_applied": True
# }
```

### NFT验证

```python
# 验证NFT持有者身份
response = await client.post("/api/v1/payment/nft/verify", json={
    "wallet_address": "0x1234...",
    "contract_address": "0xabcd...",
    "token_id": 1
})

if response.json()["data"]["is_owner"]:
    # 解锁专属内容
    pass
```

## 数据模型

### PaymentGateway

支付网关配置，存储各支付平台的API密钥和设置。

### PaymentTransaction

支付交易记录，跟踪所有支付活动。

### CryptoPayment

加密货币支付详情，包括钱包地址、交易哈希、确认数等。

### TaxConfig

税务配置，存储不同国家和地区的税率。

### Order

订单模型，包含订单项、金额、状态等信息。

### OrderItem

订单项，表示订单中的单个商品。

## 安全考虑

1. **PCI DSS合规**: 不存储原始信用卡数据，使用tokenization
2. **GDPR合规**: 用户数据保护，提供数据导出和删除功能
3. **Webhook验证**: 所有webhook都经过签名验证
4. **加密传输**: 所有API通信使用HTTPS
5. **防重放攻击**: 实现nonce和timestamp验证

## 扩展性

系统设计为模块化，可以轻松添加新的支付方式：

1. 在`payment_gateway.py`中添加新的支付服务类
2. 在`UnifiedPaymentService`中集成新功能
3. 在`payment_api.py`中添加相应的API端点

## 测试

运行支付系统测试：

```bash
pytest tests/test_payment.py -v
```

## 部署注意事项

1. 配置环境变量中的支付网关API密钥
2. 设置webhook URL指向正确的端点
3. 启用HTTPS
4. 配置数据库迁移
5. 设置日志记录和监控
