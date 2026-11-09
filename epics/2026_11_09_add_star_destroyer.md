# Plan: Slot-Together Star Destroyer

Component: `models/star-destroyer/` (new model) and the webapp's model-discovery test.

PR strategy: merge each

Execution mode: web; the assistant creates phase PRs, and only the user merges.

---

## Overview

Add a small, recognizable Star Destroyer spaceship kit made from four flat PLA
parts: a triangular hull deck, a central keel/superstructure, an underside
cross-rib, and a transverse bridge. The parts slot together without supports,
glue, magnets, or separate fasteners. This is a display/play model, with no flight
requirement.

The initial target is approximately 150 mm long, 90 mm wide, and 35 mm tall when
assembled. A broad wedge silhouette, layered-looking central superstructure,
and wide aft bridge supply the recognizable features without fragile antennae.

PRs: this plan; the complete printable model and catalog integration; removal
of this plan once the model PR is merged. Implementation waits for this plan PR
to be merged.

---

## Architecture Decision

### Four flat parts, one generator

Follow the existing stars and glider: a Python generator uses `tools/stlkit` and
`manifold3d`, exports committed STLs, and registers them in `project.json`.
No new dependency, viewer feature, or toolkit extension is expected.

The deck passes sideways through a closed horizontal slit in the central spine.
The spine retains material at both ends of that slit. The underside cross-rib
and the bridge attach with complementary, open-ended half-lap slots. Keep their
joints separate from the deck slit, and preserve a feasible assembly path:
attach the rib beneath the deck level, slide in the deck, then attach the bridge.
The rib supports the deck from below; the bridge sits above it near the stern.

Each individual part is a single connected solid. Rounded outer corners and a
blunted bow keep the silhouette robust. Omit small turrets and radar balls in
this first version; avoid adding loose decorative parts.

### Alternatives Considered

- A solid miniature uses more material and does not provide a slot-together kit.
- A fully paneled wedge with separate upper/lower skins has more joints and
  requires more fitting work. Four intersecting plates are simpler to assemble.
- Tiny separate engines, guns, or antennae add fragile pieces; suggest these
  features in the main outlines instead.

---

## User Flow

Select Star Destroyer in the existing model browser. The first file shows the
assembled ship, followed by the print plate and the individual replacement parts.
The description provides print settings, a part inventory, and assembly order.
There are no new pages or controls.

---

## Tech Specs

### Geometry and parameters

Initial values in `models/star-destroyer/generate.py`, in millimeters:

| Parameter | Initial value | Purpose |
|---|---|---|
| Hull deck length / width | 140 / 90 | Broad triangular wedge, flat stern |
| Spine length | 148 | Leaves material beyond both ends of the deck slit |
| Overall assembled height | about 35 | Includes keel and raised aft bridge |
| Part thickness | 2.0 | Ten 0.2 mm layers, sturdy flat plates |
| Slot clearance | 0.20 | Total added width, not per side |
| Minimum material around closed slots | 2.4 | Avoid thin walls at slit ends |
| Outer corner radius | at least 1.0 | Blunt bow, bridge ends, and rib tips |
| Plate gap | 5.0 | Separate parts for printing |

These are design targets, adjustable during geometric validation. Put thickness,
clearance, and overall dimensions in named constants. Do not scale an exported
STL to tune fit: scaling also changes the slot clearances. Expose clearance in
the generator for adjustment after a physical test print.

The deck outline is symmetric about the longitudinal centerline. The spine's
upper outline rises toward the stern in broad steps to suggest the command
superstructure. Use a transverse bridge approximately 30 mm wide and an
underside rib sized to remain within the deck outline. No isolated decorative
components or required support material.

Build each part in its own flat print pose at Z = 0; use rigid transforms for
the assembled preview. Validate the actual slotted shapes after rounding. The
rib's upper surface stays below the deck's insertion path; the bridge joint
does not intersect the deck or its slit. Check the swept deck insertion volume
against the installed spine and rib, as well as final-pose collisions.

### Files and catalog

The model folder contains only these eight files:

- `generate.py`, with `main()` writing next to the script using `Path(__file__)`;
- `project.json`, name `Star Destroyer`, initial version `1.0`;
- `combined.stl`: assembled preview, colored per part with `write_colored_stl`;
- `star-destroyer.stl`: all four parts arranged flat on one print plate;
- `part-hull.stl`, `part-spine.stl`, `part-rib.stl`, `part-bridge.stl`.

List all six STLs in `project.json`, in that order, with clear labels. Describe
printing in PLA at 0.2 mm layers without supports or a raft, with enough walls
and solid layers to make the 2 mm plates solid. Give assembly order and explain
that fit needs confirmation on Claus: do not force a tight joint; adjust the
clearance and regenerate if needed. Include measured bounds and calculated PLA
mass/filament estimates once generated, labeled as estimates. Do not describe
the kit as physically tested until a print has been assembled.

Use `layout_on_plate` with a layout that fits the toolkit's conservative
220 x 220 mm envelope, which also fits Claus' 256 x 256 mm build plate. The
assembled preview is for viewing, not for slicing as one piece.

Update the expected sorted model slugs in
`webapp/src/models/buildModels.test.ts` to include `star-destroyer` at the correct
position. The existing loader discovers the folder without production UI edits.

### Validation

Follow the README: do not add model-script unit tests. Add assertions inside
the generator, which also run during the existing STL regeneration check:

- Every part is nonempty, manifold, and one connected component.
- `assert_printable` passes for every flat part and for the complete print plate.
- Rounded outer profiles pass `assert_rounded` before intentional slot cuts;
  inspect the final slots for thin or detached prongs.
- All closed-slot walls meet the stated minimum, and slot widths include the
  configured clearance.
- Assembled parts have negligible pairwise intersection volume; support contact
  is allowed. The deck's sideways insertion path remains clear.
- The plate has four separated components and matches the exported part inventory.

Run `ruff check`, `ruff format --check`, and `pytest`, plus the webapp model tests,
typecheck, lint, and build. Inspect the assembled view from multiple angles and
the flat plate in the webapp; attach screenshots to the implementation PR. A
physical fit check on Claus remains a separate user validation.

---

## Implementation Phases

### Phase 1 — Plan

**Depends on:** none. **Can run in parallel:** no.

This specification only; no model or application changes.

### Phase 2 — Printable kit and catalog integration

**Depends on:** 1, merged by the user. **Can run in parallel:** no.

Add the eight model files above and update the single model-discovery expectation
in `webapp/src/models/buildModels.test.ts`. Keep the generator under approximately
300 lines and the PR to nine files. Reuse existing toolkit functions; if a shared
toolkit change becomes necessary, propose a separate phase before including it.

Review slot accessibility, material around joints, and recognizable silhouette.
The PR includes assembled/plate screenshots, generated dimensions and material
estimates, check results, and the unverified physical-fit limitation.

### Phase 3 — Remove the plan

**Depends on:** 2, merged by the user. **Can run in parallel:** no.

Delete this specification once all implementation work is merged. No unrelated
cleanup or changes to the glider epic.

---

## Open Questions and Assumptions

- Small means approximately 150 mm long; PLA and a 0.4 mm nozzle are assumed.
- This is a stylized Imperial Star Destroyer, prioritizing the wedge and bridge
  over screen-accurate surface detail.
- The initial 0.20 mm total slot clearance is a starting point. Printer accuracy
  and filament affect retention; only a physical print establishes the fit.
- No glue is required by the intended design. If friction retention is inadequate,
  revise the joint design rather than claiming an untested fit is secure.
- There are no magnets, coins, moving parts, display stand, or miniature variant.
- Work proceeds in web mode as explicitly clarified by the user, overriding the
  skill's environment-variable detection. Each phase PR targets `main`.
