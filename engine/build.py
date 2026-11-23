"""Render a day's batch of Amplifier posts.

Usage: python3 engine/build.py posts/YYYY-MM-DD/batch.json
Writes PNGs next to batch.json and prints a manifest (slug -> list of image files).

batch.json is a list of posts. Each post has "type":
  campaign | ranking | origin | tweet | didyouknow   -> single image (see formats.py)
  carousel                                           -> multi-slide (see render.py: cover + slides + cta)
Every post also carries "caption" (Instagram caption with hashtags) and "slug".
"""
import json, sys, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent))
import formats, render


async def main(batch_path):
    batch_path = Path(batch_path)
    out = batch_path.parent
    posts = json.loads(batch_path.read_text())
    manifest = {}
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={"width": 1080, "height": 1350})
        for p in posts:
            if p["type"] == "carousel":
                n = 2 + len(p["slides"])
                pages = ([render.cover(p, 1, n)]
                         + [render.content(s, k + 2, n) for k, s in enumerate(p["slides"])]
                         + [render.cta(p, n, n)])
            else:
                a = p.get("accent") or formats.CAT[p["type"]][0]
                pages = [formats.FN[p["type"]](p, a)]
            files = []
            for k, html in enumerate(pages, 1):
                await pg.set_content(html)
                await pg.wait_for_timeout(300)
                f = out / (f"{p['slug']}_{k}.png" if len(pages) > 1 else f"{p['slug']}.png")
                await pg.screenshot(path=str(f))
                files.append(f.name)
            manifest[p["slug"]] = files
        await br.close()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
