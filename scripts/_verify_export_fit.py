"""Show how much of the generated poster the export step destroys, crop vs letterbox."""
from __future__ import annotations

# gpt-image portrait bucket -> LinkedIn portrait export
CASES = [
    ("infographic / carousel", (1024, 1536), (1080, 1350)),
    ("square", (1024, 1024), (1080, 1080)),
    ("landscape static", (1536, 1024), (1200, 627)),
]


def crop_loss(src: tuple[int, int], tgt: tuple[int, int]) -> tuple[str, float]:
    sw, sh = src
    tw, th = tgt
    sa, ta = sw / sh, tw / th
    if abs(sa - ta) / ta <= 0.02:
        return "no crop", 0.0
    if sa > ta:
        crop_w = int(round(sh * ta))
        lost = (sw - crop_w) / sw
        return f"{(sw - crop_w) // 2}px off each side", lost
    crop_h = int(round(sw / ta))
    lost = (sh - crop_h) / sh
    return f"{(sh - crop_h) // 2}px off top AND bottom", lost


def letterbox_pad(src: tuple[int, int], tgt: tuple[int, int]) -> str:
    sw, sh = src
    tw, th = tgt
    scale = min(tw / sw, th / sh)
    nw, nh = round(sw * scale), round(sh * scale)
    return f"content {nw}x{nh}, pad {(tw - nw) // 2}px sides / {(th - nh) // 2}px top-bottom"


def main() -> int:
    for name, src, tgt in CASES:
        desc, lost = crop_loss(src, tgt)
        print(f"\n{name}:  {src[0]}x{src[1]}  ->  {tgt[0]}x{tgt[1]}")
        print(f"  OLD (crop)      : {desc}  = {lost:.1%} of the poster DESTROYED")
        print(f"  NEW (letterbox) : {letterbox_pad(src, tgt)}  = 0% destroyed")
    print("\nPadding is invisible because the brand background is a solid colour.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
