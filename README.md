# 罐罐的大西北旅行

小鼠兔玩偶「罐罐」的青甘旅行日记（2026.9.26 – 2026.10.3），一个纯静态、可翻页的网页（16:9，像 PPT 一样带转场动效）。

- **纯静态**：无后端、无构建、无外部 CDN 依赖。样式、脚本全部内联在 `index.html`。
- **翻页**：键盘 `← → / 空格 / Home / End`、点击左右半屏、左右箭头按钮、底部圆点、手机触屏滑动。
- **手机端**：舞台按 16:9 等比缩放、居中铺满屏幕；触屏手机**竖屏时整屏自动旋转为横屏显示**（把手机横过来即正立），横屏时正常显示 —— 不再出现竖屏下舞台跑到屏幕外的情况。
- **转场**：4 种效果按页自动轮换（`slide` 滑动 → `push` 推挤 → `zoom` 缩放 → `wipe` 四色幕布），无需操作，翻页时自然变化。
- **入场动效**：每页的图片与文字逐条错峰登场，效果刻意各不相同 —— 上浮 / 渐显 / 右侧滑入 / 左侧滑入 / 模糊聚焦 / 翻转 / 缩放 / 摇摆 / 倾斜 / 滚动 / 幕布揭开等，由 `data-anim` 控制（`--d` 调延迟）。
- **背景音乐**：进入页面自动尝试播放（`audio/xiaoxingji.mp3`，循环）；左上角 `♪` 按钮可手动暂停 / 播放。浏览器若拦截自动播放，会在你首次点击 / 按键 / 触屏后自动开始。
- **字体**：标题用站酷快乐体，已按站点实际用字**子集化并自托管**（`fonts/`），不依赖 Google Fonts。
- **图片**：`images/` 下的压缩版（最长边 ≤ 2000px、单张 < 500KB），原图不入库。

## 目录

```
index.html                 站点全部内容（HTML + CSS + JS 内联）
images/                    压缩后的照片（mascot.png = 罐罐官方形象）
audio/xiaoxingji.mp3       背景音乐（循环播放，可手动暂停）
fonts/zcool-kuaile.subset.woff2   子集化的站酷快乐体
scripts/optimize_images.py 把根目录原始照片压缩输出到 images/
scripts/subset_font.py     按 index.html 用字重新生成字体子集
scripts/verify.py          端到端验证（Playwright，仅本地用）
docs/superpowers/          设计文档与实现计划（不影响站点）
.nojekyll                  告诉 GitHub Pages 跳过 Jekyll
```

## 本地预览

直接双击 `index.html` 用浏览器打开即可（无需服务器）。

## 发布到 GitHub Pages

1. 在 GitHub 网页上新建一个**空**仓库（不要勾选 README）。
2. 在本目录执行：

   ```bash
   git remote add origin https://github.com/<你的用户名>/<仓库名>.git
   git push -u origin main
   ```

3. 仓库 **Settings → Pages → Source** 选 **`main` 分支 / 根目录（/root）**，保存。
4. 稍等片刻，访问 `https://<你的用户名>.github.io/<仓库名>/`。

## 改了文案怎么办

站酷快乐体是按 `index.html` 里出现的字做的子集。**只要改了页面上的中文文案，就要重新生成字体**，否则新字会掉回系统字体：

```bash
python scripts/subset_font.py     # 重新生成 fonts/zcool-kuaile.subset.woff2
python scripts/verify.py          # 验证（需要 playwright：pip install playwright && playwright install chromium）
```

## 重新压缩图片

把新的原始照片放到仓库根目录后，改 `scripts/optimize_images.py` 里的 `MAP`，再运行：

```bash
python scripts/optimize_images.py
```

## 换背景音乐

直接替换 `audio/xiaoxingji.mp3`（保持文件名），或在 `index.html` 里改 `<audio id="bgm-audio">` 的 `src` 即可。注意音乐版权，公开部署请使用有权使用的音频。
