# SCMDraft TrigEdit 문법 참고서

## 트리거 기본 구조
```
Trigger("Player 1","Player 2","All players"){
Conditions:
    조건1();
    조건2();
Actions:
    액션1();
    액션2();
}
```

플레이어 이름:
- "Player 1" ~ "Player 12"
- "All players"
- "Current Player"
- "Foes"
- "Allies"
- "Neutral Players"
- "Non Allied Victory Players"
- "Force 1" ~ "Force 4"

---

## 주요 조건 (Conditions)

| 조건 | 형식 |
|------|------|
| Always | `Always();` |
| Never | `Never();` |
| Elapsed Time | `Elapsed Time(At least, 60);` |
| Bring | `Bring("Player 1", "Marine", "Loc", At least, 5);` |
| Command | `Command("Player 1", "Buildings", At most, 0);` |
| Deaths | `Deaths("Player 1", "Marine", At least, 1);` |
| Switch | `Switch("Switch1", set);` |
| Countdown Timer | `Countdown Timer(At most, 0);` |
| Accumulate | `Accumulate("Player 1", At least, 500, ore);` |

Quantifier(수량 비교): `At least` / `At most` / `Exactly`

---

## 주요 액션 (Actions)

### 유닛 관련
```
Create Unit(player, unit, count, location);
Create Unit(player, unit, count, location, properties);  // with properties
Kill Unit(player, unit);
Kill Unit At Location(player, unit, count, location);
Remove Unit(player, unit);
Remove Unit At Location(player, unit, count, location);
Give Units to Player(from_player, to_player, unit, count, location);
Order(player, unit, location_from, location_to, order);
Modify Unit Energy(player, unit, percent, count, location);
Modify Unit Hit Points(player, unit, percent, count, location);
Modify Unit Shield Points(player, unit, percent, count, location);
```

예시:
```
Create Unit("Player 5", "Zerg Zergling", 4, "P1 Start");
Order("Player 5", "Men", "P5 Base", "P1 Start", Attack);
Kill Unit At Location("Player 1", "Civilian", 1, "Mission2 Goal");
```

### 자원 / 카운터
```
Set Resources(player, operation, amount, resource);
Set Deaths(player, unit, operation, count);
Set Switch(switch, action);
Set Countdown Timer(operation, seconds);
```

operation: `Set To` / `Add` / `Subtract`
resource: `ore` / `gas` / `ore and gas`
action(스위치): `set` / `clear` / `toggle` / `randomize`

예시:
```
Set Resources("Player 1", Add, 200, ore);
Set Deaths("Player 8", "Zerg Zergling", Set To, 1);
Set Switch("MissionFlag", set);
```

### 메시지 / 미션
```
Display Text Message(visibility, "text");
Set Mission Objectives("text");
Comment("text");
Play WAV("wav_path", unknown_int);
Minimap Ping("location");
Center View("location");
```

visibility: `Always Display` / `Player 1` 등

예시:
```
Display Text Message(Always Display, "Mission Complete!");
Set Mission Objectives("Mission 1: Destroy the colony");
Play WAV("sound\\Misc\\Bell.wav", 1500);
```

### AI / 게임 흐름
```
Run AI Script("4-char-code");
Run AI Script At Location("4-char-code", "location");
Wait(milliseconds);
Preserve Trigger();
Victory();
Defeat();
End Mission(condition);
```

예시:
```
Run AI Script("ZMCu");           // 저그 일반
Run AI Script("TMCx");           // 테란 강함
Wait(180000);                    // 3분 대기
Preserve Trigger();              // 트리거 반복
```

---

## AI 스크립트 4-char 코드

| 코드 | 의미 |
|------|------|
| TMCu | Terran Custom Level (테란 일반) |
| ZMCu | Zerg Custom Level (저그 일반) |
| PMCu | Protoss Custom Level (프로토스 일반) |
| TMCx | Terran Expansion (강함) |
| ZMCx | Zerg Expansion |
| PMCx | Protoss Expansion |
| +Vi0 | Junk Yard Dog (랜덤이동) |
| TLOf | Terran Lift Off |

---

## Order 종류
- Attack
- Move
- Patrol

---

## 인용부호 규칙

**큰따옴표 필요한 인자:**
- player, unit, location, text, switch, wav, script

**큰따옴표 X (열거형):**
- quantifier (At least, At most, Exactly)
- operation (Set To, Add, Subtract)
- resource (ore, gas, ore and gas)
- visibility (Always Display)
- order (Attack, Move, Patrol)

---

## 실제 예시 트리거

### 1. 시작 메시지
```
Trigger("All players"){
Conditions:
    Always();
Actions:
    Display Text Message(Always Display, "Welcome!");
    Preserve Trigger();
}
```

### 2. 5초 후 AI 시작
```
Trigger("Player 5"){
Conditions:
    Elapsed Time(At least, 5);
Actions:
    Run AI Script("ZMCu");
}
```

### 3. 적 본진 파괴 = 승리
```
Trigger("All players"){
Conditions:
    Command("Foes", "Buildings", At most, 0);
Actions:
    Display Text Message(Always Display, "Victory!");
    Wait(3000);
    Victory();
}
```

### 4. 영웅 부활
```
Trigger("Player 1"){
Conditions:
    Deaths("Player 1", "Hero Jim Raynor (Vulture)", At least, 1);
    Command("Player 1", "Hero Jim Raynor (Vulture)", Exactly, 0);
Actions:
    Wait(180000);
    Create Unit("Player 1", "Hero Jim Raynor (Vulture)", 1, "P1 Start");
    Set Deaths("Player 1", "Hero Jim Raynor (Vulture)", Set To, 0);
    Preserve Trigger();
}
```

### 5. 난민 호송
```
Trigger("Player 1"){
Conditions:
    Bring("Player 1", "Terran Civilian", "Mission2 Goal", At least, 1);
Actions:
    Remove Unit At Location("Player 1", "Terran Civilian", 1, "Mission2 Goal");
    Set Deaths("Player 8", "Terran Civilian", Add, 1);
    Preserve Trigger();
}
```

---

Source: yatapi (github.com/sethmachine/yatapi)
