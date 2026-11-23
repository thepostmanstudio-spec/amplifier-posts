"""Amplifier single-post formats. Usage: python3 formats.py posts.json out_dir
Each post: {"type": campaign|ranking|origin|tweet|didyouknow, "slug": ..., ...}
Optional "image": path/URL to a photo for campaign/origin (else a graphic is drawn).
"""
import json, sys, html, asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from render import BASE_CSS, fmt, bars, BG

CAT = {  # category colour coding
    "campaign":   ("#FFD600", "CAMPAIGN"),
    "ranking":    ("#2EE6A6", "RANKINGS"),
    "origin":     ("#FF8A00", "BRAND ORIGINS"),
    "didyouknow": ("#3DA9FC", "DID YOU KNOW?"),
    "news":       ("#FF3B30", "BUSINESS NEWS"),
    "tweet":      ("#FFD600", ""),
}

def shell(body, accent, extra=""):
    css = BASE_CSS + f"""
    .hl{{color:{accent}}} .bars i{{background:{accent}}}
    body{{background:{BG} radial-gradient(circle at 85% 0%, {accent}22 0%, transparent 45%)}}
    .grain{{position:absolute;inset:0;opacity:.06;background-image:radial-gradient(#fff 1px,transparent 1px);background-size:6px 6px}}
    .top{{position:absolute;top:56px;left:72px;right:72px;display:flex;justify-content:space-between;align-items:center}}
    .ctag{{background:{accent};color:#000;font-weight:800;font-size:24px;letter-spacing:3px;padding:10px 20px}}
    .handle{{position:absolute;right:72px;bottom:66px;font-size:24px;font-weight:700;color:#777;letter-spacing:1px}}
    h1{{font-family:Anton;text-transform:uppercase;line-height:1.05;letter-spacing:.5px}}
    """ + extra
    return f"<html><head><style>{css}</style></head><body><div class='grain'></div>{body}</body></html>"

def visual(p, accent, top, h):
    if p.get("image"):
        return (f"<div style='position:absolute;left:72px;right:72px;top:{top}px;height:{h}px;"
                f"background:url(\"{p['image']}\") center/cover;border:4px solid {accent}'></div>")
    v = p.get("visual", {})
    return f"""<div style="position:absolute;left:72px;right:72px;top:{top}px;height:{h}px;
      background:linear-gradient(135deg,{v.get('c1','#1d1d1d')},{v.get('c2','#000')});
      display:flex;align-items:center;justify-content:center;overflow:hidden;border:4px solid {accent}">
      <div style="position:absolute;right:-60px;bottom:-60px;width:380px;height:380px;border-radius:50%;border:40px solid {accent};opacity:.25"></div>
      <div style="font-family:Anton;font-size:{v.get('size',150)}px;color:#fff;text-align:center;line-height:1;
        text-shadow:0 8px 30px #0008">{fmt(v.get('text','')).replace('&lt;br&gt;','<br>')}</div></div>"""

def campaign(p, a):
    lab = CAT["campaign"][1]
    b = f"""<div class="top"><span class="ctag">{lab}</span></div>
    <h1 style="position:absolute;top:150px;left:72px;right:72px;font-size:82px">{fmt(p['headline'])}</h1>
    {visual(p, a, 560, 590)}
    {f'<div style="position:absolute;left:100px;top:1090px;background:#fff;color:#000;font-weight:800;font-size:30px;padding:12px 26px;border-radius:40px">{html.escape(p["brand"])}</div>' if p.get('brand') else ''}
    {brandbar()}<div class="handle">@amplifier.news</div>"""
    return shell(b, a)

def origin(p, a):
    b = f"""<div class="top"><span class="ctag">{CAT['origin'][1]}</span></div>
    <h1 style="position:absolute;top:150px;left:72px;right:72px;font-size:88px">{fmt(p['headline'])}</h1>
    {visual(p, a, 600, 470)}
    <div style="position:absolute;left:72px;top:1105px;font-size:34px;font-weight:700;color:{a}">{html.escape(p.get('teaser',''))} →</div>
    {brandbar()}<div class="handle">@amplifier.news</div>"""
    return shell(b, a)

def ranking(p, a):
    rows = "".join(f"""<div class="r"><span class="n">{k}</span><span class="nm">{html.escape(r[0])}</span>
       <span class="v">{html.escape(str(r[1]))}</span></div>""" for k, r in enumerate(p["rows"], 1))
    css = f"""
    .tbl{{position:absolute;top:{400 if len(p["title"])>34 else 340}px;left:72px;right:72px}}
    .hd{{display:flex;font-size:22px;font-weight:800;letter-spacing:3px;color:#888;padding:0 0 14px;border-bottom:3px solid {a}}}
    .r{{display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #2a2a2a;font-size:38px}}
    .r:nth-child(2) .n{{background:{a};color:#000}}
    .n{{width:54px;height:54px;border-radius:50%;background:#1e1e1e;display:flex;align-items:center;justify-content:center;font-family:Anton;font-size:30px;margin-right:28px}}
    .nm{{flex:1;font-weight:700}} .v{{font-family:Anton;font-size:44px;color:{a}}}
    .hd .c1{{width:90px}} .hd .c2{{flex:1}}
    """
    b = f"""<div class="top"><span class="ctag">{CAT['ranking'][1]}</span></div>
    <h1 style="position:absolute;top:150px;left:72px;right:72px;font-size:76px">{fmt(p['title'])}</h1>
    <div class="tbl"><div class="hd"><span class="c1">#</span><span class="c2">{html.escape(p['cols'][0])}</span><span>{html.escape(p['cols'][1])}</span></div>{rows}</div>
    <div style="position:absolute;left:72px;bottom:130px;font-size:22px;color:#777">Source: {html.escape(p['source'])}</div>
    {brandbar()}<div class="handle">Save this 🔖</div>"""
    return shell(b, a, css)

def tweet(p, a):
    b = f"""<div style="position:absolute;left:90px;right:90px;top:50%;transform:translateY(-55%);
      background:#fff;color:#0f1419;border-radius:28px;padding:56px 56px 48px;box-shadow:0 30px 80px #000a">
      <div style="display:flex;align-items:center;gap:22px;margin-bottom:32px">
        <div style="width:96px;height:96px;border-radius:50%;background:#000;display:flex;align-items:center;justify-content:center">{bars(1.1)}</div>
        <div><div style="font-weight:800;font-size:36px">{html.escape(p['name'])}</div>
        <div style="font-size:30px;color:#536471">{html.escape(p['handle'])}</div></div></div>
      <div style="font-size:50px;line-height:1.35;font-weight:500;white-space:pre-line">{html.escape(p['text'])}</div></div>
    {brandbar()}<div class="handle">Tag someone 👇</div>"""
    return shell(b, a)

def didyouknow(p, a):
    b = f"""<div class="top"><span class="ctag">{CAT['didyouknow'][1]}</span></div>
    <div style="position:absolute;top:230px;left:60px;right:60px;font-family:Anton;font-size:{p.get('big_size',300)}px;color:{a};line-height:1;text-align:center">{p['big']}</div>
    <h1 style="position:absolute;top:660px;left:72px;right:72px;font-size:74px;text-align:center">{fmt(p['fact'])}</h1>
    <div style="position:absolute;left:72px;right:72px;top:1010px;text-align:center;font-size:34px;color:#bbb;line-height:1.4">{fmt(p.get('sub',''))}</div>
    {brandbar()}<div class="handle">Share with a friend ↗</div>"""
    return shell(b, a)

def brandbar():
    return '<div class="brand">' + bars(1) + '<span class="w">AMPLIFIER</span></div>'

FN = {"campaign": campaign, "origin": origin, "ranking": ranking, "tweet": tweet, "didyouknow": didyouknow}

async def main(src, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    posts = json.loads(Path(src).read_text())
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={"width": 1080, "height": 1350})
        for p in posts:
            a = p.get("accent") or CAT[p["type"]][0]
            await pg.set_content(FN[p["type"]](p, a)); await pg.wait_for_timeout(300)
            f = out / f"{p['slug']}.png"; await pg.screenshot(path=str(f)); print(f)
        await br.close()

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "out"))
