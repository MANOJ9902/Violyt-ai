"""Brand Space reference templates — format match + isolation."""

from __future__ import annotations

from app.services.image_generation.reference_template import (
    extract_brand_references,
    infer_template_format,
    select_reference_template,
    template_follow_lock,
)


def test_infer_format_from_filename() -> None:
    assert infer_template_format({"name": "Q2 carousel deck.png"}) == "carousel"
    assert infer_template_format({"name": "product infographic poster.png"}) == "infographic"
    assert infer_template_format({"name": "linkedin static banner.png"}) == "static"


def test_select_carousel_reference_when_format_is_carousel() -> None:
    refs = extract_brand_references(
        visual_identity={
            "reference_creatives": [
                {
                    "name": "Education carousel.png",
                    "storage_path": "brand-a/carousel.png",
                    "url": "/storage/brand-a/carousel.png",
                },
                {
                    "name": "Infographic poster.png",
                    "storage_path": "brand-a/info.png",
                    "url": "/storage/brand-a/info.png",
                },
            ]
        }
    )
    chosen = select_reference_template(refs, fmt="carousel", user_prompt="make a swipe deck")
    assert chosen.get("name") == "Education carousel.png"
    assert chosen.get("storage_path") == "brand-a/carousel.png"


def test_select_infographic_from_prompt_when_format_blank() -> None:
    refs = extract_brand_references(
        knowledge={
            "template_files": [
                {
                    "name": "static-feed.png",
                    "storage_path": "brand-a/static.png",
                    "url": "/s/static.png",
                },
                {
                    "name": "annual infographic.png",
                    "storage_path": "brand-a/info.png",
                    "url": "/s/info.png",
                },
            ]
        }
    )
    chosen = select_reference_template(refs, fmt="", user_prompt="Create an infographic about onboarding")
    assert "infographic" in (chosen.get("name") or "").casefold()


def test_template_lock_never_mentions_built_in_samples() -> None:
    lock = template_follow_lock({"name": "Brand A carousel.png"}, fmt="carousel")
    assert "Brand A carousel.png" in lock
    assert "airports" not in lock.casefold()
    assert "jiraaf" not in lock.casefold()
    assert "letter-perfect spelling" in lock


def test_extract_skips_other_brand_paths_by_explicit_list() -> None:
    refs = extract_brand_references(
        visual_identity={
            "reference_creatives": [
                {"name": "This brand.png", "storage_path": "brand-a/a.png", "url": "/a.png"},
            ]
        },
        knowledge={
            "template_files": [
                {"name": "Also this brand.pdf", "storage_path": "brand-a/b.pdf", "url": "/b.pdf"},
            ]
        },
    )
    names = {r["name"] for r in refs}
    assert names == {"This brand.png", "Also this brand.pdf"}
    assert all("brand-a/" in (r.get("storage_path") or "") for r in refs)
