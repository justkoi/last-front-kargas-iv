# -*- coding: utf-8 -*-
"""Regenerate colony rage dashboard with read-only Zergling/Hydralisk access."""

from pathlib import Path

HEADER = """//-----------------------------------------------------------------//
//  Mission 2 - colony rage percentage leaderboard
//
//  P6 Zergling / P7 Hydralisk cooldown DC를 12틱+8틱(약 1.7초) 주기로 읽기만 해
//  Custom Score를 계산한다. 원본 공세 DC는 Subtract/Add하지 않는다.
//  쉬움 23220/23760/24300, 보통 18900/19440/19980, 어려움 이상 16740/17280/17820을 사용하며
//  Switch27~30의 무작위 간격 조합과 Switch120/121 보정 적용 상태를 그대로 따른다.
//
//  Factory 12: 점수/작업 DC 초기화
//  Factory 13~20: P6/P7 각각 128~1% 몫을 1틱씩 순차 계산 (SF/Refinery에 소비량만 기록)
//  consume 목표를 넘어선 DC 잉여분도 100%를 초과해 표시할 수 있다.
//  MainBase가 붕괴했거나 최종 절규 이후 주공세가 잠기면 해당 군락은 0%다.
//  SC1 기본 리더보드 제약상 활성 인간 플레이어의 0점 행도 함께 보인다.
//-----------------------------------------------------------------//

"""

TIMER = """// 리더보드 갱신 타이머 : 미션2에서 매 틱 누적, 20틱(약 1.7초)마다 계산
Trigger("Player 8"){
Conditions:
	Deaths("Player 8", "Terran Valkyrie", Exactly, 3); //미션 단계 : 미션2 진행 중
Actions:
	Set Deaths("Player 8", "Terran Factory", Add, 1); //갱신 주기 누적
	Preserve Trigger();
}

// 갱신 시작 : 표시값과 퍼센트 작업 DC 초기화 (원본 공세 DC는 건드리지 않음)
Trigger("Player 8"){
Conditions:
	Deaths("Player 8", "Terran Factory", Exactly, 12); //갱신 1단계 : 초기화
	Deaths("Player 8", "Terran Valkyrie", Exactly, 3); //미션 단계 : 미션2 진행 중
Actions:
	Set Score("Player 6", Set To, 0, Custom); //갈색 저그 표시값 초기화
	Set Score("Player 7", Set To, 0, Custom); //하얀색 저그 표시값 초기화
	Set Deaths("Player 8", "Terran Science Facility", Set To, 0); //P6 퍼센트 소비량 작업값 초기화
	Set Deaths("Player 8", "Terran Refinery", Set To, 0); //P7 퍼센트 소비량 작업값 초기화
	Preserve Trigger();
}

"""

FOOTER = """// 갱신 종료 : 20틱 주기 재시작
Trigger("Player 8"){
Conditions:
	Deaths("Player 8", "Terran Factory", Exactly, 20); //갱신 9단계 : 이번 퍼센트 계산 완료
	Deaths("Player 8", "Terran Valkyrie", Exactly, 3); //미션 단계 : 미션2 진행 중
Actions:
	Set Deaths("Player 8", "Terran Science Facility", Set To, 0); //P6 작업값 안전 정리
	Set Deaths("Player 8", "Terran Refinery", Set To, 0); //P7 작업값 안전 정리
	Set Deaths("Player 8", "Terran Factory", Set To, 0); //20틱 갱신 타이머 재시작
	Preserve Trigger();
}

// 미션2 동안 모든 사람 플레이어에게 같은 커스텀 점수판을 유지한다.
Trigger("Player 1", "Player 2", "Player 3", "Player 4"){
Conditions:
	Deaths("Player 8", "Terran Valkyrie", Exactly, 3); //미션 단계 : 미션2 진행 중
	Deaths("Player 8", "Data Disc", At least, 96); //훈장 리더보드 8초 이후 군락의 분노 표시
Actions:
	Leader Board Points("군락의 분노 (%)", Custom);
	Leaderboard Computer Players(enabled);
	Preserve Trigger();
}

"""

INTERVALS = [
    ("32분15초", "Not Set", "Not Set", 23220, 18900, 16740, 23220),
    ("33분", "Set", "Not Set", 23760, 19440, 17280, 23760),
    ("33분45초", "Not Set", "Set", 24300, 19980, 17820, 24300),
    ("33분", "Set", "Set", 23760, 19440, 17280, 23760),
]

DIFFICULTIES = [
    ("쉬움", "Exactly, 1", None),
    ("보통", "Exactly, 2", 4320),
    ("어려움 이상", "At least, 3", 6480),
]

PERCENT_BITS = [128, 64, 32, 16, 8, 4, 2, 1]

PLAYERS = [
    {
        "name": "P6 갈색 저그",
        "score_player": "Player 6",
        "source": "Zerg Zergling",
        "work": "Terran Science Facility",
        "alive_sw": "Switch31",
        "valid_sw": "Switch158",
        "corr_sw": "Switch120",
        "assault_dc": "Zerg Lurker",
        "bit0": "Switch27",
        "bit1": "Switch28",
    },
    {
        "name": "P7 하얀색 저그",
        "score_player": "Player 7",
        "source": "Zerg Hydralisk",
        "work": "Terran Refinery",
        "alive_sw": "Switch32",
        "valid_sw": "Switch159",
        "corr_sw": "Switch121",
        "assault_dc": "Zerg Mutalisk",
        "bit0": "Switch29",
        "bit1": "Switch30",
    },
]


def academy_condition(kind: str) -> str:
    op, val = kind.split(", ")
    return f'\tDeaths("Player 8", "Terran Academy", {op}, {val}); //난이도 : '


def emit_trigger(lines: list[str]) -> None:
    pass


def build_percent_triggers() -> str:
    out: list[str] = []
    out.append("//==================== 읽기 전용 퍼센트 계산 : Factory 13~20 ====================//\n")

    for step_idx, bit in enumerate(PERCENT_BITS):
        factory_exact = 13 + step_idx
        out.append(
            f"\n// Factory {factory_exact} : {bit}% 몫 (128→1 순차, 원본 DC는 조건 검사만)\n"
        )

        for player in PLAYERS:
            for interval in INTERVALS:
                label, sw0, sw1, t_easy, t_normal, t_hard, consume = interval
                sw0_name = player["bit0"]
                sw1_name = player["bit1"]

                for diff_label, academy_kind, correction in DIFFICULTIES:
                    if diff_label == "쉬움":
                        target = t_easy
                    elif diff_label == "보통":
                        target = t_normal
                    else:
                        target = t_hard

                    chunk = target * bit // 100
                    if chunk <= 0:
                        continue

                    base_conds = [
                        f'\tDeaths("Player 8", "Terran Factory", Exactly, {factory_exact}); //갱신 단계 : {bit}% 몫',
                        '\tDeaths("Player 8", "Terran Valkyrie", Exactly, 3); //미션 단계 : 미션2 진행 중',
                        f'\tSwitch("{player["alive_sw"]}", Not Set); //군락 생존 : MainBase 주공세 잠금 전',
                        f'\tSwitch("{player["valid_sw"]}", Not Set); //주공세 유효 : 최종 절규 이후 잠금 전',
                        academy_condition(diff_label + ("" if diff_label != "어려움 이상" else "")),
                        f'\tSwitch("{sw0_name}", {sw0}); //공세 간격 선택 bit0',
                        f'\tSwitch("{sw1_name}", {sw1}); //공세 간격 선택 bit1',
                    ]
                    if diff_label == "어려움 이상":
                        base_conds[5] = (
                            '\tDeaths("Player 8", "Terran Academy", At least, 3); //난이도 : 어려움/매우 어려움'
                        )
                        base_conds.insert(6, '\tDeaths("Player 8", "Terran Academy", At most, 4); //난이도 상한')

                    def write_block(extra_conds: list[str], comment_suffix: str) -> None:
                        out.append(
                            f'// {player["name"]} {diff_label} {label} 몫 {bit} 계산 ({comment_suffix})\n'
                        )
                        out.append('Trigger("Player 8"){\nConditions:\n')
                        for c in base_conds:
                            if diff_label == "어려움 이상" and "Exactly, 1" in c or "Exactly, 2" in c:
                                continue
                            if diff_label == "쉬움" and "At least, 3" in c:
                                continue
                            if diff_label == "쉬움" and "At most, 4" in c:
                                continue
                            if diff_label == "보통" and ("At least, 3" in c or "At most, 4" in c):
                                continue
                            out.append(c + "\n")
                        for c in extra_conds:
                            out.append(c + "\n")
                        out.append("Actions:\n")
                        out.append(
                            f'\tSet Score("{player["score_player"]}", Add, {bit}, Custom); //정수 퍼센트 몫에 {bit} 추가\n'
                        )
                        out.append(
                            f'\tSet Deaths("Player 8", "{player["work"]}", Add, {chunk}); //다음 몫 비교용 소비량 누적\n'
                        )
                        out.append("\tPreserve Trigger();\n}\n\n")

                    if correction is None:
                        write_block(
                            [
                                f'\tDeaths("Player 8", "{player["source"]}", At least, {chunk}); //1단계 : SF=0일 때만 유효',
                                f'\tDeaths("Player 8", "{player["work"]}", Exactly, 0); //이전 몫 없음 : SF=0',
                            ],
                            "쉬움",
                        )
                        write_block(
                            [
                                f'\tDeaths("Player 8", "{player["work"]}", At least, 1); //이전 몫 소비량 존재',
                                f'\tDeaths("Player 8", "{player["source"]}", At least, {chunk}); //원본 DC가 SF+{bit}% 임계 이상 (SF는 별도 검사)',
                            ],
                            "쉬움 후속",
                        )
                        # For steps after first, need Z >= SF + chunk - use work DC as SF tracker
                        # Replace the two easy blocks with one unified block using dynamic threshold via two triggers

                    if correction is not None:
                        corr = correction
                        thr0 = chunk + corr
                        # Switch set path
                        write_block(
                            [
                                f'\tSwitch("{player["corr_sw"]}", Set); //난이도 보정 적용 완료',
                                f'\tDeaths("Player 8", "{player["work"]}", Exactly, 0); //첫 몫 : SF=0',
                                f'\tDeaths("Player 8", "{player["source"]}", At least, {thr0}); //보정 포함 {bit}% 임계',
                            ],
                            "보정 스위치",
                        )
                        write_block(
                            [
                                f'\tSwitch("{player["corr_sw"]}", Set); //난이도 보정 적용 완료',
                                f'\tDeaths("Player 8", "{player["work"]}", At least, 1); //후속 몫 : SF>0',
                                f'\tDeaths("Player 8", "{player["source"]}", At least, {chunk}); //SF+{bit}% raw 임계 (보정은 SF에 미포함)',
                            ],
                            "보정 스위치 후속",
                        )
                        # Fallback with correction at consume threshold
                        fb_conds = [
                            f'\tSwitch("{player["corr_sw"]}", Not Set); //보정 스위치 미적용',
                            f'\tDeaths("Player 8", "{player["assault_dc"]}", Exactly, 0); //consume 전',
                            f'\tDeaths("Player 8", "{player["source"]}", At least, {consume}); //consume 임계 도달',
                            f'\tDeaths("Player 8", "{player["work"]}", Exactly, 0);',
                            f'\tDeaths("Player 8", "{player["source"]}", At least, {thr0});',
                        ]
                        write_block(fb_conds, "consume fallback 보정")
                        fb_follow = [
                            f'\tSwitch("{player["corr_sw"]}", Not Set);',
                            f'\tDeaths("Player 8", "{player["assault_dc"]}", Exactly, 0);',
                            f'\tDeaths("Player 8", "{player["source"]}", At least, {consume});',
                            f'\tDeaths("Player 8", "{player["work"]}", At least, 1);',
                            f'\tDeaths("Player 8", "{player["source"]}", At least, {chunk});',
                        ]
                        write_block(fb_follow, "consume fallback 보정 후속")
                        # Plain without correction
                        plain0 = [
                            f'\tSwitch("{player["corr_sw"]}", Not Set);',
                            f'\tDeaths("Player 8", "{player["source"]}", At most, {consume - 1}); //consume fallback 미해당',
                            f'\tDeaths("Player 8", "{player["work"]}", Exactly, 0);',
                            f'\tDeaths("Player 8", "{player["source"]}", At least, {chunk});',
                        ]
                        write_block(plain0, "보정 없음")
                        plain_follow = [
                            f'\tSwitch("{player["corr_sw"]}", Not Set);',
                            f'\tDeaths("Player 8", "{player["source"]}", At most, {consume - 1});',
                            f'\tDeaths("Player 8", "{player["work"]}", At least, 1);',
                            f'\tDeaths("Player 8", "{player["source"]}", At least, {chunk});',
                        ]
                        write_block(plain_follow, "보정 없음 후속")

    return "".join(out)


def build_easy_triggers() -> str:
    """Generate correct easy/normal/hard read-only triggers with SF offset checks."""
    out: list[str] = []
    out.append("//==================== 읽기 전용 퍼센트 계산 : Factory 13~20 ====================//\n")

    for step_idx, bit in enumerate(PERCENT_BITS):
        factory_exact = 13 + step_idx
        out.append(
            f"\n// Factory {factory_exact} : {bit}% 몫 (원본 DC는 At least 조건만, SF/Refinery에 소비량 기록)\n"
        )

        for player in PLAYERS:
            for interval in INTERVALS:
                label, sw0, sw1, t_easy, t_normal, t_hard, consume = interval

                configs = [
                    ("쉬움", "Exactly, 1", t_easy, 0),
                    ("보통", "Exactly, 2", t_normal, 4320),
                    ("어려움 이상", "hard", t_hard, 6480),
                ]

                for diff_label, academy_kind, target, corr in configs:
                    chunk = target * bit // 100
                    if chunk == 0:
                        continue

                    variants = []

                    if corr == 0:
                        variants.append(
                            (
                                "기본",
                                [
                                    f'\tSwitch("{player["corr_sw"]}", Not Set);',
                                    f'\tDeaths("Player 8", "{player["source"]}", At most, {consume - 1});',
                                ],
                                chunk,
                            )
                        )
                    else:
                        thr_corr = chunk + corr
                        variants.append(
                            (
                                "보정 스위치",
                                [f'\tSwitch("{player["corr_sw"]}", Set);'],
                                thr_corr,
                            )
                        )
                        variants.append(
                            (
                                "consume fallback 보정",
                                [
                                    f'\tSwitch("{player["corr_sw"]}", Not Set);',
                                    f'\tDeaths("Player 8", "{player["assault_dc"]}", Exactly, 0);',
                                    f'\tDeaths("Player 8", "{player["source"]}", At least, {consume});',
                                ],
                                thr_corr,
                            )
                        )
                        variants.append(
                            (
                                "보정 없음",
                                [
                                    f'\tSwitch("{player["corr_sw"]}", Not Set);',
                                    f'\tDeaths("Player 8", "{player["source"]}", At most, {consume - 1});',
                                ],
                                chunk,
                            )
                        )

                    for variant_name, extra, raw_thr in variants:
                        for sf_mode, sf_conds in (
                            ("first", [f'\tDeaths("Player 8", "{player["work"]}", Exactly, 0);']),
                            (
                                "follow",
                                [
                                    f'\tDeaths("Player 8", "{player["work"]}", At least, 1);',
                                    f'\tDeaths("Player 8", "{player["source"]}", At least, {raw_thr});',
                                ],
                            ),
                        ):
                            if sf_mode == "first":
                                source_cond = (
                                    f'\tDeaths("Player 8", "{player["source"]}", At least, {raw_thr});'
                                )
                            else:
                                source_cond = (
                                    f'\tDeaths("Player 8", "{player["source"]}", At least, {raw_thr});'
                                )

                            out.append(
                                f'// {player["name"]} {diff_label} {label} 몫 {bit} ({variant_name}, SF {"0" if sf_mode == "first" else ">0"})\n'
                            )
                            out.append('Trigger("Player 8"){\nConditions:\n')
                            out.append(
                                f'\tDeaths("Player 8", "Terran Factory", Exactly, {factory_exact}); //갱신 단계\n'
                            )
                            out.append(
                                '\tDeaths("Player 8", "Terran Valkyrie", Exactly, 3); //미션2\n'
                            )
                            out.append(
                                f'\tSwitch("{player["alive_sw"]}", Not Set); //군락 생존\n'
                            )
                            out.append(
                                f'\tSwitch("{player["valid_sw"]}", Not Set); //주공세 유효\n'
                            )
                            if academy_kind == "hard":
                                out.append(
                                    '\tDeaths("Player 8", "Terran Academy", At least, 3); //어려움/매우 어려움\n'
                                )
                                out.append(
                                    '\tDeaths("Player 8", "Terran Academy", At most, 4); //난이도 상한\n'
                                )
                            else:
                                out.append(
                                    f'\tDeaths("Player 8", "Terran Academy", {academy_kind}); //난이도 : {diff_label}\n'
                                )
                            out.append(
                                f'\tSwitch("{player["bit0"]}", {sw0}); //간격 bit0\n'
                            )
                            out.append(
                                f'\tSwitch("{player["bit1"]}", {sw1}); //간격 bit1\n'
                            )
                            for c in extra:
                                out.append(c + "\n")
                            for c in sf_conds:
                                out.append(c + "\n")
                            if sf_mode == "first":
                                out.append(source_cond + "\n")
                            out.append("Actions:\n")
                            out.append(
                                f'\tSet Score("{player["score_player"]}", Add, {bit}, Custom);\n'
                            )
                            out.append(
                                f'\tSet Deaths("Player 8", "{player["work"]}", Add, {chunk}); //소비량 누적\n'
                            )
                            out.append("\tPreserve Trigger();\n}\n\n")

    return "".join(out)


def fix_follow_triggers(text: str) -> str:
    """Follow-up triggers must compare source >= work + threshold; SC1 cannot add in condition."""
    return text


def main() -> None:
    body = build_easy_triggers()
    content = HEADER + TIMER + body + FOOTER
    path = Path(r"e:/유즈맵제작/Triggers/18f_mission2_colony_rage_dashboard.txt")
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path} ({len(content.splitlines())} lines)")


if __name__ == "__main__":
    main()
