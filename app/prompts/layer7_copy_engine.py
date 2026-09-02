from __future__ import annotations

from typing import Any

from app.graph.models.layer2_models import BrandIntelligenceOutput
from app.graph.models.layer6_models import FormatPlanOutput
from app.prompts.base import BasePromptBuilder
from app.prompts.brand_copy_tone import (
    SIMPLIFIED_CREATIVE_TONE_RULES,
    SOURCE_FOOTER_RULE,
    CONTENT_DEPTH_LOCK,
    HEADLINE_COLOR_LOCK,
    EDUCATION_POSTER_LAYOUT_LOCK,
    INFOGRAPHIC_EXPLAIN_LAYOUT_LOCK,
    INFOGRAPHIC_EXPLAIN_ORANGE_STUB,
    INFOGRAPHIC_EXPLAIN_QUALITY_LOCK,
    STATIC_EXPLAIN_LAYOUT_LOCK,
    STATIC_EXPLAIN_QUALITY_LOCK,
    STATIC_ORANGE_STUB,
    STATIC_RANKING_INSIGHT_LOCK,
    STATIC_HORIZONTAL_BAR_DNA_LOCK,
    STATIC_HORIZONTAL_BAR_IMAGE_STUB,
    INFOGRAPHIC_AUDIENCE_TONE_LOCK,
    RETAIL_TONE_LOCK,
    INFOGRAPHIC_RANKING_FORMAT_LOCK,
    INFOGRAPHIC_TRADE_BOARD_LOCK,
        RANKING_IMAGE_STUB,
    CAROUSEL_AUDIENCE_TONE_LOCK,
)
from app.prompts.carousel_sample_dna import CAROUSEL_SAMPLE_DNA



def _is_data_hub_topic(text: str) -> bool:
    t = (text or "").lower()
    keys = (
        "penalty",
        "penalties",
        "top 5 bank",
        "top five bank",
        "top 5 banks",
        "key rules",
        "fd ",
        "fixed deposit",
        "premature withdrawal",
    )
    return any(k in t for k in keys)


class CopyEnginePromptBuilder(BasePromptBuilder):
    """Builds prompts for Layer 7: Copy Engine."""

    PROMPT_VERSION = "1.5-carousel-retail-tone"

    _CAROUSEL_STORY_SUFFIX = f"""
{CAROUSEL_SAMPLE_DNA}
{CAROUSEL_AUDIENCE_TONE_LOCK}

CAROUSEL OUTPUT RULES (client quality — NON-NEGOTIABLE):
Emit exactly 5–6 slides in slide_copy. Follow a clear STORY ARC beat-by-beat.
This is an EDUCATION STORY in PLAIN LANGUAGE for THIS brand's Brand Space audience.

UNIQUE COMPLETE HEADLINES (critical):
- Every slide_copy[].headline MUST be unique, COMPLETE (no mid-word cuts), max 8–10 words.
- NEVER bare topic titles.
- NEVER jargon in headlines or body.
- NEVER near-duplicates.
- Write headlines fresh from THIS prompt — never reuse another campaign's lines.

STORY DEPTH (teach with numbers — keep language simple):
- Slide 1 HOOK: surprising question + concrete tension in plain words
- Slide 2 SCENARIO: mini-story in body + 3 proof_points
- Slide 3 HOW IT WORKS: mechanism + comparison numbers — explain simply
- Slide 4 CHOICE: decision + honest caveat
- Slide 5 PROS/CONS: short reason sentences in proof_points (NOT empty Pros/Cons chips)
- Slide 6 CTA: short question inviting comments
- body: 18–32 words per slide — short sentences, real facts
- supporting_line = one plain sentence with a number or "what it means" (required)
- proof_points: 2–3 lines with facts (6–12 plain words each)
- chip_labels = 3 content words — NEVER Pros/Cons/Examples/Advantages

FORBIDDEN (too technical OR too shallow):
- Sparse slides with only 1–2 vague lines
- Truncated / missing headlines
- Same headline repeated
- Body that only restates a definition with jargon and no example

TOPIC LOCK: stay on the user's topic. Use only this brand's Brand Space + web + vector data.
Spelling perfect.
"""

    _RANKING_SUFFIX = f"""
STATIC + INFOGRAPHIC RANKING / DATA BOARD (layout_type=static_ranking):
Same DNA for format=static AND format=infographic when ranking — tone + currency + Brand Space accent + flags.
{INFOGRAPHIC_AUDIENCE_TONE_LOCK}
Pick the board type from the user topic:

A) COUNTRY / TOP-N RANK (when the user asked for a ranked list):
{INFOGRAPHIC_RANKING_FORMAT_LOCK}
- Fill infographic_sections with ranked rows.
- section_label = real country (USA, Singapore, Japan, UK, UAE — NEVER HAE / ASA)
- includes = [ONE plain phrase ≤5 words] describing THAT row's entity, written fresh
  from this run's research — never reused from any sample creative
  NEVER jargon, NEVER essays, NEVER duplicate the amount as a phrase
- stat = "₹50B" style for India FDI ranks (NEVER "US $" / "$" / "ESD")
  Inflation ranks → "6.5%" ; if source USD → "USD 50 Bn" letters only
- supporting_line = one soft factual line about the user's own topic
- cta = 2–3 words ONLY — never a sentence like "Explore Investment Opportunities"
- Row COUNT must match the user request (top 6 → 6 rows).
- SPELLING: UAE not HAE; USA not ASA; tech/infrastructure letter-perfect.

B) TWO-SERIES COMPARISON / DUAL-BAR (when the user asked to compare two series):
{INFOGRAPHIC_TRADE_BOARD_LOCK}
- Punchy plain data headline (e.g. "India Buys Much More From Russia Than It Sells").
- supporting_line: one soft factual subtitle — NO "implications / exposure / hedge".
- sections[] = fiscal YEAR rows (2020-21 … 2023-24):
  section_label = year
  includes = ["Export: USD X.XXB", "Import: USD Y.YYB"]  # NEVER ESD / Emp
  stat = trade balance as signed number (e.g. "-56.9")
- Add 2–4 more sections for "What India buys most" categories with USD amounts
  (Mineral fuels, Edible oils, Fertilisers, …) from research — not invented.
- source_footer from research (e.g. Ministry of Commerce and Industry).
- body=""; customer_quote=""; NO technical side panels.
FORBIDDEN for trade boards: Capital Preservation, Regular Income, FD briefcase,
Liquidity Management, bond benefit cards, Vostro/Currency Risk cards, wrong flags,
paragraph-length CTAs.
"""

    _INFOGRAPHIC_SYSTEM_SUFFIX = f"""
INFOGRAPHIC FORMAT — CRITICAL ADDITIONAL RULES:
{RETAIL_TONE_LOCK}
Match Brand Space voice — scannable, short labels — NOT textbook essays / teaser ads.

The LOCKED layout_type above already decides the structure. Detailed rules for the
chosen structure are appended below. Do NOT borrow another structure's rules, and do
NOT borrow any sample creative's subject matter, entities, phrases or numbers:
- WHY / explain / how / what is → multi-section storytelling editorial
  Section headings + icon cards + callout box — NOT ranked rows, NOT bond benefit cards
- Ranking / top-N / country-wise / FDI → ranked rows (ONLY if the user asked to rank)
- Trade deficit → dual-bar year board
- Bank penalties / key rules → bank fact cards

When infographic explain (why/how/what is):
- The DATA-STORY CONTENT CONTRACT appended below owns the exact section and
  stat counts. Follow it literally — do not substitute your own structure.
- customer_quote = final callout insight; source_footer when research exists
- FORBIDDEN: Capital Preservation / Regular Income on unrelated topics

When ranking / comparison / top-N (user asked for it):
- section_label = name (country/bank), stat = number when useful, includes = 1 short plain fact

Top-level body usually EMPTY — facts live in sections.
Spelling perfect. CTA ≤4 words. No text breaking.
"""

    _INFOGRAPHIC_EXPLAIN_SUFFIX = f"""
INFOGRAPHIC EXPLAIN (layout_type=carousel_story on infographic) — Brand Space reference, SHORT copy:
{INFOGRAPHIC_EXPLAIN_LAYOUT_LOCK}
{INFOGRAPHIC_EXPLAIN_ORANGE_STUB}
{INFOGRAPHIC_EXPLAIN_QUALITY_LOCK}
DATA-STORY CONTENT CONTRACT — the layout renders these slots literally, so fill
every one. Big numbers carry the story; prose is support, never the main event.
- headline ≤8 words (a claim or question) + supporting_line ≤12 words
- stat_highlights = UP TO 4 headline figures for the hero band.
  Format each as "<figure> <short label>" — e.g. "15.4% annual growth in traffic",
  "352 MN+ passengers in FY2024", "2.7X increase in aircraft movements".
  The figure comes FIRST and must be a real number from approved evidence.
- sections[] = UP TO 6, split into two groups:
  * numbered proof (up to 3): each sets stat to a real figure ("148", "120+", "79")
    with section_label = ≤6-word label for that figure.
  * supporting insights (up to 3): leave stat EMPTY, section_label = ≤5-word
    heading, body = ONE concrete so-what (≤12 words) naming a real driver or
    outcome — e.g. "UDAN links Tier-2 cities to metros", "Cargo hubs cut logistics cost",
    "Greenfield airports unlock new tourism belts". MUST be specific. Ban filler:
    "everything you need to know", "India needs a lot", "key insight", "why it matters".
NO-REPEAT RULE (most important): every figure and every fact appears EXACTLY ONCE
across the whole output. A number used in stat_highlights must NOT reappear as a
section stat, label or body. Restating one fact in different words counts as a
repeat and is a failure.
FEWER IS BETTER THAN REPEATED: if approved evidence supports only 3 distinct
facts, return only 3. Do NOT pad the remaining slots by rephrasing or reusing a
fact, and never invent a figure. An honest short poster beats a padded one.
- This is a POSTER, not an essay. Keep the total word count low: 4 hero figures
  plus 3 numbered proofs are the 7 data points that carry the story.
- Leave the top-level body EMPTY. Never write a paragraph — paragraphs get
  clipped mid-sentence when rendered.
- Write every string COMPLETE. Never end a label or clause on a dangling
  connector ("and", "or", "that", "with", "for", "to", "of").
- Keep money units glued to the figure: "₹98,000 cr total investment" — never
  leave "crore" alone in the label where the image can wrap it as "cr ore".
- customer_quote = closing line 1 (≤8 words, punchy insight — not a slogan)
- cta = closing line 2 (≤10 words, forward-looking)
- source_footer = "Source: <named institutions>" whenever evidence has sources
NEVER invent a figure. If evidence supports fewer than 4 hero figures, use the
real ones you have and leave the rest out rather than fabricating.
FORBIDDEN: long paragraphs, full-width accent headers, duplicate headings, typos,
bond CTAs off-topic, placeholder text, numbered stubs like "Rationale 1",
teaser filler ("everything you need to know", "India needs a lot more")
"""

    _STATIC_EXPLAIN_SUFFIX = f"""
STATIC EXPLAIN (layout_type=carousel_story on static):
{STATIC_EXPLAIN_LAYOUT_LOCK}
{STATIC_EXPLAIN_QUALITY_LOCK}
{STATIC_ORANGE_STUB}
- 3–5 sections[]: section_label, includes, icon_hint — every card complete
"""

    _EDUCATION_POSTER_SUFFIX = _INFOGRAPHIC_EXPLAIN_SUFFIX  # legacy alias

    _STATIC_DATA_HUB_SUFFIX = """
STATIC DATA / HUB TOPICS:
Even for format=static you MUST fill infographic_sections with the actual data cards
from THIS prompt and THIS brand's research — never a borrowed entity list.
FORBIDDEN: teaser creatives that only ask a question without listing the facts.
"""

    _STATIC_RANKING_SUFFIX = f"""
STATIC RANKING — pick style from topic (both require Brand Space accent):
A) Country/FDI top-N → Top Countries vertical rows (UNCHANGED — {RANKING_IMAGE_STUB})
B) Oil/consumption/data bars → horizontal bar chart ({STATIC_HORIZONTAL_BAR_DNA_LOCK})
{STATIC_ORANGE_STUB}
- Bake ALL row labels, values, % — no missing text; flags + icons on every row
"""

    _STATIC_HORIZONTAL_RANKING_SUFFIX = f"""
STATIC HORIZONTAL BAR RANKING (oil/consumption/data only):
{STATIC_HORIZONTAL_BAR_DNA_LOCK}
{STATIC_RANKING_INSIGHT_LOCK}
{STATIC_ORANGE_STUB}
- sections[] = 7 ranked countries: section_label=NAME, stat=mb/d or value, includes=[% share, short phrase]
- If user asks why/describe focal country: put 1–2 line insight in customer_quote or last section includes
- Highlight India/focal row in Brand Space accent; bake ALL 7 rows — no missing countries
"""

    _STATIC_VERTICAL_RANKING_SUFFIX = f"""
STATIC VERTICAL COUNTRY RANKING (Top Countries — UNCHANGED):
{INFOGRAPHIC_RANKING_FORMAT_LOCK}
{RANKING_IMAGE_STUB}
{STATIC_ORANGE_STUB}
"""

    def build_system(self, format_name: str = "static", **kwargs: Any) -> str:
        user_prompt = str(kwargs.get("user_prompt") or "")
        layout_type = str(kwargs.get("layout_type") or "")
        data_hub = _is_data_hub_topic(user_prompt) or layout_type == "static_hub_facts"
        base = f"""You are Violyt's Copy Engine. Generate platform-native, brand-aligned creative copy.
Return a single JSON object matching CopyOutput.
LAYOUT_TYPE (LOCKED): {layout_type or "infer from topic"}

{SIMPLIFIED_CREATIVE_TONE_RULES}
{SOURCE_FOOTER_RULE}
- Brand voice: follow tone spectrum, emotional territory, simplicity, and preferred vocabulary from the brand model.
- Prefer short scannable lines over long explanation blocks.
- Uniqueness: avoid generic AI filler (unlock, elevate, revolutionize, transform, in todays digital landscape).
- Claim safety: note yield/performance claims in claim_safety_notes.
- For data/hub topics (bank penalties, top-N rules): fill infographic_sections with the actual facts even if format is static. body/customer_quote usually empty. NO teaser ads.

JSON OUTPUT STRUCTURE:
{{
  "headline": "Main headline or hook (max 12 words)",
  "supporting_line": "One short subhead (max 18 words) or empty",
  "body": "Usually empty for data posts",
  "cta": "Short action or empty",
  "hashtags": ["#Tag1", "#Tag2"],
  "slide_copy": [],
  "claim_safety_notes": ["Note about verify claims"],
  "infographic_sections": [
    {{
      "section_label": "Named entity from the user prompt",
      "stat": "",
      "includes": ["Short ₹/% rule line 1", "Short rule line 2"],
      "body": "",
      "icon_hint": "bank"
    }}
  ],
  "problem_statement": "",
  "solution_statement": "",
  "proof_points": [],
  "stat_highlights": [],
  "customer_quote": "",
  "customer_name": "",
  "process_steps": []
}}

No preamble. No explanations. Return ONLY raw JSON."""

        if format_name == "infographic":
            base += self._INFOGRAPHIC_SYSTEM_SUFFIX
        if data_hub or layout_type == "static_hub_facts":
            base += self._STATIC_DATA_HUB_SUFFIX
        # Ranking suffix ONLY for real rankings — never for every infographic
        if layout_type == "static_ranking":
            from app.prompts.layout_router import static_ranking_style

            if format_name == "static":
                style = static_ranking_style(user_prompt)
                if style == "horizontal_bar":
                    base += self._STATIC_HORIZONTAL_RANKING_SUFFIX
                elif style == "vertical_countries":
                    base += self._STATIC_VERTICAL_RANKING_SUFFIX
                else:
                    base += self._RANKING_SUFFIX  # trade board copy rules
            else:
                base += self._RANKING_SUFFIX
        if layout_type == "carousel_story" and format_name == "infographic":
            base += self._INFOGRAPHIC_EXPLAIN_SUFFIX
        elif layout_type == "carousel_story" and format_name == "static":
            base += self._STATIC_EXPLAIN_SUFFIX
        # layout_type "carousel_story" is the internal marker for a story/explain
        # structure, not an actual carousel. Appending slide rules to an
        # infographic told the model to emit slide_copy instead of sections.
        if format_name == "carousel":
            base += self._CAROUSEL_STORY_SUFFIX
        return base

    def build_user(
        self,
        brand_intelligence: BrandIntelligenceOutput,
        format_plan: FormatPlanOutput,
        concept: dict,
        format_name: str = "static",
        live_research: dict | None = None,
        **kwargs: Any,
    ) -> str:
        user_prompt = str(kwargs.get("user_prompt") or "")
        layout_type = str(kwargs.get("layout_type") or "")
        stands_for = ", ".join(brand_intelligence.brand_core.stands_for)
        prohibited = ", ".join(brand_intelligence.communication_behavior.prohibited_phrases)
        guardrails = "; ".join(brand_intelligence.guardrails)
        data_hub = _is_data_hub_topic(user_prompt) or layout_type == "static_hub_facts"

        from app.prompts.layout_router import requested_rank_count

        rank_n = requested_rank_count(user_prompt)
        rank_note = ""
        if layout_type == "static_ranking":
            if rank_n:
                rank_note = (
                    f"\nRANK COUNT LOCK: User asked for TOP {rank_n}. "
                    f"infographic_sections MUST contain EXACTLY {rank_n} ranked rows "
                    f"(do not stop at 5).\n"
                )
            else:
                rank_note = (
                    "\nRANK COUNT: Include every entity the user asked to compare/rank "
                    "(do not silently truncate to 5).\n"
                )
        elif layout_type == "carousel_story" and format_name in ("static", "infographic"):
            rank_note = (
                "\nEDUCATION LOCK: User asked why/benefits/explain — sections must be "
                "REASON/BENEFIT cards only. Do NOT invent country comparisons, FDI ranks, "
                "or flag tables unless the user explicitly asked to compare countries.\n"
            )

        slides_str = "\n".join([
            f"- Slide {s.slide_number} (Role: {s.role}, Focus: {s.focus}, Visual Intent: {s.visual_intent})"
            for s in format_plan.slide_plan
        ])

        data_note = ""
        if data_hub:
            data_note = f"""
USER PROMPT (DATA HUB — MUST ANSWER WITH FACTS, NOT A TEASER):
{user_prompt}

Required: headline like "Bank's Penalty Rates and Key Rules";
infographic_sections with EXACTLY 5 Indian banks (Axis, SBI, HDFC, ICICI, PNB)
each with 1–2 short ₹/% premature-withdrawal rule lines.
body="", customer_quote="", no curiosity-only bullets.
"""
        elif user_prompt:
            data_note = f'\nUSER ORIGINAL PROMPT:\n"{user_prompt}"\n{rank_note}'
        else:
            data_note = rank_note
        live_research_note = ""
        verified_facts = (live_research or {}).get("verified_facts") or []
        research_summary = (live_research or {}).get("summary") or ""
        if verified_facts or research_summary:
            facts_str = "\n".join(
                f"- {fact.get('label', '')}: {fact.get('value', '')}"
                + (f" (source: {fact.get('source_title')})" if fact.get("source_title") else "")
                + (f" [{fact.get('source_url')}]" if fact.get("source_url") else "")
                for fact in verified_facts
            )
            live_research_note = f"""
LIVE RESEARCH — GO DEEPER (client bar — not basic slogans):
Summary: {research_summary or 'N/A'}
Verified Facts:
{facts_str or 'No individually verified facts returned.'}

Source article is useful — EXTRACT concrete mechanisms, numbers, and conditions into the deck.
Each carousel slide should teach ONE insight in PLAIN RETAIL LANGUAGE (how it works / why it matters /
what to watch) — same tone as static/infographic samples. Do NOT use policy jargon or vague lines
like "Connect the Dots". Translate research into short sentences THIS brand's audience gets in 3 seconds.
"""

        return f"""BRAND SIGNAL CONTEXT:
Brand Name: {brand_intelligence.brand_core.brand_name}
Value Proposition: {brand_intelligence.brand_core.value_proposition}
Market Tension: {brand_intelligence.brand_core.market_tension}
Stands For: {stands_for}
Tone: {brand_intelligence.communication_behavior.tone_spectrum}
Emotional Territory: {brand_intelligence.communication_behavior.emotional_territory}
Prohibited terms (DO NOT USE): {prohibited}
Guardrails: {guardrails}

CREATIVE CONCEPT & FOCUS:
Concept: {concept.get('concept_name', 'Default')}
Core Idea: {concept.get('core_idea', '')}
Narrative angle: {concept.get('narrative_angle', '')}
Format layout archetype: {format_plan.layout_archetype}
Format: {format_name}
Layout type (LOCKED): {layout_type or 'auto'}

SLIDE STRUCTURE TO FOLLOW:
{slides_str}
{data_note}{live_research_note}
Generate the copy. Keep every field short, clear, and approachable — never textbook-heavy or teaser-only.
If layout is carousel_story: fill 4–7 slide_copy beats. If hub/ranking: fill complete infographic_sections.
"""
