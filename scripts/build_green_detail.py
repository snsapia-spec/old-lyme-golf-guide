#!/usr/bin/env python3
"""Build a publication-ready golf-green terrain plate from a DroneDeploy DTM.

Inputs
------
--dtm        Georeferenced elevation raster (GeoTIFF preferred)
--boundary   GeoJSON polygon tracing the putting surface
--ortho      Optional georeferenced orthomosaic
--out-dir    Output directory

Outputs
-------
green_detail.png       transparent publication plate
green_detail.svg       vector-friendly plate
green_metrics.json     measured dimensions, relief, slope and fall direction

The script intentionally keeps third-party app screenshots out of the output.
Those images are calibration references only.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.path import Path as MplPath
from rasterio.mask import mask
from scipy.ndimage import gaussian_filter


def read_polygon(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("type") == "FeatureCollection":
        geom = data["features"][0]["geometry"]
    elif data.get("type") == "Feature":
        geom = data["geometry"]
    else:
        geom = data
    if geom["type"] != "Polygon":
        raise ValueError("Boundary must be a GeoJSON Polygon")
    return geom


def compass_name(degrees: float) -> str:
    names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return names[int((degrees + 22.5) // 45) % 8]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dtm", required=True, type=Path)
    p.add_argument("--boundary", required=True, type=Path)
    p.add_argument("--ortho", type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--contour-ft", type=float, default=0.5)
    p.add_argument("--smooth-sigma", type=float, default=1.2)
    p.add_argument("--arrow-step", type=int, default=18)
    args = p.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    geom = read_polygon(args.boundary)

    with rasterio.open(args.dtm) as src:
        clipped, transform = mask(src, [geom], crop=True, filled=False)
        z = clipped[0].astype("float64")
        nodata_mask = np.ma.getmaskarray(clipped[0])
        xres = abs(transform.a)
        yres = abs(transform.e)
        crs = src.crs.to_string() if src.crs else None

    valid = ~nodata_mask & np.isfinite(z)
    if not valid.any():
        raise RuntimeError("No valid DTM pixels intersect the green boundary")

    fill = float(np.nanmedian(z[valid]))
    working = np.where(valid, z, fill)
    smooth = gaussian_filter(working, sigma=args.smooth_sigma)
    smooth[~valid] = np.nan

    dz_dy, dz_dx = np.gradient(smooth, yres, xres)
    slope = np.hypot(dz_dx, dz_dy)
    slope_pct = slope * 100.0
    down_x = -dz_dx
    down_y = dz_dy

    rows, cols = smooth.shape
    rr, cc = np.mgrid[0:rows, 0:cols]
    xs = transform.c + (cc + 0.5) * transform.a
    ys = transform.f + (rr + 0.5) * transform.e

    zmin = float(np.nanmin(smooth))
    zmax = float(np.nanmax(smooth))
    relief = zmax - zmin

    # Convert to feet only when projected coordinates/elevations are already feet.
    # The project config records units explicitly; until then metrics retain source units.
    poly = np.asarray(geom["coordinates"][0], dtype=float)
    width = float(poly[:, 0].max() - poly[:, 0].min())
    depth = float(poly[:, 1].max() - poly[:, 1].min())

    weights = np.where(valid, slope, 0.0)
    vx = float(np.nansum(down_x * weights))
    vy = float(np.nansum(down_y * weights))
    bearing = (math.degrees(math.atan2(vx, vy)) + 360.0) % 360.0

    metrics = {
        "crs": crs,
        "source_units": "FIELD_VERIFY_FROM_CRS",
        "green_width_bbox": width,
        "green_depth_bbox": depth,
        "minimum_elevation": zmin,
        "maximum_elevation": zmax,
        "elevation_range": relief,
        "average_slope_percent": float(np.nanmean(slope_pct[valid])),
        "median_slope_percent": float(np.nanmedian(slope_pct[valid])),
        "p90_slope_percent": float(np.nanpercentile(slope_pct[valid], 90)),
        "dominant_downslope_bearing_degrees": bearing,
        "dominant_downslope_compass": compass_name(bearing),
        "contour_interval": args.contour_ft,
    }
    (args.out_dir / "green_metrics.json").write_text(json.dumps(metrics, indent=2))

    fig, ax = plt.subplots(figsize=(4, 5.4), dpi=300)
    ax.set_aspect("equal")
    ax.set_axis_off()

    if args.ortho:
        with rasterio.open(args.ortho) as ortho:
            rgb, otransform = mask(ortho, [geom], crop=True, filled=True)
            if rgb.shape[0] >= 3:
                image = np.moveaxis(rgb[:3], 0, -1)
                lo, hi = np.percentile(image[image > 0], [2, 98])
                image = np.clip((image - lo) / max(hi - lo, 1), 0, 1)
                extent = [
                    otransform.c,
                    otransform.c + image.shape[1] * otransform.a,
                    otransform.f + image.shape[0] * otransform.e,
                    otransform.f,
                ]
                ax.imshow(image, extent=extent, alpha=0.42)

    levels_fill = np.linspace(zmin, zmax, 14)
    ax.contourf(xs, ys, smooth, levels=levels_fill, cmap="turbo", alpha=0.72)

    interval = args.contour_ft
    start = math.floor(zmin / interval) * interval
    contour_levels = np.arange(start, zmax + interval, interval)
    ax.contour(xs, ys, smooth, levels=contour_levels, colors="white", linewidths=0.45, alpha=0.85)

    step = max(args.arrow_step, 1)
    ar = np.s_[step // 2 :: step, step // 2 :: step]
    keep = valid[ar] & (slope_pct[ar] >= 0.75)
    ax.quiver(
        xs[ar][keep], ys[ar][keep], down_x[ar][keep], down_y[ar][keep],
        color="black", angles="xy", scale_units="xy", scale=None,
        width=0.006, headwidth=4.2, headlength=5.2, headaxislength=4.6,
    )

    ax.plot(poly[:, 0], poly[:, 1], color="black", linewidth=1.6)
    ax.text(0.02, 0.98, "HOLE 1 GREEN", transform=ax.transAxes, va="top", ha="left", fontsize=11, weight="bold")
    ax.text(0.02, 0.03, f"Dominant fall: {metrics['dominant_downslope_compass']}  |  Relief: {relief:.2f} source units",
            transform=ax.transAxes, va="bottom", ha="left", fontsize=6.5)

    fig.tight_layout(pad=0)
    fig.savefig(args.out_dir / "green_detail.png", transparent=True, bbox_inches="tight", pad_inches=0.02)
    fig.savefig(args.out_dir / "green_detail.svg", transparent=True, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    main()
