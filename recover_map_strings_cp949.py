#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import re
import struct
import tempfile
from pathlib import Path


DEFAULT_REPAIR_TOOL = Path(r"C:\Users\justk\.codex\skills\repair-starcraft-map\scripts\repair_scx.py")

TEXT_REPLACEMENTS = {
    "\u2013": "-",
    "\u2014": "-",
    "\u2212": "-",
    "\u2248": "~",
    "\u2026": "...",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
}
STRING_ACTION_FIELDS = {
    7: (1, 2),
    8: (2,),
    9: (1,),
    12: (1,),
    17: (1,),
    18: (1,),
    19: (1,),
    20: (1,),
    21: (1,),
    33: (1,),
    34: (1,),
    35: (1,),
    36: (1,),
    37: (1,),
    41: (1,),
    47: (1,),
}
STRING_ACTION_NAMES = {
    7: "Transmission",
    8: "Play WAV",
    9: "Display Text Message",
    12: "Set Mission Objectives",
    17: "Leader Board Control",
    18: "Leader Board Control At Location",
    19: "Leader Board Resources",
    20: "Leader Board Kills",
    21: "Leader Board Points",
    33: "Leaderboard Goal Control",
    34: "Leaderboard Goal Control At Location",
    35: "Leaderboard Goal Resources",
    36: "Leaderboard Goal Kills",
    37: "Leaderboard Goal Points",
    41: "Set Next Scenario",
    47: "Comment",
}
TEXT_ACTION_FIELDS = {
    "Transmission": (("str", 3), ("wav", 6)),
    "Play WAV": (("wav", 0),),
    "Display Text Message": (("str", 1),),
    "Set Mission Objectives": (("str", 0),),
    "Leader Board Control": (("str", 0),),
    "Leader Board Control At Location": (("str", 0),),
    "Leader Board Resources": (("str", 0),),
    "Leader Board Kills": (("str", 0),),
    "Leader Board Points": (("str", 0),),
    "Leaderboard Goal Control": (("str", 0),),
    "Leaderboard Goal Control At Location": (("str", 0),),
    "Leaderboard Goal Resources": (("str", 0),),
    "Leaderboard Goal Kills": (("str", 0),),
    "Leaderboard Goal Points": (("str", 0),),
    "Set Next Scenario": (("str", 0),),
    "Comment": (("str", 0),),
}
FORCE_NAME_RE = re.compile(r"^\s*Force\s*([1-4])\s*:\s*(.*?)\s*$", re.IGNORECASE)


def load_repair_tool(path: Path):
    spec = importlib.util.spec_from_file_location("repair_scx_tool", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load repair tool: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def split_null_strings(blob: bytes) -> list[bytes]:
    return blob.split(b"\0")


def parse_str(data: bytes) -> list[bytes]:
    if len(data) < 2:
        raise ValueError("STR section is too small")
    count = struct.unpack_from("<H", data, 0)[0]
    table_end = 2 + count * 2
    if table_end > len(data):
        raise ValueError("STR offset table exceeds section")
    offsets = [struct.unpack_from("<H", data, 2 + i * 2)[0] for i in range(count)]
    return read_string_values(data, offsets)


def parse_strx(data: bytes) -> list[bytes]:
    if len(data) < 4:
        raise ValueError("STRx section is too small")
    count = struct.unpack_from("<I", data, 0)[0]
    table_end = 4 + count * 4
    if table_end > len(data):
        raise ValueError("STRx offset table exceeds section")
    offsets = [struct.unpack_from("<I", data, 4 + i * 4)[0] for i in range(count)]
    return read_string_values(data, offsets)


def read_string_values(data: bytes, offsets: list[int]) -> list[bytes]:
    values: list[bytes] = []
    for index, offset in enumerate(offsets, start=1):
        if offset == 0:
            values.append(b"")
            continue
        if offset >= len(data):
            raise ValueError(f"String {index} offset is out of range: {offset}")
        end = data.find(b"\0", offset)
        if end < 0:
            raise ValueError(f"String {index} is not null-terminated")
        values.append(data[offset:end])
    return values


def build_str(values: list[bytes]) -> bytes:
    table_end = 2 + len(values) * 2
    if table_end > 0xFFFF:
        raise ValueError("Too many strings for STR")
    blob = bytearray()
    offsets: list[int] = []
    for value in values:
        if value:
            offset = table_end + len(blob)
            if offset > 0xFFFF:
                raise ValueError("STR section exceeds 16-bit offsets; use STRx")
            offsets.append(offset)
            blob.extend(value)
            blob.append(0)
        else:
            offsets.append(0)
    out = bytearray(struct.pack("<H", len(values)))
    for offset in offsets:
        out.extend(struct.pack("<H", offset))
    out.extend(blob)
    return bytes(out)


def build_strx(values: list[bytes]) -> bytes:
    table_end = 4 + len(values) * 4
    blob = bytearray()
    offsets: list[int] = []
    for value in values:
        if value:
            offsets.append(table_end + len(blob))
            blob.extend(value)
            blob.append(0)
        else:
            offsets.append(0)
    out = bytearray(struct.pack("<I", len(values)))
    for offset in offsets:
        out.extend(struct.pack("<I", offset))
    out.extend(blob)
    return bytes(out)


def normalize_text(text: str) -> str:
    for source, target in TEXT_REPLACEMENTS.items():
        text = text.replace(source, target)
    return text


def encode_starcraft_text(text: str, line_label: str) -> bytes:
    text = normalize_text(text)
    try:
        return text.encode("cp949")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{line_label} cannot be encoded as CP949: {exc}") from exc


def convert_value(value: bytes, index: int) -> tuple[bytes, bool]:
    if not value:
        return value, False
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return value, False
    # Some editor-created, unreferenced STRx entries already contain the
    # literal UTF-8 replacement character (EF BF BD).  That data cannot be
    # reconstructed and U+FFFD is not representable in CP949.  Referenced
    # trigger strings are replaced from the TrigEdit source before this path,
    # so preserve only these otherwise-unrecoverable raw entries instead of
    # aborting the whole deployment.
    if "\ufffd" in text:
        print(f"Warning: preserving unrecoverable UTF-8 bytes in string {index}")
        return value, False
    text = normalize_text(text)
    try:
        converted = encode_starcraft_text(text, f"String {index}")
    except ValueError:
        print(f"Warning: preserving non-CP949 bytes in unreferenced string {index}")
        return value, False
    return converted, converted != value


def split_args(argstr: str) -> list[str]:
    args: list[str] = []
    current: list[str] = []
    quoted = False
    escaped = False
    for char in argstr:
        if escaped:
            current.append("\\" + char)
            escaped = False
            continue
        if char == "\\" and quoted:
            escaped = True
            continue
        if char == '"':
            quoted = not quoted
            current.append(char)
            continue
        if char == "," and not quoted:
            args.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    args.append("".join(current).strip())
    return args


def unquote_arg(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def literal_to_bytes(value: str, line_number: int) -> bytes:
    out = bytearray()
    buffer: list[str] = []

    def flush() -> None:
        if buffer:
            out.extend(encode_starcraft_text("".join(buffer), f"line {line_number}"))
            buffer.clear()

    i = 0
    while i < len(value):
        if i + 3 < len(value) and value[i] == "<" and value[i + 3] == ">":
            code = value[i + 1 : i + 3]
            if re.fullmatch(r"[0-9A-Fa-f]{2}", code):
                flush()
                out.append(int(code, 16))
                i += 4
                continue

        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            flush()
            if nxt == "r":
                if i + 3 < len(value) and value[i + 2 : i + 4] == "\\n":
                    out.extend(b"\r\n")
                    i += 4
                else:
                    out.append(0x0D)
                    i += 2
                continue
            if nxt == "n":
                out.append(0x0A)
                i += 2
                continue
            if nxt == "t":
                out.append(0x09)
                i += 2
                continue
            if nxt == "\\":
                out.append(0x5C)
                i += 2
                continue
            if nxt == '"':
                out.append(0x22)
                i += 2
                continue
            out.extend(encode_starcraft_text("\\" + nxt, f"line {line_number}"))
            i += 2
            continue

        buffer.append(value[i])
        i += 1

    flush()
    return bytes(out)


def parse_trigger_text_string_calls(path: Path) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        match = re.match(r"\s*;?\s*([^()]+)\((.*)\);\s*$", line)
        if not match:
            continue
        name = match.group(1).strip()
        if name not in TEXT_ACTION_FIELDS:
            continue
        args = split_args(match.group(2))
        call: dict[str, object] = {"line": line_number, "name": name}
        for key, index in TEXT_ACTION_FIELDS[name]:
            if index >= len(args):
                raise ValueError(f"{path}:{line_number}: missing {key} argument for {name}")
            call[key] = literal_to_bytes(unquote_arg(args[index]), line_number)
        calls.append(call)
    return calls


def parse_force_names(path: Path | None) -> dict[int, bytes]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Force names file not found: {path}")

    names: dict[int, bytes] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = FORCE_NAME_RE.match(line)
        if not match:
            raise ValueError(f"{path}:{line_number}: expected 'Force1 : name'")
        force_number = int(match.group(1))
        value = match.group(2).strip()
        if not value:
            raise ValueError(f"{path}:{line_number}: force name is empty")
        names[force_number] = literal_to_bytes(value, line_number)
    return names


def unpack_action(data: bytes) -> tuple[int, ...]:
    return struct.unpack("<IIIIIIHBBBBH", data)


def collect_target_string_actions(trig: bytes) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    for trigger_index in range(len(trig) // 2400):
        trigger = trig[trigger_index * 2400 : (trigger_index + 1) * 2400]
        action_start = 16 * 20
        for action_index in range(64):
            action = unpack_action(trigger[action_start + action_index * 32 : action_start + action_index * 32 + 32])
            action_type = action[7]
            name = STRING_ACTION_NAMES.get(action_type)
            if not name:
                continue
            call: dict[str, object] = {
                "trigger": trigger_index,
                "action": action_index,
                "name": name,
            }
            for field_index in STRING_ACTION_FIELDS[action_type]:
                if field_index == 1:
                    call["str_id"] = action[field_index]
                elif field_index == 2:
                    call["wav_id"] = action[field_index]
            calls.append(call)
    return calls


def string_map_from_trigger_text(trigger_text: Path, sections: dict[bytes, bytes]) -> dict[int, bytes]:
    source_calls = parse_trigger_text_string_calls(trigger_text)
    target_trig = sections.get(b"TRIG")
    if not target_trig:
        raise ValueError("TRIG section not found in target map")
    if len(target_trig) % 2400:
        raise ValueError("TRIG size is not a multiple of 2400")
    target_calls = collect_target_string_actions(target_trig)
    if len(source_calls) > len(target_calls):
        raise ValueError(f"String action count differs: trigger_text={len(source_calls)} target_map={len(target_calls)}")
    if len(source_calls) < len(target_calls):
        extra = len(target_calls) - len(source_calls)
        first_extra = target_calls[len(source_calls)]
        print(
            f"Warning: map has {extra} extra string action(s) not present in trigger_text; "
            f"first extra is trigger {first_extra['trigger']} action {first_extra['action']} {first_extra['name']}"
        )

    string_map: dict[int, bytes] = {}
    for index, (source_call, target_call) in enumerate(zip(source_calls, target_calls, strict=False)):
        if source_call["name"] != target_call["name"]:
            raise ValueError(
                f"String action order differs at {index}: "
                f"text line {source_call['line']} {source_call['name']} vs "
                f"target trigger {target_call['trigger']} action {target_call['action']} {target_call['name']}"
            )
        for source_key, target_key in (("str", "str_id"), ("wav", "wav_id")):
            if source_key not in source_call and target_key not in target_call:
                continue
            desired = source_call.get(source_key, b"")
            string_id = int(target_call.get(target_key, 0))
            if not string_id:
                if desired:
                    raise ValueError(f"Target string id missing for text line {source_call['line']}")
                continue
            previous = string_map.get(string_id)
            if previous is not None and previous != desired:
                raise ValueError(f"Target string {string_id} maps to multiple source strings")
            string_map[string_id] = desired  # type: ignore[assignment]
    return string_map


def get_force_name_ids(data: bytes) -> list[int]:
    if len(data) < 16:
        raise ValueError("FORC section is too small")
    return list(struct.unpack_from("<HHHH", data, 8))


def set_force_name_ids(data: bytes, ids: list[int]) -> bytes:
    if len(data) < 16:
        raise ValueError("FORC section is too small")
    if len(ids) != 4:
        raise ValueError("Expected four force name string ids")
    out = bytearray(data)
    struct.pack_into("<HHHH", out, 8, *ids)
    return bytes(out)


def rebuild_chk_with_strings(
    repair,
    chk: bytes,
    trigger_text: Path | None,
    force_names_path: Path | None,
) -> tuple[bytes, int, int, bytes, int]:
    sections = repair.parse_chk(chk)
    section_data = {name: data for name, data, _off in sections}
    string_map = string_map_from_trigger_text(trigger_text, section_data) if trigger_text else {}
    force_names = parse_force_names(force_names_path)
    force_name_ids = get_force_name_ids(section_data[b"FORC"]) if force_names else []
    string_section = b"STRx" if any(name == b"STRx" for name, _data, _off in sections) else b"STR "
    changed = 0
    total = 0
    force_changed = 0
    out = bytearray()
    for name, data, _offset in sections:
        if name == string_section:
            values = parse_strx(data) if name == b"STRx" else parse_str(data)
            converted_values: list[bytes] = []
            for index, value in enumerate(values, start=1):
                if index in string_map:
                    converted = string_map[index]
                    did_change = converted != value
                else:
                    converted, did_change = convert_value(value, index)
                converted_values.append(converted)
                total += 1
                if did_change:
                    changed += 1
            for force_number, force_name in force_names.items():
                current_id = force_name_ids[force_number - 1]
                if current_id > 0 and current_id <= len(converted_values):
                    if converted_values[current_id - 1] != force_name:
                        converted_values[current_id - 1] = force_name
                        force_changed += 1
                else:
                    converted_values.append(force_name)
                    force_name_ids[force_number - 1] = len(converted_values)
                    total += 1
                    changed += 1
                    force_changed += 1
            data = build_strx(converted_values) if name == b"STRx" else build_str(converted_values)
        elif name == b"FORC" and force_names:
            data = set_force_name_ids(data, force_name_ids)
        out.extend(name)
        out.extend(struct.pack("<I", len(data)))
        out.extend(data)
    return bytes(out), changed, total, string_section, force_changed


def recover_map_strings(
    source: Path,
    output: Path,
    repair_tool: Path,
    stormlib: str | None,
    work_dir: Path,
    trigger_text: Path | None,
    force_names: Path | None,
) -> None:
    repair = load_repair_tool(repair_tool)
    storm = repair.Storm(repair.find_stormlib(stormlib))
    work_map, temp_ctx = repair.make_ascii_work_copy(source.resolve(), work_dir.resolve())
    try:
        chk, locale = storm.extract_chk(work_map)
    finally:
        if temp_ctx:
            temp_ctx.cleanup()

    rebuilt_chk, changed, total, section_name, force_changed = rebuild_chk_with_strings(
        repair,
        chk,
        trigger_text,
        force_names,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kargas_strings_cp949_") as tmpdir:
        chk_path = Path(tmpdir) / "scenario.chk"
        chk_path.write_bytes(rebuilt_chk)
        storm.pack_chk(chk_path, output.resolve())

    print(f"Read scenario.chk using locale 0x{locale:X}")
    source_label = f" from {trigger_text}" if trigger_text else ""
    print(f"Recovered {changed}/{total} {section_name.decode('ascii').strip()} string entries to CP949{source_label}")
    if force_names:
        print(f"Updated {force_changed} force name entries from {force_names}")
    print(f"Wrote {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover StarCraft map string table bytes from UTF-8 to CP949.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repair-tool", type=Path, default=DEFAULT_REPAIR_TOOL)
    parser.add_argument("--stormlib")
    parser.add_argument("--work-dir", type=Path, default=Path(r"E:\SCX_WORK"))
    parser.add_argument("--trigger-text", type=Path, help="TrigEdit text source used to restore imported strings")
    parser.add_argument("--force-names", type=Path, help="ForceNames.md file used to update FORC display names")
    args = parser.parse_args()

    recover_map_strings(
        args.source,
        args.out,
        args.repair_tool,
        args.stormlib,
        args.work_dir,
        args.trigger_text,
        args.force_names,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
