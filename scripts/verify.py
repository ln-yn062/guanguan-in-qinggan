# -*- coding: utf-8 -*-
"""端到端验证 index.html：页数、图片加载、字体、翻页竞态、转场轮换、触屏、音频、截图。

用法： python scripts/verify.py
"""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
URL = "file:///" + str(ROOT / "index.html").replace("\\", "/")
SHOTS = ROOT / "_shots"

FAILS = []


def ok(cond, msg):
    print(("  PASS  " if cond else "  FAIL  ") + msg)
    if not cond:
        FAILS.append(msg)


async def settle(pg, timeout=6000):
    """等一次翻页转场彻底结束：无离场页、幕布收放完毕。

    比固定 sleep 可靠 —— 无论这页用的是 slide/push/zoom/wipe 都能正确等到位。
    """
    await pg.wait_for_function(
        "()=>{const s=document.getElementById('stage');"
        "return !document.querySelector('.slide.leaving')"
        "&& !s.classList.contains('curtain-in') && !s.classList.contains('curtain-out');}",
        timeout=timeout)


async def wait_vis(pg, sel, min_o=0.99, timeout=5000):
    """等某元素入场动画结束（opacity 达到 min_o）。"""
    await pg.wait_for_function(
        "a=>{const e=document.querySelector(a.s);"
        "return !e || parseFloat(getComputedStyle(e).opacity)>=a.m;}",
        arg={"s": sel, "m": min_o}, timeout=timeout)


async def wait_anims(pg, timeout=8000):
    """等当前页所有 data-anim 元素入场动画结束（opacity 到 1）。

    比死等时间可靠 —— 无论这页元素用的是哪种入场动效都能正确等到位。
    """
    await pg.wait_for_function(
        "()=>[...document.querySelectorAll('.slide.active [data-anim]')]"
        ".every(e=>parseFloat(getComputedStyle(e).opacity)>=0.99)", timeout=timeout)


async def main():
    errs = []
    SHOTS.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 900}, has_touch=True)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL)
        await pg.wait_for_timeout(1400)

        print("① 页数")
        n = await pg.eval_on_selector_all(".slide", "els=>els.length")
        ok(n == 10, f".slide 数量 = {n}（应为 10）")

        print("② 图片 / 字体")
        imgs = await pg.eval_on_selector_all(
            ".slide img", "els=>els.map(e=>({s:e.getAttribute('src'), w:e.naturalWidth}))")
        bad = [i["s"] for i in imgs if not i["w"]]
        ok(not bad, f"{len(imgs)} 张图片全部加载" + (f"，未加载: {bad}" if bad else ""))
        font_ok = await pg.evaluate(
            "async()=>{await document.fonts.ready; return document.fonts.check(\"20px 'ZCOOL KuaiLe'\")}")
        ok(bool(font_ok), "展示字体 ZCOOL KuaiLe 已加载生效")

        print("③ 无报错（初始）")
        ok(not errs, f"pageerror / console error = {errs or 'none'}")

        print("④ 翻页竞态：连按 5 次右箭头")
        await pg.keyboard.press("Home"); await settle(pg)
        for _ in range(5):
            await pg.keyboard.press("ArrowRight")
        await settle(pg)
        act = await pg.eval_on_selector_all(".slide.active", "els=>els.length")
        lv = await pg.eval_on_selector_all(".slide.leaving", "els=>els.length")
        ok(act == 1 and lv == 0, f"连按后 active={act}（应 1）、leaving={lv}（应 0）")

        print("④b 逐页按下可达末页")
        await pg.keyboard.press("Home"); await settle(pg)
        for _ in range(9):
            await pg.keyboard.press("ArrowRight"); await settle(pg)
        last = await pg.eval_on_selector_all(".slide.active", "els=>els.map(e=>e.dataset.label)")
        ok(len(last) == 1 and last[0] == "旅程结束", f"末页 active={last}")

        print("⑤ 触屏滑动只前进一页")
        await pg.keyboard.press("Home"); await settle(pg)
        await pg.evaluate("""()=>{
          const el=document.getElementById('stage'); const r=el.getBoundingClientRect();
          const y=r.top+r.height/2;
          const mk=(x)=>new Touch({identifier:1,target:el,clientX:x,clientY:y,pageX:x,pageY:y});
          el.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,changedTouches:[mk(r.left+r.width*0.75)]}));
          el.dispatchEvent(new TouchEvent('touchend',  {bubbles:true,changedTouches:[mk(r.left+r.width*0.25)]}));
        }""")
        await settle(pg)
        sw = await pg.eval_on_selector_all(".slide.active", "els=>els.map(e=>e.dataset.label)")
        ok(len(sw) == 1 and sw[0] == "献词 · 给晨阳", f"swipe 后 active={sw}（应为第 2 页）")

        print("⑥ 逐页截图 + 标题可见性")
        bad_sh = []
        for i in range(10):
            await pg.keyboard.press("Home"); await settle(pg)
            for _ in range(i):
                await pg.keyboard.press("ArrowRight"); await settle(pg)
            await wait_anims(pg)
            label = await pg.eval_on_selector(".slide.active", "e=>e.dataset.label")
            sh = await pg.eval_on_selector_all(
                ".slide.active .shimmer",
                "els=>els.map(e=>({t:e.textContent.trim(), o:parseFloat(getComputedStyle(e).opacity), w:e.getBoundingClientRect().width}))")
            for s in sh:
                if s["o"] < 0.9 or s["w"] < 1:
                    bad_sh.append(f"{label}: {s}")
            await pg.screenshot(path=str(SHOTS / f"{i+1:02d}.png"))
            print(f"  _shots/{i+1:02d}.png  ({label})")
        ok(not bad_sh, "shimmer 标题均可见（opacity/宽度正常）" + (f"，异常: {bad_sh}" if bad_sh else ""))

        print("⑦ 徽章 hover 不消失（wiggle 不得覆盖入场动画的 opacity）")
        await pg.keyboard.press("Home"); await settle(pg)
        await wait_vis(pg, ".slide.active .kicker.wiggle")
        hover_bad = None
        try:
            await pg.hover(".slide.active .kicker.wiggle")
            await pg.wait_for_timeout(300)
            o = await pg.eval_on_selector(
                ".slide.active .kicker.wiggle", "e=>parseFloat(getComputedStyle(e).opacity)")
            if o < 0.9:
                hover_bad = f"opacity={o}"
        except Exception as e:
            hover_bad = str(e)
        ok(hover_bad is None, "hover 后徽章 opacity > 0.9"
           + (f"，异常: {hover_bad}" if hover_bad else ""))

        print("⑧ 装饰动效：float + spin/sway 叠加不得互相覆盖")
        combos = await pg.evaluate("""()=>{
          const names=(sel)=>{const e=document.querySelector(sel);
            return e?getComputedStyle(e).animationName.split(',').map(s=>s.trim()).filter(Boolean):null;};
          return {fs:names('.deco.float-a.spin-slow'), fc:names('.deco.float-c.sway')};
        }""")
        ok(combos["fs"] and len(combos["fs"]) == 2
           and "floatA" in combos["fs"] and "spin" in combos["fs"],
           f"float-a.spin-slow 动画 = {combos['fs']}（应含 floatA + spin）")
        ok(combos["fc"] and len(combos["fc"]) == 2
           and "floatA" in combos["fc"] and "sway" in combos["fc"],
           f"float-c.sway 动画 = {combos['fc']}（应含 floatA + sway）")

        print("⑨ 背景音乐：文件存在 + 元素就绪 + 开关可暂停/播放")
        mp3 = ROOT / "audio" / "xiaoxingji.mp3"
        ok(mp3.exists() and mp3.stat().st_size > 0,
           f"audio/xiaoxingji.mp3 存在（{mp3.stat().st_size/1024/1024:.1f} MB）" if mp3.exists() else "audio/xiaoxingji.mp3 缺失")
        a = await pg.evaluate("""()=>{const el=document.getElementById('bgm-audio');
          return el?{src:el.getAttribute('src'), loop:el.loop, vol:el.volume, tag:el.tagName}:null;}""")
        ok(bool(a) and a["tag"] == "AUDIO" and a["src"] == "audio/xiaoxingji.mp3"
           and a["loop"] is True and 0 < a["vol"] <= 1,
           f"#bgm-audio 就绪：{a}")
        ok(await pg.is_visible("#bgm"), "音乐开关 #bgm 可见")

        await pg.evaluate("()=>document.getElementById('bgm-audio').pause()")
        await pg.wait_for_timeout(120)
        paused_after = await pg.evaluate(
            "()=>{document.getElementById('bgm').click(); return document.getElementById('bgm-audio').paused;}")
        await pg.wait_for_timeout(200)
        st = await pg.evaluate("""()=>({paused:document.getElementById('bgm-audio').paused,
          on:document.getElementById('bgm').classList.contains('on'),
          pressed:document.getElementById('bgm').getAttribute('aria-pressed')})""")
        ok(paused_after is False and st["paused"] is False and st["on"] and st["pressed"] == "true",
           f"点击 → 播放：{st}")

        clicked_pause = await pg.evaluate(
            "()=>{document.getElementById('bgm').click(); return document.getElementById('bgm-audio').paused;}")
        await pg.wait_for_timeout(200)
        st2 = await pg.evaluate("""()=>({paused:document.getElementById('bgm-audio').paused,
          on:document.getElementById('bgm').classList.contains('on'),
          pressed:document.getElementById('bgm').getAttribute('aria-pressed')})""")
        ok(clicked_pause is True and st2["paused"] is True and (not st2["on"]) and st2["pressed"] == "false",
           f"再次点击 → 暂停：{st2}")

        print("⑩ 转场轮换：连续翻页依次用到 4 种 data-fx")
        await pg.keyboard.press("Home"); await settle(pg)
        seq = []
        for _ in range(4):
            await pg.keyboard.press("ArrowRight"); await settle(pg)
            seq.append(await pg.eval_on_selector("#stage", "e=>e.dataset.fx"))
        ok(len(set(seq)) == 4 and set(seq) == {"slide", "push", "zoom", "wipe"},
           f"连续 4 次翻页的转场 = {seq}（应覆盖 slide/push/zoom/wipe）")

        print("⑪ 无彩色线条动效残留")
        n_lines = await pg.eval_on_selector_all("#fxlines, #fxlines *", "els=>els.length")
        ok(n_lines == 0, f"#fxlines 元素数 = {n_lines}（应为 0，线条动效已移除）")

        print("⑫ 入场动效多样性：同页图片各用不同动画")
        await pg.keyboard.press("Home"); await settle(pg)
        for _ in range(2):
            await pg.keyboard.press("ArrowRight"); await settle(pg)   # 到第 3 页（三张图）
        names = await pg.eval_on_selector_all(
            ".slide.active figure, .slide.active .photo, .slide.active .mascot",
            "els=>els.map(e=>getComputedStyle(e).animationName)")
        ok(len(names) >= 3 and len(set(names)) >= 3,
           f"第 3 页图片入场动画 = {names}（应 ≥3 种不同）")

        print("⑬ 翻页时入场动画真的重播（而非载入时只播一次）")
        await pg.keyboard.press("Home"); await settle(pg)
        await pg.keyboard.press("ArrowRight")          # 翻到第 2 页
        await pg.wait_for_timeout(180)                 # 卡在入场动画进行中采样
        fresh = await pg.evaluate("""()=>{
          return [...document.querySelectorAll('.slide.active [data-anim]')]
            .flatMap(e=>[...e.getAnimations()])
            .filter(a=>a.playState==='running' && a.currentTime!=null && a.currentTime<500)
            .length;
        }""")
        await settle(pg)
        ok(fresh > 0,
           f"翻到第 2 页 180ms 时「刚起跑(running,currentTime<500ms)」的入场动画数 = {fresh}"
           f"（应 > 0；为 0 说明动效只在整份文档载入时播过一次，翻页看不到）")

        print("③b 无报错（全程）")
        ok(not errs, f"pageerror / console error = {errs or 'none'}")

        await b.close()

    print()
    if FAILS:
        print(f"FAILED ({len(FAILS)}):")
        for f in FAILS:
            print("  - " + f)
        sys.exit(1)
    print("ALL PASS")


if __name__ == "__main__":
    asyncio.run(main())
