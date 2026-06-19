# Mission 2 Difficulty Adjustments

Difficulty flag: `Player 8 / Terran Academy`

- `1 = easy`: first and repeated P6/P7 main assaults use the 32:15 / 33:00 / 33:45 cooldown band. Overmind Cocoon side selection always picks P6 when both colonies are still alive.
- `2 = normal`: first and repeated P6/P7 main assaults use the 26:15 / 27:00 / 27:45 cooldown band, main-assault waves gain about +10% units, and Hatchery/Lair/Hive kills accelerate that colony by 337.5 seconds.
- `3 = hard`: first and repeated P6/P7 main assaults use the 23:15 / 24:00 / 24:45 cooldown band, main-assault waves gain the hard layer plus an extra hard+ layer of about +12%, Hatchery/Lair/Hive kills accelerate that colony by 382.5 seconds, and also accelerate the opposite living colony by 191.25 seconds.
- `4 = very hard`: first and repeated P6/P7 main assaults use the same 23:15 / 24:00 / 24:45 cooldown band as hard, waves gain the very-hard layer plus the same hard+ layer, and Hatchery/Lair/Hive kills accelerate both living colonies by 427.5 seconds.

Main-assault cooldown jitter keeps the existing +/-30 second pattern from the first cycle:

- Easy: 32:15 / 33:00 / 33:45.
- Normal: 26:15 / 27:00 / 27:45.
- Hard: 23:15 / 24:00 / 24:45.
- Very hard: 23:15 / 24:00 / 24:45.

Extra Hatcheries spawn once when difficulty is locked:

- Normal: `P5 H1~P5 H2`, `P6 H1`, `P7 H1`.
- Hard: `P5 H1~P5 H4`, `P6 H1~P6 H2`, `P7 H1~P7 H2`.
- Very hard: `P5 H1~P5 H4`, `P6 H1~P6 H3`, `P7 H1~P7 H3`.

Before P5 extra Hatcheries are created, existing `Men` and `Buildings` at each used `P5 H#` location are moved to `P5 Spawn1`.

Compared with hard, very hard keeps the same main-assault cooldown band, hard+ wave layer, rewards, movement orders, 60-second relay timing, target correction, and Overmind Cocoon weakened-assault composition unchanged, but adds the very-hard wave layer and mirrors Hatchery/Lair/Hive kill acceleration at full strength to the opposite colony.

Main-assault warnings use a fixed schedule relative to spawn (coarse internal anchor at −180s, detailed at −90s, contact at −10s). Wave type is pre-seeded at game start and re-rolled after each consume, so difficulty cooldown boosts only shorten warning lead time; they do not skip warnings. Hatchery/Lair/Hive kills grant resources, cooldown acceleration, and production-web tally regardless of whether that colony's first main assault has started.
