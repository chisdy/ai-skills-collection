---
name: website-clone
description: 完整复刻一个网站——给 URL，先做合规确认与站点发现，再按固定顺序调用 website-clone-functional（产出 PRD、前端功能信息架构、admin 功能信息架构）与 website-clone-visual（采集样式 / 动画 / 图标，按所选技术栈写出页面代码并做像素对比），最后汇总成一个 clone-package/ 复刻包。只要用户说"完整复刻 / 克隆 / 仿这个网站"、"照着这个网站做一个产品"、"clone this site"、"既要它的功能也要它的样式"、"把这个站从功能到页面都还原出来"，都应使用此技能。只要样式请直接用 website-clone-visual；只要功能 / PRD 请直接用 website-clone-functional。
metadata:
  version: "1.0.0"
  author: chisdy
---

# Website Clone（主控）

**分工一句话**：用本技能 = 功能架构 + 视觉复刻都做，不再问"要哪一半"。用户只要其一时，直接用对应子技能：样式 / 动画 / 图标 / 像素级 → `website-clone-visual`；功能 / PRD / 信息架构 / 后台设计 → `website-clone-functional`。用户在本技能流程中途说"只要样式"或"只要功能"，把任务交给对应子技能并结束本技能流程。

本技能自身只做五件事：合规确认、意图问卷、站点发现、按固定顺序委派两个子技能、汇总复刻包。它不重复子技能的工作流，不写 PRD，不写页面代码，不推进后端 / 全栈开发。

## 合规边界（开始前确认）

只服务于：学习 / 练习、重建自己拥有的站点、已获授权的复刻、竞品分析与产品研究。开始前用一句话确认用途（话术见 `references/intake.md`）。硬性规则：

- 不把他人的商业站点复刻后上线冒充或直接商用；交付物中原站的图片、文案、字体、Logo 都标注版权风险，图标换开源图标库
- 采集不在目标站产生写操作（功能子技能默认拦截所有写请求；两个子技能都不提交表单、不点写按钮）
- 登录墙后的内容只在用户持有账号并授权时采集，由用户自己在内联浏览器里登录；不绕过验证码、付费墙、反爬
- `robots.txt` 有 Disallow 且用户不是所有者：`discover_site.py` 会 WARN 并跳过 Disallow 路径，把风险告诉用户由其决定

## 意图问卷（先问再动手；不问"范围"）

一次问完，答案原样传给两个子技能，子技能看到已有答案不重复问：

1. **目标 URL 与页面**：首页 URL；有没有特别要 / 不要的页面？大概规模？
2. **目的**：学习 / 自有重建 / 授权复刻 / 竞品分析（决定合规话术与交付说明）
3. **账号与后台**：能登录吗？有后台 URL 吗？是否自有 / 测试站点（决定子技能能否 `--allow-writes`，默认否）
4. **视口**：默认 1440 / 768 / 390
5. **技术栈与图标 / 动画方案**：静态 HTML/CSS/JS、React 19 + Tailwind v4、Vue 3.5 + Tailwind v4；图标库（默认 Lucide）；动画（默认 CSS + IntersectionObserver）——这是视觉子技能的问题，先问掉省一轮
6. **交付形式**：默认 `clone-package/`（结构见 `references/package-layout.md`）放在当前项目根目录

## 固定流程

```
0 确认子技能可用 → 1 发现 discover_site.py → 2 委派 website-clone-functional → 3 委派 website-clone-visual → 4 汇总 clone-package/README.md
```

### 0. 确认两个子技能都可用

按顺序找：上下文里的 `<available_skills>` → AGENTS.md 的技能表 → `openskills list`。两个都要找到（`website-clone-functional`、`website-clone-visual`）。

- 都在：继续。子技能已在当前上下文加载过的，直接委派，不重复读
- 缺任一个：**仍然做第 1 步**（合规确认 + 发现），然后停下，给出安装命令并说明缺的是哪一半：

  ```bash
  openskills install https://github.com/chisdy/ai-skills-collection/tree/main/website-clone-functional
  openskills install https://github.com/chisdy/ai-skills-collection/tree/main/website-clone-visual
  ```

  不自行复述子技能的工作流，不做半套（没有 functional 就不写 PRD；没有 visual 就不写页面代码）。`site-map.json` 留在 `clone-package/`，装好后从第 2 步继续。

### 1. 站点发现

```bash
python3 scripts/discover_site.py <url> -o clone-package/site-map.json [--max-pages 30 --max-depth 2] [--render]
```

仅标准库：robots.txt（Disallow 与 Sitemap）→ sitemap.xml（含 index）→ 首页与导航链接 BFS → 每页按 URL / 标题 / 表单分类（landing / list / detail / auth / checkout / search / account / legal / form / content）→ 登录墙识别（401 / 403 / 302→login / 只有密码表单）。产出 `site-map.json`（结构见 `references/package-layout.md`）。

看到这两种 WARN 时**不要继续委派**，先换发现方式：

| WARN | 含义 | 处理 |
|---|---|---|
| `spa: 首页只解析到 N 个同域链接…` | 导航靠 JS 渲染（SPA）或列表是 JS 拉的 | 有 Playwright → `--render`（每页渲染后抽链接，能发现 JS 渲染的详情页）；否则内联浏览器 `browser_navigate` 首页 → `Runtime.evaluate` 注入 `scripts/collect/links.js` → 把 `links[].url` 补进 `site-map.json.pages` |
| `只发现 1 页` | 同上或站点确实单页 | 单页站点确认后可继续 |

无 Python 时：内联浏览器打开首页注入 `scripts/collect/links.js`，或 `curl -s <url> | grep -o 'href="[^"]*"'` 手工整理成 `site-map.json`。

发现结果给用户看一眼（页数、类型分布、登录墙页、robots 提示），确认范围后再委派。

### 2. 委派功能子技能

读 `website-clone-functional` 的 `SKILL.md`（`<available_skills>` 给的路径，或 `openskills read website-clone-functional`），按它的流程执行，传入：问卷答案（URL / 账号 / 后台 URL / 自有站点与否 / 站点类型 / 用途）、`clone-package/site-map.json` 作为外部页面清单、输出目录 `clone-package/docs/`。产出：`docs/PRD.md`、`docs/frontend-ia.md`、`docs/admin-ia.md`，以及 `clone-package/features/`（采集原始数据）。

功能先于视觉的原因：PRD 的页面清单与优先级（Must 页面）决定视觉子技能复刻哪些页——不是 `site-map.json` 里的每一页都值得像素级复刻。

### 3. 委派视觉子技能

读 `website-clone-visual` 的 `SKILL.md`，传入：问卷答案（URL / 视口 / 技术栈 / 图标库 / 动画方案 / 登录态）、**页面范围 = PRD §6 页面清单中优先级 Must / Should 且未在登录墙后的页面**（写成 `site-map.json` 子集传给 `capture_site.py`）、输出目录 `clone-package/visual/`。产出：`visual/capture/`（含 `blueprint.md`、`icons-map.json`）、`visual/src/`（页面代码）、`visual/compare/compare-report.md`。

视觉子技能会问栈——第 5 题已问过就直接给它答案。

### 4. 汇总

写 `clone-package/README.md`（模板在 `references/package-layout.md`）：范围与合规声明、问卷答案、`site-map.json` 摘要、三份文档与视觉产物的索引与读法、两个子技能各自的"未覆盖 / 需确认"合并、版权风险清单（来自 `visual/capture/blueprint.md` §6 素材节 + PRD §10）、后续开发建议。

**后续开发建议只写一句**：文档与页面代码到此为止；要继续做成可运行产品，请另起任务用 `fullstack-expert`（选栈与脚手架、前后端接口）或 `master-architect-workflow`（工程化流程）。本技能组不接手后端与全栈开发。

## 复刻包结构

```
clone-package/
  README.md              索引、范围、合规声明、读法、后续建议
  site-map.json          发现结果
  docs/                  PRD.md  frontend-ia.md  admin-ia.md         ← functional
  features/              采集原始数据（features.json 等）              ← functional
  visual/                capture/（blueprint.md、icons-map.json…） src/  compare/   ← visual
```

详见 `references/package-layout.md`。

## 常见情况

- **用户中途说"其实只要样式 / 只要功能"**：停止本流程，把已问到的答案与 `site-map.json` 交给对应子技能，之后不再回到主控汇总（单一子技能的产出就是交付）。
- **三个技能同时被触发**：以本技能为入口；子技能已在上下文中则直接委派，不重复加载。
- **发现只有首页**：见第 1 步表格，先换发现方式。
- **登录墙页很多**：问用户是否愿意自己登录；愿意 → 两个子技能都走内联浏览器路径采登录后页；不愿意 → PRD"未覆盖"与 README 写明。
- **用户要后端 / 数据库 / 部署**：礼貌拒绝并指向 `fullstack-expert` / `master-architect-workflow`；可以把 `docs/` 与 `visual/src/` 作为那些任务的输入。
- **子技能装了但版本不匹配**（SKILL.md 里没有本技能提到的脚本）：按子技能自己的 SKILL.md 走，不按本文档的假设；产物路径以子技能实际输出为准，README 索引跟着改。

## 参考索引

- `references/intake.md`：合规确认话术、问卷措辞、答案如何传给子技能、拒绝 / 缩范围的情形
- `references/package-layout.md`：`site-map.json` 字段、`clone-package/` 逐目录说明、`README.md` 模板
- `scripts/discover_site.py`：站点发现（仅标准库；`--render` 可选 Playwright）
- `scripts/collect/links.js`：内联浏览器路径的链接采集（本技能自己的一份）
