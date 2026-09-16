# 复刻包结构与 site-map.json

## 1. `site-map.json`（`discover_site.py` 产出）

```json
{
  "origin": "https://example.com", "startUrl": "https://example.com/", "generatedAt": "…", "source": "discover_site | discover_site+render | manual",
  "robots": {"fetched": true, "disallow": ["/admin"], "sitemaps": ["https://example.com/sitemap.xml"], "crawlDelay": null},
  "pageTypes": {"landing": 1, "list": 4, "detail": 6, "auth": 1, "checkout": 1, "legal": 2},
  "pages": [{
    "url": "https://example.com/products", "pageId": "products", "type": "list", "title": "全部商品", "h1": "全部商品",
    "depth": 1, "status": 200, "finalUrl": null, "loginWall": false, "inNav": true, "linkText": "商品", "forms": 0, "fromSitemap": false, "renderedLinks": 6
  }],
  "warnings": [], "options": {"maxPages": 30, "maxDepth": 2}, "elapsedSec": 3.2
}
```

- `type`：landing / list / detail / auth / checkout / search / account / legal / form / content / admin（URL 启发式 + 标题 + 表单；子技能采集后会用 DOM 再判一次，以子技能为准）
- `loginWall`：401 / 403、302 到登录页、或页面只剩密码表单
- `inNav`：链接出现在 header / nav 里（主导航页）
- `fromSitemap`：来自 sitemap.xml 而非链接 BFS
- `renderedLinks`：`--render` 时该页渲染后新增的链接数（> 0 说明有 JS 渲染的导航 / 列表）

两个子技能都接受这个文件作为外部页面清单（`crawl_features.py site-map.json` / `capture_site.py site-map.json`）；也接受纯 URL 数组 `{"pages": ["https://…"]}`。手工补链接时最少写 `url`，`type` 缺省按 URL 分类。

## 2. `clone-package/` 逐目录

```
clone-package/
  README.md                      主控写：索引、范围、合规声明、读法、未覆盖、后续建议
  site-map.json                  发现结果（上面的结构）
  docs/                          ← website-clone-functional
    PRD.md                       产品需求文档
    frontend-ia.md               前端功能信息架构
    admin-ia.md                  admin 功能信息架构
  features/                      ← website-clone-functional 采集原始数据
    site-map.json  network.json  summary.json  features.json  features-summary.md  <page-id>/…
  visual/                        ← website-clone-visual
    pages.json                   主控写：本次复刻的页面子集（PRD Must / Should 且非登录墙）
    capture/                     契约目录：blueprint.md、icons-map.json、assets/、<page-id>/…
    src/                         页面代码（静态 / React / Vue 项目）
    compare/                     compare-report.md 与 diff 图
```

子技能实际输出路径以其 SKILL.md 为准；不一致时 README 索引跟着实际路径写。

## 3. `README.md` 模板

```markdown
# {{站点名}} 复刻包

生成：{{日期}} · 主控 website-clone 1.0.0 · 子技能 website-clone-functional {{版本}} / website-clone-visual {{版本}}

## 范围与合规
- 用途：{{学习 / 自有重建 / 已授权 / 竞品分析}}
- 原站：{{origin}}；发现 {{N}} 页（{{类型分布}}），其中 {{M}} 页在登录墙后{{未采 / 已由用户登录后采}}
- robots.txt：{{无限制 / 有 Disallow：… 已跳过}}
- 采集未在原站产生任何写操作（functional 拦截 {{k}} 个写请求；visual 只读）
- 版权：原站图片 {{n}} 张（`visual/capture/assets/manifest.json`）、字体 {{…}}、文案与 Logo 均为原站资产，仅供学习 / 参考，不得直接商用；图标已替换为 {{Lucide}}

## 问卷答案
视口 {{…}} · 技术栈 {{…}} · 图标 {{…}} · 动画 {{…}} · 账号 {{…}} · 后台 {{…}}

## 产物索引
| 产物 | 位置 | 怎么读 |
|---|---|---|
| 站点地图 | `site-map.json` | 页面 / 类型 / 登录墙 |
| PRD | `docs/PRD.md` | 角色 → 旅程 → 功能清单（MoSCoW，实采 / 推断）→ 实体 |
| 前端 IA | `docs/frontend-ia.md` | 站点地图 → 导航 → 路由 → 每页区块与状态 → 流程 |
| admin IA | `docs/admin-ia.md` | {{全推断 / 部分实采}}：角色矩阵 → 模块树 → 每模块列表 / 表单 / 状态 |
| 视觉蓝图 | `visual/capture/blueprint.md` | token → 断点 → 图标映射 → 逐页区块与动画 |
| 页面代码 | `visual/src/` | {{栈}}；`{{pnpm dev / 打开 index.html}}` |
| 像素对比 | `visual/compare/compare-report.md` | ERROR / WARN / INFO；差异 {{x}}% |

## 复刻了哪些页
{{PRD §6 Must / Should 页面列表，标出哪些做了视觉复刻}}

## 未覆盖 / 需确认
- {{PRD §9 假设 + admin IA §5 待确认 + blueprint 未采到的 hover / 交互 + compare 报告 WARN}}

## 接下来
文档与页面代码到此为止。要做成可运行的产品，请另起任务：`fullstack-expert`（选栈、脚手架、前后端接口，可把 `docs/` 与 `visual/src/` 作为输入）或 `master-architect-workflow`（工程化流程）。
```
