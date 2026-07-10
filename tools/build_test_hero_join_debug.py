from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "TestTriggersForBuild" / "95_test_hero_join_debug.txt"
DEBUG_TIMER = "Zerg Ultralisk Cavern"
SNAPSHOT_TICK = 72
PLAYERS = range(1, 5)


def trigger(owner: str, conditions: list[str], actions: list[str]) -> str:
    lines = [f'Trigger("{owner}"){{', "Conditions:"]
    lines.extend(f"\t{line}" for line in conditions)
    lines.append("Actions:")
    lines.extend(f"\t{line}" for line in actions)
    lines.append("}")
    return "\n".join(lines)


def display(owner: str, conditions: list[str], message: str) -> str:
    return trigger(owner, conditions, [f'Display Text Message(Always Display, "{message}");'])


def build() -> str:
    humans = 'Player 1", "Player 2", "Player 3", "Player 4'
    snapshot = f'Deaths("Player 8", "{DEBUG_TIMER}", Exactly, {SNAPSHOT_TICK});'
    common = [snapshot, 'Bring("Player 5", "Zerg Cerebrate", "AttackPoint1", At most, 0);']

    parts = [
        "//=================================================================//",
        "// TEST ONLY - 로크 합류 조건 진단",
        f"// Player 8 {DEBUG_TIMER} DC: 전방 정신체 부재 후 진단 타이머(0~{SNAPSHOT_TICK})",
        "// 정신체 부재 감지 직후 확인 문구, 72틱(6초) 뒤 최초 차단 조건 또는 생성 결과 표시",
        "//=================================================================//",
        "",
        display(
            humans,
            [f'Deaths("Player 8", "{DEBUG_TIMER}", Exactly, 1);'],
            "<03>[로크 진단] <04>AttackPoint1 정신체 부재를 감지했습니다. 6초 뒤 합류 조건을 점검합니다.",
        ),
        "",
        display(
            humans,
            [*common, 'Switch("Switch244", Not Set);'],
            "<06>[로크 진단 BLOCK] <04>Switch244가 꺼져 있습니다. 영웅 시스템 초기화가 완료되지 않았습니다.",
        ),
        display(
            humans,
            [*common, 'Switch("Switch244", Set);', 'Switch("Switch245", Not Set);'],
            "<06>[로크 진단 BLOCK] <04>Switch245가 꺼져 있습니다. 정신체 부재가 로크 합류 요청으로 기록되지 않았습니다.",
        ),
        display(
            humans,
            [*common, 'Switch("Switch245", Set);', 'Deaths("Player 8", "Protoss Arbiter Tribunal", Exactly, 0);'],
            "<06>[로크 진단 WAIT] <04>발렌 소유자 DC가 0입니다. 발렌의 최초 배속을 기다리고 있습니다.",
        ),
        display(
            humans,
            [*common, 'Switch("Switch245", Set);', 'Deaths("Player 8", "Protoss Arbiter Tribunal", At least, 1);', 'Deaths("Player 8", "Protoss Robotics Support Bay", Exactly, 0);'],
            "<06>[로크 진단 WAIT] <04>엘리아 소유자 DC가 0입니다. 엘리아의 최초 배속을 기다리고 있습니다.",
        ),
    ]

    for player in PLAYERS:
        registered = f'Switch("Switch{161 + player}", Set);'
        not_registered = f'Switch("Switch{161 + player}", Not Set);'
        left = f'Switch("Switch{165 + player}", Set);'
        not_left = f'Switch("Switch{165 + player}", Not Set);'
        gate = [
            *common,
            'Switch("Switch245", Set);',
            'Deaths("Player 8", "Protoss Arbiter Tribunal", At least, 1);',
            'Deaths("Player 8", "Protoss Robotics Support Bay", At least, 1);',
            'Deaths("Player 8", "Zerg Nydus Canal", Exactly, 0);',
        ]
        parts.extend([
            display(
                f"Player {player}",
                [*gate, not_registered],
                "<06>[로크 진단 BLOCK] <04>현재 지휘관의 참가 등록 스위치가 꺼져 있습니다. 하트비트 등록을 확인하십시오.",
            ),
            display(
                f"Player {player}",
                [*gate, registered, left],
                "<06>[로크 진단 BLOCK] <04>현재 지휘관이 이탈 상태로 판정되어 있습니다.",
            ),
            display(
                f"Player {player}",
                [*gate, registered, not_left],
                "<06>[로크 진단 BLOCK] <04>활성 생존자는 확인됐지만 배속이 끝나지 않았습니다. 후보 판정과 무작위 추첨 조건을 확인하십시오.",
            ),
        ])

    for player in PLAYERS:
        owner_conditions = [
            *common,
            f'Deaths("Player 8", "Zerg Nydus Canal", Exactly, {player});',
        ]
        parts.extend([
            display(
                humans,
                [*owner_conditions, f'Command("Player {player}", "Jim Raynor (Vulture)", At most, 0);'],
                "<06>[로크 진단 FAIL] <04>로크 소유자 DC는 배정됐지만 실제 로크 유닛이 없습니다. Create Unit과 HeroCJoin을 확인하십시오.",
            ),
            display(
                humans,
                [*owner_conditions, f'Command("Player {player}", "Jim Raynor (Vulture)", At least, 1);'],
                "<07>[로크 진단 PASS] <04>로크 소유자 DC와 실제 유닛 생성을 확인했습니다.",
            ),
        ])

    parts.extend([
        "",
        trigger(
            "Player 8",
            [
                f'Deaths("Player 8", "{DEBUG_TIMER}", At most, {SNAPSHOT_TICK - 1});',
                'Bring("Player 5", "Zerg Cerebrate", "AttackPoint1", At most, 0);',
            ],
            [
                f'Set Deaths("Player 8", "{DEBUG_TIMER}", Add, 1); //진단 지연 : 정신체 부재 후 72틱(6초)까지 진행',
                'Preserve Trigger();',
            ],
        ),
    ])

    text = "\n".join(parts).rstrip() + "\n"
    assert "Wait(" not in text
    assert len(re.findall(r"^Trigger\(", text, re.MULTILINE)) == len(re.findall(r"^\}$", text, re.MULTILINE))
    for line in text.splitlines():
        if "Display Text Message" in line:
            assert line.rstrip().endswith('");') and "); //" not in line
    return text


def main() -> None:
    OUT.write_text(build(), encoding="utf-8")
    print(f"generated: {OUT}")


if __name__ == "__main__":
    main()
