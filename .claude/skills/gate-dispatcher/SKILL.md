---
name: gate-dispatcher
description: 품질 GATE를 텍스트 지시(선언만)가 아닌 코드 강제로 실행하는 표준 패턴 + 가드 함수 라이브러리. 오케스트레이터가 GATE 호출을 "까먹는" 현상을 원천 차단. "GATE 자동화", "GATE 강제 호출", "gate dispatch", "GATE 스킵 방지", "검증 강제" 요청 시 반드시 트리거.
---

# GATE Dispatcher — 품질 게이트 강제 호출

텍스트 지시 "모든 GATE 통과 필수"만으로는 **오케스트레이터가 GATE 호출을 생략**하는 현상 반복. 이 스킬은:
1. GATE를 **코드 레벨 guard 함수**로 변환
2. 미호출 시 **예외 발생**으로 파이프라인 강제 중단
3. Hook 기반 자동 검증 (Phase 50-04 Hooks 패턴)

## 언제 트리거되나

- "GATE 강제 호출 구현"
- "gate dispatcher 만들어"
- "GATE가 자꾸 스킵돼"
- "검증 자동화"
- "품질 게이트 코드화"
- "오케스트레이터가 GATE 건너뛰어"

## 핵심 패턴: Guard 함수

```python
# scripts/orchestrator/gate_guard.py

class GateNotDispatchedError(Exception):
    """GATE 호출이 누락되면 파이프라인이 여기서 멈춤."""
    pass

class GateGuard:
    def __init__(self, required_gates: list[str]):
        self.required = set(required_gates)
        self.dispatched = set()

    def mark_dispatched(self, gate_id: str):
        if gate_id not in self.required:
            raise ValueError(f"Unknown gate: {gate_id}")
        self.dispatched.add(gate_id)

    def verify_all_dispatched(self):
        missing = self.required - self.dispatched
        if missing:
            raise GateNotDispatchedError(
                f"다음 GATE가 호출되지 않음: {missing}"
            )
```

**사용 예**:
```python
guard = GateGuard(required_gates=["GATE-1", "GATE-2", "GATE-3", "GATE-4", "GATE-5"])

run_gate_1()
guard.mark_dispatched("GATE-1")

run_gate_2()
guard.mark_dispatched("GATE-2")

# ...

guard.verify_all_dispatched()  # 미호출 시 즉시 예외 → 파이프라인 중단
```

이 구조는 **선언적 지시보다 강함** — 호출 안 하면 코드가 돌아가지 않음.

## 워크플로우 (스튜디오 도입 시)

### Phase 1: GATE 정의 모으기
```python
REQUIRED_GATES = [
    "GATE-1",  # blueprint
    "GATE-2",  # 대본 품질
    "GATE-3",  # 에셋
    "GATE-4",  # 최종 영상
    "GATE-5",  # 감독 검수
]
```

### Phase 2: guard 인스턴스 생성
오케스트레이터 진입점에서:
```python
from scripts.orchestrator.gate_guard import GateGuard

def run_pipeline():
    guard = GateGuard(REQUIRED_GATES)
    # ... 파이프라인 실행
    # 각 GATE 호출 후 guard.mark_dispatched(...) 누락 금지
    guard.verify_all_dispatched()
```

### Phase 3: `skip_gates=True` 같은 디버그 경로 제거
- 프로덕션 코드에 `skip_gates` 인자 **금지**
- 필요하면 환경변수 `DEBUG_SKIP_GATES=1` + 세션 단일 실행으로만

### Phase 4: Hook 백업
pre_tool_use.py에 regex 추가:
```json
{
  "regex": "skip_gates\\s*=\\s*True",
  "reason": "GATE 강제 호출 위반"
}
```
→ 코드에 재침투 시 Write 자체가 차단됨.

### Phase 5: 회귀 테스트
```python
# tests/test_gate_enforcement.py
def test_pipeline_fails_when_gate_skipped():
    with pytest.raises(GateNotDispatchedError):
        run_pipeline_with_gate_skip()
```

## 입력/출력

**입력**: 스튜디오의 GATE 목록 정의
**출력**: `gate_guard.py` 모듈 + 기존 오케스트레이터 변경 diff

## 관련 에이전트

- supervisor 계열 (GATE 호출 책임)
- inspector 계열 (GATE 자체)

## 실패 패턴

- guard.mark_dispatched() 호출하고 실제 GATE는 안 돌림 (false pass) → **mark는 GATE 함수 내부에서만**
- 예외 catch해서 조용히 넘김 (try-except) → **top-level try-except 금지**
- 환경변수로 skip 가능하게 → **허용 시 단일 세션만, 로그 필수**

## 성공 기준

- [ ] `skip_gates=True` 코드에 없음
- [ ] `TODO(next-session)` GATE wiring 전부 완료
- [ ] guard.verify_all_dispatched() 호출 필수
- [ ] 회귀 테스트 통과

## 증거 (shorts_naberal CONCERNS)

- A-5 "TODO(next-session) 4건 미연결"이 대표님 호소 "스킵" 근본 원인
- A-6 "skip_gates=True 디버그 경로 상주"가 두 번째 원인
- 이 스킬 적용 = 두 원인 동시 해결

---

> 🧩 Layer 1 공용. 모든 스튜디오 상속.
> **핵심**: 선언 대신 코드. try-except 조용한 폴백 금지. guard 예외는 파이프라인 중단의 근거.
