# 功能分类法

`analyze_features.py` 与三份文档模板共用的 12 个模块。归类原则：按**用户目的**分，不按页面分——同一页面（详情页）的"看规格"归内容浏览，"加购"归交易，"写评价"归社交互动。

| 模块 | 收什么 | 典型证据（`page.json` 字段） | 常见误归 |
|---|---|---|---|
| 账户与认证 | 注册、登录、第三方登录、找回密码、登出、登录墙、验证码、双因素 | `forms[].hasPassword`、`auth.links`、`loginWall`、`thirdParty[category=auth/captcha]` | 个人资料编辑 → 个人中心 |
| 内容浏览 | 首页、列表、详情、分页 / 加载更多、Tab、折叠、面包屑、视频、下载、相关推荐 | `pageType`、`lists`、`controls.paginations/tabs/accordions`、`breadcrumb` | 筛选 / 排序 → 搜索与筛选 |
| 搜索与筛选 | 站内搜索、分类 / 属性筛选、范围筛选、排序、对比、搜索建议 | `controls.searches/filters/ranges/sorts` | 分页 → 内容浏览 |
| 交易与支付 | 购物车、加购 / 立即购买、结算、地址、配送、支付方式、优惠码、订单、退款、订阅计划（SaaS 定价） | `interactions.cart/coupon`、`forms[intent=checkout]`、`thirdParty[payment]` | 会员权益展示 → SEO 与营销 |
| 社交与互动 | 评论 / 评价、评分、点赞、收藏 / 心愿单、分享、关注、@ / 私信、UGC 发布 | `interactions.comments/rating/like/wishlist/share/follow` | 评价审核 → admin |
| 通知与消息 | 站内通知、消息中心、邮件 / 短信通知设置、Push | `interactions.notifications` | 邮件订阅（营销）→ SEO 与营销 |
| 个人中心 | 资料、头像、地址簿、我的订单 / 收藏 / 评论、账户安全、注销 | `auth.avatar`、`pageType=account`、`forms[intent=profile]` | 登录 / 注册 → 账户与认证 |
| 国际化与本地化 | 语言切换、货币、时区、地区站 | `i18n.langSwitch/currencies`、`hreflang` | — |
| SEO 与营销 | 结构化数据、OG、邮件订阅、活动 / 专题页、优惠展示、Banner、推荐位、统计 / 广告脚本 | `jsonLd`、`openGraph`、`interactions.newsletter`、`thirdParty[analytics/ads]` | 优惠码输入（交易）→ 交易与支付 |
| 客服与帮助 | FAQ、帮助中心、联系表单、在线客服、地图 / 门店、关于、政策 / 条款 | `pageType=legal`、`interactions.chatWidget/map`、`forms[intent=contact]` | — |
| 内容管理 | 用户侧的发布 / 编辑 / 上传（投稿、发帖、上传作品）——不是后台 | `interactions.upload`、`forms[intent=upload/post]` | 后台 CRUD → admin-ia |
| 系统与基础 | 全局导航、页脚、弹窗 / 抽屉、Toast、404、Cookie 提示、主题切换、无障碍 | `navigation`、`controls.modals` | — |

## 优先级（MoSCoW）默认规则

| 情形 | 默认 |
|---|---|
| 站点类型的核心链路（电商：浏览 → 加购 → 结算；内容：列表 → 详情；SaaS：注册 → 登录 → 核心功能页） | Must |
| 登录 / 注册、全局导航、站内搜索（有搜索框时） | Must |
| 筛选 / 排序 / 分页、评论 / 评分展示、面包屑、帮助页、多语言 | Should |
| 收藏、分享、点赞、订阅、优惠码、对比、视频、地图 | Could |
| 前台没有任何证据、纯靠站点类型推出的 | Could + 推断 |

站点类型判断（`siteType`）：有购物车 / 价格 / 结算 → ecommerce；有 pricing / plan / dashboard → saas；有帖子 / 话题 / 讨论 + 评论 → community；其他 → content。`--site-type` 可强制。

## 识别规则速查（`collect/features.js`）

- **页面类型** `pageType`：先看 URL（admin / auth / checkout / search / account / legal / detail / list），再看 DOM（密码框 → auth；分页控件 → list；`/` → landing；有表单且文字少 → form；否则 content）。URL 命中优先于 DOM。
- **表单意图**：`action` + `name` + `id` + 标题 + 提交按钮文案拼成一串，按 `FORM_INTENTS` 正则匹配（登录 / 注册 / 找回密码 / 订阅 / 联系 / 评论 / 结算 / 搜索 / 资料 / 发布 / 优惠码）。匹配不到 → "表单：<标题>"归系统与基础，Could。
- **按钮读写**：`type=submit` 或表单内无 type 的 button → submit；Tab 内 → read；文案命中写词表（提交 / 保存 / 发布 / 加入 / 下单 / 购买 / 支付 / 评论 / 收藏 / 关注 / 删除…）→ write；命中读词表（查看 / 浏览 / 搜索 / 筛选 / 排序 / 展开 / 更多 / 切换 / 详情 / 下载 / 分享…）→ read；`<a>` → navigate；其余 unknown。**采集时 write / submit 一律不点**。
- **列表**：同一容器下 ≥ 3 个同 tag + 同前两个 class 的子元素，占比 ≥ 60%，单项面积 ≥ 2000px²，不在 nav / header / footer。字段类型按正则：价格（¥ / $ / 元）、日期、评分（★ / x/5 / 分）、标题（h1–h6 或 class 含 title / name）、标签（class 含 tag / badge / label / chip）。
- **筛选组**：可见的 radio / checkbox 按 `name` 分组，排除密码表单与结算 / 注册表单内的。
- **排序**：`<select>` 的 name / label / 选项文本含 sort / order / 排序。
- **登录墙**：不是登录页本身，却只有密码表单、文字 < 1500 字、无列表。`redirectedToLogin`：最终 URL 变成 auth 类。
- **第三方**：脚本 / iframe / 外链域名匹配 12 类（支付 / 统计 / 广告 / 客服 / 地图 / 认证 / CDN / 视频 / 社交 / 搜索 / 表单 / 验证码）。
