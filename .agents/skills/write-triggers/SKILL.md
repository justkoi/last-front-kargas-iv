---
name: write-triggers
description: >
  Use this skill whenever you write, edit, or debug SCMDraft 2 TrigEdit text
  triggers for this StarCraft Brood War UMS map (E:/유즈맵제작, Kargas IV).
  Apply it for Trigger("..."){ Conditions: ... Actions: ... } blocks, .scx map
  triggers, AI scripts, Death Counter logic, and anything in the Triggers/
  folder. Follow the project's conventions for 12-tick seconds, Player 8 DC
  slots, Hyper Triggers, Bring/Order syntax, AI Script codes, and individual
  unit Order calls instead of "Men". When you learn a new SC1 trigger behavior
  or corrected assumption, proactively offer to record it here.
---

# Writing SCMDraft 2 Triggers for Kargas IV

## Post-implementation explanation

After implementing or changing triggers, explain the core trigger logic and
runtime behavior to the user in Korean. Keep it concise but concrete:
- Which trigger file and location changed.
- The key conditions that must be true.
- The actions that run when those conditions pass.
- The timer/DC period, if any, using both ticks and seconds when helpful.
- How the new trigger order interacts with nearby existing triggers.
- What is intentionally blocked or skipped, and what still continues.

Prefer behavior-level explanations over only listing edited lines. For example,
describe "Overlord support is skipped when the cap is exceeded, but the Hunt
attack body still runs and resets its timer."

## SC1 Brood War supply/control/psi costs

When designing trigger-spawned forces, calculate exact in-game supply/control/psi,
not doubled integer "population points". Half-supply units stay `0.5`.
If a temporary doubled scale is used for arithmetic, label it clearly and divide
by 2 before reporting the real army size.

Verified 2026-06-01 against UnitStatistics Starcraft data, StrategyWiki unit
pages, and StarCraft Wiki/Fandom supply notes.

Terran:
- 1: SCV, Marine, Firebat, Medic, Ghost
- 2: Vulture, Siege Tank/Tank Mode, Goliath, Wraith, Dropship, Science Vessel
- 3: Valkyrie
- 6: Battlecruiser
- 8: Armed Nuclear Silo / Nuclear Missile supply reservation

Zerg:
- 0: Larva, Egg, Cocoon, Broodling, Overlord as a spawned unit
- 0.5: Zergling, Scourge
- 1: Drone, Hydralisk, Infested Terran
- 2: Mutalisk, Guardian, Devourer, Lurker, Queen, Defiler
- 4: Ultralisk
- Note: Overlord provides +8 control in normal play, but a trigger-spawned
  attack-wave Overlord should be counted as 0 consumed control unless the
  calculation explicitly concerns available control cap.

Protoss:
- 1: Probe, Observer
- 2: Zealot, Dragoon, High Templar, Dark Templar, Shuttle, Corsair
- 3: Scout
- 4: Reaver, Archon, Dark Archon, Arbiter
- 6: Carrier
- 0: Interceptor and Scarab for army-size calculations

## SC1 Brood War unit mineral/gas costs

Use these standard mineral/gas costs when estimating the value of trigger-spawned
armies. For units normally created as pairs or morphs, count the individual
trigger-created unit value shown here. If a calculation instead needs the raw
in-game production button cost, use the note beside that unit.

Verified 2026-06-01 against UnitStatistics Starcraft data, StrategyWiki unit
pages, StrategyWiki Brood War new-feature notes, StarCraft Wiki/Fandom, and
Liquipedia pages for morph/special cases.

Terran M/G:
- SCV 50/0
- Marine 50/0
- Firebat 50/25
- Medic 50/25
- Ghost 25/75
- Vulture 75/0
- Siege Tank 150/100
- Goliath 100/50
- Wraith 150/100
- Dropship 100/100
- Science Vessel 100/225
- Valkyrie 250/125
- Battlecruiser 400/300
- Nuclear Missile 200/200, plus 8 supply reservation while armed

Zerg M/G:
- Drone 50/0
- Overlord 100/0
- Zergling 25/0 each; 50/0 per larva pair in normal production
- Hydralisk 75/25
- Mutalisk 100/100
- Guardian 150/200 total value; morph step is +50/+100 from Mutalisk
- Devourer 250/150 total value; morph step is +150/+50 from Mutalisk
- Scourge 12.5/37.5 each; 25/75 per larva pair in normal production
- Queen 100/150
- Ultralisk 200/200
- Defiler 50/150
- Lurker 125/125 total value; morph step is +50/+100 from Hydralisk
- Infested Terran 100/50
- Broodling 0/0 as spawned unit; produced by Queen energy in normal play
- Larva/Egg/Cocoon 0/0 for army-value calculations

Protoss M/G:
- Probe 50/0
- Zealot 100/0
- Dragoon 125/50
- High Templar 50/150
- Dark Templar 125/100
- Archon 100/300 total value; merge cost is two High Templar
- Dark Archon 250/200 total value; merge cost is two Dark Templar
- Shuttle 200/0
- Reaver 200/100
- Observer 25/75
- Scout 275/125
- Carrier 350/250
- Arbiter 100/350
- Corsair 150/100
- Interceptor 25/0 each
- Scarab 15/0 each

## Army mix balance convention

When the user asks for a "well-composed" spawned attack force, balance
anti-air-capable and anti-ground-capable supply/control, not just raw unit count.
Use capability supply:
- Count the full supply of any unit that can attack air into the anti-air bucket.
- Count the full supply of any unit that can attack ground into the anti-ground
  bucket.
- Dual-role units such as Hydralisk and Mutalisk count in both buckets for
  coverage-ratio analysis.
- No-attack/support units such as Defiler and Overlord are reported separately
  unless the user explicitly asks to fold support supply into the ratio.

Default target for a well-composed final assault is near 50:50 anti-air to
anti-ground coverage. A slightly ground-heavier mix is acceptable, up to about
55:45 ground:air. Avoid presenting a force as well-balanced if anti-air coverage
falls below roughly 45% of attack coverage, unless the user explicitly wants a
ground-biased or air-biased wave.

이 스킬은 이 저장소(`E:/유즈맵제작`, 카르가스 IV 협동 캠페인 맵)의 트리거를 쓰고 디버그할 때 적용합니다. SC1 vanilla 트리거의 한계와 SCMDraft TrigEdit 텍스트 형식의 관용을 함께 다룹니다.

## 핵심 환경 사실

- **SCMDraft 2** 의 TrigEdit 텍스트 형식. `KargasIV_Triggers_Mission1Only.txt` 가 최종 import 대상.
- **분리된 파일들** 이 `Triggers/`에 번호순으로 있고, `build_triggers.sh` / `.bat` 가 단순 concat으로 합침.
- **인코딩** 은 UTF-8 그대로. PowerShell 빌드 스크립트는 byte 단위 concat이라 한글 보존됨.
- **Hyper Trigger 4개** 가 `Triggers/999_hyper_trigger.txt` 에 있고 **Player 8 단독 소유**. 12 DC tick = 1초 공식이 여기서 나옴.
- **마스터 틱** ([03_master_tick.txt](../../Triggers/03_master_tick.txt))이 Player 8의 10개 Terran 유닛 DC를 매 사이클 +1.
- **Player 8** 은 모든 DC 카운터의 owner (게임 내에서 상시 살아있어야 함).

## 가장 중요한 관용

1. **트리거 owner 선택**
   - DC 조작/메시지/세트피스: `Player 5` (M1) 또는 `Player 6` (M2 변종 적). 컴퓨터 슬롯이 살아있어야 그 owner의 트리거가 돔.
   - 플레이어가 직접 영향받는 트리거(자원, 패배): `Player 1, Player 2, Player 3, Player 4` 명시.
   - **`All Players` 는 P1~P8 전부** 포함. P8 owned hyper trigger와 충돌하지 않도록 Wait 사용 금지.
   - **P8 owned 트리거에 비-zero `Wait()` 절대 추가 금지** — Hyper trigger의 Wait 블록 발생 시 효과 멈춤.

2. **DC 슬롯 패턴**
   - 각 시스템은 자기 DC 슬롯을 가져야 (공유하면 충돌). 슬롯표는 [00_header.txt](../../Triggers/00_header.txt) 에.
   - 새 P8 DC를 배정하거나 기존 P8 DC를 재사용하기 전에는 `Triggers/`뿐 아니라 `TestTriggers/`, `TestTriggersForBuild/`, 현재 import용 합본에서도 같은 owner+unit DC 사용 여부를 검색한다. 테스트 대시보드가 임시 DC를 매 사이클 초기화/복원할 수 있어 실게임 로직과 충돌할 수 있다.
   - 마스터 틱에 들어있는 DC만 자동 증가 (Civilian/Marine/Firebat/Ghost/Medic/SCV/Goliath/Wraith/Vulture/Battlecruiser).
   - 그 외(Valkyrie, Probe, Zealot, Dropship 등)는 플래그/카운터로 수동 Set만 사용.

3. **Order에서 "Men" 금지**
   - "Men"은 일꾼(드론) 포함이라 Order로 보내면 일꾼이 같이 진군. 전투 유닛 타입을 개별 명시.

4. **`Bring`의 player 인자**
   - "Foes" / "Allies"는 트리거 owner의 시점에서 해석. P5 owner의 "Foes"는 P1~P4 + P6 + 기타 적.
   - 정확히 플레이어만 검출하려면 `Bring("Force 1", ...)` (force 셋업 가정) 또는 `Trigger("Player 1", "Player 2", "Player 3", "Player 4")` + `Bring("Current Player", ...)`.

5. **Move Location 으로 동적 추적**
   - `Move Location("player", "unit type", "src loc", "dst loc")` 으로 location을 유닛 위로 옮김. 11_dynamic_tracking, 14_base_defense 패턴.

6. **세트피스 vs 반복 웨이브**
   - 1회성 트리거: Preserve 안 붙임. 한 번 발동 후 SC가 자동 비활성화.
   - 반복: `Preserve Trigger();` 마지막에. DC로 쿨다운 관리.

7. **타이머 영구 정지/재개**
   - `Pause Timer();` / `Unpause Timer();` 가 SCMDraft 액션. Countdown Timer를 화면에 표시 중일 때 작동.

## AI Script 코드 (확인된 것)

| 코드 | 의미 |
|---|---|
| `ZARx` | Zerg Area Town (확장 안 함, 미션1 P5 시작) |
| `ZSUx` | Zerg Insane Setup (스토리 강함, 적 본진 가동) |
| `ZMCx` | Zerg Custom Level (적극적 공격 + 확장) |
| `+Vi#` | 현재 플레이어가 지정 플레이어의 시야를 얻는다. 0-indexed: `+Vi0`=P1 시야 획득, `+Vi1`=P2 시야 획득, `+Vi8`=P9 시야 획득. 예: P1~P4가 P9의 시야를 얻으려면 `Trigger("Player 1", "Player 2", "Player 3", "Player 4")`에서 `Run AI Script("+Vi8");`를 실행한다. |

**주의:** `+Vi`는 vision share (트리거 디버그/협동 시야)이지, AI 행동 변경이 아님. `Vi1`처럼 `+` 없이 쓰면 인식 안 될 수 있음. 방향을 헷갈리지 말 것: `+Vi0`을 P9가 실행하면 P9가 P1의 시야를 얻는 것이지, P1이 P9의 시야를 얻는 것이 아니다.

## 스위치 (Switch) 문법

SCMDraft TrigEdit는 액션과 조건의 스위치 인자 **케이스가 다름**. 헷갈리기 쉬움.

**액션은 소문자:**
```
Set Switch("Switch1", set);
Set Switch("Switch1", clear);
Set Switch("Switch1", randomize);
Set Switch("Switch1", toggle);
```

**조건은 대문자 (공백 있음):**
```
Switch("Switch1", Set);
Switch("Switch1", Not Set);
```

**스위치 이름**은 `"Switch1"` 처럼 공백 없이 (기본 256개, `Switch1`~`Switch256`). 맵 에디터에서 rename 가능.

## 유닛 이름 규칙

**일반 유닛:** `"Terran Marine"`, `"Zerg Hydralisk"`, `"Protoss Zealot"` 처럼 `"종족 + 유닛명"` 형식.

**영웅 유닛:** `"히어로명 (베이스유닛)"` 형식. 괄호 포함.
- ✅ `"Tom Kazansky (Wraith)"`
- ✅ `"Jim Raynor (Marine)"`, `"Jim Raynor (Vulture)"`
- ✅ `"Sarah Kerrigan (Ghost)"`
- ❌ `"Tom Kazansky"` (괄호 없으면 인식 안 됨)

## 자주 쓰이는 함정 (이미 마주친 버그들)

- **`Reveal Map`은 location 인자 없음** — 맵 전체만 공개. 특정 영역 fog 해제는 `Map Revealer` 유닛 스폰 → 짧게 두고 Remove. 그러면 "탐색됨" 상태 남음.
- **`sound\Misc\Bell.wav` 존재 안 함** — 대신 `sound\Misc\TRescue.wav` 등 SCMDraft Sound Editor의 Available 목록에서 확인된 것 사용. 등록 안 하면 Play WAV 무시됨.
- **Defeat 트리거 owner를 "All Players"로 두면 P5 컴퓨터까지 잡힘** → P5가 패배 상태 되면 P5 owned 트리거 멈춤. owner를 `Player 1~4`로 한정.
- **트리거 ownership 인 컴퓨터 플레이어가 모든 유닛/건물 잃으면 트리거 정지** 가능. 미션 전환 시 P5/P6에 더미 유닛이 필요할 수 있음.
- **`Wait()` 액션은 Hyper Trigger 부담** — 1회성 종결 트리거 외엔 `Wait` 대신 DC 카운터 사용.
- **트리거 owner `Player 6`가 SCMDraft에서 활성화 안 돼있으면 실행 안 됨** — Player Settings에서 P6 슬롯 확인 필수.
- **`Bring`의 location은 정밀하게** — Beacon 유닛 위 1×1 location은 유닛이 들어갈 수 없음. 3×3 이상 빈 땅 덮도록.
- **에너지 시전자 스폰은 Unit Properties 사용** — 디파일러처럼 에너지가 전술 가치인 유닛은 기존 프로젝트 관례인 슬롯 `1`로 `Create Unit with Properties("Player 7", "Zerg Defiler", 1, "Raid1", 1);`처럼 생성. 즉시 스킬 사용이 필요하면 plain `Create Unit`로 만들지 않는다.

## 빌드/배포

- 트리거 수정 후 [build_triggers.bat](../../build_triggers.bat) 더블클릭 → `KargasIV_Triggers_Mission1Only.txt` 생성
- SCMDraft에서 해당 파일 import (Triggers → Edit → Replace with file)
- 맵 저장 후 [deploy_map.bat](../../deploy_map.bat) 더블클릭 → StarCraft Maps 폴더 복사

## ⚡ 새로운 발견을 기록할 것

이 프로젝트에서 트리거 작업 중 **처음 알게 된 사실**(SC1 동작 quirk, SCMDraft 인식되는 unit/location 이름, AI Script 코드, 에러 원인 등)이 나오면, **사용자에게 먼저 제안하라**:

> "이 사실을 write-triggers 스킬에 기록할까요? 다음에 같은 함정 안 밟으려면 좋을 것 같습니다."

기록 후보 시그널:
- 사용자가 "X는 안 되더라" 하고 정정해줄 때 (예: "+Vi6 아니라 +Vi0 형식")
- SCMDraft가 거부한 경로/유닛/스크립트 이름
- 트리거 발동 안 되는 이유 추적해서 찾은 근본 원인
- 미션 전환 시 발생한 상태 충돌 패턴
- 우회 패턴 발견 (예: Map Revealer로 fog 일시 해제)

이런 발견은 **휘발성이 높음** — 한 세션에서만 알고 다음 세션에서 또 같은 실수 반복하면 시간 낭비. 사용자가 "기록해" 라고 명시 안 해도 **선제적으로 제안**할 것. 거절하면 그냥 진행, 수락하면 이 SKILL.md 의 적절한 섹션(주로 "AI Script 코드" 또는 "자주 쓰이는 함정")에 추가.

기록 형식: 짧고 구체적. **왜** 그런지보다 **무엇이** 작동하고 무엇이 안 되는지를 단호하게.
