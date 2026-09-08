# Day 3 (계속): receive_message tests — loopback, is vs ==, pytest progress

## 오늘 이어서 한 일

`receive_message`에 대한 테스트 2개를 추가로 작성하면서, CAN 통신의 loopback
필터링 문제를 직접 에러로 만나 해결했고, `is`와 `==`의 차이도 실험으로 확인했다.

---

## 개념 1: pytest 진행률(%)의 의미

```
tests/test_can_handler.py::test_send_message_has_correct_id PASSED       [ 33%]
tests/test_can_handler.py::test_receive_message_matches_sent PASSED      [ 66%]
tests/test_can_handler.py::test_receive_message_returns_none_when_nothing_sent PASSED [100%]
```

`[33%]`, `[66%]`, `[100%]`는 테스트 성공/실패와 무관하게, **전체 테스트 함수
개수 중 몇 개를 실행했는지**를 보여주는 진행률이다. `def test_...`로 시작하는
함수 하나가 pytest 입장에서 "테스트 하나(task 하나)"로 인식된다.
지금 함수가 3개이므로 1개 끝날 때마다 1/3씩 올라간 것이다.

---

## 개념 2: SocketCAN의 loopback 필터링 문제

### 증상

```python
def test_receive_message_matches_sent():
    bus = create_bus()
    send_message(bus, 0x300, [0x02])
    received = receive_message(bus)   # timeout 1초 기본값인데도 실패
    assert received.arbitration_id == 0x300
```

→ `AttributeError: 'NoneType' object has no attribute 'arbitration_id'`

`receive_message`의 기본 timeout이 1.0초라 "너무 빨리 확인해서"는 아니었다.
1초를 기다렸는데도 `None`이 나왔다는 것은, 다른 원인이 있다는 뜻이었다.

### 원인

SocketCAN에는 **"한 소켓(연결 창구)이 스스로 보낸 메시지는, 그 소켓 자신에게는
다시 들리지 않는다"**는 loopback 필터링 규칙이 있다. 같은 `bus`로 보내고
같은 `bus`로 받으려 했기 때문에 이 규칙에 걸려 계속 `None`이 나온 것이다.

candump/cansend 실습 때 문제가 없었던 이유는, cansend와 candump가
**서로 다른 프로그램(서로 다른 소켓)**이었기 때문이다.

### 해결

송신용 창구와 수신용 창구를 별도로 만든다. vcan0이라는 통신선(회선) 자체는
하나 그대로지만, 그 선에 접속하는 소켓(bus)을 두 개 만드는 것이다.

```python
def test_receive_message_matches_sent():
    sender_bus = create_bus()
    receiver_bus = create_bus()
    send_message(sender_bus, 0x300, [0x02])
    received = receive_message(receiver_bus)
    assert received.arbitration_id == 0x300
    assert received.data == bytearray([0x02])
```

### 개념 정리 (헷갈렸던 부분)

- `create_bus()`로 만든 `bus`는 **단방향이 아니라 양방향**이다.
  (송신도 되고 수신도 됨)
- 단방향/양방향의 문제가 아니라, **"자기가 보낸 걸 같은 창구로 다시 받는
  특정 경로만 막혀있다"**는 것이 정확한 이해다.
- CAN High/Low 두 가닥의 물리적 전선은 "하나의 통신선(버스)"으로 취급되며,
  `create_bus()` 한 번 호출은 그 통신선에 접속하는 창구(소켓) 하나를
  만드는 것이다. 통신선 자체가 여러 개 생기는 게 아니다.
- `send` 테스트에서 bus를 하나만 쓴 이유는 단방향이라서가 아니라, 그 테스트가
  `send_message`의 반환값만 검증하고 실제로 vcan0을 거쳐 "받는" 동작 자체를
  하지 않았기 때문이다.

### 두 receive 테스트의 timeout 지정 여부 비교

| 테스트 | timeout 지정 여부 | 실제 적용된 값 |
|---|---|---|
| `test_receive_message_matches_sent` | 지정 안 함 | 함수 기본값 1.0초 |
| `test_receive_message_returns_none_when_nothing_sent` | `timeout=0.01`로 직접 지정 | 0.01초 |

loopback 에러가 났을 때 "timeout이 너무 짧아서 못 받은 게 아닌가" 의심할 수
있었지만, 실제로는 기본값 1.0초나 기다렸는데도 실패한 것이었다. 즉 timeout
설정 문제가 아니라 loopback 필터링이 원인이었다는 걸 구분하는 게 중요했다.

`test_receive_message_returns_none_when_nothing_sent`에서 `timeout=0.01`로
짧게 준 이유: 이 테스트는 애초에 아무것도 보내지 않으므로, timeout을 1초로
두든 0.01초로 두든 결과(None)는 동일하다. 결과가 같다면 굳이 길게 기다릴
필요가 없으므로, 테스트 실행 속도를 위해 의도적으로 짧게 설정한 것이다.

### 테스트마다 데이터 값을 다르게 쓴 이유

`test_send_message_has_correct_id`는 데이터로 `[0x01]`을, `test_receive_message_matches_sent`는
`[0x02]`를 사용했다. 두 값을 굳이 다르게 쓴 이유는 "값이 우연히 겹쳐서
잘못된 결과가 나올까봐"가 아니라 (CAN 값이 우연히 일치할 확률은 무시할
수준으로 낮음), **테스트가 실패했을 때 에러 로그에 찍히는 값만 보고도
어느 함수(send 쪽인지 receive 쪽인지)에서 문제가 생겼는지 빠르게 구분하기
위함**이다. 예를 들어 에러 로그에 `0x01` 관련 값이 이상하면 send 쪽,
`0x02` 관련 값이 이상하면 receive 쪽 문제라고 짐작할 수 있다.

---

## 개념 3: is 와 == 의 차이

- `==` : 두 값의 **내용**이 같은지 비교
- `is` : 두 값이 **메모리상 완전히 동일한 하나의 객체**인지 비교 (주소 비교)

```python
a = [1, 2, 3]
b = [1, 2, 3]
a == b   # True (내용이 같음)
a is b   # False (서로 다른 메모리 위치에 만들어진 별개의 리스트)
```

`is`가 더 빠른 이유: 객체의 내용물을 하나하나 열어보지 않고, 주소(고유 식별값)
하나만 비교하면 되기 때문. 반면 `==`는 리스트처럼 내부에 여러 항목이 있는
자료형이면, 그 항목들을 순서대로 하나씩 대조한다 (비교 대상 리스트 자기 자신의
내부 원소를 순회하는 것이지, 다른 변수들을 순회하는 게 아님).

`None`은 프로그램 전체에서 단 하나만 존재하는 특수한 값이라, 항상 같은
메모리 주소를 가진다. 그래서 `is None`과 `== None`은 결과가 항상 같지만,
관례적으로 더 빠르고 명확한 `is None`을 표준으로 쓴다.

`is`는 파이썬 고유의 문법이며, "객체 동일성 비교"라는 개념 자체는 다른
언어에도 각자의 방식(Java의 `==`, C의 포인터 비교 등)으로 존재한다.

---

## 완성된 테스트 파일 (전체)

```python
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
```

실행 결과:

```
3 passed in 0.04s
```

---

## 오늘 완료 체크리스트

- [x] pytest 진행률(%) 표시의 의미 이해
- [x] SocketCAN loopback 필터링 문제를 직접 에러로 만나 원인 파악
- [x] sender/receiver bus 분리로 문제 해결
- [x] is와 ==의 차이를 개념과 실험(메모리 주소)으로 이해
- [x] 테스트 3개 전체 통과 확인, GitHub 커밋

## 다음 단계 (예고)

지금까지는 "정상 케이스" 위주로 테스트했다. 다음은 이상/실패 케이스
(잘못된 ID, 정의되지 않은 명령 등)를 추가하고, Mock ECU 설계로 넘어갈 예정.
