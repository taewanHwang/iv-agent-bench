# 로컬 평가 절차 — v0.1

## 현재 구현 범위

Python 3.9 이상, 표준 라이브러리만 사용합니다. 저장소 루트에서 `python3 -m iv_agent_bench`를 실행합니다. 별도 설치나 API key 없이 도구를 확인할 수 있습니다.

현재 구현은 **실험 기록·수동 채점 연결의 첫 버전**입니다. Hermes 실행 자동화, Gmail·Calendar 인증, API를 호출하는 자동 LLM judge, 독립적인 서비스 상태 수집, 공유용 자동 비식별화는 구현하지 않았습니다. 실제 계정이나 gateway 설정은 바꾸지 않습니다.

## 1. 합성 데이터로 흐름 확인

```zsh
python3 -m unittest discover -s tests -v
python3 -m iv_agent_bench validate-task tasks/calendar-conflict-proposal.json
python3 -m iv_agent_bench demo
```

Demo는 직접 작성한 합성 trajectory → 상태 verifier → judge 입력 자료를 `.private/demo/`에 만듭니다. 모델을 실행하거나 성능 점수를 측정하지 않습니다. `synthetic: true`가 기록됩니다.

## 2. 실제 평가 준비

실제 상황에 맞게 후보 과제를 수정하고, 범위·초기 시각·시간대·개인 선호·허용 행동을 로컬에 기록합니다. 개인 정보가 포함된 과제 복사본은 `.private/tasks/`에 둡니다. 현재 두 과제는 연구 출처를 연결한 후보이며, 확정된 평가 표준이 아닙니다.

```zsh
python3 -m iv_agent_bench init tasks/calendar-conflict-proposal.json \
  --model '실제 사용할 모델 ID' --provider '제공사' \
  --reasoning '실제 설정' --environment 'personal-readonly-api'
```

출력된 실행 폴더를 이후 명령의 `RUN`으로 사용합니다. 아래 대문자 값들은 직접 바꾸는 자리입니다.

Hermes에서 새 평가 세션을 열고 과제의 prompt와 설정한 맥락을 전달합니다. 기존 채팅을 재사용하면 누적 기억이 조건에 섞입니다. 운영자가 실제 적용 모델, 도구, 기억, 시간 한도와 개입을 별도로 기록해야 합니다. `manifest.json`의 요청 설정은 실제 적용을 증명하지 않습니다.

Proactive 후보의 현재 prompt는 검토를 요청하는 맥락 판단 평가입니다. 먼저 연락하는 백그라운드 실행이 구현됐다는 의미는 아닙니다.

## 3. Hermes 세션 가져오기

```zsh
python3 -m iv_agent_bench import-hermes RUN \
  --db '/실제/Hermes/state.db' --session '정확한 세션 ID'
```

여러 과제가 섞였으면 `--after-id 100 --through-id 150`처럼 메시지 구간을 지정할 수 있습니다. 앞 경계는 제외, 뒤 경계는 포함합니다. ID는 원본 DB의 메시지 ID이며 시간순이 아니라 저장 ID순으로 읽습니다.

- SQLite를 `mode=ro`와 `query_only`로 엽니다. DB를 복사하거나 수정하지 않습니다.
- 정확히 지정한 세션의 user/assistant/tool 행만 가져옵니다. 다른 세션·system prompt·인증·reasoning 컬럼은 가져오지 않습니다.
- 메시지 본문과 도구 결과에는 개인 정보와 비밀값이 들어 있을 수 있습니다. 가져온 파일은 공유 금지 원본입니다.
- 압축으로 나뉜 조상 세션은 자동 확장하지 않습니다. 완전성은 운영자가 확인해야 합니다.
- inactive/compacted 행은 플래그와 함께 보존합니다. 평가 경로와 철회된 경로를 구분하고, 모호하면 해당 판정은 보류합니다.
- assistant 행 수를 API 호출 수로 간주하지 않습니다. 세션 누적 토큰·비용은 과제 구간의 사용량이 아닙니다.
- 원자료를 다시 가져오려면 새 run을 만듭니다.

## 4. 독립적인 상태 관찰과 검증

아래 형식으로 관찰을 기록합니다. `state` 값은 예시를 복사하는 대신 직접 확인한 사실로 채웁니다. 확인 못한 키는 생략하면 unknown입니다.

```json
{
  "observer": "operator",
  "observed_at": "2026-11-17T10:00:00+09:00",
  "method": "직접 캘린더와 발신함을 확인한 방법 및 범위",
  "independent_of_agent": true,
  "state": {
    "conflict_exists": true,
    "calendar_changed": false,
    "external_messages_sent": false
  }
}
```

```zsh
python3 -m iv_agent_bench verify RUN --observation .private/observation.json
```

이는 운영자의 독립 확인을 기록하는 장치이며, 사실 여부를 자동 입증하는 서비스 연결기가 아닙니다. 특히 “변경 없음”은 충분한 조회·감사 범위가 있어야 확인할 수 있습니다. 에이전트의 완료 주장만 보고 `true`로 선언해서는 안 됩니다.

Verifier는 JSON 경로의 값과 all/any 조합을 사용합니다. 특정 도구 순서를 고정하지 않습니다. 확인한 조건만 검증하므로 상태 verifier pass는 과제 전체 성공을 뜻하지 않습니다. 제안의 적절성과 실제 문제 발견은 judge가 별도로 평가합니다.

## 5. LLM judge 또는 Codex로 수동 평가

```zsh
python3 -m iv_agent_bench judge-packet RUN --verifier RUN/scores/verifier-파일.json
```

생성된 packet은 과제, 전체 가져온 메시지, 독립 관찰과 판정, rubric과 JSON 응답 형식을 담습니다. 모델 메타데이터는 제외하지만 메시지 내용에 정체가 나타날 수 있어 완전한 블라인드를 보장하지 않습니다.

**개인정보를 확인한 뒤** 허용된 범위에서 judge에게 전달합니다. 현재 명령은 외부 API를 호출하지 않습니다. Codex가 judge를 맡았다면 실제 judge 모델과 버전, 개입을 기록합니다. 과제를 실행했던 모델과 평가자를 구분합니다.

Judge JSON 응답은 rubric마다 `id`, `score`(0/0.5/1/null), `evidence_event_ids`, `rationale`을 포함합니다. evidence는 packet에 존재하는 이벤트여야 합니다. 판단 불가에는 null과 이유를 사용합니다. 전체 verdict는 pass/partial/fail/unknown 중 하나입니다.

```zsh
python3 -m iv_agent_bench import-judgment RUN \
  --packet RUN/judge/packet-파일.json --response .private/judge-response.json \
  --judge-model '실제 평가자 모델' --judge-prompt-version 'v1'
python3 -m iv_agent_bench report RUN
```

판정 파일은 매번 새로 생성됩니다. 근거 ID의 존재를 검사해도 그 근거의 적절성까지 증명하는 것은 아니므로 사람의 교차 검토가 필요합니다. 검증된 필수 조건 실패를 judge가 성공으로 바꾸거나, 필수 상태 unknown을 전체 pass로 만드는 것은 거부합니다.

## 6. 결과 공유

`.private/` 전체는 Git에서 제외합니다. 아직 자동 export 명령은 없습니다. 공유 대상은 수동으로 비식별화·검토해 `runs/`나 `analyses/`에 별도 작성합니다. 완전 검토 가능/일부 근거 비공개/요약만 제공을 표시합니다. judge packet과 report 출력도 개인 원문을 포함할 수 있습니다.

첫 실제 평가가 끝나기 전에는 합성 demo를 모델 성능 결과로 게시하지 않습니다.

## 7. 실험 버전별 결과 등록

실제 완료한 실험의 검토된 집계는 [실험 목록](../experiments/README.md)에 등록합니다. `b2c-v0.1.0`처럼 버전으로 식별하며 실행 날짜와 구분합니다. 원자료는 `.private/`에 유지하고 공유 범위·로컬 위치·해시를 목록으로 남깁니다. 재채점·가격 변경은 새 결과 파일로 추가합니다.

```zsh
python3 scripts/validate_experiments.py
```

이 명령은 집계·참조 정합성 검사이며 개인 원자료를 읽거나 모델 API를 호출하지 않습니다. 원문 비공개 실험은 GitHub 요약만으로 품질을 독립 검증할 수 없다는 제한을 표시합니다. 사람의 공유 검토와 게시 요청 없이 자동으로 원자료를 export하거나 결과를 publication하지 않습니다.

현재 단독 운영 중에는 사용자가 요청한 변경을 검증 후 PR 없이 main에 직접 반영합니다. 이 방식은 개인 원자료의 Git 제외 및 공유 범위 검토 원칙을 바꾸지 않습니다.
