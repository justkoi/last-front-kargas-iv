#!/usr/bin/env python3
"""Refactor wartime rationing: 2 donor tiers (120 at 4001-5999, 300 at 6000+)."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "Triggers" / "13f_union_relief_fund.txt"

PLAYER_SWITCHES = {1: (182, 202), 2: (186, 206), 3: (190, 210), 4: (194, 214)}
TIER1_SWITCHES = {str(PLAYER_SWITCHES[p][0]) for p in range(1, 5)} | {str(PLAYER_SWITCHES[p][1]) for p in range(1, 5)}
TIER2_SWITCHES = {str(PLAYER_SWITCHES[p][0] + 1) for p in range(1, 5)} | {str(PLAYER_SWITCHES[p][1] + 1) for p in range(1, 5)}
DROP_SWITCHES = set()
for p in range(1, 5):
    ob, gb = PLAYER_SWITCHES[p]
    DROP_SWITCHES.update(map(str, (ob + 2, ob + 3, gb + 2, gb + 3)))

REMOVED_AMOUNTS = {
    "1280", "1640", "1800", "1920", "2800", "3000", "3600", "4200", "4800", "5000", "9000",
}

TRIGGER_SPLIT = re.compile(r"(?=^Trigger\()", re.MULTILINE)


def split_triggers(text: str) -> list[str]:
    parts = TRIGGER_SPLIT.split(text)
    return [parts[0]] + [p for p in parts[1:] if p.strip()]


def uses_dropped_switch(block: str) -> bool:
    for sw in DROP_SWITCHES:
        if re.search(rf'Switch\("Switch{sw}", Set\)', block):
            return True
        if re.search(rf'Set Switch\("Switch{sw}", set\)', block):
            return True
    return False


def has_removed_amount(block: str) -> bool:
    if "At least, 6000" in block or "At most, 5999" in block or "At least, 4001" in block:
        return False
    for amt in REMOVED_AMOUNTS:
        if f"Exactly, {amt}" in block:
            return True
        if f"+{amt}" in block or f"-{amt}" in block:
            return True
        if f"Add, {amt}" in block or f"Subtract, {amt}" in block:
            return True
    return False


def is_donate_message(block: str) -> bool:
    return "전환되었습니다" in block


def patch_donor_selection(block: str) -> str | None:
    if 'Deaths("Player 8", "Zerg Queen", Exactly, 30)' not in block or "Accumulate" not in block:
        return block
    if "At least, 15001" in block or "At least, 20001" in block:
        return None
    out = block
    out = out.replace("At least, 8001", "At least, 4001")
    out = out.replace("At most, 10000", "At most, 5999")
    out = out.replace("At least, 10001", "At least, 6000")
    out = re.sub(r'\n\tAccumulate\("[^"]+", At most, 15000, (ore|gas)\);', "", out)
    return out


def patch_transfer(block: str) -> str | None:
    if 'Deaths("Player 8", "Zerg Queen", Exactly, 30)' not in block or "Subtract" not in block:
        return block
    out = block
    for sw in TIER1_SWITCHES:
        if f'Switch("Switch{sw}", Set)' in out:
            out = re.sub(r", (640|1000|1800|3000),", ", 120,", out)
            out = out.replace("Add, 640", "Add, 120").replace("Add, 1000", "Add, 120")
            out = out.replace("Add, 1800", "Add, 120").replace("Add, 3000", "Add, 120")
    for sw in TIER2_SWITCHES:
        if f'Switch("Switch{sw}", Set)' in out:
            out = re.sub(r", (640|1000|1800|3000),", ", 300,", out)
            out = out.replace("Add, 640", "Add, 300").replace("Add, 1000", "Add, 300")
            out = out.replace("Add, 1800", "Add, 300").replace("Add, 3000", "Add, 300")
    return out


def patch_receive_message(block: str) -> str | None:
    out = block
    out = out.replace("Exactly, 640", "Exactly, 120")
    out = out.replace("Exactly, 1000", "Exactly, 300")
    out = out.replace("+640", "+120").replace("+1000", "+300")
    return out


def patch_cleanup(block: str) -> str:
    out = block
    out = out.replace("At most, 83", "At most, 23")
    out = out.replace("At least, 84", "At least, 24")
    return out


def patch_header(block: str) -> str:
    if "Donors: 4001-5999" not in block and "A receiver must have" in block:
        block = block.replace(
            "//  A receiver must have the relevant resource at 4000 or less. P1 wins ties.",
            "//  A receiver must have the relevant resource at 4000 or less. P1 wins ties.\n"
            "//  Donors: 4001-5999 -> 120, 6000+ -> 300. Ore and gas are judged separately.",
        )
    if "120초마다 자원 4000 이하" in block and "120/300" not in block:
        block = block.replace(
            "미네랄과 가스는 따로 판정됩니다.",
            "4001 이상은 120/300 규모로 전환됩니다. 미네랄과 가스는 따로 판정됩니다.",
        )
    return block


def generate_donate_messages() -> str:
    chunks = ["\n// Donor confirmation messages (2 ore tiers x 2 gas tiers).\n"]
    for player in range(1, 5):
        ore1, gas1 = PLAYER_SWITCHES[player]
        ore2, gas2 = ore1 + 1, gas1 + 1
        tier_defs = [
            (ore1, gas1, "미네랄 -120", "가스 -120", "미네랄 -120  <07>가스 -120"),
            (ore2, gas1, "미네랄 -300", "가스 -120", "미네랄 -300  <07>가스 -120"),
            (ore1, gas2, "미네랄 -120", "가스 -300", "미네랄 -120  <07>가스 -300"),
            (ore2, gas2, "미네랄 -300", "가스 -300", "미네랄 -300  <07>가스 -300"),
        ]
        for active_ore, active_gas, ore_txt, gas_txt, both_txt in tier_defs:
            for ore_on, gas_on, txt in (
                (True, True, both_txt),
                (True, False, ore_txt),
                (False, True, gas_txt),
            ):
                lines = [
                    f'Trigger("Player {player}"){{',
                    "Conditions:",
                    '\tSwitch("Switch177", Set);',
                    '\tDeaths("Player 8", "Zerg Queen", Exactly, 40);',
                    '\tDeaths("Player 8", "Terran Siege Tank (Tank Mode)", Exactly, 12);',
                    f'\tSwitch("Switch{active_ore}", {"Set" if ore_on else "Not Set"});',
                    f'\tSwitch("Switch{active_gas}", {"Set" if gas_on else "Not Set"});',
                ]
                for sw in (ore1, ore2, gas1, gas2):
                    if sw not in (active_ore, active_gas):
                        lines.append(f'\tSwitch("Switch{sw}", Not Set);')
                if txt == both_txt:
                    msg = f"<03>[전시 배급소] <04>전시 배급 물자로 전환되었습니다. <1F>{both_txt}"
                elif txt.startswith("미네랄"):
                    msg = f"<03>[전시 배급소] <04>전시 배급 물자로 전환되었습니다. <1F>{txt}"
                else:
                    msg = f"<03>[전시 배급소] <04>전시 배급 물자로 전환되었습니다. <07>{txt}"
                lines += [
                    "Actions:",
                    f'\tDisplay Text Message(Always Display, "{msg}");',
                    "\tPreserve Trigger();",
                    "}",
                    "",
                ]
                chunks.append("\n".join(lines))
    return "\n".join(chunks)


def process_trigger(block: str) -> str | None:
    if not block.strip():
        return block
    if uses_dropped_switch(block) or has_removed_amount(block):
        return None
    if is_donate_message(block):
        return None

    block = patch_donor_selection(block)
    if block is None:
        return None
    block = patch_transfer(block)
    if block is None:
        return None
    if "물자가 도착했습니다" in block:
        block = patch_receive_message(block)
    block = patch_cleanup(block)
    block = patch_header(block)
    return block


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    parts = split_triggers(text)
    kept = []
    dropped = 0
    for part in parts:
        res = process_trigger(part)
        if res is None:
            dropped += 1
        else:
            kept.append(res)

    out = "".join(kept).rstrip() + "\n\n" + generate_donate_messages()
    PATH.write_text(out, encoding="utf-8", newline="\n")
    print(f"refactored: dropped {dropped}, wrote {len(kept)-1} blocks + donate messages")


if __name__ == "__main__":
    main()
