---
name: trigedit-text-output
description: Use this skill when writing, editing, or reviewing SCMDraft 2 TrigEdit text output for this StarCraft Brood War UMS map, including Display Text Message, Set Mission Objectives, briefing Text Message strings, color/control codes, centered headers, dialogue readability, and separation between in-universe dialogue and system/gameplay instructions.
---

# TrigEdit Text Output Rules

Apply this skill whenever changing player-facing text in `KargasIV_Briefing.txt`, `Triggers/*.txt`, or generated TrigEdit trigger text.

## Core Rule

Make every displayed string serve one clear purpose:

- **Dialogue**: in-universe speech by a character or command channel.
- **Alert**: short tactical warning tied to an immediate event.
- **Objective**: mechanical mission instructions, preferably in `Set Mission Objectives`.
- **System/reward**: non-diegetic game information, clearly labeled or dressed as command/support text.

Do not let characters say raw editor/game terms when an in-universe phrase works. Prefer "아군 병력", "보안 타이머", "발신원", "비콘", "단말기" over "유닛", "카운트다운", or ambiguous "신호원" inside dialogue.

## SC1 Text Control Codes

SCMDraft string editor accepts one-byte control codes such as `<07>` inside strings. Use them sparingly; readability matters more than decoration.

| Code | Meaning |
|---|---|
| `<01>` | Use Default |
| `<02>` | Pale Blue |
| `<03>` | Yellow |
| `<04>` | White |
| `<05>` | Grey |
| `<06>` | Red |
| `<07>` | Green |
| `<08>` | Red (P1) |
| `<0B>` | Invisible |
| `<0C>` | Remove beyond |
| `<0E>` | Blue (P2) |
| `<0F>` | Teal (P3) |
| `<10>` | Purple (P4) |
| `<11>` | Orange (P5) |
| `<12>` | Right Align |
| `<13>` | Center Align |
| `<14>` | Invisible |
| `<15>` | Brown (P6) |
| `<16>` | White (P7) |
| `<17>` | Yellow (P8) |
| `<18>` | Green (P9) |
| `<19>` | Brighter Yellow (P10) |
| `<1A>` | Cyan |
| `<1B>` | Pinkish (P11) |
| `<1C>` | Dark Cyan (P12) |
| `<1D>` | Greygreen |
| `<1E>` | Bluegrey |
| `<1F>` | Turquoise |

Recommended palette:

- **White `<04>` or default `<01>`**: normal dialogue and objective text.
- **Yellow `<03>` / bright yellow `<19>`**: objectives, progress, important mission state.
- **Red `<06>`**: critical warnings, failure, emergency attacks.
- **Green `<07>`**: success, extraction complete, secured locations.
- **Teal/Cyan `<0F>` or `<1A>`**: intelligence/analysis lines if color-coding speakers is desired.
- **Orange `<11>` or Brown `<15>`**: enemy/unknown transmissions if color-coding factions is desired.

Avoid stacking many colors in one line. Usually color only the prefix or the key phrase.

Briefing room caution:

- Briefing `Mission Objectives` / `Text Message` color handling is not identical to in-game trigger text. Public references list title/mission briefing colors roughly as `<02>` cyan, `<03>` green, `<04>` light green, `<05>` grey, `<06>` white, and `<07>` red.
- Do not use player-color tags such as `<11>` for orange inside briefing text; title/mission briefing palettes do not provide a reliable orange. In briefing, write the faction color in words and avoid trying to color-code it. Use in-game trigger text/objectives for true player-color tags.

## StarCraft Font-Safe Symbols

Classic StarCraft/Brood War text is safest when written with ASCII punctuation, Korean text, digits, spaces, and SC control codes. Do not use modern Unicode decoration symbols in any player-facing `Display Text Message`, `Set Mission Objectives`, or briefing text unless they have been tested in-game.

Avoid these symbols in output strings:

| Avoid | Use instead |
|---|---|
| `▶` | `-` |
| `→` | `>` or `->` |
| `—` | `-`, `.`, or `:` |
| `★` | `!`, `[비상]`, or plain text |
| `⚠` | `경고:` or `<06>경고:` |
| `✓` | `완료` |
| `·` | `/` or a space |

Examples:

```
Set Mission Objectives("[미션 2]\n\n- 목표: 비콘 점령\n- 제한 시간: 15분");
Display Text Message(Always Display, "<06>경고: <04>본진 침투.");
Display Text Message(Always Display, "<03>호크: <04>뮤탈/디바우러 대편대다.");
```

## Alignment And Headers

Use `<13>` for centered headers instead of manually guessing spaces when a line must be visually centered.

Good:
```
Display Text Message(Always Display, "<13><03>[미션 2 개시] 통신 두절의 진실");
```

Acceptable for separator bars:
```
Display Text Message(Always Display, "<13><05>==========================================");
```

Avoid decorative headers that consume too many message lines during combat. In live gameplay, prefer one centered header plus one concise instruction line.

## Dialogue Formatting

Use a stable speaker prefix:

```
[호크] 15분이다. 그 안에 발신원에 도달한다.
[노바] UED 암호 패턴은 맞지만, 송출 위치가 기록된 기지 좌표와 다릅니다.
[경보] 럴커 매복 신호. 컴샛 탐지망을 유지하십시오.
```

Guidelines:

- Keep combat lines short enough to read while playing.
- Keep one idea per message. Split only when the player needs both tactical instruction and story reveal.
- Make `호크` decisive and tactical.
- Make `노바` analytical, specific, and slightly cautious.
- Make unknown/enemy transmissions fewer, colder, and more memorable.
- Use ellipses sparingly for suspense, not as a default rhythm.

## System Text Vs World Text

Prefer putting detailed mechanics in `Set Mission Objectives`, then let dialogue summarize the fiction.

Better:
```
Set Mission Objectives("[미션 2 - 추출 시작] 0%\n\n- 클리어 조건: 비콘 누적 점거 5분\n- 비콘 이탈 시 추출 일시 정지");
Display Text Message(Always Display, "[노바] 단말기 추출을 시작합니다. 비콘을 비우면 연결이 끊겨요.");
```

Avoid:
```
Display Text Message(Always Display, "[호크] 비콘에서 유닛이 떨어지면 카운트다운이 다시 작동한다.");
```

Use in-universe substitutions:

| Avoid in dialogue | Prefer |
|---|---|
| 유닛 | 병력, 아군, 선봉대 |
| 카운트다운 | 보안 타이머, 제한 시간 |
| 신호원 | 발신원, 신호 발신지, 송출원, 비콘 |
| 클리어 조건 | 확보 조건, 성공 조건, 작전 조건 |
| P5/P6 | 저그 군락, 변종 군단, 적 세력 |

## Mission Objective Text

`Set Mission Objectives` may be more explicit and mechanical than dialogue, but still keep terms player-facing.

Use:

- Korean labels first: `목표`, `성공 조건`, `제한 시간`, `위치`, `주의`.
- Concrete action verbs: `격파`, `점거`, `사수`, `도달`, `추출`.
- Percent/progress text for repeated state updates.

Avoid over-explaining every trigger implementation detail. The player needs what to do, where, how long, and what happens if they fail.

## Test And Cheat Triggers

When adding or changing test-only triggers in `TestTriggers/` or `TestTriggersForBuild/`, preserve the production mission flow whenever possible.

- Prefer forcing the same preconditions that a real player action would create, then let the normal `Triggers/` file advance the mission state.
- Do not jump directly to a later mission flag, reward state, objective state, or dialogue state if an existing production trigger owns that transition.
- Example: a "start mission 2" cheat should not directly set `Terran Valkyrie` to mission 2 phase values or grant rewards. Instead, set the mission 1 flag to the expected state and remove the required enemy Hatchery/Lair/Hive at `P5 Base`, so `Triggers/12_mission1_to_mission2_transition.txt` performs the normal mission 1 clear path.
- Use direct state jumps only for narrowly named test files whose purpose is explicitly to isolate a later system, such as a counterattack timing test. Make that isolation clear in the filename and comments.
- Keep test output minimal. If the normal production path already displays text, do not add extra visible test messages that could hide or reorder the real pacing being tested.

## Encoding Safety

Korean TrigEdit text in this repo is UTF-8. Do not use PowerShell `Get-Content | Set-Content` or `Set-Content -Encoding UTF8` for bulk edits on Korean trigger files; Windows PowerShell can misdecode existing UTF-8 text and rewrite mojibake. Prefer `apply_patch` for small edits and Node `fs.readFileSync(..., "utf8")` / `fs.writeFileSync(..., ..., "utf8")` for mechanical rewrites. After writing, verify generated output contains the expected Korean strings and no obvious mojibake fragments such as `?몃컮`, `?명겕`, or `誘명`.

## Trigger Action Limits

SC1 TrigEdit triggers can fail compile with `Too many actions` when a large wave combines many `Create Unit` and `Order` actions in one trigger.

- Keep each trigger at **64 actions or fewer**.
- For large attacks, split the same-timing logic into separate triggers:
  - one or more spawn triggers for `Create Unit` / `Create Unit with Properties`
  - one or more command triggers for `Order`
- When adding detector support such as `Zerg Overlord` to each route, count both its creation and movement/order actions.
- After bulk wave edits, scan changed trigger files for per-trigger action counts before finalizing.
- Apply the same split pattern to matching test triggers, especially `TestTriggers/*assault*.txt`, so test behavior matches production.

## Build Verification

Use the project build scripts only when the user wants build verification or when no contrary instruction has been given.

- If the user says not to run build verification, do not run `build_triggers.bat` or `build_triggers_withTest.bat` for that turn.
- In that case, still do lightweight text checks where useful, such as inspecting diffs, counting actions, or searching for referenced location names.
- If a test build is run, restore the normal generated trigger output afterward with `build_triggers.bat` unless the user explicitly wants the test output left active.

## Location Reference Changes

When adding or renaming any Location referenced by TrigEdit actions or conditions, explicitly tell the user which SCMDraft Locations must exist before import.

- Update `Locations_가이드.txt` and `Triggers/00_header.txt` when adding required locations.
- In the final response, list newly required locations under a clear "SCMDraft에 추가 필요" note.
- Do not assume a new Location exists just because a trigger text file references it.
- If compile errors mention `location name expected` or point at actions like `Move Unit`, `Move Location`, `Create Unit`, `Order`, `Minimap Ping`, or `Bring`, first check whether all referenced Location names exist in the map.
- Preserve known TrigEdit argument order from existing compiling lines. For example, local files use `Move Unit("Player X", "Unit", count, "From", "To");`.

## TrigEdit Syntax Verification

When unsure about SCMDraft 2 TrigEdit text syntax, do not guess. Search the web immediately, prefer Staredit Network / SCMDraft examples or other StarCraft Brood War UMS references, then cite or summarize the confirmed syntax in the response.

- Random switch action syntax is `Set Switch("Switch1", randomize);`.
- Do not use `Randomize Switch("Switch1");`; SCMDraft text import can reject it.
- Existing valid switch actions use the same form: `Set Switch("Switch1", set);`, `Set Switch("Switch1", clear);`, `Set Switch("Switch1", toggle);`.

## Review Checklist

Before finalizing text output, check:

- Does each line sound like the named speaker would say it?
- Does the player understand the next action within one or two lines?
- Are lore terms introduced before they become mission-critical?
- Are color codes purposeful and not noisy?
- Are centered headers using `<13>` where possible?
- Are "신호원", "유닛", and raw "카운트다운" avoided in dialogue unless intentionally system-facing?
- Are reward/system messages either clearly labeled or dressed as command/logistics messages?
