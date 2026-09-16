# 校验清单

## 1. 跑 compare

```bash
/tmp/wc-venv/bin/python scripts/compare_pages.py <原站 URL> <本地 URL> -o compare/ [--viewports 1440x900,768x1024,390x844] [--threshold 3] [--section-tolerance 8]
# 多页
/tmp/wc-venv/bin/python scripts/compare_pages.py - - --map pages.json -o compare/
```

`pages.json`：`[{"original": "https://site/", "local": "http://localhost:5173/"}, …]`

产出：`compare/<page>/<w>.original.png`、`<w>.local.png`、`<w>.diff.png`（灰底红差异热力图）、`compare/compare-report.md`、`compare.json`。

## 2. 报告分级怎么处理

| 级别 | 触发 | 处理 |
|---|---|---|
| **ERROR** | 像素差异 > 3%；本地资源 4xx / 5xx（document / css / js / image / font）；`body` 或 `h1` 字体族不同；字体加载失败回退 | 必须修，修完重跑 |
| **WARN** | 像素差异 > 1.5%；区块 boundingBox 偏差 > 8px；区块数不一致；原站区块在本地找不到；次级元素字号 / 字重不同；文档高度差 > 40px | 按热力图定位，逐块修；确认是原站随机内容（轮播 / 推荐位）导致的可在 README 注明后放过 |
| **INFO** | 其余 | 记录 |

## 3. 定位差异

1. 看 `hotBands`（差异最集中的 100px 带）→ 对应 `sections.json` 里哪个区块的 y 范围
2. 打开 `<w>.diff.png`，红色区域就是差异；整块红 = 布局错位 / 缺失，边缘红 = 尺寸差几像素，文字红 = 字体 / 字号 / 行高 / 字间距
3. 页面尺寸不同（报告会说）→ 先修高度：某区块 padding、缺失内容、图片高度
4. 字体回退 → 检查 `@font-face` 路径、`font-display`、字体文件是否复制、Google Fonts `<link>`
5. 区块偏差表：`dy` 累积增大说明上面某块高了；`dw` 说明容器宽或 padding 不对

## 4. 像素之外的人工核对

- [ ] hover 态：`hover.json.changed` 前 10 条逐个悬停核对
- [ ] 滚动显现：`scrollReveal` 元素在滚到时有动画；刷新后首屏元素不闪
- [ ] 入场 / 循环动画：与 `animations.json` 的时长 / 曲线 / 延迟一致
- [ ] 系统开启"减少动态效果"后：页面完整可读，无永久 opacity 0
- [ ] 响应式：三个视口下无横向滚动条、导航折叠行为与原站一致、图片不变形
- [ ] 图标：全部换成所选库；按钮 `aria-label` 保留；Logo 处理方式已告知
- [ ] 键盘：Tab 顺序合理，焦点可见
- [ ] 文案：与 `dom.html` 一致（或用户要求替换）
- [ ] 控制台无报错、无 404
- [ ] Lighthouse（可选）：无障碍 ≥ 90

## 5. 交付前

- [ ] README 写明：如何运行、栈与依赖、素材版权与替换建议、已知差异清单（附 compare 报告链接）、组件 ↔ 蓝图区块对照
- [ ] 不提交 `capture/`、`compare/` 的大文件到用户仓库（加 `.gitignore`），蓝图与报告可以留
- [ ] 若用户接下来要做功能 / 后端：指向 `website-clone-functional`（功能架构）或 `fullstack-expert`（开发），本技能到此为止

## 6. 没有 Python 时

- 内联浏览器对原站和本地各截一张同视口全页图，肉眼并排比
- 两边各执行一次 `collect/sections.js`，比较 `sections[].rect` 与 `layout.columns`
- 本地页用浏览器 DevTools Network 看 4xx；`document.fonts.check("16px Inter")` 看字体
- 结论写进 `compare-report.md`，注明是人工比对与保真度上限
