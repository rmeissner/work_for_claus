# Plan: RPS Flag Hunt

Component: `models/rps-flag-hunt/`, the Work for Claus catalog, and the rulebook.

PR strategy: merge each

Execution mode: web. The assistant opens PRs and the user merges them.

## Overview

Make a printable, two-player hidden-role board game. Players deploy their pieces
in secret and battle using rock–paper–scissors to capture the opposing flag.
Start with clipped cylinders, then add a grid that locates the pieces on their
squares. Try original character sculpts after the prototype has been printed
and played.

## Architecture Decision

Use a Python generator built on the repository's `tools/stlkit`. Commit the
generated STLs and register them in `project.json` so they can be previewed and
downloaded through the existing catalog. Define a common beveled foot for the
cylinder pieces so the board and later character pieces can fit the same
interface. Keep the permanent rules and print instructions in
`docs/rps-flag-hunt.md` and link them from the repository README.

Make each piece a short cylinder with a flattened edge so it stands upright.
Recess the rear face and engrave the role into the recess floor. The owner can
read the mark while the opponent across the board sees the identical blank
front of each piece. Print with the blank face down and the recess up.

### Alternatives Considered

Flat tokens would need to be lifted to check their roles. An upright piece
lets the owner read its marking while it stays on its square. Character
sculpts would add visual and printing constraints before the first playtest.

## User Flow

Download the board and one complete team plate from the catalog. Print the
board once and the plate twice, with one color per player. Use the individual
STLs for replacement pieces and test prints. Sit opposite each other and
follow the rulebook, keeping each piece's recessed face pointed at its owner.

## Tech Specs

### Printable prototype

- Board: seven columns across and six rows deep. Use 20 × 20 mm squares,
  including their beveled edges, for a 140 × 120 mm playing area plus any
  outer border. Mark the boundary between each two-row deployment zone and
  the two middle rows.
- Pieces: start at 18 mm diameter and about 10 mm front-to-back depth. Give
  each cylinder a flat, beveled foot that fits fully within a square and
  stands on a flat surface before the board is available. Keep the external
  dimensions and front geometry identical for all five roles.
- Fit: set the nominal foot dimensions and bevel in the pieces phase. In
  the board phase, add matching shallow seats that let pieces settle into
  place and lift out with one hand. Tune the seat clearance with a small
  fit print on Claus and check that adjacent pieces can be lifted separately.
- Recess: start at approximately 3 mm deep and engrave recognizable role
  symbols into its floor. Size strokes with a 0.4 mm nozzle in mind and keep
  the role marks fully inside the recess. Use the same filament and print
  settings for every role on a team. The two teams use distinct colors.
- Exports: one team-plate STL with 14 separated pieces and one standalone
  STL per role, followed by one board STL in the next phase. The board and
  pieces should print without supports at full scale. Start with PLA and
  0.2 mm layers.
- Validate mesh integrity, plate footprint, separation, and deterministic
  regeneration. Check the five recesses, blank fronts, flat feet, and board
  layout in the previews. Inspect a sliced first layer and the engraving
  layers when a slicer is available. A physical test will verify stability,
  legibility from the owner's seat, and concealment from the opponent's seat.

### Prototype rules

The prototype uses the board dimensions and team distribution from the
published rules for Rock Paper Scissors Ninja. RPS Flag Hunt uses a Bomb as
its stationary defensive piece. [Reference rules](https://app.alfonsosolutions.com/how-to-play/)

- Each team has four Rocks, four Papers, four Scissors, one Bomb, and one
  Flag. Decide who goes first at random. Each player secretly places their
  14 pieces across all the squares in the two rows nearest them. Pieces
  face their owners throughout play, except during combat reveals.
- On your turn, move one Rock, Paper, or Scissors one square orthogonally
  into an empty square or attack an adjacent opposing piece. Your own pieces
  block movement. Bombs and Flags stay where they were placed. Passing,
  jumping, and diagonal movement are forbidden.
- Reveal both roles when attacking. Rock beats Scissors, Scissors beats Paper,
  and Paper beats Rock. Remove the loser. If the attacker wins, move it onto
  the defender's square. If the defender wins, it stays put. A tie removes both
  pieces. Return any survivor to its owner-facing orientation.
- Scissors disarms a Bomb and takes its square. An attacking Rock or Paper
  is removed and the Bomb stays. Any mobile piece that attacks the opposing
  Flag wins immediately.
- A player with no legal move at the start of their turn loses. If 40
  consecutive turns end without combat and the next player has a legal move,
  the game is a draw. Count each player's move as one turn and reset the count
  after every combat.

## Implementation Phases

### Phase 1 — Epic plan

**Depends on:** none. **Can run in parallel:** no.

Agree on the printable design, proposed rules, and phased rollout in this PR.

### Phase 2 — Printable cylinder pieces

**Depends on:** phase 1. **Can run in parallel:** no.

Add the five cylindrical role pieces and the 14-piece team plate. Define the
shared foot dimensions and bevel. Register the model, include piece printing
instructions, and update the catalog expectations. Run model lint, format, and
regeneration checks, and validate the webapp catalog and build.

### Phase 3 — Printable board and rulebook

**Depends on:** phase 2. **Can run in parallel:** no.

Add the 7 × 6 board and register it in the catalog. Check the beveled seats
against the phase 2 feet. Publish the rulebook with setup, a combat reference,
win and draw conditions, and complete print instructions. Run model and
catalog checks and verify that pieces fit and lift out of neighboring seats.

### Phase 4 — Character pieces

**Depends on:** phase 3 and feedback from a first print and playtest.
**Can run in parallel:** no.

Develop original anime-inspired or similarly playful character pieces with
the same beveled foot. Use a common opponent-facing design across the five roles
within a team. Keep role markings recessed and owner-facing and preserve
role counts, stable placement, and printability. Keep the cylinder set
available for printing. Choose the character theme after prototype feedback.

### Phase 5 — Remove the plan

**Depends on:** phase 4. **Can run in parallel:** no.

Verify the printable sets, catalog downloads, and permanent rulebook, then
remove this epic specification.

## Assumptions and Playtest Checks

- Test the Scissors disarm rule and the 40-turn draw limit in the first playtest.
- Check sightlines with two people seated opposite each other.
- Confirm the pieces feel stable and the beveled seats keep them centered
  during play.
- The model assumes a flat build plate with room for the one-piece board.
- The character theme will be chosen after the prototype playtest.
