#!/usr/bin/env python3
"""Refactor wartime rationing from 4 tiers (640/1000/1800/3000) to 2 tiers (120/300)."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "Triggers" / "13f_union_relief_fund.txt"

# Per-player payment switch bases (ore, gas). Tier1 = base, Tier2 = base+1.
PLAYER_SWITCHES = {
    1: (182, 202),
    2: (186, 206),
    3: (190, 210),
    4: (194, 214),
}

# Switches to drop entirely (old tiers 3 and 4).
DROP_SWITCHES = set()
for p in range(1, 5):
    ore_base, gas_base = PLAYER_SWITCHES[p]
    DROP_SWITCHES.update({str(ore_base + 2), str(ore_base + 3), str(gas_base + 2), str(gas_base + 3)})

AMOUNT_MAP = {
    "640": "120",
    "1000": "300",
    "1280": "120",  # combined display legacy; will be removed with tier3/4
    "1640": "300",
    "1800": "120",
    "2800": "300",
    "3000": "120",
    "3600": "300",
    "4200": "120",
    "5000": "300",
    "6000": "120",
    "9000": "300",
}

TRIGGER_SPLIT = re.compile(r"(?=Trigger\()")


def split_triggers(text: str) -> list[str]:
    parts = TRIGGER_SPLIT.split(text)
    return [parts[0]] + [p for p in parts[1:] if p.strip()]


def trigger_uses_dropped_switch(block: str) -> bool:
    for sw in DROP_SWITCHES:
        if re.search(rf'Switch\("Switch{sw}", Set\)', block):
            return True
    return False


def trigger_sets_dropped_switch(block: str) -> bool:
    for sw in DROP_SWITCHES:
        if re.search(rf'Set Switch\("Switch{sw}", set\)', block):
            return True
    return False


def trigger_references_dropped_switch_only(block: str) -> bool:
    refs = set(re.findall(r'Switch\("Switch(\d+)"', block))
    payment_refs = refs & (DROP_SWITCHES | {str(PLAYER_SWITCHES[p][0] + t) for p in range(1, 5) for t in (0, 1, 2, 3)} | {str(PLAYER_SWITCHES[p][1] + t) for p in range(1, 5) for t in (0, 1, 2, 3)})
    if not payment_refs:
        return False
    active = payment_refs - DROP_SWITCHES
    return not active and bool(payment_refs & DROP_SWITCHES)


def should_drop_message_trigger(block: str) -> bool:
    if "Display Text Message" not in block and "Play WAV" not in block:
        return False
    for old in ("1800", "3000", "1280", "1640", "2800", "3600", "4200", "5000", "6000", "9000"):
        if f"Exactly, {old}" in block or f"+{old}" in block or f"-{old}" in block:
            return True
    for sw in DROP_SWITCHES:
        if f'Switch("{sw}"' in block or f'Switch("Switch{sw}"' in block:
            # donate message combos referencing tier3/4
            if f'Switch("Switch{sw}"' in block:
                return True
    # drop donate/receive messages for removed combined tiers
    for sw in DROP_SWITCHES:
        if re.search(rf'Switch\("Switch{sw}", Set\)', block):
            return True
    return False


def patch_donor_selection(block: str) -> str | None:
    if 'Deaths("Player 8", "Zerg Queen", Exactly, 30)' not in block:
        return block
    if 'Set Switch("Switch' not in block or "Accumulate" not in block:
        return block
    if trigger_sets_dropped_switch(block):
        return None

    out = block
    out = out.replace('At least, 8001', 'At least, 4001')
    out = out.replace('At most, 10000', 'At most, 5999')
    out = out.replace('At least, 10001', 'At least, 6000')
    out = re.sub(r'\n\tAccumulate\("[^"]+", At most, 15000, (ore|gas)\);', '', out)
    out = re.sub(r'\n\tAccumulate\("[^"]+", At least, 15001, (ore|gas)\);.*?$', '', out, flags=re.MULTILINE)
    out = re.sub(r'\n\tAccumulate\("[^"]+", At least, 20001, (ore|gas)\);', '', out)
    return out


def patch_transfer(block: str) -> str | None:
    if 'Deaths("Player 8", "Zerg Queen", Exactly, 30)' not in block:
        return block
    if "Set Resources" not in block or "Subtract" not in block:
        return block
    if trigger_sets_dropped_switch(block):
        return None

    out = block
    # tier1 transfers used 640, tier2 used 1000
    if 'Switch("Switch182"' in out or 'Switch("Switch186"' in out or 'Switch("Switch190"' in out or 'Switch("Switch194"' in out or 'Switch("Switch202"' in out or 'Switch("Switch206"' in out or 'Switch("Switch210"' in out or 'Switch("Switch214"' in out:
        if ", 640," in out or ", Add, 640" in out or "Add, 640" in out:
            out = out.replace(", 640,", ", 120,").replace(", Add, 640", ", Add, 120").replace("Add, 640", "Add, 120")
    if 'Switch("Switch183"' in out or 'Switch("Switch187"' in out or 'Switch("Switch191"' in out or 'Switch("Switch195"' in out or 'Switch("Switch203"' in out or 'Switch("Switch207"' in out or 'Switch("Switch211"' in out or 'Switch("Switch215"' in out:
        if ", 1000," in out or ", Add, 1000" in out:
            out = out.replace(", 1000,", ", 300,").replace(", Add, 1000", ", Add, 300").replace("Add, 1000", "Add, 300")
    return out


def patch_message(block: str) -> str | None:
    if should_drop_message_trigger(block):
        return None

    out = block
    if "Display Text Message" in out or "Exactly, 640" in out or "Exactly, 1000" in out:
        out = out.replace("Exactly, 640", "Exactly, 120")
        out = out.replace("Exactly, 1000", "Exactly, 300")
        out = out.replace("+640", "+120")
        out = out.replace("+1000", "+300")
        out = out.replace("-640", "-120")
        out = out.replace("-1000", "-300")
        out = out.replace("미네랄 -640  <07>가스 -640", "미네랄 -120  <07>가스 -120")
        out = out.replace("미네랄 -640  <07>가스 -300", "미네랄 -120  <07>가스 -300")
        out = out.replace("미네랄 -300  <07>가스 -640", "미네랄 -300  <07>가스 -120")

    # Simplify donate-message switch guards: remove tier3/4 lines
    for sw in sorted(DROP_SWITCHES, key=int):
        out = re.sub(rf'\n\tSwitch\("Switch{sw}", [^)]+\);', '', out)

    # Drop impossible combo messages still mentioning old amounts in text
    for bad in ("1800", "3000", "1280", "1640", "2800", "3600", "4200", "5000", "6000", "9000"):
        if bad in out and ("Display Text Message" in out or "Exactly, " in out):
            return None

    return out


def patch_cleanup(block: str) -> str:
    out = block
    if 'Deaths("Player 8", "Terran Siege Tank (Tank Mode)", At least, 84)' in out:
        out = out.replace("At least, 84", "At least, 24")
    if 'Deaths("Player 8", "Terran Siege Tank (Tank Mode)", At most, 83)' in out:
        out = out.replace("At most, 83", "At most, 23")
    return out


def patch_header_comment(block: str) -> str:
    if "A receiver must have the relevant resource at 4000 or less" in block:
        block = block.replace(
            "//  A receiver must have the relevant resource at 4000 or less. P1 wins ties.",
            "//  A receiver must have the relevant resource at 4000 or less. P1 wins ties.\n//  Donors: 4001-5999 -> 120, 6000+ -> 300. Ore and gas are judged separately.",
        )
    if "120초마다 자원 4000 이하" in block:
        block = block.replace(
            "<03>[전시 배급소] <04>120초마다 자원 4000 이하 지휘관에게 배급 물자를 우선 배정합니다. 미네랄과 가스는 따로 판정됩니다.",
            "<03>[전시 배급소] <04>120초마다 자원 4000 이하 지휘관에게 배급 물자를 우선 배정합니다. 4001 이상은 120/300 규모로 전환됩니다. 미네랄과 가스는 따로 판정됩니다.",
        )
    return block


def process_trigger(block: str) -> str | None:
    if not block.strip():
        return block

    if trigger_sets_dropped_switch(block) or trigger_uses_dropped_switch(block):
        return None

    block = patch_donor_selection(block)
    if block is None:
        return None

    block = patch_transfer(block)
    if block is None:
        return None

    if "Display Text Message" in block or ("Exactly, 640" in block) or ("Exactly, 1000" in block):
        block = patch_message(block)
        if block is None:
            return None

    block = patch_cleanup(block)
    block = patch_header_comment(block)
    return block


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    parts = split_triggers(text)
    kept: list[str] = []
    dropped = 0
    for part in parts:
        result = process_trigger(part)
        if result is None:
            dropped += 1
            continue
        kept.append(result)

    out = "".join(kept)
    PATH.write_text(out, encoding="utf-8", newline="\n")
    print(f"refactored {PATH.name}: dropped {dropped} triggers, kept {len(kept)-1} trigger blocks")


if __name__ == "__main__":
    main()
