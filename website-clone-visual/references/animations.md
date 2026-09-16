# 动画与交互态的复刻

## 1. 先分类

从 `animations.json` / `hover.json` / `libs.json` 把动画归到五类，每类实现方式不同：

| 类别 | 在采集里长什么样 | 复刻方案 |
|---|---|---|
| **入场（load）** | `animatedElements` 里 `animationName` 非 none、`iterationCount` 1、`delay` 递增（stagger） | 原样搬 `@keyframes` + `animation`；stagger 用 `--delay` 变量或 `:nth-child` |
| **循环（loop）** | `iterationCount: infinite`（float、pulse、marquee、shimmer） | 原样搬；确认 `prefers-reduced-motion` 下停掉 |
| **滚动显现（scroll reveal）** | `scrollReveal[]` 有条目，`classesAdded` 如 `is-visible` / `aos-animate` / `in-view`；或 `libs` 有 AOS / ScrollReveal / sal | IntersectionObserver 切 class + transition（下面模板）；不引 AOS |
| **hover / focus 态** | `hover.json.changed[]`、`transitionElements` | 写回对应选择器的 `:hover` / `:focus-visible` + `transition` |
| **时间线 / 滚动绑定 / 复杂交互** | `webAnimations` 有大量 `Animation` 且 `libs` 有 GSAP / ScrollTrigger / Motion / Lenis / Three | 决策表见 §3；多数情况下做"观感近似"并告知用户 |

## 2. 参数从哪拿

- 时长 / 曲线 / 延迟：`animatedElements[].duration / timingFunction / delay`、`transitionElements[].duration / timingFunction`。原站 `cubic-bezier(0.22, 1, 0.36, 1)` 之类的曲线做成 `--ease-out` token。
- 关键帧：`keyframes[name][]` 的 `keyText` + `style`，直接转成 CSS。
- 滚动显现的起止状态：`scrollReveal[].before` / `after`（opacity、transform、class）。
- hover 变化：`hover.json.changed[].changes` 的 `[before, after]`；带 `N:tag prop` 前缀的是子元素（如卡片 hover 时图片放大）。
- 触发阈值：采不到，按元素进入视口 15% 触发是常见值。

## 3. 何时引库

| 需求 | 纯 CSS + IO | Motion（framer-motion / motion） | GSAP（+ ScrollTrigger） |
|---|---|---|---|
| 入场 / 滚动显现 / hover | ✅ 首选 | 可 | 过重 |
| stagger 列表 | ✅（`--delay`） | ✅ 更省事 | 可 |
| 布局动画（元素位置变化平滑过渡） | ❌ | ✅ `layout` | ✅ Flip |
| 与滚动进度绑定（parallax、pin、scrub） | 部分（`animation-timeline: scroll()`，浏览器支持看目标） | 有 `useScroll` | ✅ ScrollTrigger 最成熟 |
| SVG 路径描边 / morph | 部分（`stroke-dashoffset`） | 可 | ✅ |
| 复杂时间线编排 | ❌ | 可 | ✅ |
| 平滑滚动（Lenis） | ❌ | ❌ | 另引 Lenis；影响整站手感，先问用户 |
| 3D / WebGL | ❌ | ❌ | Three.js；不在像素复刻范围 |

原则：原站用 GSAP 不代表复刻要用；看**需求**列。React 项目偏 Motion，Vue / 静态偏 GSAP 或纯 CSS。

## 4. 模板

### 滚动显现（所有栈通用）

```css
.reveal { opacity: 0; transform: translateY(24px); transition: opacity 600ms var(--ease-out), transform 600ms var(--ease-out); }
.reveal.is-visible { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) { .reveal { opacity: 1; transform: none; transition: none; } }
```

```js
const io = new IntersectionObserver((entries) => {
  for (const e of entries) if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); }
}, { threshold: 0.15, rootMargin: "0px 0px -10% 0px" });
document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
```

React：封装 `useReveal(ref)` 或 `<Reveal>` 组件；Vue：`v-reveal` 自定义指令。

### 入场 stagger

```css
.fade-up { animation: fadeUp 700ms var(--ease-out) both; animation-delay: var(--delay, 0ms); }
```
HTML 上 `style="--delay: 80ms"`，或 `.list > :nth-child(n) { --delay: calc(n * 80ms) }` 用 `@for` / 手写。

### hover 卡片（含子元素）

```css
.card { transition: transform 250ms var(--ease-out), box-shadow 250ms var(--ease-out); }
.card img { transition: transform 400ms var(--ease-out); }
.card:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); }
.card:hover img { transform: scale(1.04); }
```

### reduced-motion 全局兜底

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }
}
```
（这是唯一允许用 `!important` 的地方。）

## 5. 采不到的东西

- 鼠标跟随、磁性按钮、光标特效：`webAnimations` 里可能有蛛丝马迹，但实现要看 JS；按截图 / 录屏做近似。
- 页面切换过渡（Barba、View Transitions）：单页采集看不到；`libs` 有 Barba 时问用户是否需要。
- 视频背景的播放行为：`assets.json` 里 `video` 条目带 autoplay / loop / muted。
- Lottie：`libs` 有 Lottie 且 `assets` 有 `.json` 动画文件时可下载复用（注意版权）。

## 6. 验收

- 每个 `@keyframes` 都在复刻里出现且参数一致
- `scrollReveal` 里的每个 path 对应元素在复刻里有 reveal 行为
- `hover.json.changed` 前 10 条在复刻里逐条核对
- 开启系统"减少动态效果"后页面仍可用、无空白
- `compare_pages.py` 用 `reduced_motion="reduce"` 与 `animations="disabled"` 截图，动画不影响像素对比——所以像素差异反映的是静态布局，动画要单独人眼过一遍
