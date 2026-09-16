# 蓝图怎么读、怎么用

`analyze_capture.py` 生成的 `blueprint.md` 是复刻的总纲。这里说明各节的含义、生成规则与使用时的判断。

## 各节

### §1 页面清单
每页一行：目录、URL、标题、区块数、可见元素数、文档高度、采集告警。告警里出现"截断"、"page.hover 降级"、"未安装 Pillow" 时先处理再往下。

### §2 设计 Token
- **`:root` 自定义属性**：原站声明值与解析值（`var()` 嵌套时两者不同）。有这张表就沿用原站命名，别再发明一套。
- **颜色**：权重 = 文字颜色出现次数 + 背景色按面积对数加权 + 边框色。"角色猜测"用亮度与饱和度：亮度 > 0.92 背景、< 0.2 正文、饱和度 < 0.25 灰度，其余前 6 名为主色候选。最终命名（primary / accent / muted / border）要结合截图确认。
- **字体**：计算值里排第一的族就是实际渲染字体；`@font-face` 表给出自托管字体与 src；字体服务链接单独列。原站用商业字体（如 Inter 商用免费但 Playfair 是 OFL，GT / Söhne 等需授权）→ 在交付里注明并给开源替代。
- **字号 / 间距 / gap / 圆角 / 阴影阶梯**：按出现次数。复刻时把出现 ≥ 3 次的值做成 token，1–2 次的看是否为某区块特例。`13.3333px` 之类是浏览器默认（按钮 / 输入框）不是设计值。

### §3 断点
`@media` 条件与规则数。移动优先（`min-width`）或桌面优先（`max-width`）按多数条件决定；Tailwind 类站点这里可能为空，看 `computed.<w>.json` 的差异反推。

### §4 技术栈与动画库
每条带证据。用途是**决定复刻的动画方案与警示**（平滑滚动库、3D、轮播），不是照抄技术栈。

### §5 图标清单
每个唯一图标的类型（inline-svg stroke / fill、icon-font 家族、精灵图、img）、出现次数、尺寸、语义线索（aria-label · title · 所在按钮文字 · href · class）、映射建议（来自 `icons-map.json`）、文件。`needsReview` 的要人工对着 `icons/*.svg` 与裁片挑；Logo 不映射。

### §6 素材清单
`assets/manifest.json` 汇总：下载数量、类型、失败项、字体文件状态。**版权提示是必填交付项**。

### §7 逐页区块
表格字段：

| 字段 | 含义 |
|---|---|
| 类型 | `kindGuess`：header / hero / grid / testimonial / pricing / faq / cta / form / table / footer / nav / content，按 tag、class 关键词与位置猜测 |
| 元素 | tag 与 class（前 40 字） |
| 尺寸@y | 主视口 rect：宽×高 @ 文档 y |
| 布局 | 区块内面积最大的 flex / grid 容器：模式 × 列数、gap、`grid-template-columns` 计算值 |
| padding | 区块自身 padding |
| 背景 | 非透明时给 hex |
| 内容 | 链接 / 按钮 / 图片 / 表单 / 输入 / 列表项 数 |
| 其他视口 | 同一 `path` 在 768 / 390 下的布局与高度 |
| 裁片 | `screenshots/sections/NN-kind.png` |

其后是：**响应式变化**（各视口文档高、隐藏元素、布局变化）、**动画与交互态**（`@keyframes` 帧、transition 分组、滚动显现、Web Animations、reduced-motion、hover 差异）。

### §8 建议的复刻顺序
token → 断点 → 字体 → 图标层 → 逐区块 → 动画 → 校验。

## 多页合并规则

- tokens / 字体 / 库 / 图标：**站点级合并**，同名按频次累加、同 hash 图标合并出现页面
- sections / animations / hover：**按页分节**，不合并
- `icons-map.json` 与 `assets/manifest.json` 都是站点级

## 使用蓝图时的判断

1. 蓝图说"grid ×3, gap 24px"而截图看着是两列——相信蓝图（主视口 1440），截图可能是别的视口；核对 `sections.<w>.json`。
2. 区块表里某一块 `kindGuess` 明显不对——只是标签，不影响数值；实现时按内容命名组件。
3. 一个区块高度在 390 下暴涨——通常是多列变单列 + 图片高度；不是 bug。
4. `computed.json` 查不到某元素——见 SKILL.md 常见误判。
5. 蓝图里没有的东西（弹窗、下拉、hover 才出现的菜单）——需要路径 B 手动触发后补采，蓝图不会凭空生成。

## Token 命名建议

沿用原站变量名 > 通用语义名。通用语义名参考：

```
--color-bg / --color-surface / --color-text / --color-muted / --color-primary / --color-primary-hover / --color-accent / --color-border
--font-sans / --font-serif / --font-mono
--text-xs … --text-5xl（按阶梯映射）
--space-1 … --space-12（4px 基准或原站阶梯）
--radius-sm / -md / -lg / -full
--shadow-sm / -md / -lg
--ease-out / --duration-fast (150–200ms) / --duration-base (250–400ms) / --duration-slow (600–800ms)
```

Tailwind v4 用 `@theme { --color-primary: …; --font-sans: …; --breakpoint-md: 768px; }`，类名自动生成。
