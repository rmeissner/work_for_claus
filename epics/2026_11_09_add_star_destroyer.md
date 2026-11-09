# Plan: Slot-Together Star Destroyer

Component: `models/star-destroyer/` and the webapp catalog expectations.

PR strategy: merge each

Execution mode: web; the assistant creates PRs, and only the user merges.

## Overview

Create a small Star Destroyer kit with an enclosed wedge hull, raised buildings,
three recessed engines, and a bridge with two deflector shields. Target roughly
150 mm assembled length and support-free flat printing on Claus.

The user's annotated drawing and follow-up replace the original intersecting-plate
design. The user approved splitting the revision into hull/rear-panel work in
PR #66, then bridge/shields in the next PR. The original four-plate geometry is
superseded; implementation follows these revised requirements.

## Architecture Decision

Use one Python generator built on the existing `tools/stlkit` and `manifold3d`,
committed STLs, and `project.json`. No production viewer change or new dependency
is expected. Model folders contain only `generate.py`, metadata, and STLs.

The hull prints as a connected unfolded net, with grooves for hand folding at
room temperature, following the approach used by the 24-point star. A seven-face
stern includes narrow side facets and an 8 mm flat mounting strip between the
two building panels. The strip tapers toward the bow as part of the folding fan.
A transverse engine blade rises into the loosely folded hull from below. Its
single top tab enters a closed hole in the flat mounting strip.
The two lower faces then engage rear-open slits beneath the blade's two wider,
1 mm bottom hooks, holding the lower seam shut. This replaces the rejected rear cap, tapered
plug, and outer collar. Coincident edges alone are insufficient for retention.

Three raised engine bells print on top of the flat blade, with deep recesses
opening upward to avoid supports. The blade supports the future bridge holder.
Allow realistic clearances and leave closed stern material behind the top
tab hole. The lower slits require guided engagement beneath the wider hooks;
do not claim a complete rigid folding path or tested physical flexibility.

### Alternatives Considered

- Intersecting plates were too skeletal for the requested appearance.
- A four-face diamond hull concentrates the flank bend into an approximately
  155-degree fold. Narrow side faces split this into two gentler folds.
- Warm folding is excluded by the user: the design must target hand assembly
  at room temperature, with physical success to be verified on a test print.

## User Flow

The browser lists the assembled preview first, followed by printable layout(s)
and individual replacement parts. Its description explains print settings,
folding direction, rear-panel/seam assembly, and unverified physical fit.
The preview and flat STLs come from the same geometric definition.

## Tech Specs

- Hull surface: **0.6 mm**. Raised building areas reach **1.2 mm** and **1.8 mm
  total thickness**, not extra joining-tab thickness. Keep them clear of folds.
- Add explicit folding grooves and a configurable remaining ligament thickness;
  review both hinge continuity and room for the folded panel thickness.
- Use the conservative toolkit envelope of 220 x 220 mm for each print plate.
- Engine blade: three raised, recessed/tapered engine bells with intact floors;
  two lower retaining hooks, one top locking tab, and bearing shoulders beneath
  the mounting strip. Close the obsolete bridge-mount slot in the blade.
  The lower panels have rear-open mating slits; the mounting strip has one closed
  tab hole with at least 1 mm of material remaining toward the stern.
- Bridge support: a compact, broad tower on the aft flat mounting strip, between
  the two building panels. Match the longitudinal hull slope and keep the reach
  short. Taper the body toward the upper bridge landing.
- A short integral dovetail rail on the strip engages a channel under the tower
  and blocks lifting. Slide the tower into position before installing the engine
  blade; the blade's compact top tab then enters the tower pocket and blocks
  reverse sliding. A small bearing shoulder supports the underside of the strip.
  This replaces a purely locating saddle fit without adding a
  flexible snap or a loose fastener. Verify both restraints and their assembly order.
- Future bridge: a volumetric shape, interpreting the drawing's **10 mm** as
  fore-aft depth unless corrected; two top shield details. Choose a support-free
  shield construction and explain any approximation to spherical shape.
- Keep the accepted upper bridge exterior and shields. A keyed peg on the bridge
  underside enters a socket in the tower; the hidden coupling may change to make
  both parts printable. Print the tower inverted with its mounting channel upward and
  the bridge top-face-down with its peg upward. Check any short socket bridges
  and expanding tapers rather than requiring supports inside the mounting channel.
- Use named parameters for dimensions, shell/building heights, folds, and fit.
- Do not claim successful cold folding or secure retention before a physical
  print. PLA groove thickness and clearance may need adjustment on Claus.
- Export `combined.stl`, print layout(s), and one STL per actual printable part.
  Remove obsolete skeletal part files and list every remaining STL in metadata.
- Metadata includes current dimensions, estimated material use, assembly order,
  and a version bump whenever the model changes.
- Use the matching version 1.7 hull, engine blade, and tower together; earlier
  versions have different rail/tab dimensions. The accepted upper bridge and shields
  can be reused.

### Validation

Follow the README: no model-script unit tests. Put meaningful geometry assertions
in the generator and run the existing deterministic STL regeneration test.
Check valid connected printable parts, separated parts on the plate, continuous
hinge ligaments, thickness-aware folded geometry, and actual mating features.
Distinguish intended fit contact from destructive part intersections. Verify that
retaining features can be assembled and do not obstruct the engine cavities.

Run Python lint/format and pytest, webapp tests/lint/typecheck/build. Update both
catalog expectations when adding the model. Inspect the flat layout, top/side
hull silhouette, and stern/engines in the browser; attach current screenshots.
Keep an explicit physical-test limitation in the PR.

## Implementation Phases

### Phase 1 — Plan

**Depends on:** none. **Can run in parallel:** no.

Original planning PR #65, already merged. This document records the subsequent
user-approved design correction and phase split.

### Phase 2 — Folding hull and engine panel

**Depends on:** 1, merged. **Can run in parallel:** no.

Revise PR #66 with the thin folded shell, raised buildings, bottom-hooked engine blade,
three engine recesses, flat/assembled exports, and catalog instructions. Remove
obsolete spine/rib/bridge parts from the rejected skeletal iteration. Reserve
the bridge mount but do not include bridge/shield parts in this PR.

### Phase 3 — Bridge, holder, and shields

**Depends on:** 2, merged after user review. **Can run in parallel:** no.

Add the compact tower, integral flat-strip dovetail, volumetric bridge, and two
top shields. Validate mounting-strip seating, anti-lift and anti-slide retention,
peg/socket fits, print orientations, staged assembly access, and the complete silhouette.
Update metadata, version, exports, and screenshots.

### Phase 4 — Remove the plan

**Depends on:** 3, merged. **Can run in parallel:** no.

Verify all phases and remove this specification. Do not change the glider epic.

## Open Questions and Assumptions

- PLA, a 0.4 mm nozzle, 0.2 mm layers, and roughly 150 mm length are assumed.
- Cold folding is required; hinge durability and retention need a physical print.
- The seven-face stern and 10 mm bridge-depth interpretation are implementation
  choices derived from the drawing, to review through the next previews.
- No flight requirement, magnets, coins, or separate display stand.
