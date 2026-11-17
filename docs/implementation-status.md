# 구현 현황 — 2026-11-17

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
