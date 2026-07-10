from itertools import product
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Triggers" / "01d_hero_commanders.txt"

PLAYERS = range(1, 5)
RESPAWN_MINERALS = 100
ELIGIBLE_SWITCH = "Switch256"
VALEN_NOTICE_SWITCH = "Switch236"
ELIA_NOTICE_SWITCH = "Switch237"
ROCK_VULTURE_GIFT_PENDING = "Switch248"
HEROES = {
    "valen": {
        "unit": "Jim Raynor (Marine)",
        "name": "발렌",
        "color": "<03>",
        "holder": "Protoss Arbiter Tribunal",
        "timer": "Zerg Spire",
        "down": "Switch238",
        "draw0": "Switch240",
        "draw1": "Switch241",
    },
    "elia": {
        "unit": "Sarah Kerrigan (Ghost)",
        "name": "엘리아",
        "color": "<1B>",
        "holder": "Protoss Robotics Support Bay",
        "timer": "Zerg Greater Spire",
        "down": "Switch239",
        "draw0": "Switch242",
        "draw1": "Switch243",
    },
    "rock": {
        "unit": "Jim Raynor (Vulture)",
        "name": "로크",
        "title": "특수작전장교",
        "color": "<1A>",
        "holder": "Zerg Nydus Canal",
        "timer": "Zerg Creep Colony",
        "intro_timer": "Zerg Hatchery",
        "down": "Switch250",
        "draw0": "Switch252",
        "draw1": "Switch253",
        "join": "HeroCJoin",
        "exit": "HeroCJoinExit",
        "unlock_switch": "Switch245",
        "cerebrate_location": "AttackPoint1",
        "dialogue": "교란망이 꺼졌군. 그 틈을 기다렸다. 이 전선은 지금부터 내가 맡겠다.",
    },
    "sedin": {
        "unit": "Alan Schezar (Goliath)",
        "name": "세딘",
        "title": "병참감찰관",
        "color": "<1F>",
        "holder": "Zerg Queen's Nest",
        "timer": "Zerg Hive",
        "intro_timer": "Zerg Lair",
        "down": "Switch251",
        "draw0": "Switch254",
        "draw1": "Switch255",
        "join": "HeroDJoin",
        "exit": "HeroDJoinExit",
        "unlock_switch": "Switch157",
        "cerebrate_location": "P5 Cerebrate",
        "dialogue": "방해 신호가 사라졌습니다. 잔존 기갑대를 수습해 현 위치에서 합류하겠습니다.",
    },
}


def trigger(owner: str, conditions: list[str], actions: list[str]) -> str:
    lines = [f'Trigger("{owner}"){{', "Conditions:"]
    lines.extend(f"\t{x}" for x in conditions)
    lines.append("Actions:")
    lines.extend(f"\t{x}" for x in actions)
    lines.append("}")
    return "\n".join(lines)


def active_conditions(player: int) -> list[str]:
    return [
        f'Switch("Switch{161 + player}", Set);',
        f'Switch("Switch{165 + player}", Not Set);',
    ]


def inactive_variants(player: int) -> list[list[str]]:
    return [
        [f'Switch("Switch{161 + player}", Not Set);'],
        [f'Switch("Switch{165 + player}", Set);'],
    ]


def draw_bit_conditions(hero: dict, player: int) -> list[str]:
    # clear/clear=P1, set/clear=P2, clear/set=P3, set/set=P4
    mapping = {
        1: ("Not Set", "Not Set"),
        2: ("Set", "Not Set"),
        3: ("Not Set", "Set"),
        4: ("Set", "Set"),
    }
    b0, b1 = mapping[player]
    return [
        f'Switch("{hero["draw0"]}", {b0});',
        f'Switch("{hero["draw1"]}", {b1});',
    ]


def draw_conditions(hero: dict, player: int) -> list[str]:
    conditions = [
        'Switch("Switch244", Set);',
        f'Deaths("Player 8", "{hero["holder"]}", Exactly, 0);',
        'Elapsed Time(At least, 5);',
    ]
    if hero["unit"] == HEROES["elia"]["unit"]:
        conditions.append(f'Deaths("Player 8", "{HEROES["valen"]["holder"]}", At least, 1);')
    return [
        *conditions,
        *draw_bit_conditions(hero, player),
        *active_conditions(player),
    ]


def not_holder_variants(hero: dict, player: int) -> list[list[str]]:
    if player == 1:
        return [[f'Deaths("Player 8", "{hero["holder"]}", At least, 2);']]
    if player == 4:
        return [[f'Deaths("Player 8", "{hero["holder"]}", At most, 3);']]
    return [
        [f'Deaths("Player 8", "{hero["holder"]}", At most, {player - 1});'],
        [f'Deaths("Player 8", "{hero["holder"]}", At least, {player + 1});'],
    ]


def not_any_holder_variants(previous: list[dict], player: int) -> list[list[str]]:
    choices = [not_holder_variants(hero, player) for hero in previous]
    return [[condition for group in combo for condition in group] for combo in product(*choices)]


def hero_assignment(hero: dict, player: int) -> str:
    return trigger(
        "Player 8",
        draw_conditions(hero, player),
        [
            f'Give Units to Player("Player 9", "Player {player}", "{hero["unit"]}", 1, "Anywhere"); //영웅 무작위 배속 : P9 선배치 영웅을 활성 플레이어에게 이양',
            f'Set Deaths("Player 8", "{hero["holder"]}", Set To, {player}); //현재 소유자 기록 : {hero["name"]} 소유자=P{player}',
        ],
    )


def late_gate(hero_key: str) -> list[str]:
    hero = HEROES[hero_key]
    if hero_key == "rock":
        return [
            f'Switch("{hero["unlock_switch"]}", Set);',
            f'Deaths("Player 8", "{HEROES["valen"]["holder"]}", At least, 1);',
            f'Deaths("Player 8", "{HEROES["elia"]["holder"]}", At least, 1);',
        ]
    return [
        f'Switch("{hero["unlock_switch"]}", Set);',
        f'Deaths("Player 8", "{HEROES["rock"]["holder"]}", At least, 1);',
        f'Deaths("Player 8", "{HEROES["rock"]["intro_timer"]}", Exactly, 168);',
    ]


def unlock_request(hero: dict) -> str:
    return trigger(
        "Player 8",
        [
            'Switch("Switch244", Set);',
            f'Deaths("Player 8", "{hero["holder"]}", Exactly, 0);',
            f'Switch("{hero["unlock_switch"]}", Not Set);',
            f'Bring("Player 5", "Zerg Cerebrate", "{hero["cerebrate_location"]}", At most, 0);',
        ],
        [
            f'Set Switch("{hero["unlock_switch"]}", set); //영웅 초기화 뒤 정신체 부재를 독립 감지 : 난이도/미션 단계와 무관하게 합류 요청 보존',
        ],
    )


def join_actions(hero_key: str, hero: dict, player: int) -> list[str]:
    actions = [
        f'Move Unit("All Players", "Men", 64, "{hero["join"]}", "{hero["exit"]}"); //합류 지점 정리 : 사람/컴퓨터 소유 유닛을 출구로 이동',
        f'Move Unit("All Players", "Buildings", 64, "{hero["join"]}", "{hero["exit"]}"); //합류 지점 정리 : 사람/컴퓨터 소유 건물을 출구로 이동',
        f'Move Unit("Neutral Players", "Men", 64, "{hero["join"]}", "{hero["exit"]}"); //합류 지점 정리 : 중립 소유 유닛을 출구로 이동',
        f'Move Unit("Neutral Players", "Buildings", 64, "{hero["join"]}", "{hero["exit"]}"); //합류 지점 정리 : 중립 소유 건물을 출구로 이동',
    ]
    if hero_key == "rock":
        actions.extend([
            f'Create Unit("Player {player}", "Terran Vulture", 1, "{hero["join"]}"); //P9 직접 생성 불가 우회 : 로크 배속 플레이어 소유 일반 벌처 생성',
            f'Give Units to Player("Player {player}", "Player 9", "Terran Vulture", 1, "{hero["join"]}"); //이온 추진기 선물 준비 : 생성된 일반 벌처를 P9 소유로 전환',
        ])
    actions.extend([
        f'Create Unit("Player {player}", "{hero["unit"]}", 1, "{hero["join"]}"); //현장 합류 : 비워 둔 전용 지점에 신규 영웅 생성',
        f'Set Deaths("Player 8", "{hero["holder"]}", Set To, {player}); //현재 소유자 기록 : {hero["name"]} 소유자=P{player}',
        f'Set Deaths("Player 8", "{hero["intro_timer"]}", Set To, 0); //합류 연출 타이머 시작점',
        *([f'Set Switch("{ROCK_VULTURE_GIFT_PENDING}", set); //다음 트리거 사이클에 생성된 P9 벌처 이양 예약'] if hero_key == "rock" else []),
        f'Set Switch("{ELIGIBLE_SWITCH}", clear); //후보 탐색 임시 상태 정리',
        f'Set Switch("{hero["unlock_switch"]}", clear); //{hero["name"]} 합류 요청 소비 : 배속 뒤 재실행 방지',
    ])
    return actions


def eligibility_reset(hero_key: str, hero: dict) -> str:
    return trigger(
        "Player 8",
        [*late_gate(hero_key), f'Deaths("Player 8", "{hero["holder"]}", Exactly, 0);'],
        [f'Set Switch("{ELIGIBLE_SWITCH}", clear); //매 추첨 사이클마다 미배속 생존 후보를 다시 계산', 'Preserve Trigger();'],
    )


def eligibility_detection(hero_key: str, hero: dict, previous: list[dict], player: int, holder_conditions: list[str]) -> str:
    return trigger(
        "Player 8",
        [
            *late_gate(hero_key),
            f'Deaths("Player 8", "{hero["holder"]}", Exactly, 0);',
            *active_conditions(player),
            *holder_conditions,
        ],
        [f'Set Switch("{ELIGIBLE_SWITCH}", set); //우선 배속 후보 확인 : P{player}은 생존 중이며 기존 영웅 미배속', 'Preserve Trigger();'],
    )


def late_draw(hero_key: str, hero: dict) -> str:
    return trigger(
        "Player 8",
        [*late_gate(hero_key), f'Deaths("Player 8", "{hero["holder"]}", Exactly, 0);'],
        [
            f'Set Switch("{hero["draw0"]}", randomize); //{hero["name"]} 대상 추첨 bit0',
            f'Set Switch("{hero["draw1"]}", randomize); //{hero["name"]} 대상 추첨 bit1',
            'Preserve Trigger();',
        ],
    )


def late_assignment(hero_key: str, hero: dict, player: int, holder_conditions: list[str], eligibility: str) -> str:
    return trigger(
        "Player 8",
        [
            *late_gate(hero_key),
            f'Deaths("Player 8", "{hero["holder"]}", Exactly, 0);',
            f'Switch("{ELIGIBLE_SWITCH}", {eligibility});',
            *draw_bit_conditions(hero, player),
            *active_conditions(player),
            *holder_conditions,
        ],
        join_actions(hero_key, hero, player),
    )


def sedin_solo_assignment(hero: dict, player: int, inactive_conditions: list[str]) -> str:
    rock = HEROES["rock"]
    return trigger(
        "Player 8",
        [
            *late_gate("sedin"),
            f'Deaths("Player 8", "{hero["holder"]}", Exactly, 0);',
            f'Switch("{ELIGIBLE_SWITCH}", Not Set);',
            f'Deaths("Player 8", "{rock["holder"]}", Exactly, {player});',
            *active_conditions(player),
            *inactive_conditions,
        ],
        join_actions("sedin", hero, player),
    )


def death_detection(hero: dict, player: int) -> str:
    return trigger(
        "Player 8",
        [
            f'Deaths("Player 8", "{hero["holder"]}", Exactly, {player});',
            f'Switch("{hero["down"]}", Not Set);',
            f'Deaths("Player {player}", "{hero["unit"]}", At least, 1);',
        ],
        [
            f'Set Deaths("Player {player}", "{hero["unit"]}", Set To, 0); //사망 카운터 정리 : 다음 행동불능도 다시 감지',
            f'Set Deaths("Player 8", "{hero["timer"]}", Set To, 0); //5분 복귀 타이머 시작점',
            f'Set Switch("{hero["down"]}", set); //행동불능 상태 진입',
            'Preserve Trigger(); //반복 수명주기 : 복귀 후 다음 사망도 다시 감지',
        ],
    )


def respawn_trigger(hero: dict, player: int, building: str) -> str:
    return trigger(
        "Player 8",
        [
            f'Switch("{hero["down"]}", Set);',
            f'Deaths("Player 8", "{hero["holder"]}", Exactly, {player});',
            f'Deaths("Player 8", "{hero["timer"]}", Exactly, 3600);',
            f'Accumulate("Player {player}", At least, {RESPAWN_MINERALS}, ore);',
            f'Command("Player {player}", "{building}", At least, 1);',
        ],
        [
            f'Move Location("Player {player}", "{building}", "Anywhere", "P{player} Hunt"); //복귀 지점 갱신 : 현재 소유자의 본진 건물 위로 이동',
            f'Set Resources("Player {player}", Subtract, {RESPAWN_MINERALS}, ore); //복귀 비용 지불 : 미네랄 100 소모',
            f'Create Unit("Player {player}", "{hero["unit"]}", 1, "P{player} Hunt"); //5분 후 복귀 : 같은 플레이어 소유로 영웅 재배치',
            f'Set Deaths("Player 8", "{hero["timer"]}", Add, 1); //복귀 완료 펄스 3601 : 다음 사이클 메시지 후 상태 정리',
            'Preserve Trigger(); //반복 수명주기 : 같은 건물 종류에서도 계속 복귀 가능',
        ],
    )


def leave_update(hero: dict, leaver: int, receiver: int) -> str:
    code = leaver * 10 + receiver
    return trigger(
        "Player 8",
        [
            f'Deaths("Player 8", "Terran Beacon", Exactly, {code});',
            f'Deaths("Player 8", "{hero["holder"]}", Exactly, {leaver});',
        ],
        [f'Set Deaths("Player 8", "{hero["holder"]}", Set To, {receiver}); //이탈 승계 연동 : {hero["name"]} 소유자 P{leaver}->P{receiver}'],
    )


def collision_repair(owner: int, alternative: int) -> str:
    elia = HEROES["elia"]
    valen = HEROES["valen"]
    return trigger(
        "Player 8",
        [
            f'Deaths("Player 8", "{valen["holder"]}", Exactly, {owner});',
            f'Deaths("Player 8", "{elia["holder"]}", Exactly, {owner});',
            *active_conditions(alternative),
        ],
        [
            f'Give Units to Player("Player {owner}", "Player 9", "{elia["unit"]}", 1, "Anywhere"); //중복 소유 해소 : 엘리아를 P9 대기 상태로 회수',
            f'Set Deaths("Player 8", "{elia["holder"]}", Set To, 0); //엘리아 소유자 재추첨 준비',
        ],
    )


def append_late_hero(parts: list[str], hero_key: str, previous_keys: list[str]) -> None:
    hero = HEROES[hero_key]
    previous = [HEROES[key] for key in previous_keys]
    parts.extend(["", f'//----- {hero["name"]} 현장 합류 및 공정 배속 -----//', eligibility_reset(hero_key, hero)])

    primary_variants: dict[int, list[list[str]]] = {}
    for player in PLAYERS:
        primary_variants[player] = not_any_holder_variants(previous, player)
        for holder_conditions in primary_variants[player]:
            parts.append(eligibility_detection(hero_key, hero, previous, player, holder_conditions))

    parts.append(late_draw(hero_key, hero))
    for player in PLAYERS:
        for holder_conditions in primary_variants[player]:
            parts.append(late_assignment(hero_key, hero, player, holder_conditions, "Set"))

    if hero_key == "rock":
        for player in PLAYERS:
            parts.append(late_assignment(hero_key, hero, player, [], "Not Set"))
        return

    rock = HEROES["rock"]
    for player in PLAYERS:
        for holder_conditions in not_holder_variants(rock, player):
            parts.append(late_assignment(hero_key, hero, player, holder_conditions, "Not Set"))

    for player in PLAYERS:
        other_players = [other for other in PLAYERS if other != player]
        for inactive_combo in product(*(inactive_variants(other) for other in other_players)):
            conditions = [condition for group in inactive_combo for condition in group]
            parts.append(sedin_solo_assignment(hero, player, conditions))


def build() -> str:
    v = HEROES["valen"]
    e = HEROES["elia"]
    r = HEROES["rock"]
    s = HEROES["sedin"]
    all_heroes = (v, e, r, s)
    parts: list[str] = [
        "//=================================================================//",
        "//  발렌/엘리아/로크/세딘 영웅 지휘 시스템",
        "//  - 시작: 맵에 P9 소유로 선배치된 발렌/엘리아를 활성 P1~P4에 무작위 배속",
        "//  - 전방/지휘 정신체 파괴: 로크/세딘을 아직 영웅이 없는 생존자에게 우선 배속",
        "//  - 현장 합류: 전용 Join의 모든 Men/Buildings를 Exit으로 옮긴 뒤 같은 트리거에서 생성",
        "//  - 행동불능: 사망 감지 후 3600틱(12틱=1초, 5분) 뒤 미네랄 100을 소모해 본진 건물에서 복귀",
        "//  - 이탈: 21_player_leave_handoff의 승계 코드와 실제/행동불능 영웅 소유자 상태를 동기화",
        "//=================================================================//",
        "",
        "//----- P8 상태 슬롯 -----//",
        "// Protoss Arbiter Tribunal    : 발렌 현재 소유자(0=미배속, 1~4=P1~P4)",
        "// Protoss Robotics Support Bay: 엘리아 현재 소유자(0=미배속, 1~4=P1~P4)",
        "// Zerg Nydus Canal / Queen's Nest: 로크/세딘 현재 소유자(0=미배속, 1~4=P1~P4)",
        "// Zerg Spire / Greater Spire  : 발렌/엘리아 행동불능 복귀 타이머(0~3601)",
        "// Zerg Creep Colony / Hive   : 로크/세딘 행동불능 복귀 타이머(0~3601)",
        "// Zerg Hatchery / Lair        : 로크/세딘 합류 연출 타이머(0~168)",
        "// Switch236/237               : 발렌/엘리아 최초 배속 안내 표시 완료(소유권 상태 아님)",
        "// Switch238/239               : 발렌/엘리아 행동불능",
        "// Switch240~243               : 발렌/엘리아 2비트 무작위 대상",
        "// Switch244                   : 선배치 영웅 상태 초기화 완료",
        "// Switch245                   : 전방 정신체 파괴 후 로크 합류 요청",
        "// Switch157                   : 지휘 정신체 파괴 후 세딘 합류 요청",
        "// Switch248                   : 로크 합류 P9 일반 벌처 이양 대기",
        "// Switch250/251               : 로크/세딘 행동불능",
        "// Switch252~255               : 로크/세딘 2비트 무작위 대상",
        "// Switch256                   : 현재 합류 영웅의 미배속 생존 후보 존재",
        "",
        "//----- P9 선배치 영웅 사용 및 네 영웅 상태 초기화 -----//",
        trigger(
            "Player 8",
            ['Switch("Switch244", Not Set);', 'Elapsed Time(At least, 2);'],
            [
                *[f'Set Deaths("Player 8", "{hero["holder"]}", Set To, 0); //{hero["name"]} 소유자 초기화' for hero in all_heroes],
                *[f'Set Deaths("Player 8", "{hero["timer"]}", Set To, 0); //{hero["name"]} 복귀 타이머 초기화' for hero in all_heroes],
                f'Set Deaths("Player 8", "{r["intro_timer"]}", Set To, 0); //로크 합류 연출 타이머 초기화',
                f'Set Deaths("Player 8", "{s["intro_timer"]}", Set To, 0); //세딘 합류 연출 타이머 초기화',
                f'Set Switch("{VALEN_NOTICE_SWITCH}", clear); //발렌 최초 배속 안내 상태 초기화',
                f'Set Switch("{ELIA_NOTICE_SWITCH}", clear); //엘리아 최초 배속 안내 상태 초기화',
                *[f'Set Switch("{hero["down"]}", clear); //{hero["name"]} 활동 상태 초기화' for hero in all_heroes],
                'Set Switch("Switch245", clear); //로크 합류 요청 초기화',
                'Set Switch("Switch157", clear); //세딘 합류 요청 초기화',
                f'Set Switch("{ROCK_VULTURE_GIFT_PENDING}", clear); //로크 일반 벌처 이양 대기 초기화',
                'Set Switch("Switch252", clear); //로크 추첨 bit0 초기화',
                'Set Switch("Switch253", clear); //로크 추첨 bit1 초기화',
                'Set Switch("Switch254", clear); //세딘 추첨 bit0 초기화',
                'Set Switch("Switch255", clear); //세딘 추첨 bit1 초기화',
                f'Set Switch("{ELIGIBLE_SWITCH}", clear); //합류 후보 임시 상태 초기화',
                'Set Switch("Switch244", set); //선배치 영웅 상태 초기화 완료',
            ],
        ),
        "",
        "//----- 발렌 무작위 배속 -----//",
        trigger(
            "Player 8",
            ['Switch("Switch244", Set);', f'Deaths("Player 8", "{v["holder"]}", Exactly, 0);', 'Elapsed Time(At least, 5);'],
            [
                f'Set Switch("{v["draw0"]}", randomize); //발렌 대상 추첨 bit0',
                f'Set Switch("{v["draw1"]}", randomize); //발렌 대상 추첨 bit1',
                'Preserve Trigger();',
            ],
        ),
    ]
    parts.extend(hero_assignment(v, p) for p in PLAYERS)

    parts.extend([
        "",
        "//----- 엘리아 무작위 배속 -----//",
        trigger(
            "Player 8",
            [f'Deaths("Player 8", "{v["holder"]}", At least, 1);', f'Deaths("Player 8", "{e["holder"]}", Exactly, 0);', 'Elapsed Time(At least, 5);'],
            [
                f'Set Switch("{e["draw0"]}", randomize); //엘리아 대상 추첨 bit0',
                f'Set Switch("{e["draw1"]}", randomize); //엘리아 대상 추첨 bit1',
                'Preserve Trigger();',
            ],
        ),
    ])
    parts.extend(hero_assignment(e, p) for p in PLAYERS)

    parts.extend(["", "//----- 2명 이상인데 두 시작 영웅이 같은 플레이어에게 모이면 엘리아 재추첨 -----//"])
    for owner in PLAYERS:
        for alternative in PLAYERS:
            if alternative != owner:
                parts.append(collision_repair(owner, alternative))

    parts.extend(["", "//----- 최초 배속 개인 안내: 소유자 DC와 안내 완료 래치로 복귀 시 재표시 차단 -----//"])
    for player in PLAYERS:
        parts.append(trigger(
            f"Player {player}",
            [
                f'Switch("{VALEN_NOTICE_SWITCH}", Not Set);',
                f'Switch("{ELIA_NOTICE_SWITCH}", Not Set);',
                f'Deaths("Player 8", "{v["holder"]}", Exactly, {player});',
                f'Deaths("Player 8", "{e["holder"]}", Exactly, {player});',
            ],
            [
                'Display Text Message(Always Display, "<07>[영웅 배속] <03>발렌<04>과 <1B>엘리아<04>가 귀관의 지휘에 합류했습니다.");',
                f'Set Switch("{VALEN_NOTICE_SWITCH}", set); //발렌 최초 배속 안내 완료',
                f'Set Switch("{ELIA_NOTICE_SWITCH}", set); //엘리아 최초 배속 안내 완료',
            ],
        ))
    for player in PLAYERS:
        parts.append(trigger(
            f"Player {player}",
            [f'Switch("{VALEN_NOTICE_SWITCH}", Not Set);', f'Deaths("Player 8", "{v["holder"]}", Exactly, {player});'],
            [
                'Display Text Message(Always Display, "<07>[영웅 배속] <03>발렌<04>이 귀관의 지휘에 합류했습니다.");',
                f'Set Switch("{VALEN_NOTICE_SWITCH}", set); //발렌 최초 배속 안내 완료',
            ],
        ))
    for player in PLAYERS:
        parts.append(trigger(
            f"Player {player}",
            [f'Switch("{ELIA_NOTICE_SWITCH}", Not Set);', f'Deaths("Player 8", "{e["holder"]}", Exactly, {player});'],
            [
                'Display Text Message(Always Display, "<07>[영웅 배속] <1B>엘리아<04>가 귀관의 지휘에 합류했습니다.");',
                f'Set Switch("{ELIA_NOTICE_SWITCH}", set); //엘리아 최초 배속 안내 완료',
            ],
        ))

    parts.extend([
        "",
        "//----- 정신체 부재 독립 감지 : 난이도 선택 및 미션 진행 단계와 무관 -----//",
        unlock_request(r),
        unlock_request(s),
    ])

    parts.extend(["", "//----- 로크 이온 추진기 선물: 생성 다음 사이클에 P9 일반 벌처 확인 후 이양 -----//"])
    for player in PLAYERS:
        parts.append(trigger(
            "Player 8",
            [
                f'Switch("{ROCK_VULTURE_GIFT_PENDING}", Set);',
                f'Deaths("Player 8", "{r["holder"]}", Exactly, {player});',
                'Bring("Player 9", "Terran Vulture", "HeroCJoin", At least, 1);',
            ],
            [
                f'Give Units to Player("Player 9", "Player {player}", "Terran Vulture", 1, "HeroCJoin"); //생성 완료된 P9 벌처를 로크 소유자에게 이양',
                f'Move Unit("Player {player}", "Terran Vulture", 1, "HeroCJoin", "HeroCJoinExit"); //선물 벌처를 출구로 분리해 로크와 겹침 방지',
                f'Set Switch("{ROCK_VULTURE_GIFT_PENDING}", clear); //일반 벌처 이양 완료',
            ],
        ))

    append_late_hero(parts, "rock", ["valen", "elia"])
    append_late_hero(parts, "sedin", ["valen", "elia", "rock"])

    parts.extend(["", "//----- 신규 영웅 합류 연출: 84틱(7초) 대사, 168틱(14초) 개인 안내 -----//"])
    for hero in (r, s):
        parts.append(trigger(
            'Player 1", "Player 2", "Player 3", "Player 4',
            [f'Deaths("Player 8", "{hero["holder"]}", At least, 1);', f'Deaths("Player 8", "{hero["intro_timer"]}", Exactly, 84);'],
            [f'Display Text Message(Always Display, "{hero["color"]}{hero["title"]} {hero["name"]}: <04>{hero["dialogue"]}");'],
        ))
        for player in PLAYERS:
            parts.append(trigger(
                f"Player {player}",
                [f'Deaths("Player 8", "{hero["holder"]}", Exactly, {player});', f'Deaths("Player 8", "{hero["intro_timer"]}", Exactly, 168);'],
                [f'Display Text Message(Always Display, "<07>[영웅 합류] {hero["color"]}{hero["name"]}<04>가 귀관의 지휘에 합류했습니다.");' if hero["name"] == "로크" else f'Display Text Message(Always Display, "<07>[영웅 합류] {hero["color"]}{hero["name"]}<04>이 귀관의 지휘에 합류했습니다.");'],
            ))
        parts.append(trigger(
            "Player 8",
            [f'Deaths("Player 8", "{hero["holder"]}", At least, 1);', f'Deaths("Player 8", "{hero["intro_timer"]}", At most, 167);'],
            [f'Set Deaths("Player 8", "{hero["intro_timer"]}", Add, 1); //12틱=1초, 84틱 대사/168틱 개인 안내까지 진행', 'Preserve Trigger();'],
        ))

    parts.extend(["", "//----- 이탈 승계 코드 동기화: 21 파일이 코드를 지우기 전 P8이 먼저 읽음 -----//"])
    for leaver in PLAYERS:
        for receiver in PLAYERS:
            if receiver != leaver:
                for hero in all_heroes:
                    parts.append(leave_update(hero, leaver, receiver))

    parts.extend(["", "//----- 행동불능 감지 -----//"])
    for hero in all_heroes:
        parts.extend(death_detection(hero, p) for p in PLAYERS)

    parts.extend(["", "//----- 행동불능/복귀 메시지: Exactly 펄스로 반복 사망에도 1회씩만 표시 -----//"])
    for hero in all_heroes:
        parts.append(trigger(
            'Player 1", "Player 2", "Player 3", "Player 4',
            [f'Switch("{hero["down"]}", Set);', f'Deaths("Player 8", "{hero["timer"]}", Exactly, 1);'],
            [f'Display Text Message(Always Display, "<06>[행동 불능] {hero["color"]}{hero["name"]}<04>{"이" if hero["name"] in ("발렌", "세딘") else "가"} 후송되었습니다. 5분 후 미네랄 100을 소모해 배속된 지휘관의 본진에서 복귀합니다.");', 'Preserve Trigger();'],
        ))
        parts.append(trigger(
            'Player 1", "Player 2", "Player 3", "Player 4',
            [f'Switch("{hero["down"]}", Set);', f'Deaths("Player 8", "{hero["timer"]}", Exactly, 3601);'],
            [f'Display Text Message(Always Display, "<07>[전선 복귀] {hero["color"]}{hero["name"]}<04>{"이" if hero["name"] in ("발렌", "세딘") else "가"} 배속된 지휘관의 본진에서 복귀했습니다. <1F>(미네랄 -100)");', 'Preserve Trigger();'],
        ))

    parts.extend(["", "//----- 복귀 완료 상태 정리: 파일상 생성 트리거보다 위에 두어 3601을 한 사이클 유지 -----//"])
    for hero in all_heroes:
        parts.append(trigger(
            "Player 8",
            [f'Switch("{hero["down"]}", Set);', f'Deaths("Player 8", "{hero["timer"]}", Exactly, 3601);'],
            [
                f'Set Switch("{hero["down"]}", clear); //복귀 완료 : 활동 상태 복원',
                f'Set Deaths("Player 8", "{hero["timer"]}", Set To, 0); //다음 행동불능을 위해 타이머 초기화',
                'Preserve Trigger(); //반복 수명주기 : 매 복귀마다 상태를 다시 초기화',
            ],
        ))

    parts.extend(["", "//----- 5분 복귀 타이머: 행동불능 동안 0~3600까지만 증가 -----//"])
    for hero in all_heroes:
        parts.append(trigger(
            "Player 8",
            [f'Switch("{hero["down"]}", Set);', f'Deaths("Player 8", "{hero["timer"]}", At most, 3599);'],
            [f'Set Deaths("Player 8", "{hero["timer"]}", Add, 1); //12틱=1초, 3600틱=5분', 'Preserve Trigger();'],
        ))

    parts.extend(["", "//----- 본진 건물 복귀: CC > Hatchery > Lair > Hive > Nexus 우선 -----//"])
    buildings = ["Terran Command Center", "Zerg Hatchery", "Zerg Lair", "Zerg Hive", "Protoss Nexus"]
    for hero in all_heroes:
        for player in PLAYERS:
            for building in buildings:
                parts.append(respawn_trigger(hero, player, building))

    text = "\n".join(parts).rstrip() + "\n"
    assert len(re.findall(r"^Trigger\(", text, re.MULTILINE)) == len(re.findall(r"^\}$", text, re.MULTILINE))
    assert "Wait(" not in text
    assert text.count("반복 수명주기 : 복귀 후 다음 사망도 다시 감지") == 16
    assert text.count("반복 수명주기 : 매 복귀마다 상태를 다시 초기화") == 4
    assert text.count("반복 수명주기 : 같은 건물 종류에서도 계속 복귀 가능") == 80
    assert text.count('Accumulate("Player ') == 80
    assert text.count(f'Subtract, {RESPAWN_MINERALS}, ore); //복귀 비용 지불') == 80
    for block in re.findall(r"^Trigger\(.*?^\}$", text, re.MULTILINE | re.DOTALL):
        action_body = block.split("Actions:\n", 1)[1].rsplit("\n}", 1)[0]
        assert len([line for line in action_body.splitlines() if line.startswith("\t")]) <= 64
    for line in text.splitlines():
        if any(x in line for x in ("Display Text Message", "Set Mission Objectives", "Play WAV")):
            assert not line.rstrip().endswith("//") and "); //" not in line
    for location in ("HeroCJoin", "HeroCJoinExit", "HeroDJoin", "HeroDJoinExit"):
        assert location in text
    rock_create_count = sum(text.count(f'Create Unit("Player {player}", "Jim Raynor (Vulture)", 1, "HeroCJoin");') for player in PLAYERS)
    relay_create_count = sum(text.count(f'Create Unit("Player {player}", "Terran Vulture", 1, "HeroCJoin");') for player in PLAYERS)
    relay_to_p9_count = sum(text.count(f'Give Units to Player("Player {player}", "Player 9", "Terran Vulture", 1, "HeroCJoin");') for player in PLAYERS)
    assert 'Create Unit("Player 9", "Terran Vulture"' not in text
    assert relay_create_count == rock_create_count
    assert relay_to_p9_count == rock_create_count
    assert text.count('Give Units to Player("Player 9", "Player 1", "Terran Vulture", 1, "HeroCJoin");') == 1
    assert text.count('Give Units to Player("Player 9", "Player 2", "Terran Vulture", 1, "HeroCJoin");') == 1
    assert text.count('Give Units to Player("Player 9", "Player 3", "Terran Vulture", 1, "HeroCJoin");') == 1
    assert text.count('Give Units to Player("Player 9", "Player 4", "Terran Vulture", 1, "HeroCJoin");') == 1
    assert 'Command("Current Player", "Jim Raynor (Marine)"' not in text
    assert 'Command("Current Player", "Sarah Kerrigan (Ghost)"' not in text
    return text


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8", newline="\n")
    print(f"generated: {OUT}")
