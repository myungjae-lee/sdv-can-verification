# Day 3: Writing can_handler.py from scratch

## 오늘 한 일 (큰 그림)

어제(1-2일차)까지는 candump/cansend로 "손으로" CAN 메시지를 주고받았다.
오늘은 그걸 Python 코드로 자동화하는 `src/can_handler.py`를 직접 짰다.
완성된 코드를 받아쓰는 대신, 목표만 듣고 빈칸을 채우는 방식으로 진행해서
각 줄이 왜 그렇게 생겼는지 스스로 설명할 수 있는 수준까지 이해했다.

---

## 완성된 코드 (직접 작성)

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

---

## 개념 1: import의 의미

`import can`은 python-can 라이브러리를 "이 파일 안에서" 쓸 수 있게 불러오는 선언이다.

- `pip install python-can` = 책을 사서 책장에 꽂아두는 것 (컴퓨터 전체에 설치)
- `import can` = 그 책을 지금 이 파일 위에 펼쳐놓는 것 (이 파일에서 쓸 수 있게 함)

설치만 하고 import를 안 하면, 그 파일 안에서는 라이브러리가 "있는지도 모르는" 상태다.

---

## 개념 2: 매개변수 vs 라이브러리가 정한 고정 이름

```python
can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
```

이 줄에서 왼쪽(`arbitration_id=`)과 오른쪽(`arbitration_id`)이 우연히 이름이 같아 보이지만
성격이 다르다.

- **왼쪽**: python-can 라이브러리가 "이 이름으로 값을 달라"고 미리 정해놓은 것 (건드릴 수 없음)
- **오른쪽**: 우리가 함수를 정의할 때 직접 지은 매개변수 이름 (자유롭게 바꿔도 됨)

실험: `def send_message(bus, my_id, my_data):`로 매개변수 이름을 바꿔도
`arbitration_id=my_id, data=my_data`로 쓰면 똑같이 작동한다.
→ 왼쪽은 고정, 오른쪽은 자유라는 걸 확인함.

같은 원리가 `create_bus`의 `channel=`, `interface=`와
`receive_message`의 `timeout=`에도 그대로 적용된다.

---

## 개념 3: 데이터를 리스트로 나눠 넣는 이유 (직접 에러로 확인)

### 실수 1: 하나의 큰 숫자로 넣기

```python
send_message(bus, 0x300, [0x12345678])
```

→ `ValueError: byte must be in range(0, 256)`

CAN 데이터는 1바이트(0~255)씩 담아야 하는데, `0x12345678`은 그 범위를 훨씬 넘는
하나의 큰 숫자라서 에러가 남.

### 실수 2: 리스트를 따로따로 넘기기

```python
send_message(bus, 0x300, [0x01],[0x02],[0x03],[0x04])
```

→ `TypeError: send_message() takes 3 positional arguments but 6 were given`

대괄호를 4번 나눠 쓰면 "리스트 4개(=인자 4개)"로 인식되어,
`bus, arbitration_id, data` 3개만 받기로 한 함수에 6개를 넘긴 셈이 됨.

### 실수 3: 중첩 리스트

```python
send_message(bus, 0x300, [[0x01], [0x02], [0x03], [0x04]])
```

→ `TypeError: 'list' object cannot be interpreted as an integer`

`data`의 각 항목이 숫자(`0x01`)가 아니라 리스트(`[0x01]`) 자체가 되어버려서,
바이트로 변환할 수 없다는 에러가 남.

### 올바른 방법

```python
send_message(bus, 0x300, [0x01, 0x02, 0x03, 0x04])
```

대괄호 하나 안에 숫자 여러 개를 콤마로 나열해야, "4바이트짜리 데이터 하나"로 인식된다.

### 정리

실제 CAN 프레임은 최대 8바이트 데이터 칸을 가진 메시지 하나가 한 번에 통째로 전송된다.
Python 리스트 `[0x01, 0x02, 0x03, 0x04]`는 그 프레임 안에 들어갈 바이트들을
코드로 표현하는 방식이며, 실행 중 리스트에서 값이 하나씩 빠져나가는 게 아니라
그대로 하나의 프레임으로 묶여 전송된다.

---

## 개념 4: bus와 vcan0의 관계

- `vcan0`: 실제 통신선(전선)에 해당하는 것. 리눅스 커널이 관리하며, 하나만 존재.
- `bus` (파이썬 변수): 그 vcan0이라는 통신선에 접속하기 위한 창구(핸들).
  선 자체가 아니라 "선에 꽂는 커넥터"에 가까움.

`bus = create_bus()`로 만든 것은 새로운 통신선이 아니라, 기존 vcan0에
파이썬 코드가 접속할 수 있게 해주는 연결 객체다.

Python 코드(`bus` 변수)와 candump는 각각 별도의 프로그램이지만,
둘 다 같은 vcan0에 동시에 접속할 수 있다. 그래서 파이썬에서 보낸 메시지를
다른 터미널의 candump가 감지할 수 있었다.

---

## 개념 5: 0x300은 위치가 아니라 메시지 종류

처음에는 "0x300이 어느 센서 위치다"로 이해했으나, 정확히는 다음과 같다.

- CAN ID는 물리적 위치가 아니라, **메시지의 종류/의미를 구분하는 이름표**다
- 우리 프로젝트에서 0x300 = "도어락 명령 메시지", 0x301 = "도어락 상태 응답"이라고
  스스로 정의한 약속일 뿐, 아직 실제로 반응하는 프로그램(Mock ECU)은 작성 전이다

---

## 개념 6: return의 역할

```python
def send_message(bus, arbitration_id, data):
    msg = can.Message(...)
    bus.send(msg)
    return msg
```

함수가 끝나면 내부에서 만든 지역 변수(`msg`)는 원래 사라진다.
`return`은 그 값만 함수 밖으로 내보내는 역할을 한다.

```python
a = send_message(bus, my_id, my_data)
```

이렇게 하면 함수 안의 `msg`가 함수 밖의 `a`에 저장된다.

이 반환값은 나중에 검증(assert)에 활용된다:

```python
sent = send_message(bus, 0x300, [0x01])
assert sent.arbitration_id == 0x300
```

---

## 개념 7: assert란

`assert 조건`은 "조건이 참이면 통과, 거짓이면 즉시 에러를 낸다"는 뜻이다.

```python
assert 1 == 1   # 통과, 아무 일도 안 일어남
assert 1 == 2   # AssertionError 발생
```

이게 pytest와 결합되면, 사람이 눈으로 candump 화면을 보고 확인하던 걸
코드가 자동으로 "맞다/틀리다"를 판단하게 만드는 도구가 된다.

---

## 개념 8: blocking call (질문했던 polling/interrupt와의 차이)

`bus.recv(timeout=1.0)`은 polling(반복 확인)도 interrupt(하드웨어 신호)도 아니고
**blocking call**에 가깝다.

- polling: "왔어? 왔어?"를 코드가 반복해서 확인 (CPU 계속 사용)
- interrupt: 메시지가 오면 하드웨어가 신호를 보내 그때만 반응
- blocking call: 함수 호출 지점에서 코드 실행이 멈춘 것처럼 대기하다가,
  결과가 나오거나 timeout이 지나면 다음 줄로 넘어감

`while(1)` 반복문과 다른 점은, blocking call은 코드가 반복 실행되며 확인하는 게
아니라 "결과가 나올 때까지 리턴을 미루고 있는" 상태라는 것.

---

## 오늘 완료 체크리스트

- [x] `create_bus`, `send_message`, `receive_message`, `parse_message` 4개 함수를
      힌트만 받고 직접 작성
- [x] 잘못된 데이터 형식(큰 숫자, 분리된 리스트, 중첩 리스트)을 직접 실행해보고
      에러 메시지로 원인 확인
- [x] bus/vcan0 구조도를 보고 개념 정리
- [x] docstring을 한글에서 영어로 변경, GitHub에 커밋
- [x] nano 백업 파일(`can_handler.py.save`) 삭제 후 재커밋

## 다음 단계 (예고)

`tests/test_can_handler.py`를 만들어 pytest로 `send_message`, `receive_message`가
의도한 대로 동작하는지 자동 검증하는 테스트 작성.
