from __future__ import annotations

"""Shared creative-copy + visual quality locks. Colors come from Brand Space only."""

# Neutral fallbacks only when Brand Space has no palette. Never a client brand.
NEUTRAL_BG = "#FFFFFF"
NEUTRAL_HEADLINE = "#1F2937"
NEUTRAL_ACCENT = "#4B5563"
NEUTRAL_BODY = "#374151"
NEUTRAL_CARD = "#F3F4F6"
NEUTRAL_MUTED = "#6B7280"
NEUTRAL_GOLD = "#AE8235"

BRAND_SPACE_PALETTE_LOCK = """
BRAND SPACE COLOUR LOCK (NON-NEGOTIABLE):
Use ONLY the active Brand Space palette (primary, secondary, accent, background, fonts).
Do not invent another brand's colours, logo, mascot, or legal footer.
Headlines: Brand Space primary. Body: Brand Space body/muted. Accents: Brand Space accent.
Background: Brand Space background, full-bleed.
Logo: Brand Space composite top-right ONLY — never draw a fake wordmark or mascot.
"""

ACCENT_COVERAGE_LOCK = """
ACCENT COVERAGE LOCK:
- Brand Space accent must be clearly visible at thumbnail size (dividers, CTA, badges, key stats).
- Headlines and subheadings use Brand Space primary — not the accent colour.
- Body / supporting text uses Brand Space body colour.
"""
ORANGE_COVERAGE_LOCK = ACCENT_COVERAGE_LOCK

LEGAL_FOOTER_HINT = (
    "If Brand Space has a legal footer, reserve bottom ~14% EMPTY on carousel slides "
    "for the Pillow composite. Do NOT invent registration / disclaimer text in the image."
)

NO_LEGAL_STATIC_RULE = (
    "STATIC / INFOGRAPHIC: Do NOT reserve space for a legal disclaimer. "
    "Do NOT bake any registration / legal disclaimer text. "
    "No footer legal strip — use the full canvas for content."
)

# Locked icon DNA — ULTRA-PREMIUM HD 3D, TOPIC-SPECIFIC (not always bonds / FD)
PREMIUM_HD_ICON_LOCK = f"""
PREMIUM HD ICON LOCK (premium sample quality bar):
- Render icons like a top-tier product studio: 4K/HD clarity, razor-sharp edges, zero blur, zero pixel mush.
- Style: premium soft-touch clay + satin plastic + brushed gold metal accents (Octane/Cinema4D product-render look).
- Lighting: professional 3-point studio (key top-left, soft fill, subtle rim light); rich contact shadows on Brand Space BG.
- Materials: visible micro-detail — beveled edges, subtle grain, clean specular highlights, depth-of-field on BG only (icon stays sharp).
- Palette: Brand Space primary + Brand Space accent on icons only. Subtle metallic highlights allowed.
- FORBIDDEN: flat clipart, emoji-style icons, low-poly blocks, fuzzy blobs, plastic toy look, generic AI mush, neon chrome.
- Icons must look EXPENSIVE and CRISP even when small — like Apple/Figma premium 3D illustration packs.
"""

ICON_STYLE_LOCK = f"""
{PREMIUM_HD_ICON_LOCK}
ICON STYLE LOCK (NON-NEGOTIABLE — ULTRA-PREMIUM HD 3D, premium editorial quality):
- ULTRA-PREMIUM HD studio 3D icons: high-resolution, pixel-sharp, rich subsurface detail,
  soft-touch clay / satin materials with controlled specular highlights (premium product render).
- NOT low-poly. NOT flat clipart. NOT cheap toy blobs. NOT washed-out soft mush. NOT neon/chrome AI junk.
- NOT blurry, NOT out-of-focus, NOT low-res — icons must read crisp at 100% zoom.
- Soft keyed studio lighting (top-left key + gentle fill); deep soft contact shadows; clear depth.
- TOPIC LOCK: choose objects from the user's topic ONLY.
  Examples:
  * capital controls / policy -> gate, lock, shield, arrows, document, currency flow
  * trade deficit / imports-exports -> bars, containers, arrows, balance, table markers
  * bonds / fixed income -> bond certificate, coupon slip, wallet, chart, rupee coin
- Do NOT default to FD briefcase, handshake, bond certificate, or bank icons for unrelated topics.
- Palette: Brand Space primary + Brand Space accent only. Subtle metallic highlights allowed.
- SIZE: SMALL–MEDIUM so text/paragraphs stay readable — static/infographic icons ~8–11% of
  card/column; CAROUSEL icons/avatars ~10–12% height. HD premium clay-3D objects
  (wallet, coins, doc, lock, shield) — never giant mushy heroes that crowd out copy.
- Clean metaphors only — no clutter, no random mixed-topic objects.
- NEVER pure black / charcoal backgrounds behind icons — always Brand Space background.
"""

# Shared text + icon quality — oil bar ranking AND infographic explain use SAME family
SAMPLE_VISUAL_DNA = f"""
SAMPLE VISUAL DNA (oil bar + infographic explain — SAME quality bar):
Reference: sample_static_oil_consumption_bars.png + sample_infographic_explain_rbi_plastic_perfect.png
(fallback: sample_infographic_explain_rbi_polymer.png)

COLOURS:
- BG soft Brand Space background
- Headline: bold Brand Space primary. Optional KEY WORD in Brand Space accent
- Supporting line: Brand Space body — clearly smaller than headline
- Section headings / card titles: Brand Space primary
- Body / paragraph lines: Brand Space body — crisp, readable, NOT oversized
- Slogan pill / CTA accents: solid Brand Space accent with white text
- Reasons header + footer bars: solid Brand Space primary with white text

TYPOGRAPHY:
- Clean geometric sans-serif (Inter / Helvetica) — vector-sharp, perfect kerning
- No warped, melted, hand-drawn, or blurry baked text
- Hierarchy: headline > section heading > card title > body (each ~30% smaller)

ICONS (premium HD — match perfect sample glossy 3D quality):
- Clay-3D / glossy plastic studio render: satin materials, Brand Space primary/accent, soft shadows on Brand Space BG
- Section icons SMALL–MEDIUM and sharp at 100% zoom — NOT clipart, NOT emoji, NOT blurry blobs
- Hero cluster top-right for explain: holographic note + coins + shield (perfect sample)
{ICON_STYLE_LOCK}
"""

EXPLAIN_COLOR_VIBRANCY_LOCK = f"""
COLOUR VIBRANCY LOCK (NON-NEGOTIABLE):
Use the exact Brand Space hex values at full saturation. Washed-out / gray / beige is a FAIL.
- Headlines and titles: Brand Space primary hex, flat and fully saturated — not a generic navy.
- Accents, CTA, dividers: Brand Space accent hex — not a generic orange, tan, or gold.
- Icon surfaces: Brand Space primary and accent hexes only.
- Background stays Brand Space background so primary/accent pop.
- Never invent navy, orange, gold, teal, or ice-blue unless that exact hex is in Brand Space.
"""

PARAGRAPH_INSIGHT_LOCK = f"""
FOOTER / INSIGHT BLOCK (PERFECT sample_infographic_explain_rbi_plastic_perfect.png):
- Bottom Brand Space primary full-width bar with WHITE tagline
- Brand Space accent circle + white lightbulb on the LEFT of the footer bar
- Optional compact quote only if blueprint provides one — never a solid cream slab wall of text
- Short paragraph max 2–3 lines; never a wall of tiny text
- Annotation paragraphs may use 1–3 Brand Space accent highlight words instead
"""

CAROUSEL_ICON_LOCK = f"""
{PREMIUM_HD_ICON_LOCK}
CAROUSEL ICON LOCK (NON-NEGOTIABLE — sample PDF avatar/icons):
- ONE premium HD clay-3D illustrated avatar-object per slide (~12–16% canvas height).
- Match sample style: soft-touch wallet, coin stack, bond document, lock+gate, shield, chart, phone.
- Maximum render quality: sharp edges, satin + gold accents, studio-lit, no blur.
- Place bottom-right or mid-right — text story cards own the left/center.
- Never soft blurry low-res clay mush. Never clipart. Never emoji. Never cheap calculator blobs.
- Never omit the icon. Never make it a giant full-width hero.
- If the icon looks cheap, blurry, or toy-like — the slide FAILS.
"""

HEADLINE_COLOR_LOCK = f"""
HEADLINE & TEXT COLOUR LOCK (NON-NEGOTIABLE):
- ALL headlines: Brand Space primary hex ONLY. Never white on light BG. Never a generic navy.
- ALL subheadings / section titles: Brand Space primary hex ONLY.
- Body / supporting text: Brand Space body/muted — never Brand Space accent.
- NO accent underline directly under the main headline title.
- Brand Space accent is REQUIRED for infographic accents:
  left vertical section bars, section dividers, CTA button fill, bullet dots, callout box border.
- Brand Space accent is also for: thin dividers between cards, bar/arrow accents in charts.
- Subtle metallic is ONLY for 3D icon highlights — NEVER replace Brand Space accent.
- NEVER invent navy / orange / gold / teal / ice-blue unless that exact hex is in Brand Space.
- NEVER colour a headline, subheading, body paragraph, or amount in the accent colour.
"""

CAROUSEL_TEXT_FIT_LOCK = """
CAROUSEL TEXT FIT LOCK (NON-NEGOTIABLE — fixes broken/out-of-frame text):
1) Outer safe margin ≥8% on ALL sides. Text never touches crop edges.
2) Keep ALL content ABOVE the bottom legal-footer zone (~14% empty when Brand Space has a footer). Nothing clipped.
3) HEADLINE MUST BE COMPLETE — never truncate mid-word ("o.." / "…"). Wrap to 2 FULL lines instead.
4) Headline stays in LEFT ~75% of width — leave top-right logo pocket empty (do not cut words for logo).
5) No mid-word breaks. No awkward 1–2 word orphan lines. Prefer 2 balanced lines max per card.
6) Each explanation card: max ~14 words — wrap cleanly inside the card with padding ≥12px.
7) Never place text under/through icons. Never let icons overlap text.
8) Prefer 2–3 fully-visible story cards (sample DNA) — drop optional lines before clipping.
"""

CONTENT_DEPTH_LOCK = """
CONTENT DEPTH LOCK (NON-NEGOTIABLE — client quality bar):
Every slide / card / row must contain a REAL concrete insight — not a vague slogan.
FORBIDDEN shallow copy:
  - "Connect the dots" / "Invest wisely" / "Grow your wealth" / "Unlock potential"
  - Any line that could apply to any investment topic without a specific mechanism
  - One-word chips (Selling / Hedging / Pros / Cons) with NO explanation sentence
REQUIRED depth (pick ALL that fit):
  - A specific mechanism explained in plain English (how it works, step by step)
  - A real ₹ / % / USD number from research in a full sentence
  - A concrete "who benefits and when" statement
  - A myth-bust or caveat (penalty, condition, illustrative note)
CAROUSEL BODY: 22–36 words per slide — teach like Sweep-In samples (₹ scenario + mechanism).
Each content card = short label + one clear explanation (8–14 words), not a lone keyword.
NEVER ship a slide with only 1–2 vague lines and empty space — that is NOT sample DNA.
"""

UNIVERSAL_FIT_LOCK = f"""
UNIVERSAL FIT LOCK (NON-NEGOTIABLE — ALL formats + ALL platforms):
Applies to static / carousel / infographic on LinkedIn / Instagram / X (Twitter).
Whatever the content length, EVERYTHING must fit INSIDE the canvas with ZERO clipping.

CANVAS BOUNDARY — ABSOLUTE RULE:
Every single pixel of every element (text, icon, chip, bar, card, CTA, source line, divider)
MUST be 100% inside the canvas rectangle. Nothing may bleed, overflow, or be cropped at any edge.
If content does not fit at normal size, reduce font size or drop optional elements — NEVER clip.

HARD RULES:
1) Outer margins >=6% on ALL sides (top/right/bottom/left). Nothing touches or crosses the crop edge.
2) NO overlapping: text never overlaps icons, icons never overlap text, rows never collide, chips never collide.
3) NO cut-off: headlines, supporting lines, row facts, chip labels, CTA buttons, source lines — fully visible.
4) Prefer LESS content that fits over MORE content that breaks. Drop optional body/CTA before clipping.
5) Keep baked strings SHORT: headline <=10 words, supporting <=14, fact lines <=8 words, chip labels = 1 word.
6) CTA button (if any): COMPACT only — max ~22–28% canvas width, ~3.5–4.5% canvas height,
   short label (2–3 words), modest padding. Never a wide bar or oversized pill.
   Fully inside frame with >=8% empty space below (or omit CTA if crowded).
7) Tables/rankings: equal row heights, full-width dividers, consistent columns; no broken half-lines.
8) Icons: sized to leave clear breathing room around nearby text; never crush labels.
9) Spelling perfect — never invent broken words (technology not tecnlogy; real estate not restate).
10) Background is one continuous field edge-to-edge — no second BG color, no white side panels.
11) Scale down all elements proportionally before allowing any element to touch an edge.
"""

CAROUSEL_FIT_LOCK = f"""
{UNIVERSAL_FIT_LOCK}
{CAROUSEL_TEXT_FIT_LOCK}
{CAROUSEL_ICON_LOCK}
CAROUSEL FIT LOCK — MATCH BRAND SPACE CAROUSEL LAYOUT:
- FULL-BLEED very pale blue Brand Space background. NO white side panels. NO second BG.
- STYLE: wide rounded soft-blue Brand Space card info cards (3D icon left, divider, text right)
  with generous padding — NOT sparse empty slides, NOT quadrant grids, NOT thin Brand Space accent divider stacks.
- STORY FIRST: every slide teaches one beat of the arc with ₹/%/rules — not a slogan + icon.
- ICONS/AVATARS: ONE premium HD clay-3D object (~12–16% height) bottom-right — crisp, not mushy.
- FORBIDDEN: truncated headlines ("o.."), missing headlines, topic title alone, empty Pros/Cons,
  sparse 1–2 line slides with huge empty space.
- MANDATORY: UNIQUE COMPLETE Brand Space primary headline at top-left on EVERY slide (wrap 2 lines if needed).
- NEVER reuse topic name alone ("Capital Controls", "Sweep-in FD") as headline.
- Headlines/subheads: Brand Space primary ONLY. No accent underlines under titles.
{HEADLINE_COLOR_LOCK}
{ORANGE_COVERAGE_LOCK}
- REQUIRED: 3–4 soft-blue story cards/blocks with full short explanations (sample page density).
- Bottom ~14% EMPTY for legal footer (only if Brand Space has one). Nothing clipped. Margins ≥8%.
- Top-right corner: plain empty pale-blue only — NO AI logo, NO "Brand Logo" text, NO dashed box.
- Spelling perfect. Plain printed sans-serif.
"""

# Carousel education — same retail tone as static/infographic ranking (NOT policy-analyst speak)
CAROUSEL_AUDIENCE_TONE_LOCK = """
CAROUSEL TONE LOCK — same voice as static/infographic samples (NON-NEGOTIABLE):
Target = everyday Indian investor on LinkedIn/Instagram — NOT a policy analyst or textbook.

WRITE LIKE THIS (plain, short, human):
  "What if your savings earned FD-like returns?"
  "Let's say you keep ₹2 lakh in your account"
  "Only ₹50,000 is needed for daily expenses"
  "The rest sits idle at low savings interest"
  "Would you try a sweep-in FD?"

NEVER WRITE LIKE THIS (too technical — client rejected):
  Vostro/Nostro, liquidity risk, sector exposure, currency hedge, macro implications,
  regulatory framework, capital account convertibility, LRS without plain English,
  "implications for portfolio allocation", advisor-briefing essays, empty Pros/Cons chips

COPY RULES (every slide):
- Headline: simple question or claim — max 8–10 words, complete (no mid-word cuts)
- supporting_line: ONE short plain sentence with a ₹/% fact or "what it means"
- body + proof_points: teach with a mini ₹ scenario — words a retail investor gets in 3 seconds
- Each story card: bold label + ONE explanation ≤12 plain English words
- CTA: short invite ("Comment below!" / "What would you do?") — never a paragraph button
- India: ₹ and % default; USD only when source is USD (label "USD" — never $ / US $)
- Perfect spelling. No jargon dumps. Depth = real numbers in simple language.
"""

CAROUSEL_CONTENT_DEPTH_LOCK = """
CAROUSEL CONTENT DEPTH (plain language — still teach, never textbook):
- Every slide needs a REAL insight with ₹ / % / a simple rule — not a vague slogan.
- FORBIDDEN shallow: "Invest wisely" / "Unlock potential" / "Connect the dots"
- FORBIDDEN technical: one-word chips (Selling / Hedging / Pros) with NO explanation
- REQUIRED: mini scenario OR comparison OR honest trade-off — in words anyone understands
- body: 18–32 words per slide — shorter sentences, same teaching depth as Sweep-In samples
- Each card = label + one clear line (6–12 words) with ₹/% — NOT a jargon paragraph
- Include ONE honest caveat somewhere (penalty, condition, illustrative note) in plain English
"""

# Infographic EXPLAIN — LOCKED premium LinkedIn paragraph/info DNA
# Ranking / top-N boards stay on ranking_board.py — DO NOT route lists here.
INFOGRAPHIC_EXPLAIN_LAYOUT_LOCK = f"""
════════════════════════════════════════════════════════
INFOGRAPHIC EXPLAIN — STORYTELLING LOCK (NOT TEXTBOOK)
Canonical bake: app/services/image_generation/explain_image_prompt.py
Visual DNA: sample_infographic_explain_why_airports.png +
            sample_infographic_explain_rbi_plastic_perfect.png
NOT a hub-and-spoke web-search collage. NOT a ranking board.
════════════════════════════════════════════════════════
{BRAND_SPACE_PALETTE_LOCK}

FORMAT: 1080×1350 portrait (4:5). Data-led editorial storytelling.
Aesthetic: editorial sample DNA — Brand Space background, primary hierarchy, accent highlights, 3D icons.

COLOURS (EXACT — same as ranking / lists / paragraphs):
- BG full-bleed sky-blue Brand Space background — NEVER invent a foreign brand canvas colour
- Headlines / section titles: Brand Space primary ONLY
- Accent: Brand Space accent ONLY — never a borrowed palette
- Body gray Brand Space body
- Soft cards white/Brand Space card on ice-blue
- Footer: solid Brand Space primary bar + WHITE tagline

LOGO: empty TOP-RIGHT pocket (~24% width × ~12% height) — never draw wordmark (Brand Space composite).

STORY STRUCTURE (must feel like a narrative, not a textbook dump):
1) Hook headline (Brand Space primary) with ONE Brand Space accent keyword highlight allowed
2) One short supporting thesis line (gray) — the INSIGHT, not a definition
3) Optional hero photo/3D cluster under logo pocket
4) "At a glance" 3–4 stat chips (numbers + short labels) — proof, not essays
5) 4–6 KEY REASON cards: short TITLE + 1–2 line so-what (NOT paragraphs, NOT "Web Search:")
6) One chart / growth visual that advances the story
7) Closing insight / economic implication + Brand Space primary footer tagline

COPY RULES:
- Everyday investor language. Insight-led. Complete sentences.
- Each card body ≤18 words. NO textbook essays. NO policy jargon walls.
- FORBIDDEN baked strings: "Web Search:", "Answer WHY", research meta-labels, truncated mid-sentence.
- Spell UDAN correctly (never ADAN). CTA ≤3 words ("Explore more").

ICONS: glossy clay-3D Brand Space primary/accent — never flat emoji, never teal UI chrome.
{ORANGE_COVERAGE_LOCK}
"""

STORYTELLING_LOCK = f"""
STORYTELLING LOCK (NON-NEGOTIABLE):
- Lead with INSIGHT (why it matters), then proof numbers — never fact-dump then shrug.
- Narrative arc: hook → scale → why → effect → takeaway.
- Ban textbook tone, ban repeated identical card titles, ban "Web Search:" labels in creative.
- Each section must add a new beat of the story; never repeat the same WHY line 3×.
- Prefer one memorable thesis (e.g. "airports as regional economic anchors") over generic "India is building airports".
"""

INFOGRAPHIC_EXPLAIN_SPELLING_LOCK = """
INFOGRAPHIC EXPLAIN SPELLING LOCK (FAIL on any typo):
- Perfect English: Financial not Financrial; Exploring not Explering; could not couid
- durable not duiable; Globally not Gldbally; cautious not caurious; adoption not adeption
- crore not ctore; times not rimes; notes not hotes; hardware not herdware
- currency not currancy; designed not designad; before not berore; switch not sivitch
- RBI not OBI (NEVER OBI); polymer not polmer or palymer
- replacement not replacament; year not yaar; worn not wornn; small not smail; why not wny
- Bake ONLY quoted blueprint strings letter-perfect — zero invented misspellings
"""

# Static EXPLAIN — simple hero + heading cards (NOT infographic editorial)
STATIC_EXPLAIN_LAYOUT_LOCK = f"""
STATIC EXPLAIN LOCK (simple poster — NOT infographic editorial):
- Bold Brand Space primary headline + one supporting line
- ONE premium clay-3D hero icon (topic-matched) — NOT country flags
- 3–5 white rounded cards: short HEADING + 1–2 line EXPLANATION
- REQUIRED Brand Space accent: section dividers, CTA button fill, bullet dots (≥2% image area)
- Topic-specific copy ONLY — never paste bond examples on unrelated topics
{ORANGE_COVERAGE_LOCK}
"""

# Visual quality — dense sample-matched infographic explain
INFOGRAPHIC_EXPLAIN_QUALITY_LOCK = f"""
INFOGRAPHIC EXPLAIN QUALITY LOCK:
{INFOGRAPHIC_EXPLAIN_SPELLING_LOCK}
{SAMPLE_VISUAL_DNA}
{PARAGRAPH_INSIGHT_LOCK}
- ZERO spelling mistakes — character-perfect quoted strings only
- SAME icon quality as perfect sample: glossy clay-3D, Brand Space primary/accent, hero note cluster
- Headline: Brand Space primary ALL CAPS + solid Brand Space accent slogan pill (WHITE text)
- Footer: Brand Space primary bar + lightbulb LEFT + white tagline — NOT a sparse empty void
{ICON_STYLE_LOCK}
{UNIVERSAL_FIT_LOCK}
"""

# Visual quality + Brand Space accent — static explain posters
STATIC_EXPLAIN_QUALITY_LOCK = f"""
STATIC EXPLAIN QUALITY LOCK:
- Bake headline + supporting + EVERY card heading + explanation line — zero missing text.
- EACH white card MUST have its own distinct SMALL clay-3D icon + neat body paragraph (not text-only / not icon-only).
- Hero clay-3D icon top/center — topic-matched, premium studio render.
- Brand Space accent dividers between cards + Brand Space accent CTA button fill (≥2% image area).
- Clean premium layout: Brand Space BG, Brand Space primary headlines, Brand Space body, sharp sans-serif — no gibberish.
{ORANGE_COVERAGE_LOCK}
{ICON_STYLE_LOCK}
"""

# Mandatory Brand Space accent on ALL static creatives (explain + ranking + hub)
STATIC_ORANGE_STUB = f"""
STATIC ORANGE LOCK (ALL static formats — FAIL if missing):
Brand Space accent REQUIRED ≥2% of image on EVERY static creative:
- Explain: Brand Space accent dividers, CTA button, bullet dots, icon accents
- Horizontal bar ranking: Brand Space accent highlight row, accent headline phrase, accent arrow annotation
- Vertical country ranking (Top Countries): Brand Space accent rank badges, accent line, CTA, coin icons
- Hub facts: Brand Space accent hub ring accents, divider lines
Never tan/gold-only static that drops the Brand Space accent.
"""

INFOGRAPHIC_EXPLAIN_ORANGE_STUB = f"""
ORANGE BRAND LOCK (infographic explain — match sample):
Brand Space accent REQUIRED:
1) Thick Brand Space accent vertical bars left of EVERY section heading
2) 1–3 Brand Space accent highlight words in intro/section line OR callout
3) Brand Space accent callout box border; optional compact Brand Space accent CTA
4) Orange accents on clay-3D icons where natural
Headline stays Brand Space primary but MUST include Brand Space accent text somewhere in body.
Orange ≥2% of image. Never drop Brand Space accent.
"""

# Legacy alias — route by format in callers
EDUCATION_POSTER_LAYOUT_LOCK = INFOGRAPHIC_EXPLAIN_LAYOUT_LOCK

# Static HORIZONTAL BAR ranking — sample_static_oil_consumption_bars.png
STATIC_HORIZONTAL_BAR_DNA_LOCK = f"""
════════════════════════════════════════════════════════
STATIC HORIZONTAL BAR DNA — sample_static_oil_consumption_bars.png
Layout reference (structure only): sample_static_oil_consumption_bars.png
{SAMPLE_VISUAL_DNA}
Use for format=static + static_ranking when topic is oil/consumption/data bars (ADDITIVE — does not replace Top Countries).
════════════════════════════════════════════════════════

COLOURS:
- BG Brand Space background
- Brand Space primary headline with Brand Space accent highlight phrase in title
- Bars: Brand Space card for rows; HIGHLIGHT row (India/subject) in Brand Space accent
- Orange annotation arrow + insight text on the right
{ORANGE_COVERAGE_LOCK}
{STATIC_ORANGE_STUB}

TEXT + ICONS (every row must be complete):
- Bake country NAME + value inside bar + % outside — no missing labels
- Circular flag icon per row — correct country, never empty
- Clay-3D topic icons bottom-right (oil barrels / coins) — premium HD, not blurry
- Source footer with exact domain text

LAYOUT:
1) Centered headline — highlight key phrase in Brand Space accent
2) Horizontal BAR CHART rows (top to bottom, longest first):
   EACH row LEFT→RIGHT:
   - Country NAME (Brand Space primary, all-caps or bold)
   - Circular flag icon at bar start
   - Horizontal rounded BAR (length ∝ value)
   - Value INSIDE bar right end (e.g. "5.621 mb/d" or "₹50B")
   - % share OUTSIDE bar on the right (bold)
3) Highlight the focal country row in ORANGE bar (others blue)
4) Orange arrow annotation → 1–2 line insight text block on the right
5) Premium clay-3D topic icons bottom-right (oil barrels / coins — topic-matched)
6) Source footer bottom-left (e.g. "Source: Indian Express, Energy Institute")
7) Tiny empty top-right pocket for logo — never draw brand wordmark text

CURRENCY: mb/d · ₹ · % · USD letters — NEVER $ / US $ / ESD
FLAGS: correct per country (USA not ASA; UAE not HAE)
CTA: omit or compact ≤4 words — data posts often have no CTA button
"""

STATIC_HORIZONTAL_BAR_IMAGE_STUB = f"""
STATIC HORIZONTAL BAR = sample_static_oil_consumption_bars.png:
BG Brand Space background. Brand Space primary headline + Brand Space accent highlight phrase.
Rows: COUNTRY | flag circle | horizontal bar | value inside | % outside.
Focal row (India/topic) = ORANGE bar; others = blue bars.
Orange arrow → insight text. Clay-3D icons bottom-right. Source footer.
Never vertical rank badges. Never bond benefit cards.
"""

# Hybrid ranking + insight (e.g. "top 7 oil countries — why India is top 3")
STATIC_RANKING_INSIGHT_LOCK = f"""
STATIC RANKING + INSIGHT (when user asks top-N AND why/describe about focal country):
- Main visual = ranking board (horizontal bars OR vertical country rows — do NOT switch to education cards).
- Bake the ranked list/data as the PRIMARY layout (all 7 rows with values).
- Add 1–2 line INSIGHT annotation (Brand Space accent arrow or callout box) answering the why/describe part.
  Example: "India's rising energy demand reflects expanding mobility, industrial growth, and a fast-growing economy."
- Highlight focal country (India) in ORANGE bar/row when user mentions India.
{STATIC_ORANGE_STUB}
"""

# Generic retail tone — safe for EVERY topic/format (contains no sample copy to plagiarise)
RETAIL_TONE_LOCK = """
RETAIL AUDIENCE TONE LOCK (all formats):
Target = everyday Indian investor on LinkedIn/Instagram.
- Short, plain, human lines. Scannable. Concrete.
- Every line must be about the USER'S OWN TOPIC — written fresh from this run's research.
- BAD: textbook essays, policy jargon (Vostro/hedge/sector exposure), mid-word cuts,
  paragraph CTAs, research meta-labels ("Web Search:", "Answer WHY").
- CTA: 2–3 words maximum.
"""

# Ranking-only tone. Injected ONLY for layout_type=static_ranking.
# Sample wording is described, never quoted — quoting caused verbatim copy leaks
# (an airport prompt rendered the FDI sample creative word-for-word).
INFOGRAPHIC_AUDIENCE_TONE_LOCK = f"""
RANKING TONE LOCK — structure of sample_top_countries_investing.png:
{RETAIL_TONE_LOCK}
ANTI-PLAGIARISM RULE (HARD FAIL):
The sample creative is a LAYOUT reference only. NEVER reuse its subject matter,
entity names, phrases, amounts, headline or subtitle. If the user's topic is not
a country-investment ranking, none of that sample's wording may appear anywhere.

COPY SHAPE (write fresh wording for the user's actual topic):
- Headline: plain factual claim naming the USER'S topic and the count
- Supporting: one soft factual line about the USER'S topic
- Each row: ONE descriptive phrase ≤5 words, specific to that row's entity
- Amount: ₹ figure (or % / USD letters when the source requires)
- CTA: 2–3 words
"""

# Shared DNA for INFOGRAPHIC ranking — vertical rows (Top Countries sample)
RANKING_SAMPLE_DNA_LOCK = f"""
════════════════════════════════════════════════════════
RANKING SAMPLE DNA — Top Countries vertical rows (UNCHANGED — primary country/FDI ranking)
Layout reference (structure only): sample_top_countries_investing.png
Use for: infographic static_ranking OR static static_ranking when topic is country/FDI top-N.
(Does NOT apply to oil/consumption horizontal bar topics — those use STATIC_HORIZONTAL_BAR_DNA_LOCK.)
════════════════════════════════════════════════════════

COLOURS:
- BG Brand Space background
- Navy text Brand Space primary
- Orange Brand Space accent: rank squares, accent line under subtitle, coin/chart icons, CTA
{BRAND_SPACE_PALETTE_LOCK}
{ORANGE_COVERAGE_LOCK}
{HEADLINE_COLOR_LOCK}

LAYOUT (exact columns left→right on EVERY row):
1) Orange rounded square with white rank number
2) Rounded real country flag (matched — UAE not HAE, USA not ASA, never India flag for UAE)
3) Country NAME bold + ONE short grey phrase under it
4) Amount bold (₹50B / ₹45B …) 
5) Tiny coin + rising Brand Space accent bars icon

Header: centered Brand Space primary headline + soft supporting + short centered Brand Space accent line
Footer: compact Brand Space accent CTA ("Explore more")
Thin light dividers between rows. No dark BG. No $ / US $ signs.

CURRENCY: ₹ for India FDI ranks · % for inflation · ¥ Japan · USD letters only if source USD
{INFOGRAPHIC_AUDIENCE_TONE_LOCK}
"""

# Compact stub for any remaining AI image path
RANKING_IMAGE_STUB = f"""
RANKING = sample_top_countries_investing.png LAYOUT DNA (not its wording):
BG Brand Space background. Navy Brand Space primary. Orange badges+accent+CTA+coin icons Brand Space accent.
Row: Brand Space accent # square | real flag | NAME + ≤5-word phrase | amount | coin/chart icon.
Tone: short plain phrases about THIS run's entities — never textbook, never the sample's words.
Never HAE/ASA/$/US $/wrong flags. Same for static AND infographic.
"""

INFOGRAPHIC_RANKING_FORMAT_LOCK = RANKING_SAMPLE_DNA_LOCK

INFOGRAPHIC_TRADE_BOARD_LOCK = f"""
TRADE DEFICIT BOARD LOCK — match sample_india_russia_trade_deficit.png EXACTLY:
Layout reference (structure only): sample_india_russia_trade_deficit.png
- Punchy plain headline + one short subtitle on cream rounded strip (no jargon)
- Clean dual-bar year table ONLY: EXPORT (Brand Space accent) | TRADE BALANCE | IMPORT (Brand Space primary), Billion USD
- Year labels correct (2020-21, 2021-22, 2022-23, 2023-24…) — never "2021-2023"
- Bake exact strings: "Export: USD X.XB" / "Import: USD Y.YB" — NEVER ESD / Emp / Impp / $
- Brand Space accent export bars LEFT; Brand Space primary import bars RIGHT; balance numbers CENTER (deficit in red if large)
- Bottom Brand Space card box: category bullets + USD lines
- Source: Ministry of Commerce (or research domain)
- Thick Brand Space accent line at bottom edge optional
- FORBIDDEN technical sidebars: Key Drivers, Sector Exposure, Currency Risk, Vostro/Bistro,
  Investment Considerations, Questions for Advisors, FD briefcase, handshake as main story
- Optional CTA: COMPACT 2–4 words only — never a paragraph-length button
"""

# Static HUB facts — sample_bank_penalties.png
STATIC_HUB_FACTS_DNA_LOCK = f"""
════════════════════════════════════════════════════════
STATIC HUB FACTS DNA — sample_bank_penalties.png
Layout reference (structure only): sample_bank_penalties.png
Use for: bank penalties / key rules / top-N bank facts (layout_type=static_hub_facts).
════════════════════════════════════════════════════════

LAYOUT (hub + spoke — NOT ranking rows):
1) Centered Brand Space primary headline (topic-matched variant)
2) CENTER HUB: white circle with premium clay-3D bank building icon
   - Coloured ring segments behind hub (Brand Space accent segment required)
   - Five bank pods on the ring (Axis Bank | SBI | HDFC Bank | ICICI Bank | PNB)
3) FIVE white rounded cards around hub — one per bank:
   - Exact bank name as heading (typed text — NOT official trademark logos)
   - 1–2 SHORT lines with concrete ₹/% premature-withdrawal rules
   - Thin connector line from card to hub pod
4) BG Brand Space background — never an invented dark navy/black
5) Tiny empty top-right pocket for logo composite — never draw brand wordmark
6) NO fake customer quotes. NO teaser question without rates. body="" on blueprint.

COLOURS: Brand Space primary headlines · Brand Space accent hub ring segment + dividers (≥2%)
{ORANGE_COVERAGE_LOCK}
{STATIC_ORANGE_STUB}
"""

STATIC_HUB_FACTS_IMAGE_STUB = f"""
STATIC HUB = sample_bank_penalties.png:
Hub + 5 bank fact cards. Center clay-3D bank building. Ring with bank pods.
Cards: Axis | SBI | HDFC | ICICI | PNB — each with ₹/% penalty lines. Orange ring accent.
Never ranking rows. Never bond benefit cards. Never teaser-only headline.
"""

SIMPLIFIED_CREATIVE_TONE_RULES = f"""
BRAND SPACE LAYOUT SYSTEM LOCK (NON-NEGOTIABLE)
{BRAND_SPACE_PALETTE_LOCK}
{STORYTELLING_LOCK}

Layout quality bar:
- Ranking/lists: sample_top_countries_investing.png
- Explain/why stories: sample_infographic_explain_why_airports.png + rbi plastic perfect
Samples are LAYOUT references. Their words, entities and numbers belong to their own
topics and must never be reused on a different topic.
Educate-first, short human lines — NEVER textbook paragraphs, NEVER empty teaser ads.
NEVER bake "Web Search:" or research meta-labels into the creative.
{RETAIL_TONE_LOCK}

════════════════════════════════════════
LAYOUT ROUTER (follow layout_type)
════════════════════════════════════════
- carousel_story: education story OR single education poster
  Examples: why bonds / predictable income / liquidity / FIRE / myths / checklists
  → BENEFIT/REASON cards — NEVER invent country comparison tables unless user asked
- static_hub_facts → hub + 5 bank fact cards (sample_bank_penalties.png)
- static_ranking + oil/consumption/data bars + format=static → horizontal bar (sample_static_oil_consumption_bars.png)
- static_ranking + country/FDI top-N → vertical rank rows (sample_top_countries_investing.png)
- static_ranking + trade deficit → dual-bar board (sample_india_russia_trade_deficit.png)
- carousel_story + format=infographic → DENSE sample editorial (sample_infographic_explain_why_airports.png)
- carousel_story + format=static → simple hero + heading cards (STATIC_EXPLAIN_LAYOUT_LOCK)

════════════════════════════════════════
DATA POST vs TEASER vs EDUCATION
════════════════════════════════════════
If user asks WHY / useful / benefits / explain / how / what is:
→ INFOGRAPHIC: multi-section editorial (section headings + 3-col icon cards + callout box)
→ STATIC: simple hero + 3–5 heading/explanation cards
→ FORBIDDEN: bond benefit cards (Capital Preservation / Regular Income) on unrelated topics
→ FORBIDDEN: invent India vs USA vs Germany yield boards unless user asked compare/rank

If user asks rates / rules / top-N / comparison / FDI / inflation / bank penalties:
→ Put ACTUAL facts in sections/slides. NO curiosity-only teasers. NO fake testimonials replacing data.

TOPIC LOCK (HARD FAIL — read before using any example below):
The examples in this document exist to show SHAPE only. Every headline, entity,
phrase, statistic and CTA you emit must come from the user's own topic and this
run's research. Reusing an example's subject matter or wording is a rejection.
If the user asked about airports, nothing about FDI/countries/banks/bonds may appear.

BAD SHAPE: teaser question + "Learn more" + fake quote, with none of the actual rates
BAD SHAPE: a country/yield comparison board when the user asked neither compare nor rank
BAD SHAPE: hub-spoke collage with "Web Search:" labels + truncated text + missing logo
GOOD SHAPE: plain claim headline + 4–5 fact cards, each carrying a real ₹/% figure
GOOD SHAPE: ranked rows with flag + ≤5-word phrase + amount (only when top-N was asked)
GOOD SHAPE: storytelling editorial — hook → scale → why → effect → takeaway (why/how topics)

════════════════════════════════════════
CONTENT DEPTH
════════════════════════════════════════
{CONTENT_DEPTH_LOCK}

════════════════════════════════════════
BRAND COLOURS + ICONS + FIT
════════════════════════════════════════
- Brand Space primary + REQUIRED Brand Space accent every creative
{HEADLINE_COLOR_LOCK}
{ORANGE_COVERAGE_LOCK}
- BG Brand Space background; cream/soft cards OK as cards only — page BG stays ice-blue
- Icons: ULTRA-PREMIUM clay-3D / soft-touch studio renders (high detail, subtle gloss, strong shadows)
  — never flat clipart, never cheap low-poly, never washed-out blobs
{ICON_STYLE_LOCK}
- Content must FIT: no cut-off headlines, no overcrowding, no empty shells, no "..." truncation
{UNIVERSAL_FIT_LOCK}
- Legal footer: CAROUSEL slides only, and only if Brand Space has one (Pillow composite). Static/infographic: no legal strip.
{CAROUSEL_FIT_LOCK}

════════════════════════════════════════
CURRENCY + ACCURACY
════════════════════════════════════════
- India default: ₹ for retail/FD/banks; % for rates
- ¥ only for Japan investment commits
- USD only when source data is USD (label "USD")
- Real banks/countries only; matched flags; totals must add up
- Never invent ASA (use USA); never wrong UK↔Germany flags; never HAE (use UAE)
- Perfect English spelling on every baked word (investment not investmet; growth not grewth)

HARD CAPS:
- headline ≤10 words | supporting ≤14 | body often empty for data posts
- section_label = name | includes = 1–2 short facts | body empty
- carousel slide body 22–36 words (teach like Sweep-In samples; still scannable)
- CTA ≤4 words; compact button only
"""

BRAND_COLOR_LOCK_RULE = f"""
\n\nBRAND COLOUR + ICON QUALITY LOCK:
- Brand Space primary; REQUIRED Brand Space accent (dashes, dividers, CTA arrows, bullets).
{HEADLINE_COLOR_LOCK}
{ORANGE_COVERAGE_LOCK}
- BG Brand Space background. No purple/neon AI look. NEVER pure black / charcoal backgrounds.
- ULTRA-PREMIUM clay-3D icons (high detail, studio light, subtle gloss) — never flat/cheap/low-poly.
{ICON_STYLE_LOCK}
- All requested content must fit fully — never truncate with "...".
{UNIVERSAL_FIT_LOCK}
- {NO_LEGAL_STATIC_RULE}
"""

# SHORT locks for IMAGE API only (gpt-image-1 hard ~6000 char budget).
CAROUSEL_IMAGE_STYLE_STUB = """
CAROUSEL DESIGN SYSTEM:
- Canvas: Brand Space background full-bleed; headlines Brand Space primary; accent only for numbers/CTA.
- Info pages: 3–4 wide rounded cards — 3D isometric icon LEFT, thin divider, text RIGHT.
- NO numbers in headline. NO page counters. NO source names.
- Logo pocket empty top-right. Bottom ~14% empty only if Brand Space has a legal footer.
"""

CAROUSEL_TONE_IMAGE_STUB = """
Premium editorial carousel: Brand Space canvas, primary headline, muted subhead,
wide rounded info cards with miniature 3D isometric icons. Labels from copy only.
NO connector graphs / path lines. NO digits in headlines. Logo/disclaimer composited — never baked.
"""

CAROUSEL_IMAGE_EXTRA_LOCKS = """
NO NUMBERS in headline text. NO page numbers/badges. NO connector graphs or flowchart arrows.
Wide rounded info cards (icon left, divider, text right) + miniature 3D isometric icons.
Logo composited. Legal footer composited only if Brand Space provided one. Letter-perfect copy.
"""

STATIC_IMAGE_EXTRA_LOCKS = f"""
TOP-RIGHT CORNER: leave COMPLETELY BLANK (background colour only). NEVER draw a logo, leaf icon, compass icon, circular badge, decorative symbol, or ANY graphic element in the top-right corner. The brand logo is composited in post-processing — this area MUST be empty.
BRAND/LOGO BAN: never draw brand wordmark / watermark / "Brand Logo" placeholder anywhere.
BRAND SPACE COLOUR LOCK:
- Background MUST be Brand Space background full bleed.
- Headlines Brand Space primary only.
- Accent MUST be Brand Space accent — never a borrowed palette.
- Accent on icons/dividers/CTA ≥ visible at thumbnail size.
{NO_LEGAL_STATIC_RULE}
{STATIC_ORANGE_STUB}
INDIA: ₹/% retail · ¥ Japan · USD letters if source USD — NEVER $ / US $ / ESD / £.
Headlines Brand Space primary; accent Brand Space accent MUST show; BG Brand Space background.
Flags match countries (no ASA/HAE invents). Totals add up.
TONE: short retail hooks — no Vostro/hedge/sector-exposure jargon side panels.
CTA: compact ≤28% width, ≤4 words — never a wide paragraph button.
NO mid-word text breaks. No garbled labels.
"""

CAROUSEL_LEGAL_LOCK_RULE = f"""
\n\n{LEGAL_FOOTER_HINT}
"""

INDIA_MARKET_LOCK_RULE = """
\n\nINDIA MARKET + DATA ACCURACY LOCK:
- Prefer ₹/%; ¥ for Japan commits; USD only when source is USD (label USD).
- Real bank/country names; correct flags; totals must match rows.
- For top-5 banks / penalty rates: show ALL 5 banks with concrete ₹/% rules — never a teaser.
- When stats/rates are shown, include Source: domain.com footer from verified research URLs.
"""

SOURCE_FOOTER_RULE = """
\n\nSOURCE FOOTER LOCK:
If verified research sources exist, bake a compact footer line:
Source: domain1.com · domain2.com
Do not invent sources. Prefer official/public domains.
"""
