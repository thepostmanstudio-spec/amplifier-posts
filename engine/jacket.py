"""News 'jacket' for featuring a creator's video (WITH PERMISSION) as an Amplifier Reel.
Keeps the original video + original audio, adds headline, category tag, creator credit card and branding.
Usage: python3 engine/jacket.py jacket.json input_video.mp4 out.mp4
jacket.json: {"category","headline","creator","handle","platform"}  (put the "about" text in the caption: the bottom ~300px is covered by Instagram UI)
"""
import json, sys, asyncio, subprocess, html
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).parent))
from render import fmt, bars

Y = "#FFD600"
W, H = 1080, 1920
VX, VY, VW, VH = 60, 430, 960, 1000          # video window (contain-fit, blurred fill behind)


def frame_html(j):
    return f"""<html><head><style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{width:{W}px;height:{H}px;background:transparent;font-family:Poppins;color:#fff;position:relative;overflow:hidden}}
    .top{{position:absolute;left:0;right:0;top:0;height:{VY}px;background:#0A0A0A}}
    .bot{{position:absolute;left:0;right:0;top:{VY+VH}px;bottom:0;background:#0A0A0A}}
    .side{{position:absolute;top:{VY}px;height:{VH}px;width:{VX}px;background:#0A0A0A}}
    .win{{position:absolute;left:{VX}px;top:{VY}px;width:{VW}px;height:{VH}px;border:5px solid {Y};border-radius:26px;
          box-shadow:0 0 0 {VX}px #0A0A0A}}
    .brand{{position:absolute;left:72px;top:150px;display:flex;align-items:flex-end;gap:16px}}
    .brand .w{{font-family:Anton;font-size:44px;letter-spacing:4px}}
    .bars{{display:flex;align-items:flex-end;gap:6px}} .bars i{{display:block;background:{Y};border-radius:2px}}
    .tag{{position:absolute;right:72px;top:152px;background:{Y};color:#000;font-weight:700;font-size:26px;letter-spacing:3px;padding:10px 20px;text-transform:uppercase}}
    h1{{position:absolute;left:72px;right:72px;top:240px;font-weight:700;font-size:56px;line-height:1.14;letter-spacing:-1.5px}}
    .hl{{color:{Y}}}
    .card{{position:absolute;left:72px;right:72px;top:{VY+VH+30}px;display:flex;gap:24px;align-items:center}}
    .ic{{width:92px;height:92px;border-radius:50%;background:{Y};color:#000;display:flex;align-items:center;justify-content:center;font-size:46px;flex:none}}
    .lb{{font-size:24px;letter-spacing:3px;color:#999;font-weight:700}}
    .nm{{font-size:44px;font-weight:700;line-height:1.15}}
    .hd{{font-size:30px;color:{Y};font-weight:500}}
    .about{{position:absolute;left:72px;right:72px;top:{VY+VH+160}px;font-size:30px;line-height:1.45;color:#cfcfcf}}
    </style></head><body>
    <div class="top"></div><div class="bot"></div>
    <div class="side" style="left:0"></div><div class="side" style="right:0"></div>
    <div class="win"></div>
    <div class="brand">{bars(1.1)}<span class="w">AMPLIFIER</span></div>
    <div class="tag">{html.escape(j['category'])}</div>
    <h1>{fmt(j['headline'])}</h1>
    <div class="card"><div class="ic">🎬</div><div>
      <div class="lb">CREATED BY</div>
      <div class="nm">{html.escape(j['creator'])}</div>
      <div class="hd">{html.escape(j['handle'])} · {html.escape(j['platform'])}</div></div></div>
    </body></html>"""


async def render_frame(j, png):
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        pg = await b.new_page(viewport={"width": W, "height": H})
        await pg.set_content(frame_html(j)); await pg.wait_for_timeout(300)
        await pg.screenshot(path=png, omit_background=True)
        await b.close()


def compose(png, video, out):
    # blurred fill + contain-fit video inside the window, frame on top, ORIGINAL audio kept untouched
    fc = (f"[0:v]scale={VW}:{VH}:force_original_aspect_ratio=increase,crop={VW}:{VH},boxblur=30:2,eq=brightness=-0.25[bg];"
          f"[0:v]scale={VW}:{VH}:force_original_aspect_ratio=decrease[fg];"
          f"[bg][fg]overlay=(W-w)/2:(H-h)/2[win];"
          f"color=c=0x0A0A0A:s={W}x{H}[base];[base][win]overlay={VX}:{VY}:shortest=1[v1];"
          f"[v1][1:v]overlay=0:0,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-loop", "1", "-i", png,
                    "-filter_complex", fc, "-map", "[v]", "-map", "0:a?", "-r", "30",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)


if __name__ == "__main__":
    j = json.loads(Path(sys.argv[1]).read_text())
    png = str(Path(sys.argv[3]).with_suffix(".frame.png"))
    asyncio.run(render_frame(j, png))
    compose(png, sys.argv[2], sys.argv[3])
    print(sys.argv[3])
