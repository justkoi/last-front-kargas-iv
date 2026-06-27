---
name: write-triggers
description: >
  Use this skill whenever you write, edit, or debug SCMDraft 2 TrigEdit text
  triggers for this StarCraft Brood War UMS map (E:/유즈맵제작, Kargas IV).
  Apply it for Trigger("..."){ Conditions: ... Actions: ... } blocks, .scx map
  triggers, AI scripts, Death Counter logic, and anything in the Triggers/
  folder. Follow the project's conventions for 12-tick seconds, Player 8 DC
  slots, Hyper Triggers, Bring/Order syntax, AI Script codes, Set Countdown Timer
  for on-screen countdowns, and individual unit Order calls instead of "Men".
  When you learn a new SC1 trigger behavior or corrected assumption, proactively
  offer to record it here.
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

When reporting dialogue or objective text changes, quote every affected string in
full — same rule as `trigedit-text-output`: no paraphrase, no ellipsis, no
partial lines.

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
- **실제 시간 요청을 `Elapsed Time`에 넣을 때는 1.5배**. 사용자가 "25분", "14:07"처럼 실제 플레이 시간을 말하면 Fastest 기준 `elapsed_game_seconds = real_seconds * 1.5`로 변환해 `Elapsed Time` 조건에 쓴다. 예: 실제 25분 = 1500초 → `Elapsed Time(At least, 2250)`. 반대로 `Elapsed Time` 값을 실제 시간으로 설명할 때는 `/ 1.5`.
  - corrected example: `Elapsed Time(1890)` is real/play-clock `1890 / 1.5 = 1260s = 21:00`, not 47:15.
- **마스터 틱** ([03_master_tick.txt](../../Triggers/03_master_tick.txt))이 Player 8의 10개 Terran 유닛 DC를 매 사이클 +1.
- **Player 8** 은 모든 DC 카운터의 owner (게임 내에서 상시 살아있어야 함).

## 가장 중요한 관용

1. **트리거 owner 선택**
   - DC 조작/메시지/세트피스: `Player 5` (M1) 또는 `Player 6` (M2 변종 적). 컴퓨터 슬롯이 살아있어야 그 owner의 트리거가 돔.
   - 플레이어별로 독립 실행되어야 하는 트리거(개인 선택 보급, 개인 수입, 패배): `Player 1, Player 2, Player 3, Player 4` 명시 + `Current Player` 사용.
   - **공용 오브젝트 보상(자원/유닛 제거/상태 변경)은 `Player 8` 같은 단일 owner가 1회만 처리**한다. 그 단일 트리거 안에서 `Set Resources("Player 1"...)` ~ `Player 4`를 모두 명시하고, 보상 완료 스위치를 세운다. 가스 보관소(`11c_mission1_gas_store_rewards`) 패턴을 따른다.
   - **빈 사람 슬롯의 owner 트리거는 실행되지 않는다.** 솔로 테스트에서 heartbeat DC만 외부에서 흉내 내도 그 슬롯의 `Trigger("Player N")` 자체가 살아나는 것은 아니다. 따라서 이탈 자산처럼 빈 슬롯도 중간 수령자가 될 수 있는 공용 처리에서 `Current Player` 실행에 의존해 자원을 지급하지 말고, 살아 있는 단일 시스템 owner(P8)가 원 소유자와 수령자를 명시해 처리한다.
   - **공용 보상 메시지/사운드/핑은 별도 `Player 1, Player 2, Player 3, Player 4` 트리거에서 표시만 담당**한다. P8/P5/P6 owner의 Display/Ping/WAV는 사람에게 안 보일 수 있다.
   - 금지 패턴: `Trigger("Player 1", "Player 2", "Player 3", "Player 4")` 안에서 전역 one-shot 스위치(`SwitchXX Not Set`)를 검사하면서 `Set Resources("Current Player", ...)`를 지급하면 첫 평가 플레이어만 받을 수 있다. 반대로 그 안에서 `Set Resources("Player 1"... "Player 4")` 전체 지급을 하면 트리거가 플레이어별로 돌며 x4 지급될 위험이 있다.
   - **`All Players` 는 P1~P8 전부** 포함. P8 owned hyper trigger와 충돌하지 않도록 Wait 사용 금지.
   - **P8 owned 트리거에 비-zero `Wait()` 절대 추가 금지** — Hyper trigger의 Wait 블록 발생 시 효과 멈춤.

2. **DC 슬롯 패턴**
   - 각 시스템은 자기 DC 슬롯을 가져야 (공유하면 충돌). 슬롯표는 [00_header.txt](../../Triggers/00_header.txt) 에.
   - 새 P8 DC를 배정하거나 기존 P8 DC를 재사용하기 전에는 `Triggers/`뿐 아니라 `TestTriggers/`, `TestTriggersForBuild/`, 현재 import용 합본에서도 같은 owner+unit DC 사용 여부를 검색한다. 테스트 대시보드가 임시 DC를 매 사이클 초기화/복원할 수 있어 실게임 로직과 충돌할 수 있다.
   - **실제 생성·지급·사망할 가능성이 있는 영웅 유닛은 가능하면 DC 슬롯으로 사용하지 않는다.** 영웅의 실제 사망 수가 상태값을 오염시킬 수 있으므로, 전용으로 예약한 비생산 오브젝트 DC 또는 Switch를 우선 사용한다. 비생산 오브젝트를 DC로 예약했다면 해당 owner에게 배치·지급·파괴하지 않는다는 제약도 `00_header.txt`에 함께 기록한다.
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

7. **의미 해석 주석 유지**
   - 새로 작성하거나 변경하는 트리거의 `Conditions` / `Actions` 줄에는 가능한 한 inline 주석을 붙여, 단순 문법 설명이 아니라 **게임상 의미**와 **세부 동작**을 함께 적는다.
   - 형식은 `//큰 의미 : 세부 조건/동작`을 기본으로 한다. 예: `Deaths("Player 8", "Terran Valkyrie", At least, 1); //미션 진행 중일때 : 미션 진행 변수가 1 이상일때`
   - `Switch`, DC 슬롯, 타이머, 단계 플래그처럼 의미 있는 변수는 `00_header.txt`의 역할표와 주변 트리거 흐름을 확인해서 해석한다. 모르면 추측하지 말고 관련 사용처를 검색한다.
   - 변경하지 않는 기존 트리거 전체를 일부러 주석화할 필요는 없다. 다만 변수 의미, 단계 값, 스위치 역할, 목적지/명령 대상이 바뀌어 기존 주석이 낡게 될 가능성이 있으면 함께 수정해서 주석이 코드와 어긋나지 않게 보수한다.
   - `Order` 액션은 어느 플레이어의 어떤 유닛을 어느 위치에서 어디로 보내는지, `Patrol`/`Attack` 등 명령이 실제로 어떤 경유/공격 동작을 유도하는지 적는다.
   - **예외 — 문자열 액션 줄 끝 인라인 주석 금지:** `Display Text Message`, `Play WAV`, `Set Mission Objectives`, `Transmission`, `Comment`, `Leader Board*` 등 **문자열을 쓰는 액션**은 `); //주석` 형태로 쓰지 않는다. `deploy_map.ps1`의 `recover_map_strings_cp949.py`가 `);`로 **줄이 끝나야**만 해당 액션을 인식한다. 줄 끝 주석이 있으면 파서가 그 줄을 **통째로 건너뛰어** 맵 TRIG와 `KargasIV_Triggers_Mission1Only.txt`의 문자열 액션 개수·순서가 어긋나고 `String encoding recovery failed`로 빌드가 멈춘다. 주석은 **한 줄 위**에 둔다:
     ```
     //중앙 정렬 격파 강조 헤더
     Display Text Message(Always Display, "<13><06>[ 전방 정신체 격파 ]");
     ```
     `Deaths`, `Set Switch`, `Bring` 같은 **비문자열** 줄의 `//주석` 은 이 제한과 무관하다.

8. **카운트다운 타이머 (기본)**
   - 사용자가 **카운트다운 타이머**를 요청하고 다른 방식을 지정하지 않으면, 화면 상단 Countdown Timer를 **`Set Countdown Timer(Set To, seconds);`** 로 설정한다.
   - 단위는 **초**. 예: 3분 = `180`, 1분 30초 = `90`.
   - `Display Text Message`로 `주공세까지 3:00` / `2:00` / `1:00` 같은 mm:ss 채팅 갱신을 **기본으로 쓰지 않는다**. Countdown Timer가 화면에서 자동으로 줄어든다.
   - mm:ss 텍스트 경보·분 단위 채팅 갱신은 사용자가 **채팅 표시를 명시**할 때만.
   - 만료 감지 조건: `Countdown Timer(At most, 0);`
   - 일시 정지/재개: `Pause Timer();` / `Unpause Timer();`
   - 해제/리셋: `Set Countdown Timer(Set To, 0);`
   - 대사와 병행은 **맥락에 맞을 때만**. 예: M2 주공세 보안 타이머(`12d`) 노바 `제한시간을 표시하겠습니다.` + `Set Countdown Timer(Set To, 270);`. 반격·결집 **예고** 이벤트는 UI만 켜도 됨.
   - **DC ↔ Countdown 변환 (별개 시계)**
     - DC(Hyper Trigger, 12 tick = 1초)와 Countdown Timer(화면 UI)는 **다른 시계**. 변환비 **DC : Countdown = 1 : 1.5**.
     - `Elapsed Time`도 게임 초 기준이므로 실제 플레이 시간 요청을 조건으로 만들 때는 `real_seconds * 1.5`를 사용한다. 예: 실제 14:07 = 847초 → `Elapsed Time` 약 1270.
     - `countdown_seconds = dc_seconds × 1.5` 또는 `countdown_seconds = (dc_ticks / 12) × 1.5`
     - DC prep 시작(Dark Archon reset 등)에 `Set Countdown Timer(Set To, countdown_seconds);`, DC 접촉 milestone에서 `Set Countdown Timer(Set To, 0);`으로 종료 동기화.
     - SC Countdown Timer는 게임 초 1:1 감소 → 30 DC초 예고에 45를 넣으면 접촉 시 화면에 ~15가 남을 수 있으므로 **접촉 시 0 해제**로 맞춘다.
     - 예: 30 DC초 예고 → **45**, 180 DC초 → **270** (`12d`).

9. **조건 순서: 값싼 조건을 비싼 조건보다 먼저**
   - SC는 한 트리거의 Conditions를 **위에서 아래로 평가하다 false면 즉시 단락(short-circuit)** 한다. 따라서 자주 false가 되는 **값싼 조건을 앞에** 두면, 뒤의 비싼 조건 평가를 건너뛴다. 조건은 모두 AND라 **순서를 바꿔도 논리 결과는 동일**.
   - **비용 등급:** `Deaths`(DC)·`Switch`·`Elapsed Time` = 단순 비교, **쌈**. `Bring`·`Command` = 지역/소유 유닛을 **스캔**, **비쌈**(맵 유닛 수에 비례해 더 무거워짐).
   - **철칙:** 트리거에 **쿨다운(Deaths DC) 조건이 있으면 그 쿨다운을 맨 위로**, `Bring`/`Command`보다 먼저 둔다. 쿨다운은 대부분의 사이클에서 false라, 비싼 스캔을 매 사이클(≈12Hz) 건너뛰게 된다. 후반 유닛 누적 시 프리징 가속을 막는 핵심.
   - 같은 트리거의 값싼 `Switch`/진행 게이트 `Deaths`도 `Bring` **앞으로**. (예: `14_base_defense` P5 감지, `18_..._40/41_hunt_relay`, `18_..._00_init_and_colony_state` 교정 완료.)
   - ❌ 나쁨:
     ```
     Conditions:
       Bring("Player 1", "Men", "P5 Area", At least, 1);   // 매 사이클 스캔
       Deaths("Player 8", "Terran Marine", At least, 120);  // 쿨다운(보통 false)
     ```
   - ✅ 좋음:
     ```
     Conditions:
       Deaths("Player 8", "Terran Marine", At least, 120);  // 쿨다운 먼저 → false면 단락
       Bring("Player 1", "Men", "P5 Area", At least, 1);
     ```
   - 주의: 조건과 짝지어진 `Set Deaths` 등 **액션은 건드리지 않는다**(액션 순서는 성능과 무관).

10. **DC 시간 구간 변경 검증**
   - `Deaths(..., At least, lower)`와 `Deaths(..., At most, upper)`를 함께 쓰는 시간 창은 항상 `lower <= upper`인지 확인한다. 하한만 새 타이밍으로 옮기고 기존 상한을 남기지 않는다.
   - 경고 창을 옮길 때 같은 분기의 사전 경고, 상세 경고, 접촉 경고/consume 값을 한 묶음으로 계산한다. 12틱=1초 기준으로 `상세 경고 하한 = spawn - 90초`, `consume = spawn - 10초`, `상세 경고 상한 = consume - 1틱`을 사용한다.
   - 난이도·랜덤 분기와 P6/P7 대칭본뿐 아니라 약화·fallback 같은 우회 분기도 같은 값으로 함께 갱신한다.
   - 수정 후 소스와 통합본에서 같은 DC의 `At least`/`At most` 쌍을 검색해 역전 구간이 없는지 검사한다. 역전 구간은 트리거가 영원히 false가 되는 치명적 오류로 취급한다.
   - **미션 2 주공세 가속값·난이도 보정값을 바꿀 때는 `18f_mission2_colony_rage_dashboard.txt`도 함께 갱신한다.** 실제 DC에는 보통 `+4320`, 어려움 이상 `+6480`의 예약 보정이 뒤늦게 더해지므로, 분노 표시는 `Switch120/121`이 Set이면 작업값에서 그 보정분을 뺀 뒤 실제 목표치(기본 consume − 보정값)로 나눈다. 원본 DC를 그대로 기본 consume으로 나누면 보정 발동 순간 분노가 약 20~30% 튀어 건물 파괴 가속이 중복된 것처럼 보인다.

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
- **테스트용 MainDC 주입 트리거에서 활성 주공세 상태 DC를 지우지 말 것** — `TestTriggersForBuild/`는 정상 트리거 뒤에 붙으므로, 테스트 트리거가 `Zerg Zergling`/`Zerg Hydralisk` 같은 MainDC를 더한 뒤 `Zerg Lurker`/`Zerg Mutalisk`를 0으로 만들면 이미 P6/P7 트리거가 스폰과 Waypoint 랠리를 끝낸 공세의 상태 머신만 끊길 수 있다. 그러면 유닛은 Waypoint까지 가지만 Hunt 릴레이 조건(`state == 2`)이 닫힌다.
- **문자열 액션 줄 끝 `//주석`은 deploy 빌드를 깨뜨림** — `Display Text Message(...); //설명` 처럼 쓰면 `recover_map_strings_cp949.py`가 그 액션을 파싱하지 못한다. 주석은 반드시 **별도 줄**로 올린다. (2026-06-08, `10_mission1_waves_late.txt` 격파 헤더 사례)
- **`Player 8`(또는 컴퓨터) 소유 트리거의 `Display Text Message`/`Minimap Ping`/`Play WAV`는 사람 플레이어에게 안 보임/안 들림** — 이 액션들은 트리거 owner에게만 출력된다. 컴퓨터 슬롯(P8 등) 소유로 띄우면 사람은 못 본다. **플레이어용 메시지/핑/사운드는 반드시 `Player 1~4` 소유 트리거로** 보낸다. DC·랜덤·Give 같은 메커니즘은 P8 소유로 두되, 출력은 `Switch` 등으로 신호를 받아 P1~P4 트리거에서 별도로 표시하라. 특정 한 명에게만 보이려면 그 플레이어 소유(`Trigger("Player N")`) 트리거를 쓴다. (2026-06-08, 13e 군수시설 이양 통지)
- **바닐라 `Minimap Ping`은 색상을 지정할 수 없음** — TrigEdit 액션은 `Minimap Ping("Location");`처럼 위치만 받고, 현재 트리거 플레이어의 미니맵에 엔진 기본 핑을 표시한다. `<06>` 같은 문자열 색상 코드는 핑에 적용되지 않는다. 빨간색 P1 소유 트리거로 우회하면 P1에게만 보이고 P2~P4에게 전달되지 않으므로, 전 플레이어 알림은 `Player 1~4` 소유로 각각 실행하고 기본 핑 색상을 받아들여야 한다. (2026-06-21, TL.net StarCraft mapping guide 확인)
- **같은 사이클 내 `Switch` 연쇄 → 같은 프레임 메시지 덮어쓰기** — SC는 한 플레이어의 트리거를 한 사이클에 위→아래로 평가하며, 위 트리거가 set한 `Switch`를 **같은 사이클 아래 트리거가 즉시 본다**. 그래서 `A가 S1 set → B가 S1 조건으로 발동`을 파일 순서 A→B로 두면 둘 다 같은 사이클(같은 프레임)에 발동해, `Display Text Message`가 서로 덮어써 마지막 한 줄만 보인다. **여러 줄을 순차 노출하려면 의존 트리거를 파일상 역순으로 배치**한다(C→B→A로 두면 A는 사이클 N, B는 N+1, C는 N+2에 발동 → 표시 순서는 A,B,C). 비-Preserve 트리거는 조건이 거짓이면 비활성화되지 않고 다음 사이클에 재평가되므로 이 stagger가 성립한다. (2026-06-08, 10_mission1_waves_late 정신체 격파 칭찬 / 13e 개인 메시지)
- **`.scx`와 프로덕션 합본의 문자열 액션 순서·개수 불일치** — `deploy_map.ps1`은 clean → CP949 string recovery → STRx normalize → protect 순으로 진행한다. recovery 단계에서 `KargasIV_Triggers_Mission1Only.txt`와 `.scx` TRIG의 문자열 액션을 **같은 순서로 1:1 매칭**한다. 텍스트에만 있거나 맵에만 있으면 `String action count differs` / `String encoding recovery failed`가 난다. 예전에 `build_triggers_withTest.ps1`로 임포트한 뒤 프로덕션 합본만 빌드하면, 맵에 `Leader Board Resources` 같은 테스트 잔여가 남을 수 있다. 프로덕션 배포 전 SCMDraft에서 **`build_triggers.ps1` 결과만** 다시 임포트하는 것이 정석이다.
- **여러 트리거가 같은 사이클에 더하는 누적 DC를 `Exactly`로 게이트하면 값을 건너뛴다** — 한 DC를 **서로 독립된 다수 트리거**가 +1 하는 경우(예: P5 해처리/레어/하이브 파괴를 각각 감지하는 `10_mission1_waves_late.txt`의 3개 Preserve 트리거가 `Terran Medic` +1), 건물 2~3개가 한 사이클에 동시 파괴되면 DC가 `6 → 8/9`처럼 **한 번에 +2~+3 점프**한다. 이 DC를 `Deaths(..., Exactly, N)`으로 마일스톤 게이트하면 N을 정확히 밟지 못하고 건너뛰어 **트리거가 영영 발동 안 할 수 있다**. 마일스톤은 `At least, N` + 래치 스위치(`Switch`)로 1회성을 보장한다. **단일 +1/사이클 경로**(예: `18b_mission2_p6_minibase.txt`의 M2 Medic가 한 트리거로만 증가)에서만 `Exactly` 스태거(`Exactly 1/85/169`)가 안전하다. (2026-06-09, 09c_mission1_colony_rage 무장 조건 `Medic Exactly 8` → `At least 8` 수정)

## 빌드/배포

- 에이전트가 트리거를 편집할 때는 기본적으로 `Triggers/*.txt` 같은 소스 파일만 수정한다. **`KargasIV_Triggers_Mission1Only.txt` 합본은 직접 갱신하지 않는다.**
- 트리거 수정 후 [build_triggers.ps1](../../build_triggers.ps1) 또는 [build_triggers.bat](../../build_triggers.bat) → `KargasIV_Triggers_Mission1Only.txt` 생성 (`Triggers/*.txt` concat, **프로덕션**)은 사용자가 수행한다.
- 에이전트는 사용자가 이번 턴에 명시적으로 요청한 경우에만 빌드 스크립트 실행이나 합본 갱신을 수행한다.
- 테스트 트리거까지 합치려면 [build_triggers_withTest.ps1](../../build_triggers_withTest.ps1) → `Triggers/` + `TestTriggersForBuild/` concat. 테스트 임포트 후에는 사용자가 명시하지 않는 한 **프로덕션 합본으로 되돌릴 것**.
- SCMDraft에서 해당 파일 import (Triggers → Edit → Replace with file) → `.scx` 저장
- [deploy_map.ps1](../../deploy_map.ps1) / [deploy_map.bat](../../deploy_map.bat) → clean, CP949 string recovery, protect 후 StarCraft Maps 폴더 복사

### deploy_map string recovery (CP949)

`recover_map_strings_cp949.py`가 담당한다. TrigEdit UTF-8 텍스트의 한글/제어코드를 맵 STRx에 CP949로 되돌린다.

- **파싱 대상 문자열 액션:** `Display Text Message`, `Play WAV`, `Set Mission Objectives`, `Transmission`, `Comment`, `Leader Board Control`, `Leader Board Resources`, `Leader Board Kills`, `Leader Board Points`, `Leaderboard Goal*`, `Set Next Scenario` 등 (`recover_map_strings_cp949.py`의 `TEXT_ACTION_FIELDS` 참고)
- **매칭 규칙:** 위 액션을 `KargasIV_Triggers_Mission1Only.txt`와 `.scx` TRIG에서 **등장 순서대로** 짝지음. 한 쌍이라도 액션 종류가 다르면 즉시 실패.
- **텍스트 > 맵:** 실패 (텍스트에 있는 문자열 액션이 맵에 없음 → SCMDraft 재임포트 필요)
- **맵 > 텍스트:** 접두사까지 일치하면 **경고만 내고 진행** (맵에만 남은 테스트/잔여 문자열 액션). unmapped 문자열은 기존 STRx 값에 UTF-8→CP949 변환만 적용.
- **흔한 실패 원인**
  1. 문자열 액션 줄 끝 `//주석` → 파서 skip → 개수 불일치
  2. `Triggers/` 수정 후 `build_triggers.ps1` 안 돌림
  3. `Triggers/` 수정 후 SCMDraft 재임포트 안 함 (텍스트와 `.scx` TRIG 불일치)
  4. 테스트 합본으로 임포트한 `.scx`에 프로덕션 합본을 recovery 소스로 쓸 때 trailing extra

에러 메시지가 `String encoding recovery failed.`만 보이면, 같은 명령을 Python으로 직접 실행해 `String action count differs` 또는 `String action order differs` 본문을 확인한다.

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
