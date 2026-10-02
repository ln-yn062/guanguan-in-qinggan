# 罐罐的大西北旅行 · 静态网页 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把设计文档落成一个纯静态、10 页、可翻页（带转场动效）的 `index.html`，图片压缩、字体子集自托管，可直接推送到 GitHub Pages。

**Architecture:** 单个 `index.html`，HTML/CSS/JS 全部内联，无框架无构建。图片经 Pillow 压缩进 `images/`；中文展示字体经 Google Fonts 子集接口裁剪后自托管进 `fonts/`。翻页逻辑沿用已确认的参考模版 v3（`.slide.active` + 方向感知转场 + 元素错峰入场）。

**Tech Stack:** 原生 HTML/CSS/JS；Python（Pillow、fontTools）；Playwright（仅用于验证，不进产物）。

**Spec:** `docs/superpowers/specs/2026-10-02-guanguan-trip-design.md`

## Global Constraints

- 纯静态：`index.html` + `images/` + `fonts/`，**无运行时构建**、无外部 CDN 依赖。
- 画布固定 **16:9（1280×720）**，窗口等比缩放居中。
- 配色：`#2E9BE6` `#21C4B5` `#6FD16F` `#FFC93C` `#FFB020`，文字 `#1E3C4F`。
- 正文用系统字体栈；**展示字体为站酷快乐体，自托管于 `fonts/`**，禁止引入 Google Fonts 的 `<link>`。
- 文案一律逐字取自 spec §2.3（含献词页、尾页、名字由来卡）；聊天记录文案取自 spec §2.2；景点小标签取自 spec §2.4。
- 保留全部 5 种转场（滑动/推送/推进/揭幕/幕布）；**正式版移除左上角转场切换条**。
- 照片无持续动效；照片周围小星星在切页时弹出闪烁。
- 图片最长边 ≤ 2000px、单张 < 500KB。

## Review Focus

实现后最可能出问题的点，各自在对应任务的测试里被钉住：

1. **字体子集缺字** —— 文案里出现子集外的字会掉回系统字体（肉眼可见的突兀）。测试：子集后校验站点用到的每个字符都在 cmap 里。
2. **横/竖图被裁掉主体** —— `object-fit: cover` 可能把罐罐切出画面。测试：竖图（黑独山、西宁夜景）单独整页截图人工确认。
3. **翻页竞态** —— 快速连按导致动画重叠、旧页残留。测试：连按 5 次右箭头后断言只有 1 个 `.slide.active`。
4. **触屏点击 vs 滑动冲突** —— 手机上滑动会被当成点击翻页。测试：模拟 swipe 后只前进一步。
5. **子集请求字数上限** —— 全站字符一次请求可能超限。测试：请求返回的 woff2 有效且 cmap 覆盖全部字符，否则分块请求。

---

### Task 1: 仓库骨架

**Files:**
- Create: `D:/研究生/我的/aicoding/.gitignore`
- Create: `D:/研究生/我的/aicoding/.nojekyll`
- Create: `D:/研究生/我的/aicoding/images/`（空目录，Task 2 填充）

**Interfaces:**
- Produces: 一个 git 仓库，站点文件将放在仓库根。

- [ ] **Step 1: 初始化 git 仓库**

Run:
```bash
cd "D:/研究生/我的/aicoding" && git init -b main
```

- [ ] **Step 2: 写 `.gitignore`**

只忽略源素材与工具目录，**保留** `images/`、`fonts/`、`index.html`、`docs/`：

```
# Obsidian
.obsidian/
# 原始素材（大图，不入库；站点用 images/ 下的压缩版）
/*.jpg
/*.png
/*.jpeg
# 临时
_shot*.*
_tmp/
```

- [ ] **Step 3: 建空目录与 `.nojekyll`**

```bash
cd "D:/研究生/我的/aicoding" && mkdir -p images fonts scripts && touch .nojekyll
```

- [ ] **Step 4: 提交**

```bash
cd "D:/研究生/我的/aicoding"
git add .gitignore .nojekyll docs
git commit -m "chore: init site repo layout"
```

---

### Task 2: 图片压缩

**Files:**
- Create: `scripts/optimize_images.py`
- Output: `images/*.jpg`、`images/mascot.png`

**Interfaces:**
- Produces: `images/` 下的定名文件，供 `index.html` 引用（文件名即接口）：

| 输出文件 | 源文件 | 说明 |
|---|---|---|
| `images/mascot.png` | `bc7cb84e93bbdc9dc6a68563eb319487.png` | 卡通形象，最长边 900，保留 PNG |
| `images/d03-shop.jpg` | `17512ea1da9d472716de1f81f2100b81.jpg` | 9.26 货架 |
| `images/d03-night.jpg` | `14a2cb3b7bbb1b2293e4176252c2fb46.jpg` | 9.26 西宁夜景(竖) |
| `images/d03-nest.jpg` | `f5676fed6fec821a8321806925c3f179 1.jpg` | 9.26 罐罐的窝 |
| `images/d04-qinghaihu.jpg` | `102b50ea25193b4182ea3fef14b7127f.jpg` | 9.27 青海湖 |
| `images/d04-tv.jpg` | `988f54bbf71c68d232904baddb36adfa.jpg` | 9.27 看电视 |
| `images/d05-xiaochaidan.jpg` | `97af0a890881285dc19dfcf268e44bf0.jpg` | 9.28 小柴旦湖 |
| `images/d05-chaerhan.jpg` | `067fa39cc239545d4702c80bb9682ff1.jpg` | 9.28 察尔汗盐湖 |
| `images/d06-yadan.jpg` | `cde09798ff84703921c5fae069f82398.jpg` | 9.29 水上雅丹 |
| `images/d06-feicui.jpg` | `258ccd3d7994814734de0ca575515e46.jpg` | 9.29 翡翠湖 |
| `images/d07-heidushan.jpg` | `0cc8390c88e7ed671beb9bda1b8107c0.jpg` | 9.30 黑独山(竖) |
| `images/d08-mingsha.jpg` | `e825f2b9551bcd46b1fb94cb5244ef7a.jpg` | 10.1 鸣沙山日落 |
| `images/d08-flag.jpg` | `bcd85b19780ae3acf833098b18a896e0.jpg` | 10.1 国旗 |
| `images/d09-danxia.jpg` | `9ed561c76fc2cf7cd4f24d5acb35f391.jpg` | 10.2 七彩丹霞 |

- [ ] **Step 1: 写脚本（含自检断言）**

`scripts/optimize_images.py`：定义 `MAP`（上表）、`python optimize_images.py` 时用 Pillow 打开 → `ImageOps.exif_transpose`（纠正手机旋转）→ `thumbnail((2000,2000))`（PNG 用 900）→ JPEG 存 `quality=82, optimize=True, progressive=True` → 断言每张输出宽高 ≤ 上限且字节 < 500*1024，任一不满足则非零退出。

- [ ] **Step 2: 运行**

Run: `cd "D:/研究生/我的/aicoding" && python scripts/optimize_images.py`
Expected: 打印 14 个输出文件与其尺寸/大小，退出码 0。

- [ ] **Step 3: 校验**

Run: `cd "D:/研究生/我的/aicoding" && ls -l images/ && du -sh images/`
Expected: 14 个文件俱全，`images/` 总体积 < 6MB。

- [ ] **Step 4: 提交**

```bash
git add scripts/optimize_images.py images
git commit -m "feat: add compressed trip images"
```

---

### Task 3: index.html 骨架 + 视觉/转场系统

**Files:**
- Create: `index.html`

**Interfaces:**
- Produces: `.slide`（含 `.active`/`.leaving`、`data-label`）、`#stage[data-fx]`、`#curtain`(4×`.panel`)、`#fxlines`、`#dots`/`#counter`/`#progress`/`#prev`/`#next`；CSS 元件类 `.photo`/`.polaroid`/`.kicker`/`.card`/`.star`/`.deco`/`data-anim`；供 Task 4 复用。

- [ ] **Step 1: 从 `template.html` 抽取并改造**

以 `template.html` 为基：保留 `#viewport/#stage/.scenery`、全部 CSS（配色变量、元件、`data-anim` 动画、`.star`、5 种 `data-fx` 转场、`#curtain`、`#fxlines`、UI 样式）。**删除**：`#fxbar` 相关 CSS 与 DOM、`<link>` Google Fonts 三行。幻灯片清空为 0 张，`#stage` 内只留 `.scenery` + `#curtain` + `#fxlines`。

- [ ] **Step 2: 改写脚本**

JS 保留 `fit()`、圆点、`playLines()`、`swap()`、`runWipe()`、`go()`、键盘/点击/触屏。**删除** `#fxbar` 的 click 处理与 `updateUI` 里的 `btnNext.animate` 那行。`stage.dataset.fx` 固定为 `"slide"`（HTML 里写死）。

- [ ] **Step 3: 验证能打开且无报错**

Run:
```bash
cd "D:/研究生/我的/aicoding" && python - <<'PY'
import asyncio
from playwright.async_api import async_playwright
async def main():
    errs=[]
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={"width":1440,"height":900})
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
        await pg.goto("file:///D:/研究生/我的/aicoding/index.html"); await pg.wait_for_timeout(800)
        assert await pg.eval_on_selector("#stage","e=>getComputedStyle(e).transform") != "none", "stage 未缩放"
        await b.close()
    print("errors:", errs or "none")
asyncio.run(main())
PY
```
Expected: 打印 `errors: none`，断言通过。

- [ ] **Step 4: 提交**

```bash
git add index.html && git commit -m "feat: site shell with transitions and motion system"
```

---

### Task 4: 10 页内容

**Files:**
- Modify: `index.html`（在 `#stage` 内、`#curtain` 之前插入 10 个 `<section class="slide">`）

**Interfaces:**
- Consumes: Task 2 的 `images/*` 文件名；Task 3 的元件类；spec §2.2/§2.3/§2.4 的文案。
- Produces: 新增元件类 `.chat`/`.chat-row`/`.chat-avatar`/`.chat-bubble`、`.spot-tag`，及每页布局类。

- [ ] **Step 1: 加聊天气泡与景点标签的 CSS**

在 `<style>` 内追加：
- `.chat-row{display:flex;gap:12px;align-items:flex-start}`，头像圆形 `border:3px solid var(--ink)`，气泡白底圆角 + `::after` 尖角；`.chat-avatar` 用 `images/mascot.png` 圆形 `object-fit:cover`。
- 每条气泡 `data-anim="pop"` 并递增 `--d`（实现"逐条发进来"）。
- `.spot-tag`：圆角小标签（`border:3px solid var(--ink)`，`box-shadow:4px 4px 0`），字号 15px，前面带图标 span。

- [ ] **Step 2: 写 10 个 slide**

按 spec §2 表格顺序，每页用 `data-label` 标注；图片用 `<img class="photo-img" src="images/xxx.jpg">` 包在 `.photo` 相框里（`object-fit:cover`）；文案/聊天/标签逐字取自 spec。布局类对应：封面 `.cover`、献词 `.dedication`、9.26 `.three-up`、9.27 `.split`+名字由来 `.card`、9.28 `.dual-chat`（每个子块：`.chat` 在上、`.photo` 在下）、9.29 `.duo`、9.30 `.portrait-hero`、10.1 `.duo`+`.chat`、10.2 `.single-hero`、尾页 `.ending`。

- [ ] **Step 3: 验证页数与图片引用**

Run:
```bash
cd "D:/研究生/我的/aicoding" && python - <<'PY'
import asyncio, os, re
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={"width":1440,"height":900})
        await pg.goto("file:///D:/研究生/我的/aicoding/index.html"); await pg.wait_for_timeout(600)
        n=await pg.eval_on_selector_all(".slide","els=>els.length")
        srcs=await pg.eval_on_selector_all(".slide img","els=>els.map(e=>e.getAttribute('src'))")
        miss=[s for s in srcs if not os.path.exists("D:/研究生/我的/aicoding/"+s)]
        await b.close()
    print("slides:",n); print("missing:", miss or "none")
    assert n==10 and not miss
asyncio.run(main())
PY
```
Expected: `slides: 10`、`missing: none`，退出码 0。

- [ ] **Step 4: 提交**

```bash
git add index.html && git commit -m "feat: add all 10 trip slides with copy, photos, chats and spot tags"
```

---

### Task 5: 字体子集自托管

**Files:**
- Create: `scripts/subset_font.py`
- Output: `fonts/zcool-kuaile.subset.woff2`
- Modify: `index.html`（`<head>` 加 `@font-face`，`h1,h2,.display,.kicker` 的 `font-family` 首选改为 `'ZCOOL KuaiLe'`）

**Interfaces:**
- Consumes: `index.html` 的可见文本。
- Produces: `fonts/zcool-kuaile.subset.woff2`。

- [ ] **Step 1: 写子集脚本**

`scripts/subset_font.py`：用 `re` 剥掉 `<script>`/`<style>`/标签，取出可见文本，收集去重字符（含 UI 里的"转场"等字），拼成 `text=`，带 Chrome UA 请求 `https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&text=<urlencode>`，正则取 woff2 URL，下载存 `fonts/zcool-kuaile.subset.woff2`。**若字符数 > 900 则分批请求并把结果丢弃重来**（本方案优先：一次性请求；若 HTTP 非 200 或返回非 woff2 则报错退出，改为分批）。下载后用 `fontTools.ttLib.TTFont` 校验每个字符都在 `getBestCmap()` 里，缺字则非零退出。

- [ ] **Step 2: 运行**

Run: `cd "D:/研究生/我的/aicoding" && python scripts/subset_font.py`
Expected: 打印字符数、字体字节数、`missing: none`，退出码 0；字体应远小于 200KB。

- [ ] **Step 3: 接线 `@font-face`**

在 `<head>` 内加：
```html
<style>
@font-face{font-family:'ZCOOL KuaiLe';font-style:normal;font-weight:400;font-display:swap;
  src:url('fonts/zcool-kuaile.subset.woff2') format('woff2');}
</style>
```
并把标题/标签的 `font-family:'ZCOOL KuaiLe','Baloo 2',cursive` 调整为以 `'ZCOOL KuaiLe'` 打头、系统字体兜底（移除 `'Baloo 2'`）。

- [ ] **Step 4: 验证无 Google 依赖且字体生效**

Run: `cd "D:/研究生/我的/aicoding" && grep -c "googleapis\|gstatic\|Baloo" index.html; ls -l fonts/`
Expected: `grep` 结果为 `0`；`fonts/` 下有子集 woff2。

- [ ] **Step 5: 提交**

```bash
git add scripts/subset_font.py fonts index.html
git commit -m "feat: self-host subsetted ZCOOL KuaiLe display font"
```

---

### Task 6: 端到端验证

**Files:**
- Create: `scripts/verify.py`

**Interfaces:**
- Consumes: 完整 `index.html`、`images/`、`fonts/`。

- [ ] **Step 1: 写验证脚本**

`scripts/verify.py`（Playwright）：① 断言 10 个 `.slide`；② 全部 `img` 的 `naturalWidth>0`（图片真实加载）；③ 无 `pageerror`/console error；④ **连按 5 次 ArrowRight** 后断言 `.slide.active` 恰为 1 个且是最后一页；⑤ 触屏 swipe 一次只前进 1 页；⑥ 逐页截图到 `_shots/`。

- [ ] **Step 2: 运行**

Run: `cd "D:/研究生/我的/aicoding" && python scripts/verify.py`
Expected: 全部断言通过，打印 `ALL PASS`；`_shots/` 生成 10 张图。

- [ ] **Step 3: 人工看图**

打开 `_shots/` 逐张确认：竖图（d07 黑独山、d03 夜景）罐罐没被裁掉；聊天气泡在对应图上方；景点标签不压主体；无溢出。发现问题回改对应 slide。

- [ ] **Step 4: 提交**

```bash
git add scripts/verify.py && git commit -m "test: end-to-end verification script"
```

---

### Task 7: 部署准备

**Files:**
- Create: `README.md`
- Modify: `.gitignore`（把 `_shots/` 加入）

**Interfaces:**
- Produces: 可直接推送的仓库 + 部署说明。

- [ ] **Step 1: 写 `README.md`**

写明：这是什么、本地怎么看（直接双击 `index.html`）、如何发布到 GitHub Pages（在网页上新建**空**仓库 → `git remote add origin …` → `git push -u origin main` → Settings→Pages→main/root）、以及"改了文案要重跑 `subset_font.py` 否则会缺字"的提醒。

- [ ] **Step 2: 忽略截图目录并提交**

```bash
cd "D:/研究生/我的/aicoding"
printf "_shots/\n" >> .gitignore
git add .gitignore README.md
git commit -m "docs: add README and deploy notes"
```

- [ ] **Step 3: 交给用户完成 GitHub 侧**

打印给你：需要在 GitHub 网页建仓库、把地址给我，我来 `git remote add` + `git push`（本机没装 `gh`，建仓库这步要你在网页操作，或你先装 `gh`）。

---

## Self-Review

- **Spec coverage**：§2 页面结构→Task 4；§2.2/§2.3/§2.4 文案→Task 4；§3.1 字体→Task 5；§3.2 动效/转场→Task 3；§3.3 聊天气泡→Task 4；§4 技术方案→Task 3/5；§5 图片→Task 2；§6 部署→Task 1/7；§7 验收→Task 6。无遗漏。
- **Placeholder scan**：无 TBD；每个 Step 有可执行命令或明确产物。
- **Type/命名一致性**：`images/*` 文件名、`data-fx`、`.slide.active/.leaving`、`#curtain .panel` 在 Task 3/4/6 间一致。
- **Review Focus**：5 条各自落到 Task 5（缺字）、Task 6（裁切/竞态/触屏）、Task 5 Step 1（字数上限）。
