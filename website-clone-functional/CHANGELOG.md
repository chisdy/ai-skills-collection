# Changelog

版本号写在 `SKILL.md` 的 `metadata.version`。变更历史与设计决策放这里，不进 `SKILL.md` 正文。

## 1.0.0

首个版本。技能组 `website-clone`（主控）/ `website-clone-visual` / `website-clone-functional`（本技能）之一，可独立安装与使用。

### 为什么"零写操作"是采集层的硬约束而不是文档里的提醒

功能分析天然想去"试一下"表单和按钮——那正是最容易在别人的站点上留下垃圾数据（测试订单、假评论、订阅垃圾邮箱）的地方。所以把约束做进 `crawl_features.py`：`page.route` 拦截并 abort 所有非 GET / HEAD / OPTIONS 请求，每次采集开头向目标 origin 发一个假 POST 自检，拦不住就直接报错停止；只读探测只碰 Tab / 排序 / 筛选 / 分页 / 加载更多，且发生在拦截生效的前提下。`--allow-writes` 是唯一的后门，打开时打印警告并写进 `summary.json`，`analyze_features.py` 看到会再 WARN 一次。内联浏览器路径没有 route 钩子，只能靠 SKILL.md 与 capture-guide 里的明令，以及"点任何东西前先 snapshot 确认它不是写按钮"。

### 为什么每条输出都带 `basis: 实采 | 推断`

功能文档最大的风险是把猜测写成事实——"后台有评论审核"听起来很合理，但原站可能根本没有。`analyze_features.py` 的每个功能点、属性、角色、流程步骤、admin 模块都带 `sources[]` 与 `basis`，三份模板的每张表都有"依据"必填列；admin IA 在没有后台 URL 时开头就声明全推断。这让读者能一眼区分"原站确实这样"与"支撑这些功能至少需要这样"。

### 为什么自带 BFS 而不依赖主控的 `discover_site.py`

安装单位是目录，用户可能只装本技能。`crawl_features.py` 本来就用 Playwright 渲染页面，顺手用 `collect/links.js` 抽同域链接做 BFS，SPA 也能拿到导航——比主控的标准库爬虫还强。外部 `site-map.json` 仍然接受（主控委派时会传）。

### 为什么 `features.js` 给按钮分 read / write

它是"不点写按钮"这条规则的机器可读形式：`kind: write | submit` 的按钮在探测中一律跳过，文档里也能据此把"加入购物车"（写）与"查看详情"（读）分到不同功能。词表是中英双语正则，Tab 内的按钮强制 read（"用户评价" Tab 含"评价"会误判成写）。

### 为什么列表识别用"同 tag + 同前两个 class 的兄弟 ≥ 3 且占比 ≥ 60%"

比找 `ul/li` 可靠：现代站点的卡片网格多是 `div > div.card`。加面积下限（2000 px²）排除标签云与导航，排除 nav / header / footer 里的容器；字段类型用正则（价格 / 日期 / 评分 / 标题 / 标签）而不是 class 名，因为 class 名在 CSS-in-JS 站点上是随机的。

### 为什么响应只记"形状"

`network.json` 记 `responseShape`（键与类型，递归两层）和一份脱敏截断的样本，不存全量响应：一是体量（列表接口几百 KB × 几十页），二是隐私（用户数据、token）。实体推断只需要键名与类型。

### 为什么写文档前先找已安装的文档技能

本技能的独有价值在采证（拦截写请求的采集、带来源的分析）和推断规则，不在"把 PRD 写得像资深 PM 写的"。用户环境里常有更擅长写需求 / 规格文档的技能（`superpowers` 的 `brainstorming` / `writing-plans`、`doc-coauthoring`、`story-generator` 子代理等），它们的写作质量与交互流程通常比一份静态模板好。所以第 3 步定为：按 `<available_skills>` → AGENTS.md → `openskills list` → 子代理的顺序找文档技能，找到就委派，找不到才用 `assets/templates/` 兜底。委派有三条不变量（输入只有 `features.json` 证据、输出文件名 / 必备节不变、依据列与合规声明不可省），保证换谁写，"实采 / 推断"的纪律和复刻包的索引都不受影响。匹配与预算规则沿用 `implementation-review/references/language-skills.md` 的做法（只在已列出的范围内匹配、不安装、每份文档最多一主一辅），写在 `references/doc-writing.md` §0。

### 为什么 admin IA 从前台反推

绝大多数场景用户拿不到后台。"支撑前台这些功能至少需要什么后台"是可推的、对做产品有用的；三条公式（实体 → CRUD、行为 → 管理与报表、固定模块按站点类型裁剪）写在 `admin-inference.md`，产出全部标推断。用户给了后台 URL 时 `--admin-url` 实采，对应模块改标实采。

### 故意重复的文件

`scripts/_common.py`、`scripts/collect/links.js`、`scripts/collect/_read.js` 与 `website-clone-visual` / `website-clone` 里的同名文件内容相近但**各自独立**——`openskills install` 的安装单位是目录，任何跨目录引用都会在单独安装时失效。改动时按需同步，不做抽取。

### 与其他两个技能的边界

本技能不写页面代码、不做像素对比（那是 visual）；不做合规问卷之外的项目级问询、不汇总复刻包（那是主控）。SKILL.md 自带合规节与最小问卷，是因为它必须能在没有主控的情况下独立跑完；主控委派时传入已问到的答案，本技能看到已有答案不重复问。
