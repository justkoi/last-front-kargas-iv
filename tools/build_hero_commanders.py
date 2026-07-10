from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Triggers" / "01d_hero_commanders.txt"

PLAYERS = range(1, 5)
RESPAWN_MINERALS = 100
HEROES = {
    "valen": {
        "unit": "Jim Raynor (Marine)",
        "name": "발렌",
        "color": "<03>",
        "holder": "Protoss Arbiter Tribunal",
        "timer": "Zerg Spire",
        "assigned": "Switch236",
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
        "assigned": "Switch237",
        "down": "Switch239",
        "draw0": "Switch242",
        "draw1": "Switch243",
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


def draw_conditions(hero: dict, player: int) -> list[str]:
    # clear/clear=P1, set/clear=P2, clear/set=P3, set/set=P4
    mapping = {
        1: ("Not Set", "Not Set"),
        2: ("Set", "Not Set"),
        3: ("Not Set", "Set"),
        4: ("Set", "Set"),
    }
    b0, b1 = mapping[player]
    return [
        f'Switch("{hero["assigned"]}", Not Set);',
        f'Switch("{hero["draw0"]}", {b0});',
        f'Switch("{hero["draw1"]}", {b1});',
        *active_conditions(player),
    ]


def hero_assignment(hero: dict, player: int) -> str:
    return trigger(
        "Player 8",
        draw_conditions(hero, player),
        [
            f'Give Units to Player("Player 9", "Player {player}", "{hero["unit"]}", 1, "Anywhere"); //영웅 무작위 배속 : P9 대기 영웅을 활성 플레이어에게 이양',
            f'Set Deaths("Player 8", "{hero["holder"]}", Set To, {player}); //현재 소유자 기록 : {hero["name"]} 소유자=P{player}',
            f'Set Switch("{hero["assigned"]}", set); //배속 완료 : 재추첨 중단',
        ],
    )


def death_detection(hero: dict, player: int) -> str:
    return trigger(
        "Player 8",
        [
            f'Switch("{hero["assigned"]}", Set);',
            f'Switch("{hero["down"]}", Not Set);',
            f'Deaths("Player {player}", "{hero["unit"]}", At least, 1);',
        ],
        [
            f'Set Deaths("Player {player}", "{hero["unit"]}", Set To, 0); //사망 카운터 정리 : 다음 행동불능도 다시 감지',
            f'Set Deaths("Player 8", "{hero["holder"]}", Set To, {player}); //행동불능 당시 소유자 보존 : 복귀 위치 결정',
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
        [
            f'Set Deaths("Player 8", "{hero["holder"]}", Set To, {receiver}); //이탈 승계 연동 : {hero["name"]} 소유자 P{leaver}->P{receiver}',
        ],
    )


def collision_repair(owner: int, alternative: int) -> str:
    elia = HEROES["elia"]
    valen = HEROES["valen"]
    return trigger(
        "Player 8",
        [
            f'Switch("{elia["assigned"]}", Set);',
            f'Deaths("Player 8", "{valen["holder"]}", Exactly, {owner});',
            f'Deaths("Player 8", "{elia["holder"]}", Exactly, {owner});',
            *active_conditions(alternative),
        ],
        [
            f'Give Units to Player("Player {owner}", "Player 9", "{elia["unit"]}", 1, "Anywhere"); //중복 소유 해소 : 엘리아를 P9 대기 상태로 회수',
            f'Set Deaths("Player 8", "{elia["holder"]}", Set To, 0); //엘리아 소유자 재추첨 준비',
            f'Set Switch("{elia["assigned"]}", clear); //활성 플레이어가 2명 이상이면 발렌과 다른 소유자를 다시 추첨',
        ],
    )


def build() -> str:
    v = HEROES["valen"]
    e = HEROES["elia"]
    parts: list[str] = [
        "//=================================================================//",
        "//  발렌/엘리아 영웅 지휘 시스템",
        "//  - 시작: P9가 두 영웅 생성 후 활성 P1~P4에 완전 무작위 배속",
        "//  - 2명 이상: 서로 다른 플레이어가 소유 / 1명: 한 플레이어가 둘 다 소유",
        "//  - 행동불능: 사망 감지 후 3600틱(12틱=1초, 5분) 뒤 미네랄 100을 소모해 본진 건물에서 복귀",
        "//  - 이탈: 21_player_leave_handoff의 승계 코드와 소유자 상태를 동기화",
        "//=================================================================//",
        "",
        "//----- P8 상태 슬롯 -----//",
        "// Protoss Arbiter Tribunal   : 발렌 현재 소유자(0=미배속, 1~4=P1~P4)",
        "// Protoss Robotics Support Bay: 엘리아 현재 소유자(0=미배속, 1~4=P1~P4)",
        "// Zerg Spire                 : 발렌 행동불능 복귀 타이머(0~3601)",
        "// Zerg Greater Spire         : 엘리아 행동불능 복귀 타이머(0~3601)",
        "// Switch236/237              : 발렌/엘리아 배속 완료",
        "// Switch238/239              : 발렌/엘리아 행동불능",
        "// Switch240/241              : 발렌 2비트 무작위 대상",
        "// Switch242/243              : 엘리아 2비트 무작위 대상",
        "// Switch244                  : P9 영웅 생성 완료",
        "",
        "//----- P9 대기 영웅 생성 -----//",
        trigger(
            "Player 8",
            [
                'Switch("Switch244", Not Set);',
                'Elapsed Time(At least, 2);',
            ],
            [
                f'Set Deaths("Player 8", "{v["holder"]}", Set To, 0); //발렌 소유자 초기화',
                f'Set Deaths("Player 8", "{e["holder"]}", Set To, 0); //엘리아 소유자 초기화',
                f'Set Deaths("Player 8", "{v["timer"]}", Set To, 0); //발렌 복귀 타이머 초기화',
                f'Set Deaths("Player 8", "{e["timer"]}", Set To, 0); //엘리아 복귀 타이머 초기화',
                f'Set Switch("{v["assigned"]}", clear); //발렌 배속 상태 초기화',
                f'Set Switch("{e["assigned"]}", clear); //엘리아 배속 상태 초기화',
                f'Set Switch("{v["down"]}", clear); //발렌 활동 상태 초기화',
                f'Set Switch("{e["down"]}", clear); //엘리아 활동 상태 초기화',
                f'Create Unit("Player 9", "{v["unit"]}", 1, "BaseEntrance"); //발렌 대기 : P9 소유로 입구 거점에 생성',
                f'Create Unit("Player 9", "{e["unit"]}", 1, "BaseEntrance"); //엘리아 대기 : P9 소유로 입구 거점에 생성',
                'Set Switch("Switch244", set); //영웅 중복 생성 방지',
            ],
        ),
        "",
        "//----- 발렌 무작위 배속 -----//",
        trigger(
            "Player 8",
            [
                'Switch("Switch244", Set);',
                f'Switch("{v["assigned"]}", Not Set);',
                'Elapsed Time(At least, 5);',
            ],
            [
                f'Set Switch("{v["draw0"]}", randomize); //발렌 대상 추첨 bit0',
                f'Set Switch("{v["draw1"]}", randomize); //발렌 대상 추첨 bit1',
                'Preserve Trigger();',
            ],
        ),
    ]
    parts.extend(hero_assignment(v, p) for p in PLAYERS)

    parts.extend(
        [
            "",
            "//----- 엘리아 무작위 배속 -----//",
            trigger(
                "Player 8",
                [
                    f'Switch("{v["assigned"]}", Set);',
                    f'Switch("{e["assigned"]}", Not Set);',
                    'Elapsed Time(At least, 5);',
                ],
                [
                    f'Set Switch("{e["draw0"]}", randomize); //엘리아 대상 추첨 bit0',
                    f'Set Switch("{e["draw1"]}", randomize); //엘리아 대상 추첨 bit1',
                    'Preserve Trigger();',
                ],
            ),
        ]
    )
    parts.extend(hero_assignment(e, p) for p in PLAYERS)

    parts.extend(
        [
            "",
            "//----- 2명 이상인데 두 영웅이 같은 플레이어에게 모이면 엘리아 재추첨 -----//",
        ]
    )
    for owner in PLAYERS:
        for alternative in PLAYERS:
            if alternative != owner:
                parts.append(collision_repair(owner, alternative))

    parts.extend(
        [
            "",
            "//----- 최초 배속 개인 안내: 두 영웅 배속 완료 후 각 소유자에게 1회 -----//",
            trigger(
                "Player 1\", \"Player 2\", \"Player 3\", \"Player 4",
                [
                    f'Switch("{v["assigned"]}", Set);',
                    f'Switch("{e["assigned"]}", Set);',
                    f'Command("Current Player", "{v["unit"]}", At least, 1);',
                    f'Command("Current Player", "{e["unit"]}", At least, 1);',
                ],
                [
                    'Display Text Message(Always Display, "<07>[영웅 배속] <03>발렌<04>과 <1B>엘리아<04>가 귀관의 지휘에 합류했습니다.");',
                ],
            ),
            trigger(
                "Player 1\", \"Player 2\", \"Player 3\", \"Player 4",
                [
                    f'Switch("{v["assigned"]}", Set);',
                    f'Switch("{e["assigned"]}", Set);',
                    f'Command("Current Player", "{v["unit"]}", At least, 1);',
                    f'Command("Current Player", "{e["unit"]}", At most, 0);',
                ],
                [
                    'Display Text Message(Always Display, "<07>[영웅 배속] <03>발렌<04>이 귀관의 지휘에 합류했습니다.");',
                ],
            ),
            trigger(
                "Player 1\", \"Player 2\", \"Player 3\", \"Player 4",
                [
                    f'Switch("{v["assigned"]}", Set);',
                    f'Switch("{e["assigned"]}", Set);',
                    f'Command("Current Player", "{v["unit"]}", At most, 0);',
                    f'Command("Current Player", "{e["unit"]}", At least, 1);',
                ],
                [
                    'Display Text Message(Always Display, "<07>[영웅 배속] <1B>엘리아<04>가 귀관의 지휘에 합류했습니다.");',
                ],
            ),
            "",
            "//----- 이탈 승계 코드 동기화: 21 파일이 코드를 지우기 전 P8이 먼저 읽음 -----//",
        ]
    )
    for leaver in PLAYERS:
        for receiver in PLAYERS:
            if receiver != leaver:
                parts.append(leave_update(v, leaver, receiver))
                parts.append(leave_update(e, leaver, receiver))

    parts.extend(["", "//----- 행동불능 감지 -----//"])
    for hero in (v, e):
        parts.extend(death_detection(hero, p) for p in PLAYERS)

    parts.extend(
        [
            "",
            "//----- 행동불능/복귀 메시지: Exactly 펄스로 반복 사망에도 1회씩만 표시 -----//",
            trigger(
                "Player 1\", \"Player 2\", \"Player 3\", \"Player 4",
                [f'Switch("{v["down"]}", Set);', f'Deaths("Player 8", "{v["timer"]}", Exactly, 1);'],
                ['Display Text Message(Always Display, "<06>[행동 불능] <03>발렌<04>이 후송되었습니다. 5분 후 미네랄 100을 소모해 배속된 지휘관의 본진에서 복귀합니다.");', 'Preserve Trigger();'],
            ),
            trigger(
                "Player 1\", \"Player 2\", \"Player 3\", \"Player 4",
                [f'Switch("{e["down"]}", Set);', f'Deaths("Player 8", "{e["timer"]}", Exactly, 1);'],
                ['Display Text Message(Always Display, "<06>[행동 불능] <1B>엘리아<04>가 후송되었습니다. 5분 후 미네랄 100을 소모해 배속된 지휘관의 본진에서 복귀합니다.");', 'Preserve Trigger();'],
            ),
            trigger(
                "Player 1\", \"Player 2\", \"Player 3\", \"Player 4",
                [f'Switch("{v["down"]}", Set);', f'Deaths("Player 8", "{v["timer"]}", Exactly, 3601);'],
                ['Display Text Message(Always Display, "<07>[전선 복귀] <03>발렌<04>이 배속된 지휘관의 본진에서 복귀했습니다. <1F>(미네랄 -100)");', 'Preserve Trigger();'],
            ),
            trigger(
                "Player 1\", \"Player 2\", \"Player 3\", \"Player 4",
                [f'Switch("{e["down"]}", Set);', f'Deaths("Player 8", "{e["timer"]}", Exactly, 3601);'],
                ['Display Text Message(Always Display, "<07>[전선 복귀] <1B>엘리아<04>가 배속된 지휘관의 본진에서 복귀했습니다. <1F>(미네랄 -100)");', 'Preserve Trigger();'],
            ),
            "",
            "//----- 복귀 완료 상태 정리: 파일상 생성 트리거보다 위에 두어 3601을 한 사이클 유지 -----//",
        ]
    )
    for hero in (v, e):
        parts.append(
            trigger(
                "Player 8",
                [f'Switch("{hero["down"]}", Set);', f'Deaths("Player 8", "{hero["timer"]}", Exactly, 3601);'],
                [
                    f'Set Switch("{hero["down"]}", clear); //복귀 완료 : 활동 상태 복원',
                    f'Set Deaths("Player 8", "{hero["timer"]}", Set To, 0); //다음 행동불능을 위해 타이머 초기화',
                    'Preserve Trigger(); //반복 수명주기 : 매 복귀마다 상태를 다시 초기화',
                ],
            )
        )

    parts.extend(["", "//----- 5분 복귀 타이머: 행동불능 동안 0~3600까지만 증가 -----//"])
    for hero in (v, e):
        parts.append(
            trigger(
                "Player 8",
                [f'Switch("{hero["down"]}", Set);', f'Deaths("Player 8", "{hero["timer"]}", At most, 3599);'],
                [f'Set Deaths("Player 8", "{hero["timer"]}", Add, 1); //12틱=1초, 3600틱=5분', 'Preserve Trigger();'],
            )
        )

    parts.extend(["", "//----- 본진 건물 복귀: CC > Hatchery > Lair > Hive > Nexus 우선 -----//"])
    buildings = ["Terran Command Center", "Zerg Hatchery", "Zerg Lair", "Zerg Hive", "Protoss Nexus"]
    for hero in (v, e):
        for player in PLAYERS:
            for building in buildings:
                parts.append(respawn_trigger(hero, player, building))

    text = "\n".join(parts).rstrip() + "\n"
    assert len(re.findall(r"^Trigger\(", text, re.MULTILINE)) == len(re.findall(r"^\}$", text, re.MULTILINE))
    assert "Wait(" not in text
    assert text.count("반복 수명주기 : 복귀 후 다음 사망도 다시 감지") == 8
    assert text.count("반복 수명주기 : 매 복귀마다 상태를 다시 초기화") == 2
    assert text.count("반복 수명주기 : 같은 건물 종류에서도 계속 복귀 가능") == 40
    assert text.count(f'Accumulate("Player ') == 40
    assert text.count(f'Subtract, {RESPAWN_MINERALS}, ore); //복귀 비용 지불') == 40
    for line in text.splitlines():
        if any(x in line for x in ("Display Text Message", "Set Mission Objectives", "Play WAV")):
            assert not line.rstrip().endswith("//") and "); //" not in line
    return text


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8", newline="\n")
    print(f"generated: {OUT}")
