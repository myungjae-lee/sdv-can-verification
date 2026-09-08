# SDV CAN Verification Project — Handoff Summary

## 프로젝트 개요

- **목적**: 임베디드 SW/차량 검증 직무(SDV 통합검증 등) 지원용 포트폴리오 프로젝트
- **GitHub**: https://github.com/myungjae-lee/sdv-can-verification
- **환경**: Windows + WSL2 Ubuntu, Windows Terminal
- **작업 방식**: 완성 코드를 바로 받지 않고, 힌트만 받아 직접 코드를 작성하며 학습하는 방식으로 진행 중

---

## 완료된 것

### 1. 환경 구축
- WSL2 + Ubuntu 설치, Git 설치 및 GitHub 계정(myungjae-lee) 연동
- python-can, pytest 설치
- 가상 CAN 버스(vcan0) 생성 방법 숙지:
  ```bash
  sudo modprobe vcan
  sudo ip link add dev vcan0 type vcan
  sudo ip link set up vcan0
  ```
  (재부팅/WSL 재시작 시마다 다시 실행 필요)

### 2. src/can_handler.py (완성)

```python
import can

def create_bus(channel="vcan0", interface="socketcan"):
    """Connect to the CAN bus"""
    return can.interface.Bus(channel=channel, interface=interface)

def send_message(bus, arbitration_id, data):
    """Send a CAN message"""
    msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
    bus.send(msg)
    return msg

def receive_message(bus, timeout=1.0):
    """Receive a CAN message, waiting up to timeout seconds"""
    return bus.recv(timeout=timeout)

def parse_message(msg):
    """Extract ID and data from a received message"""
    if msg is None:
        return None
    return {"id": msg.arbitration_id, "data": list(msg.data)}
```

### 3. tests/test_can_handler.py (완성, 4개 테스트 통과)

```python
import pytest
from src.can_handler import create_bus, send_message, receive_message

def test_send_message_has_correct_id():
    bus = create_bus()
    sent = send_message(bus, 0x300, [0x01])
    assert sent.arbitration_id == 0x300
    assert sent.data == bytearray([0x01])

def test_receive_message_matches_sent():
    sender_bus = create_bus()
    receiver_bus = create_bus()
    send_message(sender_bus, 0x300, [0x02])
    received = receive_message(receiver_bus)
    assert received.arbitration_id == 0x300
    assert received.data == bytearray([0x02])

def test_receive_message_returns_none_when_nothing_sent():
    bus = create_bus()
    received = receive_message(bus, timeout=0.01)
    assert received is None

def test_send_message_rejects_out_of_range_byte():
    bus = create_bus()
    with pytest.raises(ValueError):
        send_message(bus, 0x300, [0x123])
```

실행 결과: `4 passed`

### 4. 학습 문서 (docs 폴더에 커밋됨)
- day1-2-setup-and-can-basics.md
- day3-can-handler-functions.md
- day3-first-pytest-test.md
- day3-receive-message-tests.md

---

## 겪었던 주요 이슈와 해결 (재발 방지용)

| 이슈 | 원인 | 해결 |
|---|---|---|
| git clone 실패 | `/mnt/c/Windows/system32`(윈도우 영역)에서 시도 | `cd ~`로 리눅스 홈으로 이동 후 재시도 |
| 붙여넣기 안 됨 | 구식 PowerShell 콘솔 | Windows Terminal로 전환 |
| pytest에서 ModuleNotFoundError: No module named 'src' | 패키지 인식 안 됨 | `src/__init__.py`, `tests/__init__.py` 빈 파일 생성 |
| receive_message가 계속 None | SocketCAN loopback 필터링(자기가 보낸 걸 같은 소켓으로 못 들음) | sender_bus/receiver_bus로 창구 분리 |
| TabError: inconsistent use of tabs and spaces | nano에서 직접 타이핑 시 탭과 스페이스 혼용 | 들여쓰기는 항상 스페이스만 사용. `nano -T 4`로 탭을 스페이스 변환하는 옵션도 있음 |

---

## CAN 메시지 스펙 (설계 확정된 것)

| ID | 방향 | 의미 |
|---|---|---|
| 0x300 | Test → ECU | 제어 명령 (LOCK=0x01, UNLOCK=0x02) |
| 0x301 | ECU → Test | 상태 응답 (LOCKED=0x00, UNLOCKED=0x01) |

---

## 다음 단계 (Mock ECU 설계)

### Mock ECU 클래스 뼈대 (아직 미구현)

```python
import can

class MockDoorLockECU:
    STATE_LOCKED = 0x00
    STATE_UNLOCKED = 0x01
    CMD_LOCK = 0x01
    CMD_UNLOCK = 0x02

    def __init__(self, bus):
        self.bus = bus
        self.state = self.STATE_LOCKED

    def handle_command(self, msg):
        """0x300 명령 수신 시 상태 전이 처리"""
        # TODO: 구현

    def _broadcast_status(self):
        """0x301로 현재 상태 응답"""
        # TODO: 구현
```

### 계획된 테스트 시나리오 (5개)
1. LOCK 명령 → STATE_LOCKED 응답 확인
2. UNLOCK 명령 → STATE_UNLOCKED 응답 확인
3. LOCK → UNLOCK 연속 전송 → 최종 상태 확인 (상태 누적 검증)
4. 정의되지 않은 cmd 값 → 응답 없어야 함 (결함 케이스)
5. 동일 명령 반복 전송 → 상태 유지 확인 (idempotency)

### 이후 계획 (원래 8일 계획 기준, 현재 진도는 앞서 있음)
- Mock ECU 구현 및 5개 시나리오 테스트
- GitHub Actions CI/CD 파이프라인 구축 (vcan 셋업 + pytest 자동 실행)
- README 작성 (프로젝트 목적, 구조, 실행 방법, 배운 점)
- 자소서 반영: "SDV 통합검증" 공고의 "SIL 기반 검증", "Plant Model 개발", "Test Case 개발" 문구와 연결

---

## 작업 습관 (지켜야 할 것)

1. **완결된 작업 단위가 끝날 때마다 즉시 git commit + push** (몰아서 하지 않기)
2. **코드는 힌트만 받고 직접 작성** — 이해도를 면접에서 설명 가능한 수준으로 유지하기 위함
3. **직접 타이핑 시 들여쓰기는 스페이스만 사용**
4. **당연해 보이는 것도 assert로 검증하는 이유를 스스로 설명할 수 있게 학습**
5. WSL 재시작/컴퓨터 재부팅 후에는 vcan0 재생성 필요함을 항상 확인
