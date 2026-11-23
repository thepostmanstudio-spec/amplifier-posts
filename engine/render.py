"""Amplifier post renderer: JSON post data -> 1080x1350 PNG slides (+ logo).
Usage: python3 render.py post.json out_dir [--logo]
"""
import json, sys, html, re, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

Y = "#FFD600"; BG = "#0A0A0A"

BASE_CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1350px;background:{BG};color:#fff;font-family:Montserrat;overflow:hidden;position:relative}}
.hl{{color:{Y}}}
.tag{{display:inline-block;background:{Y};color:#000;font-weight:800;font-size:26px;letter-spacing:3px;padding:12px 22px;text-transform:uppercase}}
.brand{{position:absolute;left:72px;bottom:60px;display:flex;align-items:center;gap:16px}}
.brand .w{{font-family:Anton;font-size:40px;letter-spacing:4px}}
.count{{position:absolute;right:72px;bottom:66px;font-size:26px;font-weight:700;color:#888;letter-spacing:2px}}
.bars{{display:flex;align-items:flex-end;gap:6px}}
.bars i{{display:block;width:9px;background:{Y};border-radius:2px}}
"""

def bars(scale=1.0):
    hs = [14, 26, 40, 30, 50]
    return '<div class="bars">' + "".join(
        f'<i style="height:{h*scale}px;width:{9*scale}px"></i>' for h in hs) + "</div>"

def fmt(text):
    """Escape, then turn *word* into yellow highlight."""
    t = html.escape(text).replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")
    return re.sub(r"\*(.+?)\*", r'<span class="hl">\1</span>', t)

def brand():
    return f'<div class="brand">{bars(1)}<span class="w">AMPLIFIER</span></div>'

def page(body, extra_css=""):
    return f"<html><head><style>{BASE_CSS}{extra_css}</style></head><body>{body}</body></html>"

def cover(p, i, n):
    css = f"""
    .art{{position:absolute;top:0;left:0;right:0;height:760px;overflow:hidden;
      background:radial-gradient(circle at 75% 40%, #2a2400 0%, {BG} 65%)}}
    .ring{{position:absolute;border:3px solid {Y};border-radius:50%;opacity:.0}}
    .big{{position:absolute;right:70px;top:170px;font-family:Anton;font-size:330px;line-height:1;color:{Y};text-align:right}}
    .big small{{display:block;font-family:Montserrat;font-weight:800;font-size:40px;color:#fff;letter-spacing:6px;margin-top:6px}}
    .eq{{position:absolute;left:72px;bottom:60px;display:flex;align-items:flex-end;gap:14px}}
    .eq i{{display:block;width:26px;background:{Y};opacity:.9}}
    .tagw{{position:absolute;top:72px;left:72px}}
    h1{{position:absolute;left:72px;right:72px;top:800px;font-family:Anton;font-size:96px;line-height:1.05;text-transform:uppercase;letter-spacing:1px}}
    .swipe{{position:absolute;right:72px;bottom:66px;font-size:28px;font-weight:800;color:{Y};letter-spacing:2px}}
    """
    eq = "".join(f'<i style="height:{h}px"></i>' for h in
                 [50,110,80,170,130,200,150])
    stat = p.get("stat", {})
    body = f"""
    <div class="art">
      <div class="tagw"><span class="tag">{html.escape(p['category'])}</span></div>
      <div class="big">{html.escape(stat.get('value',''))}<small>{html.escape(stat.get('label',''))}</small></div>
      <div class="eq">{eq}</div>
    </div>
    <h1>{fmt(p['headline'])}</h1>
    {brand()}<div class="swipe">SWIPE →</div>"""
    return page(body, css)

def content(s, i, n):
    css = f"""
    .num{{position:absolute;top:110px;left:72px;font-family:Anton;font-size:200px;color:{Y};line-height:1}}
    h2{{position:absolute;top:360px;left:72px;right:72px;font-family:Anton;font-size:104px;line-height:1.05;text-transform:uppercase}}
    p{{position:absolute;top:700px;left:72px;right:90px;font-size:50px;line-height:1.45;font-weight:500;color:#d8d8d8}}
    p b{{color:#fff;font-weight:800}}
    .rule{{position:absolute;top:650px;left:72px;width:120px;height:8px;background:{Y}}}
    """
    body = f"""<div class="num">{i:02d}</div><h2>{fmt(s['title'])}</h2>
    <div class="rule"></div><div style="position:absolute;right:-40px;top:60px;opacity:.12">{bars(6)}</div><p>{fmt(s['body'])}</p>{brand()}<div class="count">{i}/{n}</div>"""
    return page(body, css)

def cta(p, i, n):
    css = f"""
    body{{background:{Y};color:#000}}
    .k{{position:absolute;top:120px;left:72px;font-weight:800;font-size:32px;letter-spacing:6px}}
    h2{{position:absolute;top:200px;left:72px;right:72px;font-family:Anton;font-size:120px;line-height:1.02;text-transform:uppercase}}
    p{{position:absolute;top:620px;left:72px;right:90px;font-size:50px;line-height:1.45;font-weight:600}}
    .fol{{position:absolute;left:72px;bottom:150px;background:#000;color:{Y};font-family:Anton;font-size:52px;letter-spacing:3px;padding:22px 36px}}
    .brand .w{{color:#000}} .bars i{{background:#000!important}} .count{{color:#000}}
    """
    c = p["cta"]
    body = f"""<div class="k">THE TAKEAWAY</div><h2>{html.escape(c['title'])}</h2>
    <p>{html.escape(c['body'])}</p><div class="fol">FOLLOW @AMPLIFIER.NEWS</div>
    {brand()}<div class="count">{i}/{n}</div>"""
    return page(body, css)

def logo():
    css = f"""
    body{{width:1080px;height:1080px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px}}
    .w{{font-family:Anton;font-size:150px;letter-spacing:10px}}
    .bars{{gap:22px}} .bars i{{width:48px!important;border-radius:6px}}
    """
    hs = [90, 170, 260, 200, 330]
    b = '<div class="bars">' + "".join(f'<i style="height:{h}px"></i>' for h in hs) + "</div>"
    return page(f'{b}<div class="w">AMPLIFIER</div>', css), 1080

async def render(post_path, out, do_logo):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        files = []
        if do_logo:
            h, size = logo()
            await pg.set_viewport_size({"width": 1080, "height": 1080})
            await pg.set_content(h); await pg.wait_for_timeout(300)
            f = out / "amplifier_logo.png"; await pg.screenshot(path=str(f)); files.append(f)
            await pg.set_viewport_size({"width": 1080, "height": 1350})
        if post_path:
            p = json.loads(Path(post_path).read_text())
            n = 2 + len(p["slides"])
            pages = [cover(p, 1, n)] + [content(s, k + 2, n) for k, s in enumerate(p["slides"])] + [cta(p, n, n)]
            for k, h in enumerate(pages, 1):
                await pg.set_content(h); await pg.wait_for_timeout(300)
                f = out / f"{p['slug']}_{k}.png"; await pg.screenshot(path=str(f)); files.append(f)
        await b.close()
    print("\n".join(map(str, files)))

if __name__ == "__main__":
    a = sys.argv[1:]
    do_logo = "--logo" in a; a = [x for x in a if x != "--logo"]
    asyncio.run(render(a[0] if a and a[0] != "-" else None, a[1] if len(a) > 1 else "out", do_logo))
