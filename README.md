# Old Lyme Golf Guide

A visual, data-driven caddie guide for Old Lyme Country Club.

## Current focus: Hole 1

- Par: 4
- Handicap: 7
- Tees: 318 / 328 / 338 yards
- Current phase: geometry-accurate course survey before illustration/rendering
- Accuracy constraint: no right-side fairway bunker

## Source data

Project source material includes drone photography, photogrammetry mesh data, scorecard information, and course sketches.

Large binary survey assets are kept outside Git until they are reviewed and organized. The supplied OBJ references two texture maps that are not yet present:

- `scene_mesh_textured_material_00_map_Kd.jpg`
- `scene_mesh_textured_material_01_map_Kd.jpg`

## Workflow

1. Validate and orient the photogrammetry survey.
2. Identify Hole 1 tee, fairway, hazards, green, trees, and boundaries.
3. Review a clean survey visual.
4. Develop the illustrated caddie-guide rendering from the approved geometry.
