"""Verify card titles/bodies never end as a dangling fragment."""
from __future__ import annotations

from app.services.image_generation.explain_image_prompt import _scrub as explain_scrub
from app.services.image_generation.lean_static_prompt import _scrub as static_scrub

CASES = [
    ("Organizations with strong talent strategies see better outcomes", 5),
    ("The role of CHROs in enterprise AI adoption is expanding fast", 5),
    ("AI can enhance employee training and development across the org", 6),
    ("Companies with engaged employees see 21% greater profitability", 4),
    ("CHROs leading AI transformation drive measurable retention gains", 12),
]

BAD_ENDINGS = {"with", "of", "and", "the", "in", "to", "for", "a", "an", "by", "at"}


def main() -> int:
    failures = 0
    print(f"{'budget':>7}  {'explain':<46} {'static'}")
    print("-" * 100)
    for text, budget in CASES:
        e = explain_scrub(text, max_words=budget)
        s = static_scrub(text, budget)
        for label, out in (("explain", e), ("static", s)):
            last = out.split()[-1].lower().strip(".,;:") if out.split() else ""
            if last in BAD_ENDINGS:
                failures += 1
                print(f"  FAIL {label}: {out!r} ends on {last!r}")
        print(f"{budget:>7}  {e:<46} {s}")

    print(f"\n{'PASS' if failures == 0 else 'FAIL'}: {failures} fragment(s)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
