# Lumen fixture 站点

`website-clone` / `website-clone-visual` / `website-clone-functional` 三个技能共享的评测靶站：一个虚构的灯具电商，6 个页面，纯静态。

启动：

```bash
cd evals/website-clone/fixture-site
python3 -m http.server 8765
# 打开 http://localhost:8765/
```

## 页面

| 页面 | 类型 | 用于验证 |
|---|---|---|
| `index.html` | landing | hero、三列 feature grid、`@keyframes` 入场（`.fade-up`）、悬浮动画（`.float`）、IntersectionObserver 滚动显现（`.reveal`）、hover 过渡、内联 SVG 图标、icon-font class（`.fa-solid`）、订阅表单、语言切换、`window.AOS` 库标记 |
| `products.html` | list | 分类单选筛选、价格滑块、搜索、排序、分页、空状态、骨架屏、URL 参数同步 |
| `product.html?id=N` | detail | 图库切换、色板、数量、加入购物车、心愿单（POST）、Tab、评论列表 + 评论表单（POST）、同系列推荐 |
| `login.html` | auth | 登录 / 注册两张表单（POST）、第三方登录按钮、字段校验属性 |
| `checkout.html` | form | 购物车（localStorage）、收货 / 配送 / 支付表单（POST）、订单摘要 sticky |
| `about.html` | legal / contact | 锚点区块、联系表单（POST） |

## 故意设计的陷阱

- 所有表单和写操作都 `fetch` POST 到 `/api/*`；`http.server` 会返回 501。功能采集脚本应把这些请求**拦截并标 `blocked`**，不能真的提交。
- `styles.css` 的 `@font-face` 引用 `assets/fonts/Inter-Variable.woff2`，文件不存在：采集应记录字体 URL，校验应报告 404 / 字体回退。
- `vendor/aos.min.js` 是一个只设置 `window.AOS` 的 stub，用于验证 `libs.js` 能从全局变量识别动画库。
- `.fa-solid` 没有加载真正的 Font Awesome，只有 class：验证 icon-font 识别不依赖字体文件。
- 图片全部是 SVG（文本），不入二进制。

## 数据

`api/products.json`（8 件商品，5 个分类）、`api/reviews.json`（4 条评论）。实体推断应至少得到 Product、Review、CartItem、Order、User。
