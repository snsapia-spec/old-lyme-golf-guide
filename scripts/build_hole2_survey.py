#!/usr/bin/env python3
"""Build survey-derived Hole 2 diagnostic assets.

This script never invents golf features. It reads already-extracted DroneDeploy
files, records their geometry, and produces orthomosaic/DTM diagnostic plates
that must be reviewed before any illustrated map is drawn.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

try:
    import rasterio
    from rasterio.enums import Resampling
except ImportError:  # JPEG + TFW mode can still run.
    rasterio = None
    Resampling = None


ORTHO_HINTS = ("ortho", "orthomosaic")
DTM_HINTS = ("dtm", "elevation", "dem")


def files(root: Path, suffixes: Iterable[str]) -> list[Path]:
    wanted = {s.lower() for s in suffixes}
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in wanted)


def score(path: Path, hints: tuple[str, ...]) -> tuple[int, int]:
    name = path.name.lower()
    return (sum(h in name for h in hints), path.stat().st_size)


def choose(root: Path, suffixes: Iterable[str], hints: tuple[str, ...]) -> Path | None:
    candidates = files(root, suffixes)
    if not candidates:
        return None
    return max(candidates, key=lambda p: score(p, hints))


def read_world_file(path: Path) -> dict:
    vals = [float(v.strip()) for v in path.read_text().splitlines() if v.strip()]
    if len(vals) != 6:
        raise ValueError(f"Expected six values in world file: {path}")
    a, d, b, e, c, f = vals
    return {"a": a, "d": d, "b": b, "e": e, "c": c, "f": f}


def world_bounds(width: int, height: int, t: dict) -> list[float]:
    # World files store the center of the upper-left pixel.
    x0 = t["c"] - 0.5 * t["a"] - 0.5 * t["b"]
    y0 = t["f"] - 0.5 * t["d"] - 0.5 * t["e"]
    corners = []
    for col, row in ((0, 0), (width, 0), (0, height), (width, height)):
        x = x0 + col * t["a"] + row * t["b"]
        y = y0 + col * t["d"] + row * t["e"]
        corners.append((x, y))
    xs, ys = zip(*corners)
    return [min(xs), min(ys), max(xs), max(ys)]


def stretch_rgb(image: np.ndarray) -> np.ndarray:
    image = image.astype(np.float32)
    finite = image[np.isfinite(image)]
    positive = finite[finite > 0]
    sample = positive if positive.size else finite
    if not sample.size:
        return np.zeros_like(image, dtype=np.float32)
    lo, hi = np.percentile(sample, [1.5, 98.5])
    return np.clip((image - lo) / max(float(hi - lo), 1.0), 0, 1)


def save_ortho_plate(path: Path, out: Path, metadata: dict) -> None:
    if path.suffix.lower() in {".tif", ".tiff"} and rasterio is not None:
        with rasterio.open(path) as ds:
            scale = max(ds.width / 2600, ds.height / 2600, 1)
            h, w = max(1, int(ds.height / scale)), max(1, int(ds.width / scale))
            bands = [1, 2, 3] if ds.count >= 3 else [1, 1, 1]
            rgb = ds.read(bands, out_shape=(3, h, w), resampling=Resampling.bilinear)
            image = np.moveaxis(rgb, 0, -1)
            metadata["orthomosaic"] = {
                "path": str(path), "width": ds.width, "height": ds.height,
                "bands": ds.count, "crs": str(ds.crs),
                "transform": list(ds.transform), "bounds": list(ds.bounds),
            }
    else:
        with Image.open(path) as im:
            im = im.convert("RGB")
            width, height = im.size
            scale = max(width / 2600, height / 2600, 1)
            if scale > 1:
                im.thumbnail((int(width / scale), int(height / scale)), Image.Resampling.LANCZOS)
            image = np.asarray(im)
        tfw = path.with_suffix(".tfw")
        if not tfw.exists():
            tfws = list(path.parent.glob("*.tfw"))
            tfw = tfws[0] if len(tfws) == 1 else tfw
        info = {"path": str(path), "width": width, "height": height}
        if tfw.exists():
            transform = read_world_file(tfw)
            info.update({"world_file": str(tfw), "world_transform": transform,
                         "bounds": world_bounds(width, height, transform)})
        metadata["orthomosaic"] = info

    fig, ax = plt.subplots(figsize=(8, 12), dpi=220)
    ax.imshow(stretch_rgb(image))
    ax.set_title("HOLE 2 — SURVEY ORTHOMOSAIC\nGeometry review; no invented features", fontsize=13)
    ax.set_axis_off()
    fig.tight_layout(pad=0.25)
    fig.savefig(out / "hole2_orthomosaic_review.jpg", bbox_inches="tight", quality=95)
    plt.close(fig)


def save_dtm_plate(path: Path, out: Path, metadata: dict) -> None:
    if rasterio is None:
        raise RuntimeError("rasterio is required to process the DTM")
    with rasterio.open(path) as ds:
        scale = max(ds.width / 2200, ds.height / 2200, 1)
        h, w = max(1, int(ds.height / scale)), max(1, int(ds.width / scale))
        z = ds.read(1, out_shape=(h, w), resampling=Resampling.bilinear).astype(float)
        if ds.nodata is not None:
            z[z == ds.nodata] = np.nan
        z[~np.isfinite(z)] = np.nan
        metadata["dtm"] = {
            "path": str(path), "width": ds.width, "height": ds.height,
            "crs": str(ds.crs), "transform": list(ds.transform),
            "bounds": list(ds.bounds), "min": float(np.nanmin(z)),
            "max": float(np.nanmax(z)), "range": float(np.nanmax(z) - np.nanmin(z)),
        }

    gy, gx = np.gradient(z)
    slope = np.hypot(gx, gy)
    shade = np.cos(math.radians(45)) + 0.8 * (-gx + gy) / np.maximum(slope, 1e-9)

    fig, ax = plt.subplots(figsize=(8, 12), dpi=220)
    ax.imshow(z, cmap="terrain")
    valid = z[np.isfinite(z)]
    if valid.size:
        levels = np.linspace(float(np.nanmin(valid)), float(np.nanmax(valid)), 30)
        ax.contour(z, levels=levels, colors="black", linewidths=0.22, alpha=0.55)
    ax.imshow(shade, cmap="gray", alpha=0.22)
    ax.set_title("HOLE 2 — DTM TERRAIN REVIEW\nMeasured elevation surface", fontsize=13)
    ax.set_axis_off()
    fig.tight_layout(pad=0.25)
    fig.savefig(out / "hole2_dtm_review.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("source/hole-2"))
    parser.add_argument("--out", type=Path, default=Path("outputs/hole-2"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    if not args.source.exists():
        raise FileNotFoundError(f"Source directory does not exist: {args.source}")

    ortho = choose(args.source, (".tif", ".tiff", ".jpg", ".jpeg", ".png"), ORTHO_HINTS)
    dtm = choose(args.source, (".tif", ".tiff"), DTM_HINTS)
    kml = choose(args.source, (".kml",), ("hole2", "ortho"))
    las = choose(args.source, (".las", ".laz"), ("point", "cloud", "hole2"))
    obj = choose(args.source, (".obj",), ("scene", "mesh", "hole2"))

    if ortho is None:
        raise FileNotFoundError("No Hole 2 orthomosaic raster/JPEG was found")

    metadata = {
        "hole": 2,
        "pipeline": "survey-only",
        "publication_status": "DIAGNOSTIC_NOT_FINAL",
        "rules": [
            "Orthomosaic controls plan geometry",
            "DTM controls terrain and contours",
            "No bunker, water, tree, fairway, tee, or green may be invented",
            "Illustration begins only after diagnostic review",
        ],
        "supporting_sources": {
            "kml": str(kml) if kml else None,
            "point_cloud": str(las) if las else None,
            "mesh": str(obj) if obj else None,
        },
    }

    save_ortho_plate(ortho, args.out, metadata)
    if dtm:
        save_dtm_plate(dtm, args.out, metadata)
    else:
        metadata["dtm"] = {"status": "NOT_FOUND", "note": "Terrain metrics withheld."}

    (args.out / "hole2_source_report.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
