# RPS Flag Hunt

Two players move hidden Rock, Paper, and Scissors pieces across the board.
Capture the opposing Flag to win.

## Print the game

- Print one [board](../models/rps-flag-hunt/board.stl) flat, with the seats
  facing up. The full board measures 169 × 146 × 3.2 mm.
- The board's underside is a rib grid that saves filament; it prints seats up
  without supports.
- Print one team plate per player, each in that player's color. Choose the
  [spiky-haired ninja team](../models/rps-flag-hunt/ninja-team-plate.stl) or the
  [swept-haired rival team](../models/rps-flag-hunt/rival-ninja-team-plate.stl).
  Each plate holds 14 bodies and 14 keyed heads. Print the parts upright on
  their circular feet; the two teams can play against each other or two sets
  of the same design.
- Start with PLA, a 0.4 mm nozzle, and 0.2 mm layers. Print at 100% scale with
  supports off. Every figure has a 20 mm circular foot, and the board seats are 23 mm
  apart, leaving a 3 mm gap between neighboring feet.
- The [board preview](../models/rps-flag-hunt/board-assembled.stl) shows both
  teams standing in their setup rows. The assembled
  [ninja](../models/rps-flag-hunt/ninja-assembled.stl) and
  [rival](../models/rps-flag-hunt/rival-ninja-assembled.stl) previews show a
  single figure.

### Test the fit

Before printing a whole team, test the fit with one body and head. Either
print a team plate and use two parts from it, or extract one body and head from
the plate in your slicer and print only those.

1. Slide the head straight onto the keyed neck peg. The peg and socket have
   the same nominal dimensions. If the fit is tight, check the socket opening
   for first-layer flare and adjust your slicer's elephant-foot compensation.
2. Check that the assembled figure fits a seat and that you can read the rear
   symbol from your side. Neighboring seats are 23 mm apart, so the 20 mm
   feet have a 3 mm gap. Check that two figures can sit next to each other and
   lift out separately.
3. Fill a seven-piece row on the board before printing the second team. Remove
   any brim from the feet and tune your slicer's XY or elephant-foot
   compensation if the fit is tight.

Each team has four Rock, four Paper, four Scissors, one Bomb, and one Flag.

## Set up

1. Sit opposite each other along the board's long edges. The board is seven
   columns wide and six rows deep. The notches on the side rims mark the
   boundary between each player's two setup rows and the two middle rows.
2. Take four Rocks, four Papers, four Scissors, one Bomb, and one Flag of
   your color. Secretly place them in any order, one piece in each seat of
   the two rows nearest you. Leave the two middle rows empty.
3. Point each piece's rear role symbol toward its owner. Keep it that way
   except when revealing roles during an attack.
4. Decide who goes first at random. Players alternate turns.

## Take a turn

Choose one of your Rocks, Papers, or Scissors. Move it one square forward,
backward, left, or right. Enter the square if it is empty. If an opposing
piece occupies it, attack that piece. Your own pieces block movement.

Bombs and Flags stay in their starting squares. You must take a legal move
or attack if you have one. Jumping, diagonal moves, and passing are forbidden.

## Resolve an attack

Reveal the attacker and defender to both players.

| Matchup | Result |
| --- | --- |
| Two different mobile roles | Rock beats Scissors, Scissors beats Paper, and Paper beats Rock. Remove the loser. |
| Same mobile role | Remove both pieces. |
| Scissors attacks a Bomb | Remove the Bomb. |
| Rock or Paper attacks a Bomb | Remove the attacker. The Bomb stays in place. |
| Any mobile piece attacks the Flag | The attacker captures the Flag and wins immediately. |

When the attacker survives and the defender is removed, move the attacker onto
the defender's square. A surviving defender stays in place. Turn any surviving
piece back toward its owner.

## End the game

You win by capturing the opposing Flag or when your opponent starts their turn
with no legal move or attack.

Keep a shared count of consecutive turns without combat. Each player's move
counts as one turn. Start at zero and reset to zero after every attack.
After 40 consecutive turns without combat, the game is a draw if the next
player has a legal move or attack. If they have none, they lose.
