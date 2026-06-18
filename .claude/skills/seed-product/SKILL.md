---
name: seed-product
description: >-
  向酱菜交易平台 PostgreSQL 存入商品：收集并校验标题、分类、价格、成色、交易方式、库存、描述与图片，
  经 API 或种子脚本写入。用户说「录入商品」「存入商品」「添加商品」「seed product」时使用。
---

# 存入商品（seed-product）

## 执行前：必须收齐商品信息

**未收齐必填项前不得写入数据库。** 用下方清单向用户确认；用户已给全则可跳过追问。

复制并填写（未知项标 `待确认`）：

```markdown
## 商品录入单

- [ ] **标题** title：（1～200 字）
- [ ] **分类** category：（数码 / 服饰 / 图书 / 家居 / 其他 → 对应 category_id）
- [ ] **价格** price：（元，> 0，最多两位小数）
- [ ] **成色** condition：（见下表枚举）
- [ ] **交易方式** trade_type：（见下表枚举）
- [ ] **库存** stock：（默认 1，≥1）
- [ ] **描述** description：（可选，建议 20 字以上）
- [ ] **封面/图片** images：（0～6 张，jpg/png/webp，单张 ≤2MB）
- [ ] **卖家** seller：（API 录入=当前登录用户；脚本录入=username 或 user_id）
- [ ] **上架状态** status：（默认 `pending` 待审核；演示数据可用 `approved`）
```

### 枚举（与后端 `ProductCreate` 一致）

| 字段 | 合法值 | 中文 |
|------|--------|------|
| condition | `brand_new` `like_new` `excellent` `good` `fair` | 全新 / 99新 / 成色优 / 良好 / 一般 |
| trade_type | `pickup` `shipping` `both` | 自提 / 邮寄 / 自提或邮寄 |
| status（仅脚本/DB） | `pending` `approved` `rejected` `offline` | 待审核 / 已上架 / 已驳回 / 已下架 |

### 分类 ID（种子数据默认）

| 分类名 | category_id |
|--------|-------------|
| 数码 | 1 |
| 服饰 | 2 |
| 图书 | 3 |
| 家居 | 4 |
| 其他 | 5 |

不确定时先查库：`GET /api/v1/categories` 或 `SELECT id, name FROM categories ORDER BY sort_order;`

---

## 写入方式（按场景选一）

### 方式 A：HTTP API（与线上一致，需卖家 JWT）

1. `POST /api/v1/auth/login` → `access_token`
2. `POST /api/v1/products` JSON body（`ProductCreate`）
3. `POST /api/v1/products/{id}/images` multipart 字段名 **`files`**

```json
{
  "category_id": 1,
  "title": "示例标题",
  "description": "详细描述",
  "price": 99.9,
  "condition": "excellent",
  "trade_type": "both",
  "stock": 1
}
```

创建后状态为 **`pending`**，管理员 `POST /api/v1/admin/products/{id}/approve` 后前台可见。

### 方式 B：项目脚本（开发/批量/演示，推荐 Agent 使用）

在 `backend` 目录：

```bash
.venv/bin/python scripts/insert_product.py \
  --seller demo_seller1 \
  --category 数码 \
  --title "商品标题" \
  --price 199.00 \
  --condition excellent \
  --trade-type both \
  --stock 1 \
  --description "商品描述" \
  --image ../path/to/cover.png \
  --status approved
```

- `--seller`：用户名；`--seller-id` 可替代
- `--category`：分类中文名或数字 id
- `--image`：可重复传入多张（最多 6 张）
- `--status approved`：直接上架（跳过审核，仅演示/运营数据）

### 方式 C：扩展 `app/db/seed.py`

批量、可重复执行的演示数据放入 `seed_demo_users_and_products` 或新增 `seed_*` 函数，并在 `run_seed_data(..., include_demo_products=True)` 中调用。图片走 `seed_demo_product_images`，文件放 `backend/seed_images/`。

---

## Agent 工作流

```
任务进度：
- [ ] 1. 用「商品录入单」收集/核对全部字段
- [ ] 2. 校验价格>0、枚举合法、分类存在、图片格式/大小
- [ ] 3. 选择写入方式（API / insert_product.py / seed.py）
- [ ] 4. 执行写入
- [ ] 5. 验证：GET /api/v1/products/{id} 或查 product_images 表
- [ ] 6. 告知用户：商品 id、状态、前台是否可见、登录账号（若用 API）
```

**图片路径**：复制到 `backend/uploads/`，库中 `product_images.path` 为 `/static/文件名`。

**禁止**：编造 category_id；跳过成色/交易方式；把演示商品标为 approved 却不告知用户需审核流程。

---

## 常见问题

| 现象 | 处理 |
|------|------|
| 前台列表看不到 | 状态须为 `approved` |
| 401 | API 需先登录卖家账号 |
| 分类不存在 | 先 `run_seed_data()` 或查 categories 表 |
| 图片不显示 | 确认 `uploads/` 有文件且后端挂载 `/static` |

详细字段说明见 [product-fields.md](product-fields.md)。
