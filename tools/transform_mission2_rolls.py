#!/usr/bin/env python3
"""Transform P6/P7 main assault roll files for 3-stage warnings + pre-seeded waves."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_nonrepeat_rerolls(colony: str, phase_dc: str, wave_s1: str, wave_s2: str,
                            spawn_s1: str, spawn_s2: str) -> str:
    """Reject a next-wave roll that matches this colony's last regular wave."""
    owner = "Player 6" if colony == "P6" else "Player 7"
    bits = (("Not Set", "Not Set"), ("Set", "Not Set"),
            ("Not Set", "Set"), ("Set", "Set"))
    blocks: list[str] = [
        f"// {colony} next-wave rejection sampling: keep re-rolling while the next regular wave matches the last one."
    ]
    for bit1, bit2 in bits:
        blocks.append(
            f'Trigger("{owner}"){{\n'
            f'Conditions:\n'
            f'\tDeaths("Player 8", "{phase_dc}", Exactly, 3); //공세 소비 직후 : 다음 일반 공세 후보를 확정하는 준비 상태\n'
            f'\tSwitch("{spawn_s1}", {bit1}); //직전 일반 공세 bit0 : 실제 스폰에 사용한 구성 기록\n'
            f'\tSwitch("{spawn_s2}", {bit2}); //직전 일반 공세 bit1 : 실제 스폰에 사용한 구성 기록\n'
            f'\tSwitch("{wave_s1}", {bit1}); //다음 일반 공세 bit0 : 직전 구성과 같은 후보\n'
            f'\tSwitch("{wave_s2}", {bit2}); //다음 일반 공세 bit1 : 직전 구성과 같은 후보\n'
            f'Actions:\n'
            f'\tSet Switch("{wave_s1}", randomize); //연속 중복 거부 : 다음 후보 bit0 재추첨\n'
            f'\tSet Switch("{wave_s2}", randomize); //연속 중복 거부 : 다음 후보 bit1 재추첨\n'
            f'\tPreserve Trigger();\n'
            f'}}'
        )
    return "\n\n".join(blocks) + "\n"


def append_nonrepeat_rerolls(content: str, colony: str, phase_dc: str,
                             wave_s1: str, wave_s2: str,
                             spawn_s1: str, spawn_s2: str) -> str:
    marker = f"// {colony} next-wave rejection sampling:"
    if marker in content:
        return content
    return content.rstrip() + "\n\n" + build_nonrepeat_rerolls(
        colony, phase_dc, wave_s1, wave_s2, spawn_s1, spawn_s2
    )


def jitter_thresholds(label: str, conds: str) -> tuple[int, str, str]:
    if "cooldown 21m -" in label:
        return 13080, "Not Set", "Not Set"
    if "cooldown 22m -" in label:
        return 13800, "Not Set", "Set"
    if 'Switch("Switch27", Set)' in conds and 'Switch("Switch28", Set)' in conds:
        return 13440, "Set", "Set"
    return 13440, "Set", "Not Set"


def build_coarse_triggers(content: str, colony: str, lurker_dc: str, cd_unit: str,
                          switch_colony_lock: str, switch_coarse_roll: str,
                          switch_j27: str, switch_j28: str) -> str:
    pattern = (
        rf"// {colony} detailed analysis anchor - ([^\n]+)\n"
        rf'Trigger\("{colony}"\)\{{\nConditions:\n((?:\t[^\n]+\n)+?)Actions:\n((?:\t[^\n]+\n)+?)\}}'
    )
    blocks = list(re.finditer(pattern, content))
    seen: set[str] = set()
    parts: list[str] = []
    for m in blocks:
        label = m.group(1).strip()
        if label in seen:
            continue
        seen.add(label)
        conds = m.group(2)
        thresh, _, _ = jitter_thresholds(label, conds)
        new_conds = re.sub(
            r'\tDeaths\("Player 8", "[^"]+", At least, \d+\);\n'
            r'\tDeaths\("Player 8", "[^"]+", At most, \d+\);\n',
            f'\tDeaths("Player 8", "{cd_unit}", At least, {thresh});\n',
            conds,
            count=1,
        )
        new_conds = re.sub(r'\tSwitch\("Switch129", Set\);\n', "", new_conds)
        new_conds = re.sub(r'\tSwitch\("Switch131", Set\);\n', "", new_conds)
        new_conds = re.sub(r'\tSwitch\("Switch63", Not Set\);\n', "", new_conds)
        new_conds = re.sub(r'\tSwitch\("Switch67", Not Set\);\n', "", new_conds)
        if f'Switch("{switch_coarse_roll}"' not in new_conds:
            new_conds = new_conds.replace(
                f'Switch("{switch_colony_lock}", Not Set);\n',
                f'Switch("{switch_colony_lock}", Not Set);\n\tSwitch("{switch_coarse_roll}", Not Set);\n',
            )
        parts.append(
            f"// {colony} coarse warning roll - {label}\n"
            f'Trigger("{colony}"){{\nConditions:\n{new_conds}'
            f"Actions:\n\tSet Switch(\"{switch_coarse_roll}\", set);\n\tPreserve Trigger();\n}}\n"
        )
    return "\n".join(parts)


def transform_rolls(content: str, colony: str, cd_unit: str, phase_dc: str, sub_dc: str,
                    wave_s1: str, wave_s2: str, spawn_s1: str, spawn_s2: str,
                    switch_colony_lock: str, switch_j27: str, switch_j28: str,
                    switch_det_active: str, switch_det_shown: str,
                    switch_coarse_roll: str, switch_coarse_shown: str) -> str:
    prefix = colony.split()[-1] if " " in colony else colony
    tag = f"P{prefix[-1]}" if prefix.startswith("P") else colony

    content = content.replace(
        f"//-----------------------------------------------------------------//\n"
        f"//  {colony} main-assault roll with safe wave-only pre-roll\n"
        f"//  Pre-roll stores only the upcoming wave in dedicated switches.\n"
        f"//  Route, Hunt target, and assault state are decided at the original warning timing.\n"
        f"//-----------------------------------------------------------------//\n\n"
        f"// {colony} wave-only pre-rolls fire 80 seconds before the original warning timing.",
        f"//-----------------------------------------------------------------//\n"
        f"//  {colony} main-assault roll with pre-seeded wave type and 3-stage warnings\n"
        f"//  Wave type ({wave_s1}/{wave_s2}) is seeded at game start and re-rolled after each consume.\n"
        f"//  Coarse air/ground warning at spawn-180s, detailed analysis at spawn-90s,\n"
        f"//  route/Hunt target and assault state at consume (spawn-10s).\n"
        f"//-----------------------------------------------------------------//\n\n"
        f"// {colony} coarse warning roll - spawn-180s (cooldown T-2040). At least threshold: no upper cap.\n"
        f"COARSE_BLOCK_PLACEHOLDER",
        1,
    )

    content = re.sub(
        rf"// {colony} pre-roll wave - ",
        f"// {colony} detailed analysis anchor - ",
        content,
    )
    content = content.replace(
        f"// {colony} pre-roll wave copy. This runs only when the selected roll threshold is reached.",
        f"// {colony} wave copy at detailed-analysis timing (spawn-90s). "
        f"Idempotent; copies pre-seeded {wave_s1}/{wave_s2} to {spawn_s1}/{spawn_s2}.",
    )
    content = content.replace(
        f"// {colony} confirmed pre-rolls reach the original warning state.\n"
        f"// {colony} consume pre-roll -",
        f"// {colony} consume at contact-warning timing (spawn-10s).\n"
        f"// {colony} consume -",
    )
    content = content.replace(f"// {colony} consume pre-roll -", f"// {colony} consume -")
    content = content.replace(
        f"// {colony} fallback rolls: if cooldown acceleration skips the pre-roll window, decide at the selected timing.",
        f"// {colony} fallback rolls: if acceleration skips the detailed-analysis window, "
        f"consume at spawn-10s with pre-seeded wave.",
    )
    content = content.replace(f"// {colony} roll random wave -", f"// {colony} fallback consume -")

    coarse_block = build_coarse_triggers(
        content, colony, phase_dc, cd_unit,
        switch_colony_lock, switch_coarse_roll, switch_j27, switch_j28,
    )
    content = content.replace("COARSE_BLOCK_PLACEHOLDER", coarse_block + "\n", 1)

    content = re.sub(
        rf'\tSet Switch\("{wave_s1}", randomize\);\n\tSet Switch\("{wave_s2}", randomize\);\n',
        "",
        content,
    )

    content = re.sub(
        rf'(// {colony} detailed analysis anchor[^\n]*\nTrigger\("{colony}"\)\{{\nConditions:\n(?:[^\n]+\n)+?\tSwitch\("{switch_colony_lock}", Not Set\);\n)'
        rf'\tSwitch\("{switch_det_active}", Not Set\);',
        rf'\1\tSwitch("{switch_coarse_shown}", Set);\n\tSwitch("{switch_det_active}", Not Set);',
        content,
    )

    def copy_replacer(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(rf'\tSwitch\("{switch_det_active}", Set\);\n', "", block)
        block = block.replace("At least, 15120", "At least, 14160")
        block = block.replace("At least, 15480", "At least, 14520")
        block = block.replace("At least, 15840", "At least, 14880")
        return block

    content = re.sub(
        rf"// {colony} copy Wave[^\n]*\nTrigger\(\"{colony}\"\)\{{.*?\n\}}",
        copy_replacer,
        content,
        flags=re.DOTALL,
    )

    content = re.sub(
        rf'\tSet Switch\("{wave_s1}", clear\);\n\tSet Switch\("{wave_s2}", clear\);\n'
        rf'\tSet Switch\("{switch_det_active}", clear\);',
        rf'\tSet Switch("{wave_s1}", randomize);\n\tSet Switch("{wave_s2}", randomize);\n'
        rf'\tSet Switch("{switch_coarse_roll}", clear);\n\tSet Switch("{switch_coarse_shown}", clear);\n'
        rf'\tSet Switch("{switch_det_active}", clear);',
        content,
    )

    def fallback_replacer(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(
            rf'\tSet Switch\("{spawn_s1}", randomize\);\n\tSet Switch\("{spawn_s2}", randomize\);\n',
            "",
            block,
        )
        if switch_coarse_roll not in block:
            block = block.replace(
                f'\tSet Deaths("Player 8", "{cd_unit}", Subtract,',
                f'\tSet Switch("{wave_s1}", randomize);\n\tSet Switch("{wave_s2}", randomize);\n'
                f'\tSet Switch("{switch_coarse_roll}", clear);\n\tSet Switch("{switch_coarse_shown}", clear);\n'
                f'\tSet Deaths("Player 8", "{cd_unit}", Subtract,',
            )
        return block

    content = re.sub(
        rf"// {colony} fallback consume[^\n]*\nTrigger\(\"{colony}\"\)\{{.*?\n\}}",
        fallback_replacer,
        content,
        flags=re.DOTALL,
    )

    return content


def main() -> None:
    p6_path = ROOT / "Triggers/18_mission2_main_assaults_01_p6_rolls.txt"
    p7_path = ROOT / "Triggers/18_mission2_main_assaults_02_p7_rolls.txt"

    p6 = transform_rolls(
        p6_path.read_text(encoding="utf-8"),
        colony="P6",
        cd_unit="Zerg Zergling",
        phase_dc="Zerg Lurker",
        sub_dc="Zerg Ultralisk",
        wave_s1="Switch61",
        wave_s2="Switch62",
        spawn_s1="Switch9",
        spawn_s2="Switch10",
        switch_colony_lock="Switch31",
        switch_j27="Switch27",
        switch_j28="Switch28",
        switch_det_active="Switch63",
        switch_det_shown="Switch64",
        switch_coarse_roll="Switch128",
        switch_coarse_shown="Switch129",
    )
    p6 = append_nonrepeat_rerolls(
        p6, "P6", "Zerg Lurker", "Switch61", "Switch62", "Switch9", "Switch10"
    )
    p6_path.write_text(p6, encoding="utf-8")

    p7 = transform_rolls(
        p7_path.read_text(encoding="utf-8"),
        colony="P7",
        cd_unit="Zerg Hydralisk",
        phase_dc="Zerg Mutalisk",
        sub_dc="Zerg Devourer",
        wave_s1="Switch65",
        wave_s2="Switch66",
        spawn_s1="Switch11",
        spawn_s2="Switch12",
        switch_colony_lock="Switch32",
        switch_j27="Switch29",
        switch_j28="Switch30",
        switch_det_active="Switch67",
        switch_det_shown="Switch68",
        switch_coarse_roll="Switch130",
        switch_coarse_shown="Switch131",
    )
    p7 = append_nonrepeat_rerolls(
        p7, "P7", "Zerg Mutalisk", "Switch65", "Switch66", "Switch11", "Switch12"
    )
    p7_path.write_text(p7, encoding="utf-8")

    for name, text in [("P6", p6), ("P7", p7)]:
        assert "coarse warning roll" in text
        assert 'Switch9", randomize' not in text
        assert 'Switch11", randomize' not in text
        assert text.count(f"// {name} next-wave rejection sampling:") == 1
        assert text.count("//연속 중복 거부 : 다음 후보 bit0 재추첨") == 4
        assert text.count("//연속 중복 거부 : 다음 후보 bit1 재추첨") == 4
        print(f"{name}: ok ({len(text)} bytes)")


if __name__ == "__main__":
    main()
