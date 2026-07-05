#!/usr/bin/env python3
"""Rebuild wartime rationing payment tiers: 120/300/640/1000/1800/3000."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "Triggers" / "13f_union_relief_fund.txt"

TIERS = [
    (4001, 5999, 120),
    (6000, 7999, 300),
    (8000, 10000, 640),
    (10001, 15000, 1000),
    (15001, 20000, 1800),
    (20001, None, 3000),
]

# player -> (cycle_flag, ore switches tier1-6, gas switches tier1-6)
PLAYERS = {
    1: (178, (182, 183, 184, 185, 198, 199), (202, 203, 204, 205, 226, 227)),
    2: (179, (186, 187, 188, 189, 200, 201), (206, 207, 208, 209, 228, 229)),
    3: (180, (190, 191, 192, 193, 222, 223), (210, 211, 212, 213, 230, 231)),
    4: (181, (194, 195, 196, 197, 224, 225), (214, 215, 216, 217, 232, 233)),
}

ALL_PAYMENT_SWITCHES = sorted(
    {sw for _, ore, gas in PLAYERS.values() for sw in ore + gas}
)


def accumulate_lines(resource: str, low: int, high: int | None) -> list[str]:
    lines = [f'\tAccumulate("Player {player}", At least, {low}, {resource});' for player in range(1, 5)]
    # replaced per-player below
    return []


def accumulate_for_player(player: int, resource: str, low: int, high: int | None) -> list[str]:
    lines = [f'\tAccumulate("Player {player}", At least, {low}, {resource});']
    if high is not None:
        lines.append(f'\tAccumulate("Player {player}", At most, {high}, {resource});')
    return lines


def gen_donor_selection() -> str:
    chunks = ["// Donor tier selection (Queen=30).\n"]
    for donor, (cycle_sw, ore_sws, gas_sws) in PLAYERS.items():
        for receiver in range(1, 5):
            for tier_idx, (low, high, _amount) in enumerate(TIERS):
                ore_sw = ore_sws[tier_idx]
                lines = [
                    'Trigger("Player 8"){',
                    "Conditions:",
                    '\tSwitch("Switch177", Set);',
                    '\tDeaths("Player 8", "Zerg Queen", Exactly, 30);',
                    f'\tSwitch("Switch{cycle_sw}", Set);',
                    f'\tDeaths("Player 8", "Zerg Spawning Pool", Exactly, {receiver});',
                ]
                lines.extend(accumulate_for_player(donor, "ore", low, high))
                lines += [
                    "Actions:",
                    f'\tSet Switch("Switch{ore_sw}", set);',
                    "\tPreserve Trigger();",
                    "}",
                    "",
                ]
                chunks.append("\n".join(lines))

                gas_sw = gas_sws[tier_idx]
                lines = [
                    'Trigger("Player 8"){',
                    "Conditions:",
                    '\tSwitch("Switch177", Set);',
                    '\tDeaths("Player 8", "Zerg Queen", Exactly, 30);',
                    f'\tSwitch("Switch{cycle_sw}", Set);',
                    f'\tDeaths("Player 8", "Zerg Evolution Chamber", Exactly, {receiver});',
                ]
                lines.extend(accumulate_for_player(donor, "gas", low, high))
                lines += [
                    "Actions:",
                    f'\tSet Switch("Switch{gas_sw}", set);',
                    "\tPreserve Trigger();",
                    "}",
                    "",
                ]
                chunks.append("\n".join(lines))
    return "\n".join(chunks)


def switch_to_donor(switch: int) -> int:
    for player, (_, ore_sws, gas_sws) in PLAYERS.items():
        if switch in ore_sws or switch in gas_sws:
            return player
    raise ValueError(switch)


def is_ore_switch(switch: int) -> bool:
    for _, ore_sws, _ in PLAYERS.values():
        if switch in ore_sws:
            return True
    return False


def gen_transfers() -> str:
    chunks = ["// Resource transfers (Queen=30).\n"]
    for _, (_, ore_sws, gas_sws) in PLAYERS.items():
        for sw in ore_sws:
            donor = switch_to_donor(sw)
            amount = TIERS[ore_sws.index(sw)][2]
            for receiver in range(1, 5):
                if receiver == donor:
                    continue
                lines = [
                    'Trigger("Player 8"){',
                    "Conditions:",
                    '\tSwitch("Switch177", Set);',
                    '\tDeaths("Player 8", "Zerg Queen", Exactly, 30);',
                    f'\tDeaths("Player 8", "Zerg Spawning Pool", Exactly, {receiver});',
                    f'\tSwitch("Switch{sw}", Set);',
                    "Actions:",
                    f'\tSet Resources("Player {donor}", Subtract, {amount}, ore);',
                    f'\tSet Resources("Player {receiver}", Add, {amount}, ore);',
                    f'\tSet Deaths("Player 8", "Protoss Pylon", Add, {amount});',
                    "\tPreserve Trigger();",
                    "}",
                    "",
                ]
                chunks.append("\n".join(lines))
        for sw in gas_sws:
            donor = switch_to_donor(sw)
            amount = TIERS[gas_sws.index(sw)][2]
            for receiver in range(1, 5):
                if receiver == donor:
                    continue
                lines = [
                    'Trigger("Player 8"){',
                    "Conditions:",
                    '\tSwitch("Switch177", Set);',
                    '\tDeaths("Player 8", "Zerg Queen", Exactly, 30);',
                    f'\tDeaths("Player 8", "Zerg Evolution Chamber", Exactly, {receiver});',
                    f'\tSwitch("Switch{sw}", Set);',
                    "Actions:",
                    f'\tSet Resources("Player {donor}", Subtract, {amount}, gas);',
                    f'\tSet Resources("Player {receiver}", Add, {amount}, gas);',
                    f'\tSet Deaths("Player 8", "Zerg Hydralisk Den", Add, {amount});',
                    "\tPreserve Trigger();",
                    "}",
                    "",
                ]
                chunks.append("\n".join(lines))
    return "\n".join(chunks)


def gen_receive_messages() -> str:
    chunks = ["// Receive confirmation messages (Queen=40).\n"]
    amounts = [t[2] for t in TIERS]
    for player in range(1, 5):
        for amount in amounts:
            lines = [
                f'Trigger("Player {player}"){{',
                "Conditions:",
                '\tSwitch("Switch177", Set);',
                '\tDeaths("Player 8", "Zerg Queen", Exactly, 40);',
                '\tDeaths("Player 8", "Terran Siege Tank (Tank Mode)", Exactly, 1);',
                f'\tDeaths("Player 8", "Zerg Spawning Pool", Exactly, {player});',
                f'\tDeaths("Player 8", "Protoss Pylon", Exactly, {amount});',
                "Actions:",
                f'\tDisplay Text Message(Always Display, "<03>[전시 배급소] <04>전시 배급 물자가 도착했습니다. <1F>미네랄 +{amount}");',
                "\tPreserve Trigger();",
                "}",
                "",
            ]
            chunks.append("\n".join(lines))
        for amount in amounts:
            lines = [
                f'Trigger("Player {player}"){{',
                "Conditions:",
                '\tSwitch("Switch177", Set);',
                '\tDeaths("Player 8", "Zerg Queen", Exactly, 40);',
                '\tDeaths("Player 8", "Terran Siege Tank (Tank Mode)", Exactly, 24);',
                f'\tDeaths("Player 8", "Zerg Evolution Chamber", Exactly, {player});',
                f'\tDeaths("Player 8", "Zerg Hydralisk Den", Exactly, {amount});',
                "Actions:",
                f'\tDisplay Text Message(Always Display, "<03>[전시 배급소] <04>전시 배급 물자가 도착했습니다. <07>가스 +{amount}");',
                "\tPreserve Trigger();",
                "}",
                "",
            ]
            chunks.append("\n".join(lines))
    return "\n".join(chunks)


def gen_donate_messages() -> str:
    chunks = ["// Donor confirmation messages (Queen=40, Tank=48).\n"]
    amounts = {}
    for _, (_, ore_sws, gas_sws) in PLAYERS.items():
        for idx, sw in enumerate(ore_sws):
            amounts[sw] = TIERS[idx][2]
        for idx, sw in enumerate(gas_sws):
            amounts[sw] = TIERS[idx][2]

    for player, (_, ore_sws, gas_sws) in PLAYERS.items():
        all_player_sws = list(ore_sws) + list(gas_sws)

        def emit(ore_active: set[int], gas_active: set[int]) -> None:
            if not ore_active and not gas_active:
                return
            parts = []
            if ore_active:
                parts.append("<1F>미네랄 " + "  ".join(f"-{amounts[sw]}" for sw in ore_sws if sw in ore_active))
            if gas_active:
                parts.append("<07>가스 " + "  ".join(f"-{amounts[sw]}" for sw in gas_sws if sw in gas_active))
            msg_body = "  ".join(parts)
            lines = [
                f'Trigger("Player {player}"){{',
                "Conditions:",
                '\tSwitch("Switch177", Set);',
                '\tDeaths("Player 8", "Zerg Queen", Exactly, 40);',
                '\tDeaths("Player 8", "Terran Siege Tank (Tank Mode)", Exactly, 48);',
            ]
            for sw in all_player_sws:
                on = sw in ore_active or sw in gas_active
                lines.append(f'\tSwitch("Switch{sw}", {"Set" if on else "Not Set"});')
            lines += [
                "Actions:",
                f'\tDisplay Text Message(Always Display, "<03>[전시 배급소] <04>전시 배급 물자로 전환되었습니다. {msg_body}");',
                "\tPreserve Trigger();",
                "}",
                "",
            ]
            chunks.append("\n".join(lines))

        for sw in ore_sws:
            emit({sw}, set())
        for sw in gas_sws:
            emit(set(), {sw})
        for ore_sw in ore_sws:
            for gas_sw in gas_sws:
                emit({ore_sw}, {gas_sw})

    return "\n".join(chunks)


def gen_queen_advance() -> str:
    return """Trigger("Player 8"){
Conditions:
\tSwitch("Switch177", Set);
\tDeaths("Player 8", "Zerg Queen", Exactly, 30);
Actions:
\tSet Deaths("Player 8", "Zerg Queen", Set To, 40);
\tPreserve Trigger();
}

Trigger("Player 8"){
Conditions:
\tSwitch("Switch177", Set);
\tDeaths("Player 8", "Zerg Queen", Exactly, 40);
\tDeaths("Player 8", "Terran Siege Tank (Tank Mode)", At most, 83);
Actions:
\tSet Deaths("Player 8", "Terran Siege Tank (Tank Mode)", Add, 1);
\tPreserve Trigger();
}

"""


def gen_switch_clears() -> str:
    lines = []
    for sw in ALL_PAYMENT_SWITCHES:
        lines.append(f'\tSet Switch("Switch{sw}", clear);')
    return "\n".join(lines)


def patch_switch_clears(text: str) -> str:
    for sw in ALL_PAYMENT_SWITCHES:
        if f'Set Switch("Switch{sw}", clear);' not in text:
            pass
    # append missing clears after existing payment switch clears in each cleanup block
    for old in ('\tSet Switch("Switch217", clear);', '\tSet Switch("Switch205", clear);'):
        if old in text and f'Switch{ALL_PAYMENT_SWITCHES[-1]}' not in text.split(old)[0][-500:]:
            extra = "\n".join(
                f'\tSet Switch("Switch{sw}", clear);'
                for sw in ALL_PAYMENT_SWITCHES
                if f'Switch("{sw}"' not in text  # naive skip
            )
    pattern = r'(Set Switch\("Switch217", clear\);)'
    extra_lines = "\n".join(
        f'\tSet Switch("Switch{sw}", clear);' for sw in (198, 199, 200, 201, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233)
    )
    return text.replace(
        '\tSet Switch("Switch217", clear);',
        '\tSet Switch("Switch217", clear);\n' + extra_lines,
    )


def main() -> None:
    text = PATH.read_text(encoding="utf-8")

    m = re.search(
        r'(?ms)// Donor tier selection \(Queen=30\)\.\n\nTrigger\("Player 8"\)',
        text,
    )
    if m:
        start = m.start() + len("// Donor tier selection (Queen=30).\n\n")
    else:
        m = re.search(
            r'(?ms)Trigger\("Player 8"\)\{\nConditions:\n\tSwitch\("Switch177", Set\);\n\tDeaths\("Player 8", "Zerg Queen", Exactly, 30\);\n\tSwitch\("Switch178", Set\);',
            text,
        )
        if not m:
            raise SystemExit("donor selection start not found")
        start = m.start()

    m_end = re.search(
        r'(?ms)^Trigger\("Player 8"\)\{\nConditions:\n\tSwitch\("Switch177", Set\);\n\tDeaths\("Player 8", "Zerg Queen", Exactly, 40\);\n\tDeaths\("Player 8", "Terran Siege Tank \(Tank Mode\)", At least, \d+\);',
        text,
    )
    if not m_end:
        raise SystemExit("cleanup start not found")
    end = m_end.start()

    middle = (
        gen_donor_selection()
        + "\n"
        + gen_transfers()
        + "\n"
        + gen_queen_advance()
        + gen_receive_messages()
        + gen_donate_messages()
    )

    header_comment = (
        "//  Donors: 4001-5999 -> 120, 6000-7999 -> 300, 8000-10000 -> 640, "
        "10001-15000 -> 1000, 15001-20000 -> 1800, 20001+ -> 3000. Ore and gas are judged separately."
    )
    text = re.sub(
        r"//  Donors:.*",
        header_comment,
        text,
        count=1,
    )

    out = text[:start] + middle + text[end:]
    # add clears for tier 5/6 switches after tier 4 clears in each cleanup block
    extra_clears = "\n".join(
        f'\tSet Switch("Switch{sw}", clear);'
        for sw in (198, 199, 200, 201, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233)
    )
    if 'Set Switch("Switch198", clear);' not in out:
        out = out.replace(
            '\tSet Switch("Switch217", clear);',
            '\tSet Switch("Switch217", clear);\n' + extra_clears,
        )
    PATH.write_text(out, encoding="utf-8", newline="\n")
    print(f"rebuilt 6-tier payment section in {PATH.name}")


if __name__ == "__main__":
    main()
