# Day 4 마무리 (9/15) - 시나리오 5 구현 및 개념 정리

## 오늘 한 것 (전체)
- 시나리오 4(정의되지 않은 명령값 → 응답 없음) 작성 및 통과
- 시나리오 5(동일 명령 반복 전송 → idempotency) 작성 및 통과
- **`tests/test_mock_ecu.py` 테스트 시나리오 5개 전부 완료 (5/5) — Day 4 대단원 완료**
- None/is 비교, timeout 값 선정 기준, 가상머신 vs WSL2 차이 등 개념 정리

---

## 구현 내용

### 시나리오 5: 동일 명령 반복 전송 → 상태 유지(idempotency)
```python
def test_repeated_lock_command_is_idempotent():
    """Sending LOCK_CMD twice in a row should keep the state as LOCKED (idempotency)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()
    raw_msg1 = receive_message(test_bus)   # First response
    assert raw_msg1.data == bytearray([0x00])

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()
    raw_msg2 = receive_message(test_bus)   # Second response (should be identical)
    assert raw_msg2.data == bytearray([0x00])
```
- idempotency(멱등성): 같은 연산을 여러 번 반복해도 결과가 달라지지 않는 성질. LOCK을 한 번 보내든 두 번 연달아 보내든 최종 상태가 동일하게 LOCKED여야 함을 검증
- 두 응답을 `raw_msg1`, `raw_msg2`로 구분해서 저장한 이유: 같은 변수명(`raw_msg`)을 재사용해도 문법적으로는 동작하지만, 테스트 실패 시 "첫 번째 응답이 잘못된 건지 두 번째가 잘못된 건지"를 변수명만으로 구분할 수 없게 됨. 변수를 나눠두면 디버깅 시 어느 시점의 응답인지 코드만 보고도 명확히 알 수 있음

---

## 전체 테스트 파일 최종본 (5개 시나리오)
```python
import pytest
from src.can_handler import create_bus, send_message, receive_message, parse_message
from src.mock_ecu import MockDoorLockECU


def test_lock_command_returns_locked_status():
    """Sending LOCK_CMD (0x300) should update ECU state and respond with LOCKED (0x301)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()

    raw_msg = receive_message(test_bus)
    assert raw_msg.data == bytearray([0x00])


def test_unlock_command_returns_unlocked_status():
    """Sending UNLOCK_CMD (0x300) should update ECU state and respond with UNLOCKED (0x301)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x02])
    ecu.process_command()

    raw_msg = receive_message(test_bus)
    assert raw_msg.data == bytearray([0x01])


def test_consecutive_lock_unlock_final_state():
    """Sending LOCK then UNLOCK consecutively should result in final state UNLOCKED."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()
    receive_message(test_bus)   # Consume LOCK response, not checked here

    send_message(test_bus, 0x300, [0x02])
    ecu.process_command()
    raw_msg = receive_message(test_bus)

    assert raw_msg.data == bytearray([0x01])
    assert ecu.state == MockDoorLockECU.UNLOCKED


def test_undefined_command_produces_no_response():
    """Sending an undefined command value should not produce any response (fault case)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x99])
    ecu.process_command()

    raw_msg = receive_message(test_bus, timeout=0.1)
    assert raw_msg is None


def test_repeated_lock_command_is_idempotent():
    """Sending LOCK_CMD twice in a row should keep the state as LOCKED (idempotency)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()
    raw_msg1 = receive_message(test_bus)
    assert raw_msg1.data == bytearray([0x00])

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()
    raw_msg2 = receive_message(test_bus)
    assert raw_msg2.data == bytearray([0x00])
```

---

## Q&A 정리

### 1. 전통적 가상머신(VMware, VirtualBox, Hyper-V) vs WSL2 - 개발환경으로 뭐가 나은가
- **전통적 VM**: 전체 컴퓨터를 통째로 흉내냄(가상 CPU, 메모리, 디스크, 커널까지 별도 시뮬레이션) — 상대적으로 무겁고 느리며, 설치/설정 절차가 필요함
- **WSL2**: 리눅스 커널만 가볍게 돌리며 Windows와 리소스를 공유 — 상대적으로 가볍고 빠르며, Windows ↔ 리눅스 파일 접근이 매끄러움
- 결론: 지금 프로젝트(vcan0 등 리눅스 네트워크 기능만 필요, 다른 OS 전체 테스트나 격리 환경이 불필요)에는 WSL2가 더 적합. 이미 세팅 완료되어 잘 동작 중이라 옮길 필요 없음
- 전통적 VM이 필요한 경우: 여러 다른 리눅스 배포판을 동시에 비교하거나, 부팅 과정부터 테스트해야 하는 임베디드 부트로더 개발 등 — 지금 프로젝트 범위 밖

### 2. 변수명을 구분해서 저장하는 이유 (raw_msg1 vs raw_msg2)
- 같은 이름(`raw_msg`)을 재사용해도 문법적으로 동작은 하지만, 두 번째 값이 첫 번째 값을 덮어써서 "이전 결과가 뭐였는지" 코드상에서 추적이 어려워짐
- 테스트가 실패했을 때 "어느 시점의 응답이 문제였는지"를 변수명만으로 구분할 수 있어야 디버깅이 명확해짐
- 이는 단순 스타일 문제가 아니라, 실수 방지와 가독성을 위한 실용적인 이유

---

## 커밋 이력 (오늘)
```
Add fault case test for undefined command
Add idempotency test scenario - all 5 test scenarios complete
```

## Day 4 완료 요약
- `src/can_handler.py`: 4개 함수 (create_bus, send_message, receive_message, parse_message)
- `src/mock_ecu.py`: MockDoorLockECU 클래스 (상태 관리, 명령 처리)
- `tests/test_can_handler.py`: 4개 테스트 통과
- `tests/test_mock_ecu.py`: 5개 테스트 통과 (LOCK, UNLOCK, 연속전송, 결함케이스, idempotency)

## 다음 할 일 (Day 5~)
- README 최종 정리 (Completed So Far, Next Steps 갱신 + Limitations/Future Improvements 섹션에 CAN-FD, ID 마스킹, blocking receive, CAN 보안 구조적 한계 등 반영)
- GitHub Actions CI/CD 파이프라인 구축 (push 시 vcan 자동 설정 + pytest 자동 실행)
