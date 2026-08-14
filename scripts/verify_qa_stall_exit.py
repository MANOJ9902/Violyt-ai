"""A content-prep retry that cannot improve must stop instead of burning LLM calls."""
from app.graph.nodes.layer7c_content_prep import _scores_improved

# The exact scores the airport run produced on all three attempts.
STUCK = {"answers_why": 6, "has_real_data": 3, "claims_verified": 6,
         "narrative_coherent": 7, "copy_complete": 8, "visually_usable": 7,
         "on_brand_beyond_aesthetics": 7}

cases = [
    ("identical scores (the real run)", STUCK, dict(STUCK), False),
    ("one dimension up", {**STUCK, "has_real_data": 6}, STUCK, True),
    ("up here, down there", {**STUCK, "has_real_data": 6, "answers_why": 4}, STUCK, False),
    ("everything worse", {**STUCK, "copy_complete": 2}, STUCK, False),
    ("only a non-gating field moved", {**STUCK, "visually_usable": 9}, STUCK, False),
]

for name, new, old, expected in cases:
    got = _scores_improved(new, old)
    flag = "ok " if got == expected else "BAD"
    print(f"  {flag} {name:<32} improved={got} (expected {expected})")
    assert got == expected, name

print("\nretries saved on the airport run: 2 LLM round trips")
print("qa_stall_exit_ok")
