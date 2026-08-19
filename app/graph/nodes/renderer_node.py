from __future__ import annotations

from copy import deepcopy

from app.core.logging import get_logger
from app.graph.models.layer9_models import SceneElement, SceneGraphOutput
from app.graph.state import ViolytState

logger = get_logger(__name__)

_PLATFORM_CANVAS = {
    "linkedin": (1200, 627),
    "instagram": (1080, 1080),
    "twitter": (1200, 675),
    "x": (1200, 675),
    "story": (1080, 1920),
}


def _canvas_for(platform: str, fmt: str) -> tuple[int, int]:
    fmt_lower = str(fmt or "static").strip().lower()
    if fmt_lower == "infographic":
        return (1080, 1350)
    if fmt_lower == "carousel":
        return (1080, 1080)
    return _PLATFORM_CANVAS.get(str(platform or "linkedin").lower(), (1200, 627))


def _ensure_scene_graph(
    scene_graph: SceneGraphOutput | None,
    *,
    platform: str,
    fmt: str,
    image_urls: list[str],
) -> SceneGraphOutput:
    if scene_graph is not None:
        return scene_graph
    width, height = _canvas_for(platform, fmt)
    elements: list[SceneElement] = [
        SceneElement(
            element_id="background",
            element_type="background",
            content="canvas",
            position={"x": 0, "y": 0, "width": width, "height": height},
            style={"role": "background"},
        )
    ]
    if image_urls:
        elements.append(
            SceneElement(
                element_id="hero_visual",
                element_type="visual",
                content="generated_image",
                position={"x": 0, "y": 0, "width": width, "height": height},
                style={"role": "visual"},
                asset_url=image_urls[0],
            )
        )
    return SceneGraphOutput(
        platform=platform,
        platform_ratio=f"{width}x{height}",
        canvas_width=width,
        canvas_height=height,
        layers=["background", "visual", "copy", "logo", "cta"],
        elements=elements,
        styles={},
        assets=list(image_urls),
    )


async def renderer_node(state: ViolytState) -> dict:
    """Deliver AI images through the Layer 9 scene-graph contract (platform ratios, layers, assets)."""
    visual_reasoning = state.get("visual_reasoning")
    blueprint = state.get("creative_blueprint")
    platform = state.get("platform", "linkedin")
    fmt = state.get("format", "static")
    evaluation = state.get("evaluation")

    image_urls: list[str] = []
    if visual_reasoning:
        image_urls = [u for u in (visual_reasoning.generated_image_urls or []) if u]
        if visual_reasoning.generated_image_url and visual_reasoning.generated_image_url not in image_urls:
            image_urls.insert(0, visual_reasoning.generated_image_url)

    scene_graph = _ensure_scene_graph(
        state.get("scene_graph"),
        platform=platform,
        fmt=fmt,
        image_urls=image_urls,
    )
    for url in image_urls:
        if url not in scene_graph.assets:
            scene_graph.assets.append(url)

    if not visual_reasoning:
        logger.warning("renderer_node.missing_visual_reasoning")
        return {
            "scene_graph": scene_graph,
            "final_output": {
                "platform": platform,
                "format": fmt,
                "canvas_ratio": scene_graph.platform_ratio,
                "canvas_width": scene_graph.canvas_width,
                "canvas_height": scene_graph.canvas_height,
                "asset_url": "",
                "asset_urls": [],
                "slide_count": 0,
                "render_status": "failed",
                "message": "No AI artwork available.",
                "blueprint_approved": bool(blueprint),
                "render_contract": "scene_graph",
                "layers": scene_graph.layers,
                "element_count": len(scene_graph.elements),
                "evaluation_passed": bool(evaluation.overall_pass) if evaluation else False,
            },
        }

    final_image_url = image_urls[0] if image_urls else ""
    logger.info(
        "renderer_node.scene_graph_deliver format=%s urls=%s elements=%s canvas=%s",
        fmt,
        len(image_urls),
        len(scene_graph.elements),
        scene_graph.platform_ratio,
    )

    updated_visual_reasoning = deepcopy(visual_reasoning)
    updated_visual_reasoning.generated_image_url = final_image_url
    updated_visual_reasoning.generated_image_urls = image_urls

    return {
        "visual_reasoning": updated_visual_reasoning,
        "scene_graph": scene_graph,
        "final_output": {
            "platform": platform,
            "format": fmt,
            "canvas_ratio": scene_graph.platform_ratio or f"{scene_graph.canvas_width}x{scene_graph.canvas_height}",
            "canvas_width": scene_graph.canvas_width,
            "canvas_height": scene_graph.canvas_height,
            "asset_url": final_image_url,
            "asset_urls": image_urls,
            "slide_count": len(image_urls),
            "render_status": "success" if final_image_url else "failed",
            "message": (
                "AI creative ready — scene graph bound (text baked in image)."
                if final_image_url
                else "Image generation returned no asset."
            ),
            "blueprint_approved": bool(blueprint),
            "render_contract": "scene_graph",
            "layers": scene_graph.layers,
            "element_count": len(scene_graph.elements),
            "evaluation_passed": bool(evaluation.overall_pass) if evaluation else False,
        },
    }
