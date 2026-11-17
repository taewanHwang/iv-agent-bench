# 실험 목록

실험은 **버전**으로 식별한다. 실행 날짜는 메타데이터이며 버전의 대체 식별자가 아니다. 합성 pipeline 검증과 실제 모델 실험을 분리한다.

| 실험 버전 | 목적·coverage | 실행 규모 | 요약 결과 | 원자료 공개 범위 |
|---|---|---|---|---|
| [b2c-v0.1.0](b2c-v0.1.0/README.md) | 고정된 개인 메일·일정의 중요 업무 브리핑 | 시나리오 1 × 모델 3 × 반복 1 | Terra가 가장 안정적, Luna 일부 누락, Solar 중요 기한·사실 오류. 단일 사례의 잠정 판단 | 요약만 제공; 원문은 로컬 비공개 |

기계가 읽는 목록: [index.json](index.json). 실험별 상세 정의: `EXPERIMENT/experiment.json`.

## 버전과 디렉터리

```text
experiments/
  index.json
  b2c-v0.1.0/
    experiment.json             # 목적, coverage, 환경·권한, 버전, 산출물
    README.md                   # 실험 결과 보고서
    results/
      metrics-v1.json            # 실제 측정 요약
      quality-v1.json            # rubric·판정·근거 이벤트
      cost-v1.json               # 가격표·가정·환산 비용
    data/
      README.md                  # 공유 범위와 접근 방법
      raw-manifest-v1.json       # 비공개 원자료 목록·SHA-256·로컬 위치
```

- **실험 버전**: `b2c-vMAJOR.MINOR.PATCH`. 새로운 입력·모델 구성·실행 묶음은 새 실험 버전으로 기록한다. 같은 날짜에 여러 버전이 생길 수 있다.
- **run ID**: 개별 모델의 한 실행을 식별한다. 재시도 HTTP 요청 수와 run 수는 다르다.
- **suite/task 버전**: 평가 과제와 데이터 조건을 식별한다. 후보 과제를 보정된 benchmark로 부르지 않는다.
- **채점 버전**: 원자료를 그대로 두고 재채점하면 `quality-v2.json`처럼 추가한다. 과거 점수는 덮어쓰지 않는다. 새 결과를 artifacts 목록에 추가하고 current_results 포인터를 명시적으로 갱신한다.
- **가격 버전**: 가격·할인·장문 기준을 바꾸면 `cost-v2.json`을 추가한다. 실제 청구액과 단가 환산 비용을 구분한다.
- **보고서 revision**: 사실 정정은 변경 이력에 이유를 남긴다. 표를 수정해도 이전 원자료·측정·채점을 몰래 대체하지 않는다.

## 새 실험 등록

1. 새 버전 디렉터리와 `experiment.json`을 만든다. 목적, 포함·제외 coverage, 출처, 승인 범위, 성공 조건, 모델·하네스·입력·과제 버전을 기록한다.
2. 원문·인증 정보·judge packet은 `.private/`에 보관한다. 개별 run과 중단·개입을 보존한다.
3. 측정, 판정, 가격 가정을 별도 파일로 정리한다. `unknown`, `not measured`, `fail`을 구분한다.
4. `data/`에는 공유 가능한 목록과 접근 제한을 기록한다. 원문이 없으면 독립 검토·재현의 한계를 명시한다.
5. 사람이 공유 범위를 검토하고 GitHub 게시를 요청한 뒤, 검토한 요약만 등록한다. 자동 export·자동 publication은 하지 않는다.
6. `index.json`과 이 목록에 행을 추가하고 아래 검증을 수행한다.

```zsh
python3 scripts/validate_experiments.py
python3 -m unittest discover -s tests -v
python3 -m iv_agent_bench demo
```

검증기는 구조·파일 연결·집계 정합성만 확인한다. 개인정보 검토나 주장·근거의 의미 검증을 대체하지 않는다. 정규식 검사로 비식별화를 보장하지 않는다.
