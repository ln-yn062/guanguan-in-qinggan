# -*- coding: utf-8 -*-
"""压缩旅行照片到 images/，供 index.html 引用。

用法： python scripts/optimize_images.py
从仓库根运行（脚本用相对路径）。
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images"

# (输出文件, 源文件, 最长边, 是否 PNG)
MAP = [
    ("mascot.png",          "bc7cb84e93bbdc9dc6a68563eb319487.png", 900, True),
    ("d03-shop.jpg",        "17512ea1da9d472716de1f81f2100b81.jpg", 2000, False),
    ("d03-night.jpg",       "14a2cb3b7bbb1b2293e4176252c2fb46.jpg", 2000, False),
    ("d03-nest.jpg",        "f5676fed6fec821a8321806925c3f179 1.jpg", 2000, False),
    ("d04-qinghaihu.jpg",   "102b50ea25193b4182ea3fef14b7127f.jpg", 2000, False),
    ("d04-tv.jpg",          "988f54bbf71c68d232904baddb36adfa.jpg", 2000, False),
    ("d05-xiaochaidan.jpg", "97af0a890881285dc19dfcf268e44bf0.jpg", 2000, False),
    ("d05-chaerhan.jpg",    "067fa39cc239545d4702c80bb9682ff1.jpg", 2000, False),
    ("d06-yadan.jpg",       "cde09798ff84703921c5fae069f82398.jpg", 2000, False),
    ("d06-feicui.jpg",      "258ccd3d7994814734de0ca575515e46.jpg", 2000, False),
    ("d07-heidushan.jpg",   "0cc8390c88e7ed671beb9bda1b8107c0.jpg", 2000, False),
    ("d08-mingsha.jpg",     "e825f2b9551bcd46b1fb94cb5244ef7a.jpg", 2000, False),
    ("d08-flag.jpg",        "bcd85b19780ae3acf833098b18a896e0.jpg", 2000, False),
    ("d09-danxia.jpg",      "9ed561c76fc2cf7cd4f24d5acb35f391.jpg", 2000, False),
]

MAX_BYTES = 500 * 1024


def process(out_name, src_name, max_edge, is_png):
    src = ROOT / src_name
    if not src.exists():
        raise FileNotFoundError(src)
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)          # 纠正手机旋转
    if not is_png:
        im = im.convert("RGB")                 # JPEG 无 alpha
    im.thumbnail((max_edge, max_edge), Image.LANCZOS)
    dst = OUT / out_name
    if is_png:
        im.save(dst, "PNG", optimize=True)
    else:
        im.save(dst, "JPEG", quality=82, optimize=True, progressive=True)
    size = dst.stat().st_size
    w, h = im.size
    print(f"{out_name:24s} {w:4d}x{h:<4d} {size/1024:7.1f} KB  <- {src_name}")
    assert max(w, h) <= max_edge, f"{out_name} 最长边 {max(w,h)} > {max_edge}"
    assert size < MAX_BYTES, f"{out_name} {size/1024:.0f}KB >= 500KB"
    return size


def main():
    OUT.mkdir(exist_ok=True)
    total = 0
    for out_name, src_name, max_edge, is_png in MAP:
        total += process(out_name, src_name, max_edge, is_png)
    print(f"\n共 {len(MAP)} 个文件，images/ 合计 {total/1024/1024:.2f} MB")
    assert total < 6 * 1024 * 1024, "images/ 总体积 >= 6MB"
    print("OK")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)
