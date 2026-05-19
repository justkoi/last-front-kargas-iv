#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import shutil
import tempfile
from pathlib import Path


DEFAULT_REPAIR_TOOL = Path(r"C:\Users\justk\.codex\skills\repair-starcraft-map\scripts\repair_scx.py")


def load_repair_tool(path: Path):
    spec = importlib.util.spec_from_file_location("repair_scx_tool", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load repair tool: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def patch_protected_header(path: Path) -> None:
    with path.open("r+b") as f:
        f.seek(8)
        f.write(b"\xFF\xFF\xFF\xFF")
        f.seek(12)
        f.write(b"\xFF\xFF")


def pack_chk_with_locale(repair, storm, chk_path: Path, out_path: Path, locale: int) -> None:
    if out_path.exists():
        out_path.unlink()

    h_archive = ctypes.c_void_p()
    if not storm.lib.SFileCreateArchive(repair._win_bytes(out_path), 0, 16, ctypes.byref(h_archive)):
        raise OSError(f"SFileCreateArchive failed: {ctypes.get_last_error()}")
    try:
        storm.set_locale(locale)
        ok = storm.lib.SFileAddFileEx(
            h_archive,
            repair._win_bytes(chk_path),
            repair.SCENARIO_NAME,
            repair.MPQ_FILE_COMPRESS,
            repair.MPQ_COMPRESSION_PKWARE,
            repair.MPQ_COMPRESSION_PKWARE,
        )
        if not ok:
            raise OSError(f"SFileAddFileEx scenario.chk failed: {ctypes.get_last_error()}")
    finally:
        storm.lib.SFileCloseArchive(h_archive)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a protected StarCraft map copy from a clean SCX.")
    parser.add_argument("clean_map", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path(r"E:\SCX_WORK"))
    parser.add_argument("--locale", default="0x409")
    parser.add_argument("--repair-tool", type=Path, default=DEFAULT_REPAIR_TOOL)
    parser.add_argument("--stormlib")
    args = parser.parse_args()

    repair = load_repair_tool(args.repair_tool)
    locale = int(str(args.locale), 0)
    source = args.clean_map.resolve()
    out_path = args.out.resolve()
    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    storm = repair.Storm(repair.find_stormlib(args.stormlib))
    work_map, temp_ctx = repair.make_ascii_work_copy(source, work_dir)
    try:
        chk, read_locale = storm.extract_chk(work_map)
    finally:
        if temp_ctx:
            temp_ctx.cleanup()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="scmap_protect_") as tmp:
        chk_path = Path(tmp) / "scenario.chk"
        chk_path.write_bytes(chk)
        pack_path = Path(tmp) / "protected.scx"
        pack_chk_with_locale(repair, storm, chk_path, pack_path, locale)
        patch_protected_header(pack_path)
        shutil.copy2(pack_path, out_path)

    check_map, check_tmp = repair.make_ascii_work_copy(out_path, work_dir)
    try:
        check_chk, protected_locale = storm.extract_chk(check_map, locales=(0, locale))
    finally:
        if check_tmp:
            check_tmp.cleanup()

    if hashlib.sha256(check_chk).digest() != hashlib.sha256(chk).digest():
        raise RuntimeError("Protected map verification failed: extracted CHK hash mismatch")

    print(f"Read clean scenario.chk using locale 0x{read_locale:X}")
    print(f"Protected scenario.chk verified using locale 0x{protected_locale:X}")
    print(f"Protected CHK sha256: {hashlib.sha256(chk).hexdigest()}")
    print(f"Wrote protected map: {out_path}")
    print(f"Output size: {out_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
