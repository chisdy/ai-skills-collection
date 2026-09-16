# 从网络记录读出 API 与数据结构

`crawl_features.py` 用 Playwright 的 `page.route` + `page.on("response")` 记录每页加载与只读探测期间的请求，落到 `features/network.json`。这里说明各字段的含义、怎么从中读出 API 清单与实体，以及拦截机制。

## 1. `network.json` 结构

```json
{
  "allowWrites": false, "blocked": 1, "count": 15,
  "entries": [{
    "page": "http://…/products.html", "trigger": "load | tab | sort | filter | pagination | load-more | self-test",
    "method": "GET", "url": "…", "host": "…", "path": "/api/products.json", "queryKeys": ["category", "page"],
    "resourceType": "fetch | xhr | document", "sameSite": true, "status": 200, "blocked": false,
    "bodyKeys": null, "bodySample": null,
    "contentType": "application/json", "responseBytes": 2048,
    "responseShape": {"__array__": 8, "item": {"id": "int", "name": "str", "price": "int"}},
    "responseSample": {"id": 1, "name": "…"}
  }]
}
```

- **只记录 API 类请求**：`resourceType` 为 xhr / fetch / document，或 URL 含 `.json` / `/api/` / `/graphql` / `/v1/`。图片、CSS、字体不记。
- **`trigger`**：`load` = 页面加载与滚动期间；其他 = 哪个只读探测动作触发的（能把"排序下拉 → 哪个接口"对上）；`self-test` = 拦截器自检发出的假 POST，分析时忽略。
- **`responseShape`**：JSON 顶层形状递归两层——对象给键与值类型，数组给长度与首项形状。这是实体属性最可靠的来源。
- **`responseSample`**：首项 / 顶层对象的前 20 个键，字符串截到 200 字，命中敏感键名（password / token / secret / authorization / cookie / session / card / cvv / 身份证）的值替换成 `***`。
- **`bodyKeys` / `bodySample`**：仅非 GET 请求；JSON 体给键名（与脱敏样本），表单编码体给字段名。被拦截的请求也有这两个字段——这是了解写接口的唯一途径。
- **`blocked: true`**：被 `page.route` abort 的请求，`status` 为 null。

## 2. 拦截机制（合规）

默认所有 **非 GET / HEAD / OPTIONS** 请求在浏览器发出前被 abort（`route.abort("blockedbyclient")`），记录为 `blocked`，服务器端不会收到。每次采集开始时脚本会向目标 origin 的 `/__website-clone-probe__` 发一个 POST 做自检，被 abort 才继续，否则报错停止。这意味着：

- 页面加载时的埋点 POST、心跳、A/B 实验上报都会被拦——所以 `network.json` 里可能出现 `blocked` 的统计域名，不是错误
- 有些站点的**读接口也是 POST**（GraphQL、部分国内站的列表接口）——会被拦，页面可能渲染不出列表。此时 `page.json.lists` 为空、`network.json` 有大量 `blocked` 的同域 POST。处理：告诉用户情况；若用户确认站点自有 / 测试环境，`--allow-writes` 重采；否则改走内联浏览器路径（用户自己的浏览会话里正常请求，模型只读 DOM）
- `--allow-writes` 开启时 `summary.json.options.allow_writes = true`，`network.json.allowWrites = true`，`analyze_features.py` 会 WARN

内联浏览器路径没有 `page.route`，所以**只能靠不点写按钮来保证不产生写操作**；`collect/network.js` 用 Performance API 读到的条目没有方法与响应内容（`methodKnown: false`），Playwright MCP 的 `browser_network_requests` 能给方法与状态。

## 3. 从记录到 API 清单

`analyze_features.py` 按 `method + path` 去重聚合到 `features.json.api[]`：`pages`（哪几页发的）、`triggers`、`queryKeys` 合并、`responseShape`、`blocked`。写文档时：

| 现象 | 结论 |
|---|---|
| 同一 path 在 `load` 与 `filter` / `sort` 触发下都出现，`queryKeys` 含 category / sort / page | 服务端筛选排序分页；URL 参数就是接口参数 |
| 探测动作 `urlChanged: true` 但 `requests: 0` | 前端筛选（一次拉全量，本地过滤），URL 用 `replaceState` 同步 |
| 详情页请求 `/api/products/123` 或 `?id=123` | RESTful 详情接口；实体 id 来自路径 |
| `.json` 静态文件 | 原站可能是静态站 / 预渲染，或 fixture；实体字段仍可用 |
| `POST /api/orders` blocked，`bodyKeys: [receiver, phone, items…]` | 写接口，字段名可用于 Order 实体与结算表单校验规则；响应未知 |
| `document` 类型条目 `redirected: true, location: /login` | 该页在登录墙后 |
| 第三方域名（analytics / payment SDK） | 进 `thirdParty`，不进实体 |

分页参数辨识：`page` / `p` / `offset` / `cursor` / `after`；排序：`sort` / `order` / `orderBy`；筛选：其他键。响应里的分页元数据（`total` / `pageSize` / `hasMore` / `nextCursor`）写进 PRD 的分页功能描述。

## 4. 局限

- 只看到页面加载 + 五种只读探测触发的请求；需要登录、需要点击写按钮才发的接口看不到（写按钮对应的接口通常能从表单 `action` 推出）
- 响应体 > 2 MB 的只记字节数，不解析
- WebSocket、SSE、Beacon 不记录
- Service Worker 缓存命中的请求可能不经过 route（Playwright 默认绕过 SW，通常无此问题）
