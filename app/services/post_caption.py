from __future__ import annotations

from app.graph.models.layer7c_models import CreativeBlueprint


def build_post_caption_from_blueprint(blueprint: CreativeBlueprint, platform: str = "instagram") -> str:
    """Build a platform-ready social caption when the LLM omitted post_caption."""
    if str(blueprint.post_caption or "").strip():
        return str(blueprint.post_caption).strip()

    platform_key = (platform or "instagram").strip().lower()
    if platform_key == "x":
        platform_key = "twitter"

    paragraphs: list[str] = []
    hook = str(blueprint.hook or "").strip()
    headline = str(blueprint.headline or blueprint.title or "").strip()
    body = str(blueprint.body or "").strip()
    supporting = str(blueprint.supporting_line or "").strip()

    lead = hook or headline
    if lead:
        paragraphs.append(lead)

    for line in list(blueprint.story_flow or [])[:5]:
        text = str(line or "").strip()
        if text and text not in paragraphs:
            paragraphs.append(text)

    if supporting and supporting not in paragraphs:
        paragraphs.append(supporting)

    if body:
        if platform_key == "twitter" and len(body) > 220:
            paragraphs.append(body[:217].rstrip() + "…")
        else:
            for chunk in [p.strip() for p in body.split("\n\n") if p.strip()]:
                if chunk not in paragraphs:
                    paragraphs.append(chunk)

    for point in list(blueprint.proof_points or [])[:2]:
        text = str(point or "").strip()
        if text and text not in paragraphs:
            paragraphs.append(text)

    cta = str(blueprint.cta or "").strip()
    if cta and not any(cta.casefold() in p.casefold() for p in paragraphs):
        if platform_key == "linkedin":
            paragraphs.append(cta)
        elif "?" not in cta:
            paragraphs.append(cta)

    if not any("?" in p for p in paragraphs):
        topic = headline or hook or "this"
        paragraphs.append(f"What stands out to you about {topic.rstrip('?')}?")

    tags = [
        str(tag).strip()
        for tag in (blueprint.hashtags or [])
        if str(tag).strip()
    ]
    tags = [t if t.startswith("#") else f"#{t.lstrip('#')}" for t in tags]
    if tags:
        limit = 5 if platform_key == "linkedin" else 8 if platform_key == "instagram" else 3
        paragraphs.append(" ".join(tags[:limit]))

    return "\n\n".join(paragraphs).strip()
