# Hole 1 Green Detail — Drone Terrain + Field-App Calibration

Status: in development

## Objective

Replace the generic Page 2 green image with a publication-quality Hole 1 green plate derived from the original DroneDeploy terrain workflow and calibrated against the newly supplied green heatmap, 3D-green, and putt-map screenshots.

The third-party screenshots are reference/validation data only. They are not to be reproduced as branded screenshots in the guide.

## Source hierarchy

1. DroneDeploy DTM / elevation raster — primary geometry and elevations
2. DroneDeploy orthomosaic — green, collar, bunker, water, and approach edges
3. DroneDeploy point cloud / mesh — secondary check for surface form
4. Supplied green-app screenshots — directional and qualitative validation
5. Garmin yardages — front / center / back distance reference

## Locked Hole 1 facts

- Par 4
- Handicap 7
- White tee: 330 yards
- Garmin: 318 / 328 / 338
- No right fairway bunker
- Unverified dimensions remain labeled FIELD VERIFY

## Green interpretation from supplied screenshots

The screenshots consistently indicate:

- dominant high area at the back-left portion of the green
- dominant low area at the front-right portion
- general fall from back-left toward front-right / pond side
- stronger downhill behavior for putts played from above the hole
- a broad internal transition/ridge rather than a simple planar tilt

These observations must be checked against the DroneDeploy DTM before publishing numeric slope or elevation values.

## Processing workflow

1. Load the georeferenced DTM and orthomosaic used for the first-hole rendering.
2. Clip a green-detail window that includes:
   - putting surface
   - collar
   - left-side bunker(s)
   - pond edge
   - final approach apron
3. Trace the actual green boundary from the orthomosaic.
4. Remove vegetation/noise artifacts from the DTM using a light median or Gaussian filter that preserves broad putting-surface form.
5. Normalize elevation within the traced green only.
6. Generate:
   - 0.25 ft working contours
   - 0.5 ft publication contours
   - optional 1.0 ft indexed contours
7. Compute slope magnitude and downslope aspect from the filtered DTM.
8. Suppress arrows below the minimum meaningful slope threshold and thin the vector field for legibility.
9. Compare the resulting high/low zones and arrow directions against every supplied app screenshot.
10. Flag discrepancies for manual inspection rather than forcing the terrain to match the screenshots.

## Page 2 graphic package

### Main green plate

- north-up or tee-to-green orientation, whichever matches the approved spread
- true green outline
- muted illustrated orthomosaic base
- subtle elevation tint, high = warm and low = cool
- 0.5 ft contour lines
- 12–18 simplified fall-line arrows
- visible bunker and pond relationship
- front, middle, and back labels

### Strategic overlays

- preferred approach zone: left-center / below-hole side, subject to terrain verification
- caution zone: above-hole back-left
- caution zone: front-right pond-side quadrant
- three pin-zone target diagrams
- three representative putt-break diagrams generated from the measured slope field

### Metrics panel

Publish only values directly computed from the terrain data:

- green depth
- maximum width
- elevation range
- average slope
- steepest practical putting zone
- dominant fall direction

Any value not resolved from the actual raster remains FIELD VERIFY.

## Editorial language — provisional

> The first green is highest toward the back-left and generally releases toward the front-right pond side. Approaches finishing below the hole leave the most controllable putts; shots above a back or left pin can become quick across the central fall line.

This text is provisional until the DTM-derived slope map is complete.

## Visual standard

The final plate must match the approved detailed illustrated style of the Hole 1 guide—not a watercolor wash and not a copied app interface. Contours, arrows, dimensions, labels, and strategy graphics should read clearly at the finished 4 × 7 inch page size.
