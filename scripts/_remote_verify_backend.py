#!/usr/bin/env python3
from app.services.pipeline.format_resolution import resolve_pipeline_format
from app.graph.models.content_intelligence_models import AgencyBrief  # noqa: F401

r = resolve_pipeline_format(studio_format="static", user_prompt="make an infographic")
assert r.format == "infographic", r
print("backend_ok", r.format)
