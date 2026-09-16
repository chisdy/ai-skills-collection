# 栈：静态 HTML / CSS / JS

适合：单页或少量页面的展示型站点、落地页、用户只要"能打开看"的复刻、没有构建工具的环境。

## 骨架

```
site/
  index.html  products.html …        每页一个文件，公共 header / footer 内联（或构建期用简单模板拼）
  css/tokens.css                     :root 变量（蓝图 §2）
  css/base.css                       reset、排版、链接、按钮、表单基类
  css/layout.css                     容器、栅格、断点（蓝图 §3）
  css/components.css                 卡片、导航、页脚等区块样式（按蓝图 §7 逐块）
  css/animations.css                 @keyframes、reveal、hover（蓝图 §7 动画）
  js/main.js                         IntersectionObserver、导航折叠、Tab 等交互
  assets/                            从 capture/assets/ 复制过来的图片（版权已标注）
  icons/                             内联或 sprite 的 SVG
```

单文件更省事时（落地页）合并成 `index.html` + `styles.css` + `app.js` 也可以，fixture 站就是这种。

## token 落地

```css
:root {
  --color-bg: #faf7f2; --color-text: #1f1a17; --color-primary: #c8742a; …
  --font-sans: "Inter", "PingFang SC", system-ui, sans-serif;
  --space-3: 16px; --space-4: 24px; --radius-md: 12px; --shadow-md: 0 8px 24px rgb(31 26 23 / .10);
  --ease-out: cubic-bezier(.22,1,.36,1);
}
```
原站有 `:root` 变量就照抄名字与值；没有的按 `references/blueprint.md` 的命名建议。

## 布局

- 容器：`.container { max-width: <sections.json 主内容 rect.w>px; margin-inline: auto; padding-inline: var(--space-5); }`
- 栅格：蓝图说 `grid ×3, gap 24px` → `display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4);`；响应式列数看"其他视口"列
- 断点：桌面优先 `@media (max-width: 1024px) / (max-width: 768px) / (max-width: 480px)` 或按蓝图 §3
- 不写死像素宽，除非原站也是固定宽（`computed.json` 里 `width` 为 px 且 `max-width` none）

## 字体

- 自托管：`@font-face` 照 `tokens.json.fontFaces`，文件从 `capture/assets/` 复制（注意版权），`font-display: swap`
- Google Fonts：`libs.json.fontLinks` 里的 `<link>` 直接用
- 中文字体：一般依赖系统（PingFang / 微软雅黑），不下载

## 交互

- 滚动显现、Tab、折叠导航、轮播（少量用 CSS scroll-snap）都写在 `main.js`，无依赖
- 需要轮播库时用 Swiper CDN（`<link>` + `<script type="module">`），不手写复杂轮播

## 图片

- `<img src width height loading="lazy" alt>` 尺寸来自 `assets.json.rendered` / `natural`
- 背景图 `background-image: url(assets/…)`；`background-size / position` 来自 `assets.json` 对应条目
- 用不到原图时用同尺寸占位（`https://placehold.co/400x300` 或纯色块）并在 README 标注

## 本地运行与校验

```bash
python3 -m http.server 5173 -d site/
/tmp/wc-venv/bin/python scripts/compare_pages.py <原站 URL> http://localhost:5173/index.html -o compare/
```

## 交付物

`site/`、`README.md`（如何打开、素材版权说明、已知差异）、`compare/compare-report.md`。
