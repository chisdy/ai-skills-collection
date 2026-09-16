# 实体与角色推断规则

`analyze_features.py` 的 `entities` / `roles` / `flows` 三段怎么来的，以及模型在写文档时如何补全与修正。原则：**每个属性带来源；能从页面 / 请求直接看到的标实采，其余标推断**。

## 1. 实体来源（按可信度排序）

| 来源 | 怎么取 | 可信度 | 例 |
|---|---|---|---|
| API 响应 JSON | `network.json[].responseShape`：数组首项的键与类型 → 实体属性；路径最后一个名词单数化作实体名（`/api/products.json` → Product） | 最高：字段名与类型都是真的 | `{id:int, name:str, price:int, rating:float, category:str}` |
| JSON-LD | `page.json.jsonLd[].type/keys`：`Product` / `Article` / `Event` / `Recipe` 等 schema.org 类型直接是实体 | 高 | `Product: name, offers, aggregateRating` |
| 表单字段 | `forms[].fields[].name` 按 `FIELD_ENTITY` 映射：email / password / name / phone → User；receiver / region / address / postcode → Address；shipping / payment / coupon / note → Order；rating / body → Review | 高：字段名是开发者起的 | 结算表单 → Order + Address |
| 列表项字段 | `lists[].fields[].kind`：有价格 → Product；有评分无图 → Review；有日期 → Article；否则 Item。title / image / price / rating / date / tag → 对应属性 | 中：属性存在但名字是推断的 | 商品卡片 → Product.title/image/price/rating/tag |
| 详情页 | h1 → title；正文 → description；价格 / 评分 / Tab 名 / 规格表行首 → 属性 | 中 | 规格表「光源 / 功率 / 色温」→ Product.spec:* |
| 被拦截的写请求 | `network.json[].bodyKeys`（只有键名） | 中：知道字段不知道类型 | `POST /api/orders {receiver, phone, items…}` |
| 互动点 | `interactions.cart` → CartItem(productId, quantity)；`wishlist` → Wishlist(productId) | 低：只知道实体存在 | — |
| 站点类型 | 电商必有 Order / User；内容站必有 Article / Category | 最低：纯推断 | — |

命名：实体用英文单数 PascalCase（Product / Order / Review / User / Address / Category / Article / Post / Comment / Coupon / Subscriber / Message）；属性用 camelCase，来源不同的同义属性合并（`name` 与 `title` 二选一，以 API 字段为准）。

## 2. 关系推断

| 条件 | 关系 | 依据 |
|---|---|---|
| Product 与 Review 同时存在 | Product 1..n Review（Review.productId） | 评价出现在商品详情页 |
| User 与 Review | User 1..n Review（Review.userId / author） | 评论有作者 |
| User 与 Order | User 1..n Order | 下单需要账户（访客下单是变体，标注） |
| Order 与 CartItem | Order 1..n OrderItem（由 CartItem 转化） | 订单包含多个商品行 |
| CartItem / OrderItem 与 Product | n..1 | 商品行指向商品 |
| Wishlist | User n..m Product | 关联表 |
| User 与 Address | 1..n | 地址簿 |
| Product 有 category 属性 | Category 1..n Product | 分类筛选存在 |
| Article | Category 1..n Article；Article n..m Tag（有标签时） | 栏目 / 标签 |

全部标推断。写进 PRD §7 时用 Mermaid `erDiagram`；带 `?` 的属性在表里注明来源为空。

## 3. 角色推断

| 角色 | 实采证据 | 推断证据 |
|---|---|---|
| 访客 | 所有未登录可访问的页面 | — |
| 注册用户 | 密码表单、登录墙、`redirectedToLogin`、头像 / 账户菜单 | 站点有收藏 / 评论 / 下单（需要身份） |
| 付费用户 / 会员 | 文案含 会员 / VIP / Premium / Pro / 企业版；pricing 页 | — |
| 商家 / 卖家 | 文案含 商家 / 卖家 / 店铺 / 供应商 / seller / merchant / vendor；"商家入驻"入口 | 多店铺电商 |
| 创作者 / 作者 | 作者页、"投稿 / 发布"入口、`interactions.upload` | UGC 站 |
| 管理员 | 用户提供了后台 URL 并采到 `admin` 页 | 任何有内容 / 用户 / 订单的站点都需要——永远列出，标推断 |

`roles[].can` 由功能点的 `roles` 字段汇总（功能点默认访客；收藏 / 评论 / 上传 / 通知 / 头像归注册用户；加购同时给访客与注册用户）。

## 4. 流程推断

流程由"页面类型组合 + 功能点存在"触发，步骤对应具体页面（有 `page` 的标实采，没有的标推断）：

| 触发条件 | 流程 | 推断步骤 |
|---|---|---|
| 有登录或注册表单 | 注册 / 登录 | 成功后回跳与 Header 变化 |
| 有 list + detail | 浏览 → 筛选 → 详情 | — |
| 有购物车或加购按钮 | 加购 → 结算 → 下单 → 支付 | 支付与订单状态流转 |
| 有站内搜索 | 搜索 → 结果 → 详情 | 空态 / 加载态 |
| 有评价表单 | 发表评价 | 是否需审核 |
| 有邮件订阅 | 订阅 | 确认邮件 |
| 有联系表单 | 联系 / 留言 | 后台工单 |
| 有收藏 | 收藏 | 个人中心收藏列表 |

模型补全流程时只补"常规产品逻辑必然存在"的步骤（支付回调、成功页），不补原站可能没有的功能（推荐算法、积分）。

## 5. 常见误判与修正

- **API 路径名词不是实体**：`/api/search`、`/api/config`、`/api/init` 等动词 / 配置类路径会生成 Search / Config 实体——删掉，把字段并入相关实体或忽略。
- **`Item` 占位实体**：列表既无价格也无评分也无日期时叫 Item；有 Product / Article 时脚本会丢弃只有 ≤ 2 个属性的 Item；仍出现时按列表标题改名（"精选灯具" → Product，"最新文章" → Article，"三大卖点" → 删除，那是静态内容）。
- **表单字段映射到错实体**：`name` 在联系表单里是"联系人姓名"不是 User.name——按表单意图修正（contact → Message.name）。
- **多语言站点重复实体**：`/en/products` 与 `/products` 产生同一实体两次——按路径去语言前缀合并。
- **响应包了一层**：`{code, data: {list: [...]}}` 的 `responseShape` 顶层是 code / data，实体字段在 `data.list.item` 里；`shape_of` 递归两层通常能看到，看不到就读 `responseSample`。
- **GraphQL**：所有请求都是 `POST /graphql` 且默认被拦截——只能从 `bodyKeys`（query / variables / operationName）知道有 GraphQL；实体只能靠 DOM。告诉用户开 `--allow-writes`（GraphQL 查询是只读的 POST）仅当他确认站点自有。
