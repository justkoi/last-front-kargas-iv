---
name: korean-commits
description: >
  Use this skill whenever you are about to create a git commit in this repository
  (E:/유즈맵제작, the Kargas IV StarCraft UMS map project). Commit messages and
  commit-related explanations here must be written in Korean — both the subject
  line and the body, plus the user-facing post-commit summary. Apply this rule
  even if the user asks for a commit in English, in mixed English/Korean, or
  with default phrasing; default to Korean and only deviate if the user explicitly
  overrides with something like "영어로 커밋해줘" in this turn. Trigger for any
  phrasing of a commit request: "커밋해줘", "커밋해주세요", "commit this",
  "commit the work", "make a commit", "stage and commit", etc.
---

# Korean Commit Messages

이 저장소의 모든 커밋 메시지는 한국어로 작성합니다.
커밋 후 사용자에게 설명할 때도 커밋 해시, 제목, 포함/제외한 변경 사항을 한국어로 설명합니다.

## 적용 범위

- **제목 (subject)**: 한국어로 작성. 50자 이내 권장.
- **본문 (body)**: 한국어로 작성. 변경 이유와 영향을 간결히 설명.
- **커밋 후 설명**: 한국어로 작성. 커밋 해시, 커밋 제목, 포함한 파일/제외한 파일을 짧게 설명.
- **Co-Authored-By 등 트레일러**: 영어 그대로 유지 (관습대로).
- **파일 경로/식별자/명령어/심볼 이름**: 원문(영어) 유지. 번역하지 말 것.

## 제목 작성 규칙

- 동사로 시작 (명령형): "추가", "수정", "교체", "정리", "리팩터", "제거" 등.
- 마침표 없이 끝.
- 무엇을 했는지 + 가능하면 어디에 했는지를 한 줄로.

**예시:**
- `미션2 페이즈2 비콘 점령 메커니즘 추가`
- `오버로드 무한 생성 문제 수정 (반복 웨이브에서 제거)`
- `웨이브 트리거에 저그 건물 잔존 조건 추가`
- `미션2 대사를 통일성 있는 추리 흐름으로 재작성`

## 본문 작성 규칙

본문은 "무엇을" 보다 "왜"를 적습니다. 변경의 이유, 부작용, 결정 사항을 짧게.

영어 단어/심볼이 더 명확하면 그대로 씁니다 (예: `DC slot`, `Preserve Trigger`, `Player 5`, `Bring 조건`). 무리해서 번역하면 오히려 의미가 흐려집니다.

**예시 본문:**
```
무한 반복 웨이브가 게임 후반 오버로드 200기 이상 누적시켰음.
보급(06)이 이미 20기 미만 유지하므로 웨이브의 오버로드 생성은 잉여.
1회성 early 웨이브는 그대로 두고 반복 late 웨이브에서만 제거.
```

## HEREDOC 사용

여러 줄 메시지는 HEREDOC으로 전달합니다 (이스케이프 문제 회피):

```bash
git commit -m "$(cat <<'EOF'
미션2 페이즈2 비콘 점령 메커니즘 추가

- Probe DC를 점령 시작 플래그로, Zealot DC를 점령 카운터로 사용
- 비콘 진입 시 타이머 영구 정지, 60초마다 P6 반격조 스폰
- 5회 격퇴 = 100% 점령 = 미션 클리어
EOF
)"
```

## 사용자가 영어를 요구할 때만 예외

명시적으로 "영어로 커밋해", "in English"라고 한 턴에 한정해서만 영어로 작성합니다. 그 외에는 한국어 기본.
