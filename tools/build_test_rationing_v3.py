# -*- coding: utf-8 -*-
"""Rebuild TestTriggersForBuild/94_test_union_relief_fund.txt (rationing v3 test).

Six sequential scenarios driven by a linear script counter
(P8 "Zerg Ultralisk Cavern" DC, test-only). Each stage:
  setup -> arm timer (Depot=1439) -> wait cycle start/end -> assert frames.

Assertions compare exact expected resources with Accumulate and print
PASS/FAIL text, because SC1 leaderboards only show ACTIVE players -- empty
human slots (P2~P4 in a solo test) never appear there. The ore/gas
leaderboard flip is kept for the tester's own numbers only.

Stages:
  1. two-way: P1 ore donor + gas receiver, P2 the opposite (original case)
  2. multi-donor + tier boundaries: P2/P3/P4 -> P1 (ore t1/t2/t6, gas t1/t5/t6
     at boundary values 4001/15001/20001); P1 must see 3+3 receive lines
  3~5. random receiver x3 rounds: P2~P4 all eligible, P1 sole donor (640);
     shows which player won each draw
  6. no receiver: everyone at 8000 -> cycle aborts, nothing may change

NOTE: designed for solo (or 2-human) testing. With 3-4 humans the per-stage
registration clears are re-latched by live heartbeats and isolation breaks.
"""

import io
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..",
                        "TestTriggersForBuild", "94_test_union_relief_fund.txt")

SCRIPT = "Zerg Ultralisk Cavern"     # test-only script counter (P8)
FLIP = "Zerg Defiler Mound"          # test-only leaderboard flip timer (P8)
QUEEN = "Zerg Queen"
DEPOT = "Terran Supply Depot"
REG_SW = {1: 218, 2: 219, 3: 220, 4: 221}
HUMANS = '"Player 1", "Player 2", "Player 3", "Player 4"'

STAGE_STEP = 60                      # script values reserved per stage

L = []
def w(line=""):
    L.append(line)

def trig(owner, comment, conds, acts, preserve=True):
    if comment:
        w("//" + comment)
    w("Trigger(%s){" % owner)
    w("Conditions:")
    for c in conds:
        w("\t" + c)
    w("Actions:")
    for a in acts:
        w("\t" + a)
    if preserve:
        w("\tPreserve Trigger();")
    w("}")
    w()

def p8(comment, conds, acts, preserve=True):
    trig('"Player 8"', comment, conds, acts, preserve)

def dc(unit, op, val, player=8):
    return 'Deaths("Player %d", "%s", %s, %d);' % (player, unit, op, val)

def set_dc(unit, op, val, player=8):
    return 'Set Deaths("Player %d", "%s", %s, %d);' % (player, unit, op, val)

def sw(n, state):
    return 'Switch("Switch%d", %s);' % (n, state)

def set_sw(n, verb):
    return 'Set Switch("Switch%d", %s);' % (n, verb)

def acc(player, op, val, res):
    return 'Accumulate("Player %d", %s, %d, %s);' % (player, op, val, res)

def set_res(player, val, res):
    return 'Set Resources("Player %d", Set To, %d, %s);' % (player, val, res)

def display(text):
    return 'Display Text Message(Always Display, "%s");' % text

RES_KOR = {"ore": "미네랄", "gas": "가스"}

def check(frame, player, res, expected):
    """PASS/FAIL assertion at one script frame (3 triggers)."""
    kor = RES_KOR[res]
    base_conds = [sw(246, "Set"), dc(SCRIPT, "Exactly", frame)]
    trig(HUMANS, "검증(프레임 %d): P%d %s = %d 기대" % (frame, player, kor, expected),
         base_conds + [acc(player, "At least", expected, res),
                       acc(player, "At most", expected, res)],
         [display("<03>[TEST] <07>PASS: P%d %s = %d" % (player, kor, expected))],
         preserve=False)
    if expected > 0:
        trig(HUMANS, None,
             base_conds + [acc(player, "At most", expected - 1, res)],
             [display("<03>[TEST] <08>FAIL: P%d %s < %d (부족)" % (player, kor, expected))],
             preserve=False)
    trig(HUMANS, None,
         base_conds + [acc(player, "At least", expected + 1, res)],
         [display("<03>[TEST] <08>FAIL: P%d %s > %d (초과)" % (player, kor, expected))],
         preserve=False)

def stage_setup(base, comment, regs, resources, extra_conds=None, extra_acts=None):
    """Setup trigger at script==base: registration, resources, arm the timer."""
    conds = (extra_conds or []) + [dc(SCRIPT, "Exactly", base),
                                   dc(QUEEN, "Exactly", 0) + " //배급 사이클 대기 중"]
    acts = list(extra_acts or [])
    for pnum in (1, 2, 3, 4):
        acts.append(set_sw(REG_SW[pnum], "set" if pnum in regs else "clear")
                    + " //P%d 등록 %s" % (pnum, "ON" if pnum in regs else "OFF"))
    for pnum, ore, gas in resources:
        acts.append(set_res(pnum, ore, "ore"))
        acts.append(set_res(pnum, gas, "gas"))
    acts.append(set_dc(DEPOT, "Set To", 1079) + " //다음 사이클에 1080 도달, 즉시 배급 개시")
    acts.append(set_dc(SCRIPT, "Set To", base + 1))
    p8(comment, conds, acts)

def stage_title(base, text):
    trig(HUMANS, None,
         [sw(246, "Set"), dc(SCRIPT, "Exactly", base + 1)],
         [display(text)], preserve=False)

def stage_waits(base):
    p8("사이클 개시 감지",
       [dc(SCRIPT, "Exactly", base + 1),
        dc(QUEEN, "At least", 10) + " //추첨 단계 진입"],
       [set_dc(SCRIPT, "Set To", base + 2)])
    p8("사이클 종료 감지 (정리까지 완료)",
       [dc(SCRIPT, "Exactly", base + 2),
        dc(QUEEN, "Exactly", 0) + " //대기 단계 복귀"],
       [set_dc(SCRIPT, "Set To", base + 3)])

def stage_advance(base, next_base):
    p8("검증 프레임 진행: 매 사이클 +1 (다음 스테이지 %d까지)" % next_base,
       [dc(SCRIPT, "At least", base + 3),
        dc(SCRIPT, "At most", next_base - 1)],
       [set_dc(SCRIPT, "Add", 1)])

# ------------------------------------------------------------------ header
w("//-----------------------------------------------------------------//")
w("//  [TEST MODE] Wartime rationing v3 -- 6 sequential scenarios")
w("//  Script counter: P8 \"Zerg Ultralisk Cavern\" (test-only DC)")
w("//  Leaderboard flip: P8 \"Zerg Defiler Mound\" (test-only DC)")
w("//  Switch246: init guard. Stage bases 0/60/120/180/240/300, end 360.")
w("//")
w("//  SC1 leaderboards only show ACTIVE players: empty human slots never")
w("//  appear there. All cross-player verification is therefore done with")
w("//  Accumulate PASS/FAIL messages; the leaderboard is only for P1's own")
w("//  numbers. Designed for solo/2-human tests -- with 3-4 humans the")
w("//  registration clears are re-latched by heartbeats and stages overlap.")
w("//")
w("//  1: two-way        P1 ore donor t3 -640 -> P2 / P2 gas donor t3 -> P1")
w("//  2: multi-donor    P2/P3/P4 -> P1, ore t1/t2/t6, gas boundary t1/t5/t6")
w("//  3~5: random x3    P2~P4 eligible, P1 donor 640; winner printed")
w("//  6: no receiver    everyone 8000, cycle must abort with no change")
w("//  Generated by tools/build_test_rationing_v3.py -- edit the script.")
w("//-----------------------------------------------------------------//")
w()

# ------------------------------------------------------- stage 1: two-way
stage_setup(0, "스테이지1 셋업: 양방향 배급 (P1<->P2), 테스트 초기화 겸용",
            regs=(1, 2),
            resources=[(1, 10000, 300), (2, 500, 10000),
                       (3, 0, 0), (4, 0, 0)],
            extra_conds=[sw(246, "Not Set")],
            extra_acts=[set_sw(246, "set") + " //테스트 1회 초기화 가드",
                        set_sw(177, "set") + " //배급제 강제 활성화 (미션 게이트 우회)"])
stage_title(0, "<03>[TEST 1/6] <04>양방향 배급: P1 미네랄 -640 기부, 가스 +640 수령 (P2 반대 역할)")
stage_waits(0)
check(3, 1, "ore", 9360)
check(4, 2, "ore", 1140)
check(5, 1, "gas", 940)
check(6, 2, "gas", 9360)
stage_advance(0, 60)

# -------------------------------------- stage 2: multi-donor + boundaries
stage_setup(60, "스테이지2 셋업: 다중 도너 + 티어 경계값 (P2/P3/P4 -> P1)",
            regs=(1, 2, 3, 4),
            resources=[(1, 1000, 2000),
                       (2, 5000, 4001),    # ore t1 120, gas t1 boundary 120
                       (3, 7000, 15001),   # ore t2 300, gas t5 boundary 1800
                       (4, 25000, 20001)]) # ore t6 3000, gas t6 boundary 3000
stage_title(60, "<03>[TEST 2/6] <04>다중 도너: P1이 합산 한 줄씩 수령 예정 (미네랄 +3420, 가스 +4920)")
stage_waits(60)
check(63, 1, "ore", 4420)
check(64, 1, "gas", 6920)
check(65, 2, "ore", 4880)
check(66, 2, "gas", 3881)
check(67, 3, "ore", 6700)
check(68, 3, "gas", 13201)
check(69, 4, "ore", 22000)
check(70, 4, "gas", 17001)
stage_advance(60, 120)

# ------------------------------------------- stages 3~5: random receiver
for round_no, base in ((1, 120), (2, 180), (3, 240)):
    stage_setup(base, "스테이지%d 셋업: 무작위 수령자 %d회차 (P2~P4 자격, P1 도너)" % (round_no + 2, round_no),
                regs=(1, 2, 3, 4),
                resources=[(1, 10000, 0), (2, 0, 0), (3, 0, 0), (4, 0, 0)])
    stage_title(base, "<03>[TEST %d/6] <04>무작위 수령자 %d회차: P2~P4 중 한 명이 미네랄 640 수령"
                % (round_no + 2, round_no))
    stage_waits(base)
    check(base + 3, 1, "ore", 9360)
    for pnum in (2, 3, 4):
        trig(HUMANS, "무작위 수령자 식별: P%d가 뽑혔으면 640 보유" % pnum,
             [sw(246, "Set"), dc(SCRIPT, "Exactly", base + 4),
              acc(pnum, "At least", 640, "ore"),
              acc(pnum, "At most", 640, "ore")],
             [display("<03>[TEST] <04>%d회차 무작위 수령자 = <07>P%d (미네랄 +640)" % (round_no, pnum))],
             preserve=False)
    check(base + 5, 1, "gas", 0)
    stage_advance(base, base + STAGE_STEP)

# -------------------------------------------------- stage 6: no receiver
stage_setup(300, "스테이지6 셋업: 수령자 전무 (전원 8000, 사이클 무산 확인)",
            regs=(1, 2),
            resources=[(1, 8000, 8000), (2, 8000, 8000),
                       (3, 8000, 8000), (4, 8000, 8000)])
stage_title(300, "<03>[TEST 6/6] <04>수령자 전무: 전원 8000 보유, 약 4초 후 무산 (자원 변동 없어야 정상)")
stage_waits(300)
check(303, 1, "ore", 8000)
check(304, 2, "ore", 8000)
check(305, 1, "gas", 8000)
check(306, 2, "gas", 8000)
stage_advance(300, 360)

trig(HUMANS, "테스트 종료 안내",
     [sw(246, "Set"), dc(SCRIPT, "Exactly", 360)],
     [display("<03>[TEST] <07>배급 테스트 종료 — 6개 시나리오 완료")],
     preserve=False)

# --------------------------------------------- leaderboard (P1 own view)
w("// Leaderboard flip: ore 5s <-> gas 5s. ACTIVE players only (engine limit);")
w("// empty-slot values are verified by the PASS/FAIL messages above instead.")
w()
p8("리더보드 전환 타이머",
   [sw(246, "Set")],
   [set_dc(FLIP, "Add", 1)])
p8("리더보드 전환 타이머 리셋 (120틱 = 10초 주기)",
   [sw(246, "Set"), dc(FLIP, "At least", 120)],
   [set_dc(FLIP, "Set To", 0)])
trig(HUMANS, "리더보드: 앞 5초는 미네랄",
     [sw(246, "Set"), dc(FLIP, "At most", 59)],
     ['Leader Board Resources("TEST 배급 미네랄", ore);',
      "Leaderboard Computer Players(disabled);"])
trig(HUMANS, "리더보드: 뒤 5초는 가스",
     [sw(246, "Set"), dc(FLIP, "At least", 60), dc(FLIP, "At most", 119)],
     ['Leader Board Resources("TEST 배급 가스", gas);',
      "Leaderboard Computer Players(disabled);"])

# -------------------------------------------------------------------- out
text = "\n".join(L) + "\n"

n_open = sum(1 for line in text.splitlines() if line.startswith("Trigger("))
n_close = sum(1 for line in text.splitlines() if line == "}")
assert n_open == n_close, "unbalanced: %d vs %d" % (n_open, n_close)
for line in text.splitlines():
    if "Display Text Message" in line or "Leader Board" in line:
        assert line.rstrip().endswith(");"), "string action must end the line: " + line
assert "Wait(" not in text

out = os.path.abspath(OUT_PATH)
with io.open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print("wrote %s: %d triggers, %d lines" % (out, n_open, text.count("\n")))
