#!/usr/bin/env bash
# Triggers/ 폴더의 단일책임 트리거 파일들을 번호순으로 이어붙여
# KargasIV_Triggers_Mission1Only.txt 를 생성한다.
set -euo pipefail
cd "$(dirname "$0")"
out="KargasIV_Triggers_Mission1Only.txt"
: > "$out"
for f in Triggers/*.txt; do
  cat "$f" >> "$out"
done
echo "built: $out ($(wc -l < "$out") lines from $(ls Triggers/*.txt | wc -l) parts)"
