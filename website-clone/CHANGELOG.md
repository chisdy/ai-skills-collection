# Changelog

版本号写在 `SKILL.md` 的 `metadata.version`。变更历史与设计决策放这里，不进 `SKILL.md` 正文。

## 1.0.0

首个版本。技能组 `website-clone`（本技能，主控）/ `website-clone-visual` / `website-clone-functional`。

### 为什么主控固定调用两个子技能、不问"范围"

三个技能都能独立触发。如果主控还问"要功能还是要样式"，就和直接用子技能重复了，而且 description 的触发边界会糊掉。所以定义：用主控 = 两者都要；只要其一的用户由 description 直接导向子技能；用户在主控流程中途改口时，主控把任务交给对应子技能并退出。主控的工作因此只剩问卷、发现、委派、汇总。

### 为什么功能先于视觉

PRD 的页面清单与优先级决定哪些页值得像素级复刻——`site-map.json` 里可能有 30 页，Must / Should 的只有 6 页。反过来（先视觉）会浪费采集与复刻时间，也没有依据挑页。

### 为什么缺子技能时"做完发现再停下"而不是立即停或自己做半套

发现步骤只依赖主控自己的脚本，做完它用户装好子技能后能直接从第 2 步继续，不浪费一轮；而"自己做半套"意味着主控要复述子技能的工作流，一旦子技能更新就会漂移——主控只按技能名委派，不引用子技能目录下的任何文件。

### 为什么 `discover_site.py` 仅标准库、`--render` 可选

主控要在没有 Playwright 的环境里也能给出页面清单（内联浏览器路径的用户）；标准库 `urllib` + `html.parser` 够做 sitemap / robots / 链接 BFS / URL 分类。SPA 与 JS 渲染的列表（商品卡片）是标准库的盲区——首页同域链接 < 3 或根容器为空 + module 脚本时 WARN，有 Playwright 的加 `--render` 让每页渲染后再抽链接，没有的用内联浏览器注入 `scripts/collect/links.js`。fixture 验证：不加 `--render` 发现 8 页（无详情页），加 `--render` 发现 12 页（含 4 个 JS 渲染出来的详情页）。

### 故意重复的文件

`scripts/_common.py`、`scripts/collect/links.js` 与两个子技能里的同名文件内容相近但各自独立——`openskills install` 的安装单位是目录，跨目录引用在单独安装时会失效。发现逻辑也有两份：主控的标准库版（这里）与功能子技能的 Playwright 版（`crawl_features.py` 自带 BFS），后者在子技能单独使用时不依赖主控。

### 边界

主控不写 PRD、不写页面代码、不做像素对比、不推进后端 / 全栈开发；用户要继续开发时指向 `fullstack-expert` / `master-architect-workflow`。
