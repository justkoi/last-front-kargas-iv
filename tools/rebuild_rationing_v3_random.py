# -*- coding: utf-8 -*-
"""Rebuild Triggers/13f_union_relief_fund.txt (wartime rationing) v3.

Design changes vs v2 (6-tier rebuild):
  1. Receiver draw has two priority bands: <=2000 first, then <=4000 only
     when the first band has no participant. Each band uses the 2-bit retry
     loop (Switch234/235) and deterministic fallback after 24 misses.
  2. Donor tier selection and resource transfer are merged into ONE trigger
     per (donor, tier, receiver, resource). Per-player tier DCs are written
     only when transfer actions fire. A receiver may also contribute.
  3. Receive messages show ONE summed line per resource: every reachable
     external-donor total (1..3 donors) is enumerated against the Pylon/Den
     running-total DCs. A receiver's net-zero self contribution is excluded.
  4. Donor confirmation is ONE combined line (ore and/or gas) per donor.
     Tier DCs are set only by real transfers and tier bands are exclusive.
  5. The third system announcement is shortened.

Phase machine (P8 "Zerg Queen" DC):
  0  idle          : "Terran Supply Depot" +1 per cycle; 1080 ticks = 90s.
  10 ore draw      : randomize Switch234/235 each cycle, pick eligible player.
  20 gas draw      : same for gas.
  30 transfer      : all eligible donors pay the drawn receiver(s), 1 cycle.
  40 messages      : "Tank Mode" DC frames 0..30 stagger the text output.
  50 cleanup       : clear everything, back to 0.
"""

import io
import itertools
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "Triggers", "13f_union_relief_fund.txt")

PLAYERS = [1, 2, 3, 4]
HUMAN_OWNERS = 'Player 1", "Player 2", "Player 3", "Player 4'

# (lower, upper or None, amount)
TIERS = [
    (2001, 4000, 60),
    (4001, 5999, 120),
    (6000, 7999, 300),
    (8000, 10000, 640),
    (10001, 15000, 1000),
    (15001, 20000, 1800),
    (20001, None, 3000),
]

# Per-player tier codes replace the old 48 tier switches. 0=none, 1..7=tier.
ORE_TIER_DC = "Terran Physics Lab"
GAS_TIER_DC = "Terran Covert Ops"
PART_SW = {1: 178, 2: 179, 3: 180, 4: 181}   # this-cycle participant flags
REG_SW = {1: 218, 2: 219, 3: 220, 4: 221}    # slot registration latch
DEP_SW = {1: 166, 2: 167, 3: 168, 4: 169}    # leave-handoff departed marks
RAND_B0, RAND_B1 = 234, 235                  # receiver draw random bits

# (bit1 state, bit0 state) -> player. "Set"/"Not Set" condition case.
RAND_COMBO = {1: ("Not Set", "Not Set"), 2: ("Not Set", "Set"),
              3: ("Set", "Not Set"), 4: ("Set", "Set")}

DEPOT = "Terran Supply Depot"
QUEEN = "Zerg Queen"
POOL = "Zerg Spawning Pool"
EVO = "Zerg Evolution Chamber"
TANK = "Terran Siege Tank (Tank Mode)"
ORE_TOTAL = "Protoss Pylon"        # summed ore transferred this cycle
GAS_TOTAL = "Zerg Hydralisk Den"   # summed gas transferred this cycle

TRY_LIMIT = 25          # fallback when Tank >= 25 (24 random draws)
FRAME_RECV_ORE = 2      # receiver ore total line
FRAME_RECV_GAS = 5      # receiver gas total line
FRAME_DONOR = 8         # combined donor line (all donors, own copy each)
END_TANK = 12           # Queen=40 ends when Tank >= 12

AMOUNTS = [t[2] for t in TIERS]

def reachable_totals():
    """Distinct net aid sums from the receiver's 1..3 other participants."""
    sums = set()
    for count in range(1, len(PLAYERS)):
        for combo in itertools.combinations_with_replacement(AMOUNTS, count):
            sums.add(sum(combo))
    return sorted(sums)

TOTALS = reachable_totals()

L = []          # output lines
def w(line=""):
    L.append(line)

def p8(comment, conds, acts, preserve=True):
    """Emit a Player 8 owned trigger."""
    trig("Player 8", comment, conds, acts, preserve)

def trig(owner, comment, conds, acts, preserve=True):
    if comment:
        w("//" + comment)
    w('Trigger("%s"){' % owner)
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

def sw(n, state):
    return 'Switch("Switch%d", %s);' % (n, state)

def set_sw(n, verb):
    return 'Set Switch("Switch%d", %s);' % (n, verb)

def dc(unit, op, val, player=8):
    return 'Deaths("Player %d", "%s", %s, %d);' % (player, unit, op, val)

def set_dc(unit, op, val, player=8):
    return 'Set Deaths("Player %d", "%s", %s, %d);' % (player, unit, op, val)

def acc(player, op, val, res):
    return 'Accumulate("Player %d", %s, %d, %s);' % (player, op, val, res)

def res_act(player, op, val, res):
    return 'Set Resources("Player %d", %s, %d, %s);' % (player, op, val, res)

def clear_all_work_state():
    """Actions that wipe every per-cycle work variable."""
    acts = [
        set_dc(POOL, "Set To", 0) + " //미네랄 수령자 없음",
        set_dc(EVO, "Set To", 0) + " //가스 수령자 없음",
        set_dc(ORE_TOTAL, "Set To", 0) + " //미네랄 이전 총액 리셋",
        set_dc(GAS_TOTAL, "Set To", 0) + " //가스 이전 총액 리셋",
        set_dc(TANK, "Set To", 0) + " //프레임/추첨 카운터 리셋",
        set_sw(RAND_B0, "clear"),
        set_sw(RAND_B1, "clear"),
    ]
    for pnum in PLAYERS:
        acts.append(set_dc(ORE_TIER_DC, "Set To", 0, player=pnum))
        acts.append(set_dc(GAS_TIER_DC, "Set To", 0, player=pnum))
    return acts

def tier_cond(player, lo, hi, res):
    conds = [acc(player, "At least", lo, res)]
    if hi is not None:
        conds.append(acc(player, "At most", hi, res))
    return conds


# ------------------------------------------------------------------ header
w("//-----------------------------------------------------------------//")
w("//  Wartime rationing (v3: random receiver draw)")
w("//  Switch177 : rationing active after the delayed mission 2 logistics briefing.")
w("//  Mission 2 briefing ends at tick 1536; logistics notice starts at 2616 (+90s),")
w("//  first transfer starts at 2784, then repeats every 90s = 1080 DC ticks.")
w("//  Receiver priority: draw resource <=2000 first; if none, draw <=4000.")
w("//  (Switch234/235 2-bit retry, deterministic P1-priority fallback at Tank>=25).")
w("//  Donors: 2001-4000 -> 60, 4001-5999 -> 120, 6000-7999 -> 300,")
w("//          8000-10000 -> 640,")
w("//          10001-15000 -> 1000, 15001-20000 -> 1800, 20001+ -> 3000.")
w("//  Ore and gas are judged separately. Tier DCs are set ONLY when a")
w("//  real transfer fired. Receiver sees ONE summed line per resource")
w("//  (Pylon/Den totals, all 1..3 external-donor sums); donor sees ONE")
w("//  combined ore/gas line.")
w("//  Queen phase: 0 idle / 10 ore draw / 20 gas draw / 30 transfer / 40 message / 50 cleanup.")
w("//  Generated by tools/rebuild_rationing_v3_random.py -- edit the script, not this file.")
w("//-----------------------------------------------------------------//")
w()

# ------------------------------------------------------------- delayed activation
# 미션2 마지막 전술 설명 창은 1512~1536틱. 그 뒤 정확히 1080틱(90초)이 지난
# 2616틱부터 배급 안내를 시작하고, 두 안내가 끝난 2784틱에 첫 배급을 즉시 실행한다.
p8("배급제 활성화: 미션2 전체 설명 종료 + 약 104초, 안내 종료 뒤 첫 배급 즉시 실행",
   [dc("Terran Valkyrie", "Exactly", 3) + " //미션2 진행 단계",
    dc("Terran Vulture", "At least", 2784) + " //미션2 설명 종료 뒤 배급 안내까지 완료",
    sw(177, "Not Set") + " //아직 비활성"],
   [set_sw(177, "set") + " //전시 배급제 가동",
    set_dc(DEPOT, "Set To", 1080) + " //첫 배급 사이클 즉시 개시"])

trig(HUMAN_OWNERS, "활성화 안내 1: 엘리아 (틱 2616~2640 창)",
     [dc("Terran Valkyrie", "Exactly", 3),
      dc("Terran Vulture", "At least", 2616),
      dc("Terran Vulture", "At most", 2640)],
     ['Display Text Message(Always Display, "<1B>엘리아: <04>일부 전선에는 물자가 남고, 다른 전선은 보급이 부족합니다. 여유 물자를 필요한 전선으로 돌리겠습니다.");'],
     preserve=False)

trig(HUMAN_OWNERS, "활성화 안내 2: 시스템 규칙 요약 (틱 2700~2724 창)",
     [dc("Terran Valkyrie", "Exactly", 3),
      dc("Terran Vulture", "At least", 2700),
      dc("Terran Vulture", "At most", 2724)],
     ['Display Text Message(Always Display, "<03>[전시 배급소] <04>전선별 보급 현황을 분석해 여유 물자를 가장 부족한 지휘부에 우선 배정합니다.");'],
     preserve=False)

# ----------------------------------------------------------- registration
w("// Rationing slot registration (Switch218~221). Separate from leave-handoff Switch162~165.")
w("// Zerg Beacon DC = 접속 생존 하트비트 (21_player_leave_handoff).")
w()
for pnum in PLAYERS:
    p8("P%d 등록 래치: 하트비트가 한 번이라도 잡힌 슬롯" % pnum,
       [sw(REG_SW[pnum], "Not Set"),
        dc("Zerg Beacon", "At least", 1, player=pnum) + " //P%d 생존 신호" % pnum],
       [set_sw(REG_SW[pnum], "set")])

# ------------------------------------------------- pre-activation upkeep
p8("비활성 유지보수: 배급제 꺼져 있는 동안 작업 변수 상시 청소",
   [sw(177, "Not Set")],
   [set_dc(DEPOT, "Set To", 0) + " //90초 타이머 리셋",
    set_dc(QUEEN, "Set To", 0) + " //단계 리셋"]
   + clear_all_work_state()
   + [set_sw(PART_SW[pnum], "clear") for pnum in PLAYERS])

# ------------------------------------------------------------ idle timer
p8("90초 타이머: 대기(Queen=0) 중에만 매 사이클 +1 (1080틱 = 90초)",
   [sw(177, "Set"),
    dc(QUEEN, "Exactly", 0) + " //대기 단계"],
   [set_dc(DEPOT, "Add", 1)])

w("// Copy Switch218~221 -> Switch178~181 on the firing cycle, before the draw starts.")
w("// Departed players (Switch166~169) are excluded from both donate and receive.")
w()
for pnum in PLAYERS:
    p8("P%d 참가 플래그 복사 (이탈자 제외)" % pnum,
       [sw(177, "Set"),
        dc(QUEEN, "Exactly", 0),
        dc(DEPOT, "At least", 1080) + " //90초 경과",
        sw(REG_SW[pnum], "Set") + " //P%d 등록됨" % pnum,
        sw(DEP_SW[pnum], "Not Set") + " //P%d 이탈 아님" % pnum],
       [set_sw(PART_SW[pnum], "set") + " //이번 사이클 참가"])

p8("사이클 개시: 타이머 소모 후 미네랄 수령자 추첨 단계로",
   [sw(177, "Set"),
    dc(QUEEN, "Exactly", 0),
    dc(DEPOT, "At least", 1080)],
   [set_dc(DEPOT, "Set To", 0),
    set_dc(POOL, "Set To", 0),
    set_dc(EVO, "Set To", 0),
    set_dc(TANK, "Set To", 0) + " //추첨 시도 카운터",
    set_dc(QUEEN, "Set To", 10) + " //미네랄 수령자 추첨 단계"])

# -------------------------------------------------------- receiver draws
def legacy_single_band_draw_phase(phase, res, recv_dc, next_phase, label):
    w("// %s receiver draw (Queen=%d). Random 2-bit retry, P1-priority fallback at Tank>=%d." % (label, phase, TRY_LIMIT))
    w()
    p8("%s 추첨 굴림: 매 사이클 2비트 재굴림 + 시도 횟수 +1" % label,
       [sw(177, "Set"),
        dc(QUEEN, "Exactly", phase)],
       [set_sw(RAND_B0, "randomize"),
        set_sw(RAND_B1, "randomize"),
        set_dc(TANK, "Add", 1) + " //추첨 시도 횟수"])

    for pnum in PLAYERS:
        b1, b0 = RAND_COMBO[pnum]
        p8("%s 추첨 적중: 굴림=P%d, 참가+%s 4000 이하이면 확정" % (label, pnum, label),
           [sw(177, "Set"),
            dc(QUEEN, "Exactly", phase),
            sw(RAND_B1, b1) + " //굴림 상위 비트",
            sw(RAND_B0, b0) + " //굴림 하위 비트",
            sw(PART_SW[pnum], "Set") + " //P%d 참가" % pnum,
            acc(pnum, "At most", 4000, res) + " //수령 자격"],
           [set_dc(recv_dc, "Set To", pnum) + " //%s 수령자 = P%d" % (label, pnum),
            set_dc(TANK, "Set To", 0),
            set_dc(QUEEN, "Set To", next_phase)])

    for pnum in reversed(PLAYERS):  # P4 first -> P1 overwrites last (P1 wins)
        p8("%s 추첨 실패 보정: 자격자 순차 스캔 (동률 P1 우선)" % label if pnum == 4 else None,
           [sw(177, "Set"),
            dc(QUEEN, "Exactly", phase),
            dc(TANK, "At least", TRY_LIMIT) + " //무작위 %d회 실패" % (TRY_LIMIT - 1),
            sw(PART_SW[pnum], "Set"),
            acc(pnum, "At most", 4000, res)],
           [set_dc(recv_dc, "Set To", pnum) + " //보정 수령자 = P%d" % pnum])

    p8("%s 추첨 마감: 보정 후 다음 단계로 (자격자 없으면 수령자 0 유지)" % label,
       [sw(177, "Set"),
        dc(QUEEN, "Exactly", phase),
        dc(TANK, "At least", TRY_LIMIT)],
       [set_dc(TANK, "Set To", 0),
        set_dc(QUEEN, "Set To", next_phase)])

# Two-band priority receiver policy.
def draw_phase(phase, res, recv_dc, next_phase, label):
    w("// %s receiver draw (Queen=%d). Priority: <=2000, then <=4000." % (label, phase))
    w()
    p8("%s 수령자 추첨: 2비트 무작위 + 시도 횟수" % label,
       [sw(177, "Set"), dc(QUEEN, "Exactly", phase)],
       [set_sw(RAND_B0, "randomize"), set_sw(RAND_B1, "randomize"),
        set_dc(TANK, "Add", 1)])

    # Band 1: <=2000. A direct hit advances immediately.
    for pnum in PLAYERS:
        b1, b0 = RAND_COMBO[pnum]
        p8("%s 1순위 추첨: P%d, 2000 이하" % (label, pnum),
           [sw(177, "Set"), dc(QUEEN, "Exactly", phase),
            sw(RAND_B1, b1), sw(RAND_B0, b0), sw(PART_SW[pnum], "Set"),
            acc(pnum, "At most", 2000, res)],
           [set_dc(recv_dc, "Set To", pnum), set_dc(TANK, "Set To", 0),
            set_dc(QUEEN, "Set To", next_phase)])

    # After 24 misses, find whether band 1 has any eligible participant.
    for pnum in reversed(PLAYERS):
        p8("%s 1순위 보정: 2000 이하 참가자 확인" % label if pnum == 4 else None,
           [sw(177, "Set"), dc(QUEEN, "Exactly", phase),
            dc(TANK, "At least", TRY_LIMIT), sw(PART_SW[pnum], "Set"),
            acc(pnum, "At most", 2000, res)],
           [set_dc(recv_dc, "Set To", pnum)])
    p8("%s 1순위 확정" % label,
       [sw(177, "Set"), dc(QUEEN, "Exactly", phase),
        dc(TANK, "At least", TRY_LIMIT), dc(recv_dc, "At least", 1)],
       [set_dc(TANK, "Set To", 0), set_dc(QUEEN, "Set To", next_phase)])

    # Band 2: only reached when nobody in band 1 exists.
    for pnum in PLAYERS:
        b1, b0 = RAND_COMBO[pnum]
        p8("%s 2순위 추첨: P%d, 4000 이하" % (label, pnum),
           [sw(177, "Set"), dc(QUEEN, "Exactly", phase),
            dc(TANK, "At least", TRY_LIMIT), sw(RAND_B1, b1), sw(RAND_B0, b0),
            sw(PART_SW[pnum], "Set"), acc(pnum, "At most", 4000, res)],
           [set_dc(recv_dc, "Set To", pnum), set_dc(TANK, "Set To", 0),
            set_dc(QUEEN, "Set To", next_phase)])

    for pnum in reversed(PLAYERS):
        p8("%s 2순위 보정: 4000 이하 참가자 확인" % label if pnum == 4 else None,
           [sw(177, "Set"), dc(QUEEN, "Exactly", phase),
            dc(TANK, "At least", TRY_LIMIT * 2), sw(PART_SW[pnum], "Set"),
            acc(pnum, "At most", 4000, res)],
           [set_dc(recv_dc, "Set To", pnum)])
    p8("%s 추첨 마감: 적격자 없으면 수령자 0 유지" % label,
       [sw(177, "Set"), dc(QUEEN, "Exactly", phase),
        dc(TANK, "At least", TRY_LIMIT * 2)],
       [set_dc(TANK, "Set To", 0), set_dc(QUEEN, "Set To", next_phase)])

draw_phase(10, "ore", POOL, 20, "미네랄")
draw_phase(20, "gas", EVO, 30, "가스")

# --------------------------------------------------------------- transfer
w("// Transfer phase (Queen=30). One trigger per (donor, tier, receiver, resource).")
w("// Tier switch is set only here, i.e. only when the transfer really fired.")
w()
p8("수령자 전무: 미네랄·가스 모두 수령자 없으면 사이클 무산",
   [sw(177, "Set"),
    dc(QUEEN, "Exactly", 30),
    dc(POOL, "Exactly", 0),
    dc(EVO, "Exactly", 0)],
   [set_dc(QUEEN, "Set To", 50) + " //정리 단계로"])

for res, recv_dc, tier_dc, total_dc, res_kor in (("ore", POOL, ORE_TIER_DC, ORE_TOTAL, "미네랄"),
                                                 ("gas", EVO, GAS_TIER_DC, GAS_TOTAL, "가스")):
    for recv in PLAYERS:
        for donor in PLAYERS:
            for t, (lo, hi, amt) in enumerate(TIERS):
                hi_txt = "%d" % hi if hi is not None else "20001+"
                acts = [res_act(donor, "Subtract", amt, res),
                        res_act(recv, "Add", amt, res)]
                # A receiver may be taxed too, but its own contribution is
                # net-zero and is excluded from the displayed received aid.
                if donor != recv:
                    acts.append(set_dc(total_dc, "Add", amt)
                                + " //%s 순수 이전 총액 누적(수령 메시지용)" % res_kor)
                acts.append(set_dc(tier_dc, "Set To", t + 1, player=donor)
                            + " //P%d %s %d티어 수금 기록" % (donor, res_kor, t + 1))
                p8("배급 이전: P%d(%s %d~%s, %d티어) -> P%d %d" %
                   (donor, res_kor, lo, hi_txt, t + 1, recv, amt),
                   [sw(177, "Set"),
                    dc(QUEEN, "Exactly", 30),
                    dc(recv_dc, "Exactly", recv) + " //%s 수령자 = P%d" % (res_kor, recv),
                    sw(PART_SW[donor], "Set") + " //P%d 참가" % donor]
                   + tier_cond(donor, lo, hi, res),
                   acts)

p8("이전 완료: 메시지 단계로",
   [sw(177, "Set"),
    dc(QUEEN, "Exactly", 30)],
   [set_dc(TANK, "Set To", 0) + " //메시지 프레임 카운터",
    set_dc(QUEEN, "Set To", 40)])

# --------------------------------------------------------------- messages
w("// Message phase (Queen=40). Tank frame stagger so lines never share a frame:")
w("//   recv ore total -> Tank %d, recv gas total -> Tank %d (one summed line each," % (FRAME_RECV_ORE, FRAME_RECV_GAS))
w("//   every reachable 1..3 external-donor total enumerated), combined donor line -> Tank %d," % FRAME_DONOR)
w("//   end at %d. Tier bands are exclusive, so a donor has at most one ore and" % END_TANK)
w("//   one gas tier switch set -> combined line needs few Not Set guards.")
w()
p8("메시지 프레임 진행: 매 사이클 +1",
   [sw(177, "Set"),
    dc(QUEEN, "Exactly", 40),
    dc(TANK, "At most", END_TANK - 1)],
   [set_dc(TANK, "Add", 1)])

for res, recv_dc, total_dc, frame, res_kor, color in (
        ("ore", POOL, ORE_TOTAL, FRAME_RECV_ORE, "미네랄", "<1F>"),
        ("gas", EVO, GAS_TOTAL, FRAME_RECV_GAS, "가스", "<07>")):
    for recv in PLAYERS:
        for total in TOTALS:
            trig("Player %d" % recv,
                 "수령 확인: P%d %s 합산 +%d (프레임 %d)" % (recv, res_kor, total, frame),
                 [sw(177, "Set"),
                  dc(QUEEN, "Exactly", 40),
                  dc(TANK, "Exactly", frame) + " //%s 수령 표시 프레임" % res_kor,
                  dc(recv_dc, "Exactly", recv) + " //%s 수령자 = P%d" % (res_kor, recv),
                  dc(total_dc, "Exactly", total) + " //이번 사이클 %s 이전 총액" % res_kor],
                 ['Display Text Message(Always Display, "<03>[전시 배급소] <04>전시 배급 물자가 도착했습니다. %s%s +%d");' % (color, res_kor, total)])

# Combined donor confirmation: (ore tier | none) x (gas tier | none), minus (none, none).
for donor in PLAYERS:
    for t_ore in list(range(len(TIERS))) + [None]:
        for t_gas in list(range(len(TIERS))) + [None]:
            if t_ore is None and t_gas is None:
                continue
            conds = [sw(177, "Set"),
                     dc(QUEEN, "Exactly", 40),
                     dc(TANK, "Exactly", FRAME_DONOR) + " //기부 확인 표시 프레임"]
            parts = []
            if t_ore is not None:
                conds.append(dc(ORE_TIER_DC, "Exactly", t_ore + 1, player=donor)
                             + " //P%d 미네랄 %d티어 기부 발생" % (donor, t_ore + 1))
                parts.append("<1F>미네랄 -%d" % TIERS[t_ore][2])
            else:
                conds.append(dc(ORE_TIER_DC, "Exactly", 0, player=donor))
            if t_gas is not None:
                conds.append(dc(GAS_TIER_DC, "Exactly", t_gas + 1, player=donor)
                             + " //P%d 가스 %d티어 기부 발생" % (donor, t_gas + 1))
                parts.append("<07>가스 -%d" % TIERS[t_gas][2])
            else:
                conds.append(dc(GAS_TIER_DC, "Exactly", 0, player=donor))
            trig("Player %d" % donor,
                 "기부 확인: P%d %s (프레임 %d)" %
                 (donor, " / ".join(p.replace("<1F>", "").replace("<07>", "") for p in parts), FRAME_DONOR),
                 conds,
                 ['Display Text Message(Always Display, "<03>[전시 배급소] <04>전시 배급 물자로 전환되었습니다. %s");' % "  ".join(parts)])

p8("메시지 종료: 정리 단계로",
   [sw(177, "Set"),
    dc(QUEEN, "Exactly", 40),
    dc(TANK, "At least", END_TANK)],
   [set_dc(QUEEN, "Set To", 50)])

# ---------------------------------------------------------------- cleanup
p8("사이클 정리: 작업 변수 전체 초기화 후 대기 복귀 (타이머 재개)",
   [sw(177, "Set"),
    dc(QUEEN, "Exactly", 50)],
   [set_dc(QUEEN, "Set To", 0)] + clear_all_work_state())

p8("대기 중 참가 플래그 청소: 다음 사이클 개시 때 새로 복사",
   [sw(177, "Set"),
    dc(QUEEN, "Exactly", 0)],
   [set_sw(PART_SW[pnum], "clear") for pnum in PLAYERS])

# -------------------------------------------------------------------- out
text = "\n".join(L).rstrip() + "\n"

# sanity checks
n_open = sum(1 for line in text.splitlines() if line.startswith('Trigger("'))
n_close = sum(1 for line in text.splitlines() if line == "}")
assert n_open == n_close, "unbalanced trigger blocks: %d vs %d" % (n_open, n_close)
for line in text.splitlines():
    if "Display Text Message" in line:
        assert line.rstrip().endswith(');'), "string action must end the line: " + line
assert "Wait(" not in text, "Wait is forbidden"

out = os.path.abspath(OUT_PATH)
with io.open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)

n_trig = n_open
print("wrote %s: %d triggers, %d lines" % (out, n_trig, text.count("\n")))
