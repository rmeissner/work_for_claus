# Plan: Ledger Nano Gen5 Case

Component: new model `models/ledger-nano-gen5-case/` and the webapp catalog expectations.

PR strategy: stacked

Execution mode: web; the assistant creates PRs, and only the user merges.

---

## Overview

Add a printable replacement case for a bare Ledger Nano Gen5 board. Its original case was opened
to verify the board's integrity. The board stays in the new case permanently, and the touchscreen,
the side button and the USB-C port stay usable. The board has the touchscreen glued on top and a
battery attached. Keep the case as simple as possible: two PLA parts that print without supports.
Like the original case, the board is screwed into posts on the inside of the screen side (the
bezel), and the tray closes the back with snap hooks.

1. Plan (this PR).
2. Bottom tray: holds the board and battery, with the USB-C and side-button openings.
3. Top bezel: a frame with a screen window and screw posts for the board that snaps onto the tray,
   plus the assembled preview.
4. Remove this plan.

---

## Architecture Decision

One generator script, `models/ledger-nano-gen5-case/generate.py`, built on the existing
`tools/stlkit` (`round_corners`, `extrude`, `assert_printable`, `write_stl`), like the other
generated models. It adds no new dependencies and no webapp changes, apart from the catalog test
expectation. All board dimensions are named parameters, so the case can be adjusted after a test
fit without touching the geometry code.

- **Tray:** a flat floor and four walls around a pocket for the board stack (board, screen,
  battery). Prints floor-down, so every wall is vertical and needs no supports. The USB-C and
  side-button openings are notches cut down from the top edge of the wall, so they need no bridging.
  The side button is pressed through its opening with a finger; there is no printed pusher.
- **Bezel:** a flat frame with a window over the touchscreen. It overlaps the screen's edge by a
  small lip. It prints face-down (the visible side on the bed) with snap hooks and screw posts
  pointing up, so neither needs supports. The hooks catch in grooves at the bottom of channels in
  the tray walls (the board leaves no room for a hook arm inside the pocket).
- **Screw posts:** as in the original case, posts rise from the inside of the bezel, outside the
  screen area, to the board's top surface. The board is screwed to them from the back (battery
  side) with small self-tapping screws that cut their own thread into the PLA. The board is thus
  held by the bezel, not by the tray.
- **Assembly:** screw the board into the bezel, then snap the tray on from behind.

### Alternatives Considered

- **Slip-in sleeve** (the first version of this plan): not usable, because the device has to stay
  in the case with the screen working.
- **Tray and bezel held together by screws:** sturdier, but needs more screws and bosses through
  the tray; the snap fit stays simpler. Only the board is screwed in, like in the original case.
- **Board held only by the bezel lip (no screws):** simpler, but the board could rattle and the
  original case used screws.
- **One-piece frame the board slides into:** one part, but the lips around the window are overhangs
  and inserting the board stack risks damaging it.

---

## Tech Specs

### Board measurements

The bare board's size is not published (the finished device is 79.40 × 53.35 × 8.64 mm), and no
teardown with dimensions was found. Phase 2 uses placeholders, each marked `# TODO: measure` in
`generate.py`, and the user replaces them with caliper measurements (all in mm) later:

- Board outline: length × width of the largest part of the stack (board, screen or battery).
- Stack height: from the lowest point (battery or underside parts) to the screen surface.
- Screen: visible area length × width and its offset from the board edges, and the width of the
  glued edge the bezel lip can rest on.
- USB-C: which short edge, centre offset from a long edge, height of its centre above the lowest
  point, and the plug's overmold size (so a cable fits).
- Side button: which edge, centre offset from a short edge, height of its centre, button size.
- Anything sticking out (flex cables, battery wires, antennas) that needs extra room.
- Screw holes in the board: how many, centre positions from the board edges, hole diameter, screw
  size and length, and the height from the board's top surface (where the posts rest) to the
  screen surface.

Placeholders: outline 76 × 50 mm (the device minus a ~1.7 mm shell per side), stack height 7.5 mm,
screen visible area 57 × 43 mm centred (2.8" 4:3 E Ink, 400 × 300 px), glued border 2 mm,
USB-C centred on a short edge at 3 mm height with a 12 × 7 mm plug opening, side button centred
on a long edge at 4 mm height, 8 mm long. Screws: 4 holes, 3 mm in from each board corner (outside
the screen area), M2 self-tapping (1.6 mm pilot hole, 4 mm post diameter), board top surface
1.5 mm below the screen surface.

### Parameters

- Board measurements above, plus `CLEARANCE` (default 0.3 mm per side), `WALL` (2.0 mm, to fit
  the hook channels), `FLOOR` (default 1.2 mm), bezel thickness (default 1.6 mm) and window lip
  (default 1 mm).
- Screw posts: positions, post diameter and pilot hole diameter as named parameters.
- `CORNER_RADIUS` (outer): a placeholder default of 3 mm, to be adjusted later by the user.
- Snap fit: hook arm 0.7 mm in a 0.8 mm channel, 0.4 mm barb overhang into a 1.2 mm groove with a
  45° roof, to tune after the first print.
- PLA, 0.4 mm nozzle, 0.2 mm layers.

### Outputs

- `tray.stl` and `bezel.stl`, each in its print orientation.
- `assembled.stl` (added in Phase 3): both parts put together, listed first as the preview.
- `project.json` with version `1.0` and a description covering print settings (PLA, no supports),
  assembly (screw the board into the bezel, snap on the tray) and the fact that the fit hasn't been tested yet.

### Validation

- `generate.py` asserts that each part is one connected, printable solid (`assert_printable`,
  `decompose()`), and that the board stack fits the pocket with the clearance on every side.
  In Phase 3 it also asserts that the bezel and tray don't intersect apart from the snap contact,
  that the posts stay outside the screen window and the board stack touches them only on its top
  surface.
- `pytest` checks that the committed STLs match the script.
- Add the slug to the expected list in `webapp/src/models/buildModels.test.ts` (Phase 2).
- Check the preview in the webapp and attach screenshots to each PR.

---

## Implementation Phases

### Phase 1 — Plan

**Depends on:** none. **Can run in parallel:** no.

This file only.

### Phase 2 — Bottom tray

**Depends on:** 1, approved (stacked). **Can run in parallel:** no.

Add `models/ledger-nano-gen5-case/` with `generate.py` (parameters and the tray), `project.json`
and `tray.stl`, plus the slug in `webapp/src/models/buildModels.test.ts`. Include the snap grooves
in the tray walls so Phase 3 only adds the bezel.

### Phase 3 — Top bezel and assembled preview

**Depends on:** 2. **Can run in parallel:** no.

Add the bezel with the screen window, lip, snap hooks and screw posts, plus `bezel.stl` and `assembled.stl` in
`project.json`. Bump the version if Phase 2 is already merged.

### Phase 4 — Remove the plan

**Depends on:** 3, merged. **Can run in parallel:** no.

Verify that phases 2 and 3 are merged and delete this file.

---

## Open Questions and Assumptions

- Board dimensions and screw positions are placeholders until the user measures the board; the
  fit is not verified.
- The battery must leave the screw holes reachable from the back; to check when measuring.
- The side button is pressed through an opening, not through a printed pusher. If it turns out to
  sit too deep to reach, a pusher can be added later.
- The corner radius is a placeholder and will be adjusted later.
- The clearance and snap-fit values are estimates and need a test print on Claus. Test the snap
  fit before putting the board in.
- The case adds no NFC, magnet or lanyard features. PLA doesn't block NFC.
