# 酱菜交易平台 — 实现待办（模块与界面规划）

依据 [docs/需求规格说明书.md](./需求规格说明书.md)。状态：`[ ]` 未开始、`[~]` 进行中、`[x]` 已完成。

---

## M0 工程基础

- [~] 后端：统一异常与错误码、请求 ID 日志、`/api/v1` 路由分包（路由分包与全局异常处理仍可增强）
- [x] 后端：SQLAlchemy 模型 + Alembic 迁移（`init_database` 启动升级）；`app_settings` 种子；Repository 层统一数据访问；PostgreSQL + pgvector（`docker-compose.yml`）便于后续 RAG
- [~] 后端：JWT 依赖注入；`get_current_admin` 已预留；管理路由待接
- [x] 前端：路由（vue-router）、布局骨架、API 封装（fetch）、401 跳转登录
- [x] 前端：全局样式与响应式断点（与 SRS 5.3 一致）
- [x] 静态资源：本地上传目录与 URL 映射、图片大小/类型校验（头像 JPG/PNG/WEBP，≤2MB）

---

## M1 用户中心（注册 / 登录 / 个人资料）

**后端**

- [x] `POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`GET/PATCH /api/v1/users/me`
- [x] 密码 bcrypt；用户表字段：昵称、头像路径、手机、地址、角色、禁用标记

**界面**

- [x] 登录页
- [x] 注册页
- [x] 个人中心（资料编辑：昵称、头像上传、联系方式、收货地址）
- [x] 头部导航：登录态显示昵称/头像、退出

---

## M2 商品交易（发布 / 列表 / 详情 / 搜索 / 审核流）

**后端**

- [x] 分类 CRUD（管理员）+ 普通用户 `GET` 列表
- [x] 商品：创建（待审核）、编辑、下架；多图；成色、交易方式、库存、价格
- [x] 商品编辑重审：已上架 / 已驳回 / 已下架商品修改核心信息或补图后重新进入待审核
- [x] 商品列表：分页、分类筛选、关键词搜索、状态过滤（前台仅已上架）
- [x] 热门标签逻辑（卖家 `rating_avg` 非空且 ≥ 4.5 时 `is_hot`）
- [x] 卖家信誉摘要（详情/列表嵌入 `seller.rating_avg`，评价聚合在 M4 再完善）
- [x] 商品收藏：收藏 / 取消收藏接口、收藏数量与我的收藏列表

**界面**

- [x] 首页：热门 + 最新区块 + 分类入口
- [x] 商品列表页（筛选、排序、分页）
- [x] 商品详情页（轮播、参数、卖家信息、立即购买占位链到订单）
- [x] 商品详情页收藏按钮；我的收藏页（`/favorites`）
- [x] 发布商品页（表单 + 多图上传）
- [x] 我的商品（卖家：待审核 / 已上架 / 已驳回 / 已下架，支持编辑与下架）
- [x] 驳回原因展示（卖家可见）
- [x] 管理端：商品审核页（管理员可见导航「审核」）

---

## M3 订单与模拟支付

**后端**

- [x] `POST /orders` 创建订单（待付款）、库存校验与扣减/锁定策略
- [x] `POST /orders/{id}/mock-pay` 模拟支付成功/失败
- [x] `POST /orders/{id}/fulfill` 卖家确认发货/交付；`POST /orders/{id}/confirm-receipt`、`POST /orders/{id}/cancel`（状态机校验）
- [x] 买家订单列表、卖家相关订单视图（`GET /orders`、`GET /orders/sales`）
- [x] 支付抽象：`MockPaymentProvider`，预留真实网关接口

**界面**

- [x] 下单确认页（备注、交易方式展示）
- [x] 模拟支付页（成功/失败演示）
- [x] 我的订单（买家/卖家切换 + 状态 Tab；卖家可确认履约）
- [x] 订单详情页（卖家履约、买家确认收货、退款申请）

---

## M4 评价与意见反馈

**后端**

- [x] 订单完成后评价接口；评价与卖家 `rating_avg` 按评价均值更新
- [x] 意见反馈提交与管理员列表/处理状态（`pending` / `processing` / `resolved`）

**界面**

- [x] 订单完成后评价弹窗（`ReviewModal`）
- [x] 意见反馈表单页（`/feedback`）
- [x] 我的反馈列表（`/feedback/mine`）
- [x] 管理员反馈管理（`/admin/feedback`）

---

## M5 AI 智能服务

**后端**

- [x] `POST /ai/search`：向量 + 关键词混合检索；可选 LLM 抽槽位（`AI_SEARCH_USE_LLM`）；失败降级关键词
- [x] `POST /ai/chat`：Ollama 流式 SSE；RAG 召回商品；`AIConversation` / `ai_messages` 落库；`GET /ai/conversations` 历史列表与详情；`DELETE /ai/conversations/{id}` 删除会话（级联消息）
- [x] `POST /ai/browse` 浏览历史；`GET /ai/recommendations` 推荐（浏览向量 / 热门降级）
- [x] `product_embeddings` JSON 存储（本机 PG 无 pgvector 时可用）；`POST /ai/embeddings/reindex`（管理员）

**界面**

- [x] 商品列表：自然语言提示 +「智能搜索」
- [x] AI 抽屉：历史记录侧栏、会话恢复、新对话、单条删除（二次确认）；悬浮入口（仅 assistant 流式）
- [x] 首页 / 详情「猜你喜欢」

**后续（非阻塞）**

- [ ] M5 收尾后评估迁 `docker compose` pgvector 与库内向量索引
- [ ] 环境变量：`OLLAMA_*`、`AI_SEARCH_USE_LLM`、`AI_EMBED_BATCH_ON_STARTUP` 写入 `.env.example`

---

## M6 管理员后台

**后端**

- [x] 管理员鉴权（`get_current_admin`）；商品待审核列表、通过/驳回（原因必填）
- [x] `GET/PATCH /admin/users`、`POST /admin/users/{id}/reset-password`；`admin_audit_logs` 审计
- [x] 分类管理 CRUD（`/admin/categories`）
- [x] `GET /admin/orders` 订单监管；`POST .../refund-approve|refund-reject`；买家 `POST /orders/{id}/request-refund`；退款驳回原因回显

**界面**

- [x] `AdminLayout` 侧栏 + 内容区（`/admin/*`，仅 admin）
- [x] 待审核商品、用户管理（含审计日志）、分类管理、订单/退款审核（含驳回原因）、反馈管理

---

## M7 非功能与上线准备

- [ ] 友好错误页或全局 Toast；生产环境关闭文档栈暴露
- [ ] CORS、HTTPS、环境变量与密钥管理说明
- [ ] 基础安全自测：SQL 注入、XSS、越权（用户调 admin 接口）
- [ ] README 部署说明与数据库备份提示

---

## 建议实现顺序

1. M0 → M1（可登录后才有后续）  
2. M2 商品与分类（含审核流）  
3. M3 订单与模拟支付  
4. M4 评价反馈  
5. M6 管理后台（可与 M2 审核并行后半段）  
6. M5 AI（依赖商品与浏览数据）  
7. M7 收尾

---

*完成某项后请将对应 `[ ]` 改为 `[x]`，便于团队同步。*
