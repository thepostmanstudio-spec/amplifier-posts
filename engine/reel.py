"""Turn a carousel post (same JSON as render.py) into a 1080x1920 animated Reel (MP4 with synthesised beat + SFX).
Usage: python3 engine/reel.py post.json out.mp4
Audio: add Instagram trending audio when publishing (Metricool audioConfiguration) or mix a licensed track in.
"""
import json, sys, asyncio, subprocess, tempfile, shutil, html
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).parent))
from render import fmt, bars
import re
from sfx import build_track

Y = "#FFD600"; BG = "#0A0A0A"; SCENE = 4.5  # seconds per scene


def page(p):
    slides = p["slides"]
    n = 2 + len(slides)
    total = n * SCENE
    scenes = []
    stat = p.get("stat", {})
    # scene 1: cover
    scenes.append(f"""
      <div class="tag a" style="--d:.2s">{html.escape(p['category'])}</div>
      <div class="big pop" style="--d:.5s">{html.escape(stat.get('value',''))}</div>
      <div class="lab a" style="--d:1.0s">{html.escape(stat.get('label',''))}</div>
      <h1 class="a" style="--d:1.5s">{fmt(p['headline'])}</h1>""")
    for k, s in enumerate(slides, 2):
        scenes.append(f"""
      <div class="num pop" style="--d:.2s">{k:02d}</div>
      <h2 class="a" style="--d:.6s">{fmt(s['title'])}</h2>
      <div class="rule grow" style="--d:1.0s"></div>
      <p class="a" style="--d:1.3s">{fmt(s['body'])}</p>""")
    c = p["cta"]
    scenes.append(f"""
      <div class="k a" style="--d:.2s">THE TAKEAWAY</div>
      <h2 class="a dark" style="--d:.5s">{html.escape(c['title'])}</h2>
      <p class="a dark" style="--d:1.1s">{html.escape(c['body'])}</p>
      <div class="fol pop" style="--d:1.8s">FOLLOW @AMPLIFIER.NEWS</div>""")
    divs = ""
    brand = '<div class="brand">' + bars(1.3) + '<span class="w">AMPLIFIER</span></div>'
    for i, sc in enumerate(scenes):
        bg = Y if i == n - 1 else BG
        divs += (f'<section class="{'last' if i == n - 1 else ''}" style="background:{bg};animation:show {SCENE}s linear {i*SCENE}s forwards">'
                 f'{brand}<div class="inner" style="--o:{i*SCENE}s">{sc}</div></section>')
    css = f"""
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{width:1080px;height:1920px;background:{BG};font-family:Poppins;color:#fff;overflow:hidden;position:relative}}
    section{{position:absolute;inset:0;opacity:0}}
    @keyframes show{{0%{{opacity:1}}99.9%{{opacity:1}}100%{{opacity:0}}}}
    .inner{{position:absolute;left:80px;right:80px;top:330px;bottom:420px;display:flex;flex-direction:column;justify-content:center;gap:34px}}
    .a,.pop,.grow{{opacity:0;animation-fill-mode:both;animation-duration:.6s;animation-timing-function:cubic-bezier(.2,.8,.2,1);
       animation-delay:calc(var(--o) + var(--d))}}
    .a{{animation-name:up}} .pop{{animation-name:pop}} .grow{{animation-name:grow}}
    @keyframes up{{from{{opacity:0;transform:translateY(60px)}}to{{opacity:1;transform:none}}}}
    @keyframes pop{{0%{{opacity:0;transform:scale(.6)}}70%{{opacity:1;transform:scale(1.06)}}100%{{opacity:1;transform:scale(1)}}}}
    @keyframes grow{{from{{opacity:1;width:0}}to{{opacity:1;width:160px}}}}
    .hl{{color:{Y}}}
    .tag{{align-self:flex-start;background:{Y};color:#000;font-weight:700;font-size:34px;letter-spacing:4px;padding:14px 28px;text-transform:uppercase}}
    .big{{font-weight:700;font-size:380px;line-height:.9;color:{Y};letter-spacing:-16px;transform-origin:left}}
    .lab{{font-weight:700;font-size:44px;letter-spacing:6px}}
    h1{{font-weight:700;font-size:96px;line-height:1.12;letter-spacing:-2px}}
    .num{{font-weight:700;font-size:220px;color:{Y};line-height:1;letter-spacing:-8px;transform-origin:left}}
    h2{{font-weight:700;font-size:100px;line-height:1.12;letter-spacing:-2px}}
    .rule{{height:10px;background:{Y}}}
    p{{font-size:52px;line-height:1.5;color:#d8d8d8}} p b{{color:#fff}}
    .dark{{color:#000}} .k{{color:#000;font-weight:700;font-size:38px;letter-spacing:8px}}
    .fol{{align-self:flex-start;background:#000;color:{Y};font-weight:700;font-size:48px;padding:26px 40px;transform-origin:left}}
    .brand{{position:absolute;left:80px;top:150px;display:flex;align-items:flex-end;gap:18px;z-index:5}}
    .brand .w{{font-family:Anton;font-size:52px;letter-spacing:5px;color:#fff}}
    .last .brand .w{{color:#000}} .last .bars i{{background:#000}} .last ~ .prog{{}}
    .bars{{display:flex;align-items:flex-end;gap:7px}} .bars i{{display:block;background:{Y};border-radius:2px}}
    .prog{{position:absolute;left:80px;right:80px;top:100px;height:8px;background:#ffffff33;z-index:5}}
    .prog i{{display:block;height:100%;background:{Y};animation:fill {total}s linear both}}
    @keyframes fill{{from{{width:0}}to{{width:100%}}}}
    """
    events = []
    for i, sc in enumerate(scenes):
        st = i * SCENE
        if i > 0:
            events.append((st - .25, "whoosh"))
        if i == n - 1:
            events.append((st + .15, "riser"))
        for cls, d in re.findall(r'class="([^"]+)" style="--d:([\d.]+)s"', sc):
            kinds = cls.split()
            events.append((st + float(d) + .05, "pop" if "pop" in kinds else "tick"))
    return (f"<html><head><style>{css}</style></head><body>{divs}"
            f"<div class='prog'><i></i></div></body></html>"), total, events


async def main(src, out):
    p = json.loads(Path(src).read_text())
    doc, total, events = page(p)
    tmp = Path(tempfile.mkdtemp())
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        ctx = await br.new_context(viewport={"width": 1080, "height": 1920},
                                   record_video_dir=str(tmp), record_video_size={"width": 1080, "height": 1920})
        pg = await ctx.new_page()
        await pg.set_content(doc.replace("<body>", "<body style='animation-play-state:paused'>"))
        await pg.wait_for_timeout(int(total * 1000) + 600)
        await ctx.close(); await br.close()
    webm = next(tmp.glob("*.webm"))
    wav = tmp / "audio.wav"
    build_track(events, total, str(wav))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.35", "-i", str(webm), "-i", str(wav),
                    "-t", str(total), "-map", "0:v", "-map", "1:a",
                    "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-af", "loudnorm=I=-20:TP=-3:LRA=11", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    shutil.rmtree(tmp)
    print(out)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
