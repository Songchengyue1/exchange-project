# 商品字段参考

## 数据表 `products`

| 列 | 类型 | 说明 |
|----|------|------|
| seller_id | int | 卖家 users.id |
| category_id | int | 外键 categories.id |
| title | string(200) | 标题 |
| description | text | 描述 |
| price | numeric(12,2) | 售价 |
| condition | string(32) | 成色枚举 |
| trade_type | string(16) | 交易方式枚举 |
| stock | int | 库存 |
| status | string(16) | pending / approved / rejected / offline |
| reject_reason | text | 驳回原因（可空） |

## 数据表 `product_images`

| 列 | 说明 |
|----|------|
| product_id | 商品 id |
| path | 如 `/static/demo_p1_iphone.png` |
| sort_order | 从 0 起 |

## API 路由（前缀 `/api/v1`）

| 方法 | 路径 | 认证 |
|------|------|------|
| POST | /products | 卖家 JWT |
| POST | /products/{id}/images | 卖家 JWT，multipart `files` |
| POST | /admin/products/{id}/approve | 管理员 JWT |
| GET | /categories | 无 |

## 演示账号（种子数据）

| 用户名 | 密码 | 角色 |
|--------|------|------|
| demo_seller1 | demo123 | 卖家 |
| admin | admin123 | 管理员 |
