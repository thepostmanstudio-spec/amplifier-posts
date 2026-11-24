# Amplifier — @amplifier.news

India's daily dose of marketing, ads & startup stories. This repo holds the post templates and every day's rendered posts. Images are served publicly from `raw.githubusercontent.com` so Metricool can publish them.

## Layout
- `engine/render.py` — carousel template (cover, numbered slides, yellow takeaway slide)
- `engine/formats.py` — single-image formats: `campaign` (yellow), `ranking` (green), `origin` (orange), `tweet`, `didyouknow` (blue), `quote` (FOUNDER WISDOM quote card: big quote with *yellow* key phrase, initials monogram, name, role, source)
- `engine/reel.py` — turns a carousel post into a 1080x1920 animated Reel (MP4) with sound
- Reel motion identity (from the motion-design skill): **Premium** — signature easing cubic-bezier(0.05,0.7,0.1,1) for entrances, cubic-bezier(0.3,0,1,1) for exits, 0% overshoot, 0.55s entrances, subtle ambient yellow glow drifting behind each scene
- `engine/sfx.py` — synthesised, royalty-free sound. House style: decent and SOFT effects only (gentle whoosh, light pluck, soft chime) — no background beat, no loud or harsh SFX
- `engine/build.py` — renders a day's `batch.json` into PNGs + `manifest.json`
- `engine/samples.json`, `engine/amul.json` — example post data for every format
- `assets/amplifier_logo.png` — profile picture
- `posts/YYYY-MM-DD/` — that day's `batch.json`, PNGs, `manifest.json`

## Daily pipeline
1. Research the day's marketing, advertising, startup and brand stories (Indian first, then global).
2. Write `posts/YYYY-MM-DD/batch.json` — 5 posts, mixing segments.
3. `python3 engine/build.py posts/YYYY-MM-DD/batch.json`
4. Commit and push to `main`.
5. Image URL: `https://raw.githubusercontent.com/thepostmanstudio-spec/amplifier-posts/main/posts/YYYY-MM-DD/<file>.png`
6. Schedule each post in Metricool (blogId 8316520, timezone Asia/Calcutta, Instagram, autoPublish true).

## Text conventions
- Wrap a phrase in `*stars*` to highlight it in the accent colour.
- `<b>bold</b>` is allowed in carousel slide bodies.
- Headlines: max ~12 words. Carousel slide bodies: max ~35 words.
- Fonts needed: Anton, Montserrat (system fonts in the build environment).

## Editorial rules
- Every fact must be confirmed by at least one reliable source (company release, ET/Mint/Business Standard, exchange4media, afaqs, Campaign India, BestMediaInfo, etc.). Skip anything unverifiable.
- No other brands' ad stills, logos or news photos — use graphic visuals or original/AI art.
- Never invent quotes or tweets from real people. Tweet cards are written as @amplifier.news.
- `quote` posts: only real quotes, word-for-word, confirmed in a reliable source (interview, talk, book, shareholder letter, reputable publication) that names where/when it was said — put that in `source`. Skip popular "quotes" that are misattributed or only found on quote sites. No photos of the person; the monogram stands in. Prefer Indian founders/marketers (Shark Tank India judges, D2C founders, ad legends) with a customer, brand or growth lesson. Caption: hook, why it matters for marketers, "Save this 🔖", Source.
- Captions: 1-line hook, 2–3 lines of context, a question or "Save this", 5–8 hashtags, source credit.
