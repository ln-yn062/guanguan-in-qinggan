# -*- coding: utf-8 -*-
"""把站酷快乐体按站点实际用字裁剪成子集 woff2，自托管到 fonts/。

用法： python scripts/subset_font.py
原理：抓取 index.html 的可见文本 → 带 Chrome UA 请求 Google Fonts 的
      `text=` 子集接口 → 下载 woff2 → 用 fontTools 校验每个用字都在 cmap 里。

说明（Ruling）：装饰符号与 emoji（✦ ✧ ★ ⭐ 🌾 ✉️ 🌊 ⊙ ω …）本就交给
系统 / emoji 字体渲染，不纳入展示字体子集，也不参与 cmap 校验。
"""
import re
import sys
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

from fontTools.ttLib import TTFont

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "index.html"
OUT = ROOT / "fonts" / "zcool-kuaile.subset.woff2"

FAMILY = "ZCOOL+KuaiLe"
CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# 展示字体负责的字符范围；范围外的交给兜底字体
def is_webfont_char(cp):
    return (
        0x20 <= cp <= 0x7E or          # ASCII 可打印
        0xA0 <= cp <= 0xFF or          # Latin-1（含 · ´）
        0x2000 <= cp <= 0x206F or      # 常规标点（— … “ ” ‘ ’ ~）
        0x3000 <= cp <= 0x303F or      # 中日韩标点（。「」、；：）
        0x4E00 <= cp <= 0x9FFF or      # 中日韩统一表意
        0xFF00 <= cp <= 0xFFEF         # 全角字符（；～）
    )


# 明确交给兜底字体、不参与 cmap 校验的少量字符（站酷快乐体无此字形）：
#   ´  只出现在颜文字 (´；ω；`) 里，本就走兜底；
#   ‹ › 是翻页按钮的 UI 字形，按钮用系统字体栈（非展示字体）。
FALLBACK_OK = set("´‹›")


def fetch(url, tries=3, timeout=30):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": CHROME_UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if r.status != 200:
                    last = Exception(f"HTTP {r.status}"); continue
                return r.read()
        except Exception as e:
            last = e
    raise last


def visible_text(html):
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<!--[\s\S]*?-->", " ", html)
    text = re.sub(r"<[^>]+>", " ", html)
    return unescape(text)


def main():
    chars = sorted(set(visible_text(HTML.read_text(encoding="utf-8"))))
    chars = [c for c in chars if not c.isspace()]
    webfont = [c for c in chars if is_webfont_char(ord(c))]
    fallback = [c for c in chars if not is_webfont_char(ord(c))]
    print(f"可见字符 {len(chars)} 个：展示字体 {len(webfont)}，兜底 {len(fallback)}")
    if fallback:
        print("  兜底（emoji/符号）:", "".join(fallback))
    if len(webfont) > 900:
        print(f"FAIL: 展示字体用字 {len(webfont)} > 900，需分批请求", file=sys.stderr)
        sys.exit(1)

    text = "".join(webfont)
    url = ("https://fonts.googleapis.com/css2?family=" + FAMILY
           + "&text=" + urllib.parse.quote(text))
    try:
        css = fetch(url).decode("utf-8")
    except Exception as e:
        print(f"FAIL: 请求子集接口失败: {e}", file=sys.stderr); sys.exit(1)

    m = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css)
    if not m:
        print("FAIL: 返回里没有 gstatic URL\n" + css[:400], file=sys.stderr); sys.exit(1)

    try:
        data = fetch(m.group(1))
    except Exception as e:
        print(f"FAIL: 下载 woff2 失败: {e}", file=sys.stderr); sys.exit(1)
    if data[:4] != b"wOF2":
        print(f"FAIL: 下载的不是 woff2（magic={data[:4]!r}）", file=sys.stderr); sys.exit(1)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(data)
    print(f"写出 {OUT.relative_to(ROOT)}  {len(data)/1024:.1f} KB")

    # 校验：每个展示字体用字都在 cmap 里
    cmap = set(TTFont(OUT).getBestCmap().keys())
    missing = [c for c in webfont if ord(c) not in cmap and c not in FALLBACK_OK]
    fallback_ok = [c for c in webfont if ord(c) not in cmap and c in FALLBACK_OK]
    print(f"字体覆盖 {len(cmap)} 个码位；缺字: {''.join(missing) if missing else 'none'}"
          f"；按设计兜底: {''.join(fallback_ok) if fallback_ok else 'none'}")
    if missing:
        print(f"FAIL: 子集缺少 {len(missing)} 个字符", file=sys.stderr); sys.exit(1)
    if len(data) > 200 * 1024:
        print("FAIL: 字体 > 200KB，异常", file=sys.stderr); sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
