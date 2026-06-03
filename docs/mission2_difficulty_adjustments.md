# Mission 2 Difficulty Adjustments

Difficulty flag: `Player 8 / Terran Academy`

- `1 = easy`: current Mission 2 behavior.
- `2 = normal`: first P6/P7 main assaults are advanced by 30 seconds, repeated main-assault standard cooldown is 17:00, and main-assault waves gain about +10% units.
- `3 = hard`: first P6/P7 main assaults are advanced by 60 seconds, repeated main-assault standard cooldown is 15:00, and main-assault waves gain about +15% units.

Repeated cooldown jitter keeps the existing +/-30 second pattern:

- Easy: 20:30 / 21:00 / 21:30.
- Normal: 16:30 / 17:00 / 17:30.
- Hard: 14:30 / 15:00 / 15:30.

Extra Hatcheries spawn once when difficulty is locked:

- Normal: `P5 H1~P5 H2`, `P6 H1~P6 H4`, `P7 H1~P7 H2`.
- Hard: `P5 H1~P5 H4`, `P6 H1~P6 H8`, `P7 H1~P7 H4`.

Before P5 extra Hatcheries are created, existing `Men` and `Buildings` at each used `P5 H#` location are moved to `P5 Spawn1`.

Rewards, movement orders, relay timing, target correction, and Overmind Cocoon weakened-assault composition are unchanged.
