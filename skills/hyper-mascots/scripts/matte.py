#!/usr/bin/env python3
"""Cut the guide character out of black, using a BiRefNet v2 mask.

  matte.py <raw_dir> <mask_dir> <out_dir> <glow|outline> [captions|all]

raw_dir and mask_dir hold matching PNG frames (the generated clip, and the
mask BiRefNet returned for it). The mask is the character: body and rings,
always solid. Two finishes:

  glow     for dark surfaces. The character is opaque; the yellow glow around
           it keeps a transparency taken from its brightness.
  outline  for light surfaces. No glow; a cel-shaded ink outline is drawn
           around the silhouette so it reads on any colour.

Needs: pip install pillow numpy scipy
"""
import glob, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

value = os.environ.get("MASCOT_INK", "#0B0B0F").lstrip("#")
if len(value) != 6:
    raise ValueError("MASCOT_INK must be a six-digit RGB hex color")
INK = np.array([int(value[index:index+2], 16) for index in (0, 2, 4)], np.float32) / 255.0


def prepare_mask(mask, keep_mode="captions"):
    if keep_mode not in ("captions", "all"):
        raise ValueError("keep mode must be captions/all")
    m = np.clip((mask.astype(np.float32) / 255.0 - 0.12) / 0.7, 0, 1)
    original = m.copy()
    stats = {"bottom_rule_pixels": 0, "distance_rule_pixels": 0}
    lab, n = ndi.label(m > 0.4)
    if keep_mode == "captions" and n > 1:
        sizes = ndi.sum(m > 0.4, lab, range(1, n + 1))
        main_id = 1 + int(np.argmax(sizes))
        main = lab == main_id
        near = ndi.binary_dilation(main, iterations=max(2, m.shape[1] // 14))
        nearby = set(np.unique(lab[near & (lab > 0)]))
        centres = ndi.center_of_mass(m > 0.4, lab, range(1, n + 1))
        bottom = {i for i, centre in enumerate(centres, 1) if i != main_id and centre[0] >= m.shape[0] * 0.86}
        distant = set(range(1, n + 1)) - nearby - bottom
        stats["bottom_rule_pixels"] = int(np.count_nonzero(np.isin(lab, list(bottom))))
        stats["distance_rule_pixels"] = int(np.count_nonzero(np.isin(lab, list(distant))))
        keep = np.isin(lab, list(nearby - bottom))
        m *= ndi.binary_dilation(keep, iterations=2)
    stats["dropped_pixels"] = int(np.count_nonzero((original > 0.4) & (m <= 0.4)))
    return m, stats


def matte(rgb, mask, style, keep_mode="captions", report=None):
    if style not in ("glow", "outline"):
        raise ValueError("style must be glow/outline")
    if rgb.shape[:2] != mask.shape:
        raise ValueError("raw frame and mask dimensions must match")
    a = rgb.astype(np.float32) / 255.0
    m, stats = prepare_mask(mask, keep_mode)
    w = m.shape[1]
    if report is not None:
        report.update(stats)
    if style == "outline":
        r = max(2, round(w / 60))  # ink width: about 5px on a 320px frame
        yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
        ring = ndi.grey_dilation(m, footprint=(xx * xx + yy * yy) <= r * r)
        ring = ndi.gaussian_filter(ring, 0.6)
        alpha = np.maximum(m, ring)
        out = a * m[..., None] + INK * (1 - m[..., None])
    else:
        mx = a.max(axis=2)
        glow = np.clip((mx - 0.07) / 0.5, 0, 1)
        discarded = (mask > 102) & (m <= 0.4)
        glow[ndi.binary_dilation(discarded, iterations=max(2, w // 60))] = 0
        alpha = np.maximum(m, glow)
        # Un-premultiply the glow so it is not darkened twice when composited.
        un = np.clip(a / np.maximum(glow[..., None], 0.08), 0, 1)
        out = a * m[..., None] + un * (1 - m[..., None])
    return (np.dstack([out, alpha]) * 255).astype(np.uint8)


if __name__ == "__main__":
    if len(sys.argv) not in (5, 6):
        raise SystemExit("usage: matte.py <raw_dir> <mask_dir> <out_dir> <glow|outline> [captions|all]")
    raw, masks, dst, style = sys.argv[1:5]
    mode = sys.argv[5] if len(sys.argv) == 6 else "captions"
    files = sorted(glob.glob(os.path.join(raw, "*.png")))
    if not files:
        raise SystemExit("No raw PNG frames found")
    names = {os.path.basename(f) for f in files}
    mask_names = {os.path.basename(f) for f in glob.glob(os.path.join(masks, "*.png"))}
    if names != mask_names:
        raise SystemExit("Raw/mask frame names must match exactly; check duration, fps and frame extraction")
    os.makedirs(dst, exist_ok=True)
    largest = (0, "none")
    max_bottom = 0
    max_distance = (0, "none")
    for f in files:
        name = os.path.basename(f)
        rgb = np.asarray(Image.open(f).convert("RGB"))
        mk = np.asarray(Image.open(os.path.join(masks, name)).convert("L"))
        report = {}
        Image.fromarray(matte(rgb, mk, style, mode, report), "RGBA").save(os.path.join(dst, name))
        max_bottom = max(max_bottom, report["bottom_rule_pixels"])
        if report["distance_rule_pixels"] > max_distance[0]:
            max_distance = (report["distance_rule_pixels"], name)
        if report["dropped_pixels"] > largest[0]:
            largest = (report["dropped_pixels"], name)
    result = {"keep_mode": mode, "frames": len(files), "max_dropped_pixels": largest[0],
              "max_bottom_rule_pixels": max_bottom, "max_distance_rule_pixels": max_distance[0],
              "distance_frame": max_distance[1]}
    print(json.dumps(result))
    if max_distance[0]:
        print(f"WARNING: distance filter removed {max_distance[0]} pixels at {max_distance[1]}; inspect detached props or use keep=all", file=sys.stderr)
