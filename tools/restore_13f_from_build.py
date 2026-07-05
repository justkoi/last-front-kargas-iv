from pathlib import Path

built = Path(r"e:\유즈맵제작\KargasIV_Triggers_Mission1Only.txt").read_text(encoding="utf-8")
start = built.index("//  Wartime rationing\n")
end = built.index("//  Base defense response\n")
out = Path(r"e:\유즈맵제작\Triggers\13f_union_relief_fund.txt")
out.write_text(built[start:end], encoding="utf-8", newline="\n")
print(f"restored {out} ({end-start} chars)")
