# RPS Flag Hunt

Two players move hidden Rock, Paper, and Scissors pieces across the board.
Capture the opposing Flag to win.

## Print the game

- Print one [board](../models/rps-flag-hunt/board.stl) flat, with the seats
  facing up. The full board measures 148 × 128 × 3.2 mm.
- Print the [14-piece team plate](../models/rps-flag-hunt/team-plate.stl) once
  per player in a distinct color. Print the pieces upright on their circular
  feet. [Individual STLs](../models/rps-flag-hunt/) are available for test prints
  and replacements.
- Start with PLA, a 0.4 mm nozzle, and 0.2 mm layers. Print at 100% scale with
  supports off. Each piece is 50 mm tall with a 20 mm diameter circular foot.

Use the [2 × 2 test board](../models/rps-flag-hunt/test-board-2x2.stl) to
check fit before printing the full board. It measures 48 × 48 × 3.2 mm and
uses the same beveled seats, 20 mm spacing, and outer bevel. Print it
flat with the seats up to test the recessed “Claus RPS” lettering against
the build plate. The 20 mm feet touch at nominal size when centered
in neighboring seats. Check that two printed pieces can sit next to each
other and lift out separately, then try filling a seven-piece row on the
full board before printing the second team. Remove any brim from the feet
and tune your slicer's XY or elephant-foot compensation if the fit is tight.

## Set up

1. Sit opposite each other along the board's long edges. The board is seven
   columns wide and six rows deep. The notches on the side rims mark the
   boundary between each player's two setup rows and the two middle rows.
2. Take four Rocks, four Papers, four Scissors, one Bomb, and one Flag of
   your color. Secretly place them in any order, one piece in each seat of
   the two rows nearest you. Leave the two middle rows empty.
3. Face each piece's engraved side toward its owner. Keep it that way
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
