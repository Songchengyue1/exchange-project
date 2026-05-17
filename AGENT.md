# Agent 会话上下文（由 Cursor 规则维护）

本文件由规则 **「会话上下文落盘」** 在每轮回复后更新；用于承接跨会话的决策与进度。勿提交生产环境密钥与真实用户密码。

## 测试账号（本地演示）

> 以下账号由 `backend/app/db/seed.py` 写入，**仅用于本地开发/演示**。生产环境勿使用这些弱密码。

### 登录入口

| 项目 | 地址 |
|------|------|
| 前端 | http://127.0.0.1:5173/login 或 http://localhost:5173/login |
| 后端 API 文档 | http://127.0.0.1:8000/docs |
| 登录接口 | `POST /api/v1/auth/login`，body：`{"username":"…","password":"…"}` |

### 账号列表

| 用户名 | 密码 | 角色 | 昵称 | 说明 |
|--------|------|------|------|------|
| `admin` | `admin123` | 管理员 | 管理员 | 顶栏「审核」、商品审核通过/驳回 |
| `demo_seller1` | `demo123` | 卖家 | 阿杰 | 信誉 4.85；发布 iPhone、MacBook、宜家书桌等 |
| `demo_seller2` | `demo123` | 卖家 | 小雨 | 信誉 4.2；发布球鞋、图书、Switch 卡带等 |
| `demo_buyer` | `demo123` | 买家 | 买家小明 | 下单、支付、确认收货等买家流程 |

### 演示数据概要

- **分类**（5 个）：数码、服饰、图书、家居、其他  
- **已上架商品**（6 件）：含封面图（`product_images` → `/static/demo_p*.png`）  
- **待审核商品**（1 件）：索尼 WH-1000XM4 耳机（`demo_seller2`），供 `admin` 审核  
- **平台配置**：`app_settings.hot_rating_threshold = 4.5`

### 数据库（PostgreSQL）

| 项 | 值 |
|----|-----|
| 库名 | `secondhand` |
| 本机示例连接 | `postgresql+psycopg://wepie@127.0.0.1:5432/secondhand`（见 `backend/.env`，用户因环境而异） |
| TablePlus | Host `127.0.0.1`，Port `5432`，User 填本机 PG 用户，**Database 填 `secondhand`** |

### 重新写入演示账号与商品

```bash
cd backend
.venv/bin/python -c "
from app.db.seed import run_seed_data
run_seed_data(include_demo_admin=True, include_demo_products=True, include_demo_images=True)
"
```

若已存在 `demo_seller1`，用户/商品种子会跳过；需清空 `users`/`products` 相关表后再执行，或删库重建。

---

## 最新会话

### 2026-05-17 — 稍后支付 + 30 分钟付款倒计时

- **用户诉求**：模拟支付页增加「稍后支付」；订单页 30 分钟倒计时，超时自动取消。
- **结论**：支付页「稍后支付」跳转订单列表；`OrderPaymentCountdown` 展示剩余时间；后端 `order_payment_timeout`（30 分钟）在列表/详情/支付时自动取消并恢复库存；前端倒计时结束刷新/跳转。
- **涉及文件**：`backend/app/services/order_payment_timeout.py`、`routers/orders.py`；`frontend/src/views/OrderPayView.vue`、`OrderListView.vue`、`OrderDetailView.vue`、`OrderPaymentCountdown.vue`。

### 2026-05-17 — 默认地址标签配色

- **用户诉求**：默认地址标识不要用红色。
- **结论**：`AddressSelector` 中「默认」胶囊改为灰白中性色；单选 `accent-color` 改为 `--color-on-dark`。
- **涉及文件**：`frontend/src/components/AddressSelector.vue`。

### 2026-05-17 — 更新高德 JS API 凭据

- **用户诉求**：提供新的 JS API Key 与安全密钥。
- **结论**：已写入本地 `frontend/.env`（未进仓库）。
- **建议下一步**：重启 `npm run dev`；确认控制台白名单含 localhost。

### 2026-05-17 — 高德 USERKEY_PLAT_NOMATCH 说明

- **用户诉求**：地图报错 `USERKEY_PLAT_NOMATCH` / `Unimplemented type: 3`。
- **结论**：属 Key 平台类型不符（多为用了 Web 服务 Key 而非 JS API）；代码已支持 `VITE_AMAP_SECURITY_CODE` 与更明确的前端提示，需用户在控制台换 JS API Key + 安全密钥。
- **涉及文件**：`frontend/src/lib/amap.ts`、`AmapAddressPicker.vue`、`frontend/.env.example`。

### 2026-05-17 — 配置高德 Key

- **用户诉求**：提供高德 Web Key，用于地址地图选点。
- **结论**：已写入本地 `frontend/.env` 的 `VITE_AMAP_KEY`（未写入示例文件与版本库）。
- **涉及文件**：`frontend/.env`（gitignore）。
- **建议下一步**：重启 `npm run dev`；在高德控制台为 Key 配置 `localhost` 等安全域名白名单。

### 2026-05-17 — 收货地址切换 + 高德地图选点

- **用户诉求**：确认订单处不要静态展示地址，需可切换地址并接入高德地图选点。
- **结论**：新增 `user_addresses` 表与 CRUD API；`AddressSelector` 支持单选切换、新增/编辑/删除/默认；`AmapAddressPicker` 集成高德搜索与地图打点；下单携带 `shipping_address_id` 并快照至订单；旧 `users.address` 首次拉取时自动迁移为默认地址。
- **配置**：`frontend/.env` 增加 `VITE_AMAP_KEY`（高德 Web 端 Key）；迁移 `g7h8i9j0k1l2`。
- **涉及文件**：`backend/app/models/user_address.py`、`routers/user_addresses.py`、`orders.py`；`frontend/src/components/AddressSelector.vue`、`AmapAddressPicker.vue`、`OrderCheckoutView.vue` 等。

### 2026-05-17 — 确认订单页双栏与补充信息

- **用户诉求**：确认订单左侧空档需补充信息，参照其他平台。
- **结论**：双栏布局：左侧商品/收货联系/履约说明/备注；右侧 sticky 订单明细、流程步骤、费用拆解、平台提示与提交。
- **涉及文件**：`frontend/src/views/OrderCheckoutView.vue`。

### 2026-05-17 — 应用图标

- **用户诉求**：使用 `docs/ChatGPT Image 2026年5月17日 01_07_01.png` 作为 App 图标。
- **结论**：复制为 `frontend/public/app-icon.png`；favicon / apple-touch-icon、顶栏与管理后台侧栏品牌图已接入；`APP_ICON` 常量。
- **涉及文件**：`frontend/public/app-icon.png`、`constants/app.ts`、`index.html`、`MainLayout.vue`、`AdminLayout.vue`。

### 2026-05-16 — 平台更名为酱菜交易平台

- **用户诉求**：交易平台名字改为「酱菜交易平台」。
- **结论**：顶栏品牌、`index.html` title、静态页/隐私条款、后端 API 名与 AI 提示词、文档标题已统一；`frontend/src/constants/app.ts` 集中站点名。
- **涉及文件**：`MainLayout.vue`、`constants/app.ts`、`index.html`、`sitePages.ts`、`config.py`、`main.py`、`chat_service.py`、`llm_parse.py`、部分 docs。

### 2026-05-16 — 商品详情页管理员审核操作

- **用户诉求**：管理后台审核商品点进详情页后，应有通过审核/返回审核列表。
- **结论**：`ProductDetailView` 在管理员 + 待审核时显示审核区（通过/驳回）；`?from=admin` 或待审核时显示「返回审核列表」；审核列表标题链携带 `from=admin`。
- **涉及文件**：`frontend/src/views/ProductDetailView.vue`、`AdminProductsView.vue`。

### 2026-05-16 — 发布页图片缩略图预览

- **用户诉求**：发布商品页上传的图片需在小框内预览。
- **结论**：`SellView` 选图后 88×88 缩略图网格；支持多张累加（最多 6 张）、单张移除；`createObjectURL` 预览并在卸载/提交后释放。
- **涉及文件**：`frontend/src/views/SellView.vue`。

### 2026-05-16 — 页脚静态页（关于/帮助/隐私/条款）

- **用户诉求**：为页脚「关于、帮助、隐私、条款」补充正文内容。
- **结论**：新增 `SitePageView` + `content/sitePages.ts`；路由 `/about`、`/help`、`/privacy`、`/terms`；页脚链接已指向对应页面。
- **涉及文件**：`frontend/src/content/sitePages.ts`、`views/SitePageView.vue`、`router/index.ts`、`layouts/MainLayout.vue`。

### 2026-05-16 — M6 管理员后台

- **用户诉求**：实现 M6 管理员后台。
- **结论**：后端补用户管理、分类 CRUD（已有）、订单监管与退款审核、`admin_audit_logs` 迁移；买家可申请退款（`refund_pending`）。前端 `AdminLayout` + 五子页；顶栏合并为「管理后台」；订单详情支持申请退款。
- **涉及文件**：`backend/app/routers/admin.py`、`orders.py`、`models/admin_audit_log.py`、`alembic/versions/f6a7b8c9d0e2_*`；`frontend/src/layouts/AdminLayout.vue`、`views/Admin*View.vue`、`router/index.ts`、`api/admin.ts` 等。
- **建议下一步**：M7 非功能收尾；管理端分页与搜索；退款驳回原因展示给买家。

### 2026-05-16 — 删除 AI 历史对话

- **用户诉求**：添加删除历史对话的功能。
- **结论**：后端 `DELETE /api/v1/ai/conversations/{id}`（登录、仅本人会话，204）；仓库 `AIConversationRepository.delete`；消息表 FK 已 `ondelete=CASCADE`。前端历史项右侧「×」、二次确认（danger）；删当前会话则 `startNewChat()`，并清理 `localStorage` 上次会话 id。
- **涉及文件**：`backend/app/repositories/ai.py`、`backend/app/routers/ai.py`；`frontend/src/api/ai.ts`、`frontend/src/components/AiChatDrawer.vue`；`docs/实现待办-TODO.md`。
- **建议下一步**：批量清空全部历史；删除后 toast 提示；管理端查看用户对话（若需要）。

### 2026-05-16 — AI 对话历史记录（前端）

- **用户诉求**：AI 对话助手需要记录并查看历史记录。
- **结论**：后端已有 `ai_conversations` / `ai_messages` 落库；补充消息 `product_ids` 返回；前端抽屉左侧历史列表、点击恢复、新对话、记住上次会话。
- **涉及文件**：`backend/app/routers/ai.py`、`schemas/ai.py`；`frontend/src/components/AiChatDrawer.vue`、`api/ai.ts`、`types/ai.ts`、`composables/useAiChat.ts`。

### 2026-05-16 — 修复 AI 悬浮钮不显示

- **现象**：右下角看不到 AI 悬浮入口。
- **原因**：模板里 `v-show="!aiChat.open"` 未解包 Ref，条件恒为 false。
- **处理**：改为解构 `const { open, show } = useAiChat()` 与 `v-show="ready && !open"`；提高 z-index；校验 localStorage 坐标。
- **涉及文件**：`frontend/src/components/AiChatFab.vue`、`composables/useAiFabPosition.ts`。

### 2026-05-16 — AI 助手悬浮可拖动入口

- **用户诉求**：主页 AI 入口改为悬浮样式，初始在右下角，可拖动自行放置。
- **结论**：新增 `AiChatFab`（圆角悬浮钮、hover 上浮阴影、M 色顶条）；`localStorage` 记忆位置；拖动与点击区分；顶栏「AI 助手」已移除。全局挂载于 `App.vue`。
- **涉及文件**：`frontend/src/components/AiChatFab.vue`、`composables/useAiFabPosition.ts`、`App.vue`、`layouts/MainLayout.vue`。

### 2026-05-16 — AI 抽屉 UI：圆角与「AI 思考中」

- **用户诉求**：对话框/回复框圆角；发送按钮不要在回复时显示「生成中」；在 AI 气泡内显示思考状态。
- **结论**：`AiChatDrawer` 气泡圆角（用户右下、助手左下小角）；底部 composer 圆角；`thinking` 状态 + 三点动画「AI 思考中」；发送按钮恒为「发送」，流式期间仅禁用（防连发）。
- **涉及文件**：`frontend/src/components/AiChatDrawer.vue`。

### 2026-05-16 — AI 对话响应加速

- **用户诉求**：AI 回复偏慢。
- **结论**：对话默认**关键词检索**（跳过每次 embed）；`think=false` + `num_predict=320` + `keep_alive`；缩短 system/历史；检索与落库放线程池；SSE 先返回「正在匹配…」；商品向量进程内缓存。
- **涉及文件**：`chat_service.py`、`ollama_client.py`、`embedding_index.py`、`config.py`、`AiChatDrawer.vue`、`api/ai.ts`。

### 2026-05-16 — 修复 AI 对话「暂无匹配商品」

- **现象**：问「上架了什么」「mac 电脑多少钱」时上下文为「暂无匹配商品」。
- **原因**：① `product_embeddings` 未建索引；② Ollama 新版 embedding 应调 `/api/embed`，旧 `/api/embeddings` 返回空数组。
- **处理**：修正 `ollama_client.embed`；对话检索增加关键词降级；已为 6 件上架商品写入向量。
- **涉及文件**：`backend/app/services/ai/ollama_client.py`、`chat_service.py`。

### 2026-05-16 — 实现 M5 AI 智能服务（Ollama + LangChain）

- **用户诉求**：按对齐方案实现 M5；本机 Ollama（`mxbai-embed-large`、`qwen3.5:0.8b`）；向量+关键词混合搜索；对话 assistant 流式 SSE；pgvector 后续再评估。
- **结论**：迁移 `e5f6a7b8c0d1`（`browse_histories`、`ai_conversations`、`ai_messages`、`product_embeddings`）；`app/services/ai/`（Ollama httpx、向量近邻、可选 LangChain 抽槽位、RAG 流式对话）；API `/api/v1/ai/*`。前端：智能搜索、顶栏 AI 抽屉、首页/详情猜你喜欢。
- **涉及文件**：`backend/app/routers/ai.py`、`services/ai/*`、`models/browse_history.py` 等；`frontend/src/api/ai.ts`、`components/AiChatDrawer.vue`；`docs/实现待办-TODO.md`、`backend/.env.example`。
- **使用**：启动 Ollama → 后端 → 登录后可用 AI 助手；管理员 `POST /api/v1/ai/embeddings/reindex` 建向量；`AI_SEARCH_USE_LLM=true` 开启 LLM 抽槽位。
- **验证**：`npm run build` 通过；Alembic head `e5f6a7b8c0d1`。

### 2026-05-16 — 首页与各页鼠标悬浮特效

- **用户诉求**：在首页和其他页面增加鼠标悬浮的特殊效果。
- **结论**：在 `style.css` 新增可复用交互类（`ds-hover-card` 卡片上浮/渐变遮罩/图片缩放、`ds-text-link` 下划线动画、`ds-hover-row` 列表行、`ds-hover-tab` 筛选 Tab、`ds-hover-pill`）；增强 `.ds-btn` 悬浮上浮与阴影；支持 `prefers-reduced-motion`。已应用到首页商品卡、商品列表、顶栏导航/用户芯片、订单与我的商品列表、反馈管理/我的反馈等。
- **涉及文件**：`frontend/src/style.css`、`views/HomeView.vue`、`ProductListView.vue`、`layouts/MainLayout.vue`、`views/OrderListView.vue`、`MyProductsView.vue`、`AdminFeedbackView.vue`、`MyFeedbackView.vue`。
- **验证**：`npm run build` 通过。
- **建议下一步**：商品详情页卖家信息区、登录/注册表单卡片可同样套用 `ds-hover-card`；按需微调移动端导航下划线表现。

### 2026-05-16 — 实现 M4 评价与意见反馈

- **用户诉求**：继续实现 M4。
- **结论**：后端 `reviews` / `feedbacks` 表与迁移 `d4e5f6a7b8c9`；`POST /orders/{id}/review`、评价后刷新卖家 `rating_avg`；`POST/GET /feedback`、`GET/PATCH /admin/feedback`。前端评价弹窗、反馈页、我的反馈、管理员反馈管理。
- **涉及文件**：`backend/app/models/review.py`、`feedback.py`、`routers/*`、`alembic/versions/d4e5f6a7b8c9_*`；`frontend/src/components/ReviewModal.vue`、`views/Feedback*.vue`、`AdminFeedbackView.vue`；`docs/实现待办-TODO.md`。
- **测试**：买家 `demo_buyer` 完成订单后可评价；`admin` 处理 `/admin/feedback`。

### 2026-05-16 — AGENT.md 收录测试账号

- **用户诉求**：把当前测试账号写入 AGENT.md。
- **结论**：在文首新增「测试账号（本地演示）」固定区块（账号表、入口、演示数据、库连接、种子命令）。
- **涉及文件**：`AGENT.md`。

### 2026-05-16 — 通用二次确认弹窗组件

### 2026-05-16 — 通用二次确认弹窗组件

- **用户诉求**：不用浏览器 confirm/toast，做可复用二次确认弹窗（退出、发布商品、保存资料等）。
- **结论**：`showConfirm()` + 全局 `ConfirmDialog`（挂 App.vue）；已替换退出、发布/编辑商品、保存资料、下架、取消订单、确认收货等场景。
- **涉及文件**：`frontend/src/composables/useConfirm.ts`、`components/ConfirmDialog.vue`、`App.vue`、各业务 View/MainLayout。

### 2026-05-16 — 圆形头像与昵称首字占位

- **用户诉求**：头像圆形；未上传时显示名字第一个字。
- **结论**：新增 `UserAvatar.vue`（sm/md/lg）；顶栏、个人中心、商品详情卖家区已接入。
- **涉及文件**：`frontend/src/components/UserAvatar.vue`、`MainLayout.vue`、`ProfileView.vue`、`ProductDetailView.vue`。

### 2026-05-16 — 退出登录二次确认

- **用户诉求**：退出登录增加二次确认。
- **结论**：`MainLayout.vue` 退出按钮改为 `window.confirm` 后执行 `logout` 并跳转 `/login`。
- **涉及文件**：`frontend/src/layouts/MainLayout.vue`。

### 2026-05-16 — 修复登录 500（bcrypt / passlib）

- **用户诉求**：`POST /api/v1/auth/login` 返回 500。
- **结论**：`passlib` 与新版 `bcrypt` 不兼容，`verify_password` 抛错；改为 `bcrypt` 直调 `checkpw`/`hashpw`，依赖去掉 passlib。
- **涉及文件**：`backend/app/core/security.py`、`backend/requirements.txt`。

### 2026-05-16 — 创建「存入商品」Cursor Skill

- **用户诉求**：生成 skill 用于存入商品，需填写对应商品信息。
- **结论**：新增 `.cursor/skills/seed-product/`（录入单清单、API/脚本/seed 三种写入方式）；`backend/scripts/insert_product.py` CLI 录入脚本。
- **涉及文件**：`.cursor/skills/seed-product/SKILL.md`、`product-fields.md`、`backend/scripts/insert_product.py`。
- **使用**：对话中说「按 seed-product skill 录入商品」或 @seed-product；Agent 会先收齐字段再执行。

### 2026-05-16 — 演示商品封面图入库

- **用户诉求**：将 6 张商品图关联到 iPhone、MacBook、Nike、算法导论、宜家书桌、Switch 卡带。
- **结论**：图片存 `backend/uploads/`，源文件备份在 `backend/seed_images/`；`product_images` 表写入 `/static/demo_p*.png`；`seed_demo_product_images()` 可重复执行（已有图则跳过）。
- **涉及文件**：`backend/app/db/seed.py`、`backend/seed_images/*`、`backend/uploads/demo_p*.png`。

### 2026-05-16 — 写入演示种子数据

- **用户诉求**：加入一些数据便于在 TablePlus / 前端查看。
- **结论**：扩展 `app/db/seed.py` 的 `seed_demo_users_and_products`：4 个演示账号 + 7 件商品（6 已上架、1 待审核）；演示密码统一 `demo123`；管理员 `admin` / `admin123`。
- **涉及文件**：`backend/app/db/seed.py`。
- **TablePlus**：刷新 `users`、`products` 表即可看到。
- **登录**：`demo_seller1` / `demo123` 或 `admin` / `admin123`。

### 2026-05-16 — 本地启动 PostgreSQL 前后端

- **用户诉求**：帮忙启动并查看是否正常。
- **结论**：本机 PostgreSQL（用户 `wepie`）已建库 `secondhand` 并跑完迁移；`backend/.env` 指向该库；后端 `http://127.0.0.1:8000`、前端 `http://127.0.0.1:5173` 已运行；分类种子 5 条正常，商品列表为空（新库）。
- **涉及文件**：`backend/.env`（本地，勿提交）、`alembic/versions/c3d4e5f6a7b8_enable_pgvector.py`（无 pgvector 时跳过）。
- **注意**：本机未装 pgvector 扩展；需 RAG 时用 `docker compose up` 的 pgvector 镜像。
- **下一步**：浏览器打开前端；注册账号后可发布商品测试。

### 2026-05-16 — 数据库切换为 PostgreSQL（pgvector）

- **用户诉求**：使用 PostgreSQL，方便后续大模型 RAG 向量检索。
- **结论**：默认连接 `postgresql+psycopg://…`（可由 `DATABASE_URL` 或 `POSTGRES_*` 配置）；依赖增加 `psycopg[binary]`；连接池 `pool_pre_ping`；根目录 `docker-compose.yml` 使用 `pgvector/pgvector:pg16`；迁移修正时间戳为 `now()`，新增 `c3d4e5f6a7b8` 启用 `vector` 扩展。
- **涉及文件**：`backend/app/config.py`、`database.py`、`db/bootstrap.py`、`requirements.txt`、`.env.example`、`docker-compose.yml`、`alembic/versions/*`、`docs/实现待办-TODO.md`。
- **未完成 / 风险**：需本机 `docker compose up -d` 或自备 PostgreSQL；复制 `backend/.env.example` 为 `.env` 后重启后端；旧 SQLite 数据需迁移或重建。
- **下一步**：业务表增加 `embedding vector` 列与检索 API（RAG）；或继续 M4 评价模块。

### 2026-05-16 — 完善数据库与 Repository 层

- **用户诉求**：数据都从数据库读取，完善数据库逻辑。
- **结论**：启动改为 `init_database()` + `run_seed_data()`（分类、`app_settings.hot_rating_threshold`）；新增 `app_settings` 表迁移 `a1b2c3d4e5f6`；路由层统一走 `UserRepository` / `CategoryRepository` / `ProductRepository` / `OrderRepository` / `SettingsRepository`；商品热门标识阈值从库读取。
- **涉及文件**：`backend/app/main.py`、`db/seed.py`、`db/bootstrap.py`、`models/app_setting.py`、`repositories/*`、`routers/{auth,categories,products,orders,admin,users}.py`、`alembic/versions/a1b2c3d4e5f6_add_app_settings.py`、`docs/实现待办-TODO.md`。
- **未完成 / 风险**：若本地库曾 `stamp head` 但缺 `app_settings` 表，需执行 `alembic upgrade head` 或删 `backend/data/app.db` 重建；管理员仍须在库中设 `role='admin'`。
- **下一步**：重启后端使迁移生效；可继续 M4 评价或 M3 售后退款。

### 2026-05-14 — 实现 M3 订单与模拟支付

- **用户诉求**：继续实现 M3。
- **结论**：后端新增 `Order` 模型与 `orders` 路由（下单扣库存、模拟支付、确认收货、取消恢复库存、买家/卖家列表）；`MockPaymentProvider` 支付抽象。前端新增下单确认、模拟支付、订单列表（我买/我卖 + 状态 Tab）、订单详情；商品详情「立即购买」链至 `/orders/checkout/:productId`。
- **涉及文件**：`backend/app/models/order.py`、`schemas/order.py`、`services/payment.py`、`services/order_serializers.py`、`routers/orders.py`、`main.py`；`frontend/src/api/orders.ts`、`types/order.ts`、`constants/orderLabels.ts`、`views/Order*.vue`、`router/index.ts`、`ProductDetailView.vue`；`docs/实现待办-TODO.md`。
- **状态机**：`pending_payment` →（mock-pay 成功）→ `pending_fulfillment` →（确认收货）→ `completed`；`pending_payment` →（取消）→ `cancelled` 并恢复库存。
- **下一步**：M4 评价反馈；M3 售后退款可后续扩展。

### 2026-05-14 — 启动后端

- **用户诉求**：起后端。
- **结论**：已在 `backend` 目录后台运行 `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`。
- **涉及文件**：无代码变更。
- **访问**：API <http://127.0.0.1:8000/docs> ，健康检查 <http://127.0.0.1:8000/health> 。
- **下一步**：结束进程时在对应终端 `Ctrl+C`。

### 2026-05-14 — 实现 M2 商品与分类

- **用户诉求**：实现 M2。
- **结论**：后端新增 `Category`、`Product`、`ProductImage` 模型与 `User.rating_avg`；公开 `GET /categories`、`GET/POST/PATCH/POST offline /images` 商品流；`GET /admin/products/pending|approve|reject` 与 `GET/POST/PATCH/DELETE /admin/categories`；启动 `seed_categories`；序列化热门 `is_hot`；静态图仍走 `/static`。前端新增列表/详情/发布/我的商品/管理审核页与路由，`HomeView` 接入分类与热门/最新区块；`MainLayout` 增加「我的商品」「审核（admin）」入口；`router-meta.d.ts` 扩展 `RouteMeta`。
- **涉及文件**：`backend/app/models/*`、`schemas/category.py`、`schemas/product.py`、`services/product_serializers.py`、`routers/{categories,products,admin}.py`、`main.py`；`frontend/src/api/*`、`views/*`、`router/index.ts`、`layouts/MainLayout.vue`、`router-meta.d.ts`、`README.md`、`docs/实现待办-TODO.md`。
- **注意**：旧 SQLite 若无新列需删库或手动迁移；管理员需在库中改 `role`。
- **下一步**：M3 订单与模拟支付；M4 评价写入并驱动 `rating_avg` 聚合。

### 2026-05-14 — 启动 M0/M1：用户与前后端骨架

- **用户诉求**：开始实现项目。
- **结论**：后端新增 SQLite + SQLAlchemy `User` 表、JWT（python-jose）、bcrypt 密码、`/api/v1/auth/register|login`、`/api/v1/users/me` GET/PATCH、头像 `POST /users/me/avatar` + `/static` 挂载与 `uploads/` 目录；启动时 `create_all`。前端接入 `vue-router`、`pinia`、fetch 封装（401 处理）、`MainLayout` + 首页/登录/注册/个人中心/占位路由；Vite 代理补充 `/static`、`/docs`、`/openapi.json`。已更新 `README.md`、`docs/实现待办-TODO.md`、`.gitignore`。
- **涉及文件**：`backend/app/`（database、models、schemas、core/security、deps、routers/auth、routers/users、main）、`frontend/src/`（router、stores、api、layouts、views、App、main）、`frontend/vite.config.ts`、`frontend/package.json`、`README.md`、`docs/实现待办-TODO.md`、`.gitignore`
- **未完成**：Alembic 迁移、统一错误码与请求 ID、管理端接口与商品/订单模块（M2+）。
- **下一步**：实现 M2 分类与商品（含审核状态）及列表页对接。

### 2026-05-14 — 启动前端开发服务

- **用户诉求**：运行前端界面供本地查看。
- **结论**：已在 `frontend` 目录后台启动 `npm run dev -- --host 127.0.0.1`（Vite 8），本机访问 `http://127.0.0.1:5173/`。
- **涉及文件**：无代码变更。
- **提示**：顶栏健康状态依赖 `/health` 代理；若需显示「后端在线」，另开终端在 `backend` 执行 `uvicorn app.main:app --reload --port 8000`。
- **下一步**：浏览器打开上述地址；结束服务时在对应终端 `Ctrl+C`。

### 2026-05-14 — 前端对齐 DESIGN.md

- **用户诉求**：前端样式模仿 `docs/DESIGN.md` 中的设计系统。
- **结论**：全局 `style.css` 写入 DESIGN 色板、间距、Inter 替代字体与通用类（`.ds-btn`、`.ds-label-caps`、`.ds-m-stripe`）；`App.vue` 重构为顶栏 64px、M 三色条、大标题 hero、分类 tab、三列 feature 卡片（surface-card + 发丝线 + 0 圆角）、CTA 带与页脚；移动端全屏菜单顶部含三色条；`index.html` 去掉与旧模板冲突的居中布局依赖。
- **涉及文件**：`frontend/src/style.css`、`frontend/src/App.vue`、`frontend/index.html`
- **注意**：未使用 BMW 官方字体与实拍图，仅用文档中的开源替代（Inter）与抽象渐变块；若需完全离线可改为本地托管字体。
- **下一步**：新增页面时复用 CSS 变量与 `.ds-*` 类，或抽离 `BaseButton` / `MStripe` 组件。

### 2026-05-14 — Cursor 规则与实现待办

- **用户诉求**：新增两条项目规则——(1) 每轮回答后将上下文写入 `AGENT.md`；(2) 每次写完或改完代码后检查完整性与准确性；另需一份模块与界面的 todolist。
- **结论**：已在 `.cursor/rules/` 创建 `agent-context-to-agent-md.mdc`（`alwaysApply: true`）与 `post-code-change-verification.mdc`（匹配 `**/*.{py,vue,ts,tsx,js}`）；初始化 `AGENT.md`；新增 `docs/实现待办-TODO.md`（M0～M7 后端+界面清单与推荐顺序）；`README.md` 增加上述文档链接。
- **涉及文件**：`.cursor/rules/agent-context-to-agent-md.mdc`、`.cursor/rules/post-code-change-verification.mdc`、`AGENT.md`、`docs/实现待办-TODO.md`、`README.md`
- **未完成 / 风险**：`globs` 中大括号扩展是否被 Cursor 全版本支持未实测；若规则未触发，可改为多条 `globs` 或缩小为 `backend/**/*.py` + `frontend/**/*.{vue,ts}`。
- **下一步**：在 Cursor 设置中确认项目规则已启用；按 `docs/实现待办-TODO.md` 从 M0/M1 开始实现。
