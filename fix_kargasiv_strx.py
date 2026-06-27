#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import struct
import tempfile
from pathlib import Path


REPAIR_SCRIPT = Path(r"C:\Users\justk\.codex\skills\repair-starcraft-map\scripts\repair_scx.py")
SCENARIO_NAME = b"staredit\\scenario.chk"


def load_repair_module():
    spec = importlib.util.spec_from_file_location("repair_scx", REPAIR_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {REPAIR_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_even_if_locked(src: Path, dst: Path) -> None:
    import ctypes
    import msvcrt

    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    FILE_SHARE_DELETE = 0x00000004
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    handle = ctypes.windll.kernel32.CreateFileW(
        str(src),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        raise OSError(ctypes.get_last_error(), f"CreateFileW failed: {src}")
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY)
        with os.fdopen(fd, "rb", closefd=True) as in_file, dst.open("wb") as out_file:
            shutil.copyfileobj(in_file, out_file, length=1024 * 1024)
    except Exception:
        ctypes.windll.kernel32.CloseHandle(handle)
        raise


def iter_sections(chk: bytes):
    off = 0
    while off < len(chk):
        if off + 8 > len(chk):
            raise ValueError(f"Trailing CHK bytes at 0x{off:X}")
        name = chk[off : off + 4]
        size = struct.unpack_from("<I", chk, off + 4)[0]
        start = off + 8
        end = start + size
        if end > len(chk):
            raise ValueError(f"Section {name!r} overshoots EOF")
        yield name, chk[start:end]
        off = end


def parse_strx(data: bytes) -> list[bytes]:
    count = struct.unpack_from("<I", data, 0)[0]
    table_end = 4 + count * 4
    if table_end > len(data):
        raise ValueError("STRx offset table exceeds section size")
    strings: list[bytes] = []
    for i in range(count):
        off = struct.unpack_from("<I", data, 4 + i * 4)[0]
        end = data.find(b"\0", off)
        if off < table_end or end < 0:
            raise ValueError(f"Bad STRx offset for string {i + 1}: {off}")
        strings.append(data[off:end])
    return strings


def build_strx(strings: list[bytes]) -> bytes:
    table_end = 4 + len(strings) * 4
    blob = bytearray()
    offsets: list[int] = []
    for s in strings:
        offsets.append(table_end + len(blob))
        blob.extend(s)
        blob.append(0)

    out = bytearray(struct.pack("<I", len(strings)))
    for off in offsets:
        out.extend(struct.pack("<I", off))
    out.extend(blob)
    return bytes(out)


def build_legacy_str(strings: list[bytes]) -> bytes:
    if len(strings) > 0xFFFF:
        raise ValueError("Legacy STR cannot hold more than 65535 strings")
    table_end = 2 + len(strings) * 2
    blob = bytearray()
    offsets: list[int] = []
    for s in strings:
        offsets.append(table_end + len(blob))
        blob.extend(s)
        blob.append(0)
    total_size = table_end + len(blob)
    if total_size > 0xFFFF:
        raise ValueError(f"Legacy STR section would exceed 64 KiB: {total_size}")

    out = bytearray(struct.pack("<H", len(strings)))
    for off in offsets:
        out.extend(struct.pack("<H", off))
    out.extend(blob)
    return bytes(out)


def fill_empty_strings(strings: list[bytes]) -> tuple[list[bytes], int]:
    fixed: list[bytes] = []
    changed = 0
    for idx, value in enumerate(strings, start=1):
        if value:
            fixed.append(value)
            continue

        # Text color control bytes render no glyph by themselves in StarCraft text.
        # Vary them so editors are less likely to deduplicate empty placeholders.
        fixed.append(bytes([0x03 + (idx % 0x10)]))
        changed += 1
    return fixed, changed


def patch_chk(chk: bytes, legacy_str: bool) -> tuple[bytes, int]:
    out = bytearray()
    total_changed = 0
    for name, data in iter_sections(chk):
        if name == b"STRx":
            strings = parse_strx(data)
            strings, changed = fill_empty_strings(strings)
            if legacy_str:
                name = b"STR "
                data = build_legacy_str(strings)
            else:
                data = build_strx(strings)
            total_changed += changed
        out.extend(name)
        out.extend(struct.pack("<I", len(data)))
        out.extend(data)
    return bytes(out), total_changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=r"E:\KargasIV_Work\KargasIV.scx")
    parser.add_argument("--output", default=r"E:\KargasIV_Work\KargasIV_strx_fixed.scx")
    parser.add_argument("--work-dir", default=r"E:\SCX_test")
    parser.add_argument("--legacy-str", action="store_true")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    work_dir = Path(args.work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    repair = load_repair_module()
    storm = repair.Storm(repair.find_stormlib(None))

    locked_copy = work_dir / "KargasIV_strx_input.scx"
    copy_even_if_locked(source, locked_copy)

    chk, locale = storm.extract_chk(locked_copy)
    patched_chk, changed = patch_chk(chk, legacy_str=args.legacy_str)

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kargasiv_strx_") as tmp:
        tmp_dir = Path(tmp)
        chk_path = tmp_dir / "scenario.chk"
        pack_path = tmp_dir / "out.scx"
        chk_path.write_bytes(patched_chk)
        storm.pack_chk(chk_path, pack_path)
        shutil.copy2(pack_path, output)

    check_chk, _ = storm.extract_chk(output)
    if check_chk != patched_chk:
        raise RuntimeError("Packed map verification failed")

    print(f"Read locale: 0x{locale:X}")
    print(f"Filled empty STRx strings: {changed}")
    print(f"Wrote: {output}")
    print(f"Output size: {output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
