# 구현 현황 — 2026-11-17

현재 실제 실험 결과는 [b2c-v0.1.0](../experiments/b2c-v0.1.0/README.md), 전체 목록과 버전 규칙은 [experiments/](../experiments/README.md)에서 확인한다. 아래 초기 점검 문단은 개발 순서의 이력이며 최신 상태는 후속 완료 기록을 우선한다.

## 동작 확인

- 표준 라이브러리 기반 CLI, 과제 검사와 실행 manifest/과제 스냅샷
- 지정 Hermes SQLite 세션·메시지 구간의 읽기 전용 import
- 기존 trajectory 보존, 버전별 별도 채점 결과
- all/any 경로 조건, pass/fail/unknown 상태 verifier
- trajectory·과제·verifier가 연결된 judge packet 및 수동 판정 import
- 근거 이벤트 검증, 상태 실패/불확실성의 judge 덮어쓰기 방지
- 합성 demo 및 핵심 동작 테스트 10개

## 미구현 / 다음 단계

1. 설치된 실제 Hermes 세션으로 import 호환성 점검 및 누적·압축 세션 처리 검토
2. 실제 고객 사례 출처 목록 확장, 무개입·과잉알림을 포함한 시나리오 확정
3. 개인 Gmail·Calendar 연결 방식·권한 범위 결정과 독립 상태 조회
4. 첫 실제 read-only 과제 실행과 수동 judge 교차 검토
5. 제공사별 호출·비용·시간·개입 기록의 정확한 수집
6. 수동 검토를 포함한 공유본 export와 비교 보고서
7. 필요 시 API 기반 judge와 실행 어댑터

현재 테스트는 합성 데이터로 실행했습니다. 개인 메일·일정을 조회하거나 실제 모델 평가를 실행하지 않았습니다. 외부 API 비용은 발생하지 않았습니다.

## 후속 점검 — 2026-11-17

실제 Hermes 단일 세션 import 호환성을 확인했다. 56개 이벤트의 원본 ID 및 호출·결과 대응은 일치하지만 자식 세션이 있어 전체 작업 완전성은 미확정이다. SQLite 연결 종료를 보완했다. Codex Gmail·Calendar 프로필 조회는 성공했으며 Hermes 연결과 본문 읽기 권한은 미확인이다. 위의 “개인 메일·일정 미조회” 상태는 유지한다. 실제 평가와 외부 judge 실행은 하지 않았다. [첫 평가 준비](first-evaluation-preparation.md)를 참조한다.

## 현재 상태 정정 및 오프라인 실행 준비

위의 초기 “메일·일정 미조회” 기록은 이후 수집으로 갱신됐다. 확정 범위의 메일 69개와 기본 캘린더 일정 16개를 읽어 .private/에 보관했다. 세 모델의 도구·기억 없는 생성 및 요청 구성 점검을 완료했다. GPT는 요청 builder만, Solar는 mock HTTP conversation까지 확인했다. 개인 모델 평가, 인증 유효성 검사, 외부 judge 전송은 미실행이다. 공통 출력 상한과 hard deadline은 실제 실행 전 정리가 필요하다. 상세 범위와 한계는 [첫 평가 준비](first-evaluation-preparation.md)를 따른다.

## 첫 실제 고정 스냅샷 실행 완료

2026-11-17, gpt-6-luna(medium), gpt-6.1-terra(medium), solar-mini-4-5-preview로 각각 한 번의 개인 브리핑 실행을 완료했다. 세 실행 모두 HTTP 200 응답과 completed=true를 기록했다. 동일 입력 전체 전달, 도구 없음, DB와 import 메시지·답변 일치를 확인했다. 원자료·답변·세부 사용량·비공개 보고서는 .private/에 보관한다.

이 결과는 합성 demo와 구분되는 실제 제공사 호출이다. 정확성·중요도·누락의 품질 채점은 미실행이며 외부 judge 전송도 없다. 실시간 서비스 상태의 독립 감사를 하지 않아 기존 상태 verifier는 unknown으로 보존했다. 최초 네트워크 제한으로 중단된 두 run과 개입 기록은 따로 남겼다. Solar 베타 보관 조건을 고지하고 사용자 인지를 확인한 뒤 실행했다. 기존 gateway·모델·서비스 설정은 변경하지 않았다. 상세 보고서는 비공개 검토 후 공유 범위를 정한다.

## 첫 수동 품질 평가 완료

사용자 요청에 따라 현재 Codex(gpt-6.1-sol)가 세 답변을 고정 입력과 대조했다. 새 외부 judge API는 호출하지 않았다. task rubric의 coverage/prioritization/grounding 차원과 근거 이벤트 ID를 사용해 새 judge packet·판정 파일을 생성했다. 기존 원자료·운영 결과·상태 verifier는 변경하지 않았다.

이번 단일 사례의 잠정 판단은 Terra가 가장 안정적, Luna는 일부 누락·우선순위 보완 필요, Solar는 중요 기한·사실 오류로 그대로 사용하기 어렵다는 것이다. 사용자 중요도 기준 미작성·사후 기준·비블라인드 단일 평가자 한계를 기록했다. 서비스 상태 검증 unknown은 유지한다. 세부 근거와 개인 사례는 .private/의 별도 품질 보고서에 보관하며 사람 검토 전 공유하지 않는다.

## 실험 레지스트리 및 GitHub 요약

실험 날짜와 별개인 `b2c-v0.1.0` 식별자, index.json, 목적·coverage·실행/과제/채점/가격 버전, 결과 파일과 비공개 raw manifest를 추가했다. 개인 원문과 전체 답변·judge packet은 Git에서 제외한다. 레지스트리 검증은 원자료가 없는 checkout에서도 수행되며, 산술·모델/run 연결·중복 버전·unknown 판정·경로 범위를 검사한다. 테스트 16개와 합성 demo가 통과했다. 이 검증은 의미 수준의 정확성 검증이나 개인정보 검토를 대체하지 않는다.
