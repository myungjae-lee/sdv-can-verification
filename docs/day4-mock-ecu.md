# Day 4 - MockDoorLockECU 설계 및 개념 정리

## 오늘 한 것
- `src/mock_ecu.py`에 `MockDoorLockECU` 클래스 작성 (힌트 기반 직접 구현)
- `__init__`, `process_command` 완성
- 다음: `tests/test_mock_ecu.py` 테스트 시나리오 5개 작성

---

## Q&A 정리

### 1. `pass`는 뭘 하는 키워드인가?
Python은 함수/클래스 블록이 비어있으면 `IndentationError`가 남. `pass`는 "여기 블록엔 아무 내용 없음"을 문법적으로 표시하는 자리표시자. 이미 코드가 채워진 블록에서는 불필요 (지워도 됨).

### 2. `return`과 `pass`의 차이
- `pass` = 이 블록은 비워둠, 그냥 다음 줄로 진행
- `return` = **함수 실행 자체를 여기서 끝내고 빠져나감**

`process_command`에서 `parsed is None`이거나 정의 안 된 명령일 때 `return`을 쓴 이유: 뒤에 있는 `send_message` 호출까지 도달하면 안 되니까(응답을 보내면 안 되는 상황), 함수를 통째로 종료시켜야 했음.

### 3. 인스턴스(instance) 개념
- 클래스 = 설계도, 인스턴스 = 그 설계도로 실제로 만든 객체 (붕어빵 틀 vs 붕어빵)
- `ecu1 = MockDoorLockECU(bus1)`, `ecu2 = MockDoorLockECU(bus2)` → 서로 완전히 독립적인 `self.state`, `self.bus`를 가짐
- 차량으로 치면 운전석 도어락 ECU, 조수석 도어락 ECU를 각각 별도 인스턴스로 만들면 서로 상태가 안 섞임

### 4. `self.변수명`은 전역변수가 되는 건가?
아니다. **인스턴스 변수**라는 별개 개념.
- 전역변수: 파일 전체에서 딱 1개, 아무데서나 접근 가능
- `self.변수`: 인스턴스마다 각각 독립적으로 존재, 그 인스턴스를 통해서만 접근 가능 (`ecu1.state`처럼)

Python은 접근 제한을 강제하지 않아서 외부에서도 `ecu.state`처럼 들여다볼 수 있지만, 이건 "전역변수라서"가 아니라 "캡슐화를 강제 안 해서"임.

### 5. `__init__(self, bus)`의 파라미터 개수가 인스턴스 변수 개수를 제한하나?
아니다. 전혀 무관. `__init__` 안에서 `self.무언가 = 값` 형태는 원하는 만큼 만들 수 있음. 파라미터는 "외부에서 값을 받아와야 하는 것"만 정의하는 것 (예: `bus`는 ECU마다 다르니 외부에서 받음, `state`는 항상 LOCKED로 시작하니 파라미터로 안 받음).

### 6. 매직넘버(Magic Number)란?
코드에 이름 없이 뜬금없이 등장하는 숫자. `if cmd == 0x01:`처럼 쓰면 0x01이 뭘 의미하는지 코드만 봐서 모름. `LOCK_CMD = 0x01`처럼 이름 붙이면 가독성이 좋아짐.

### 7. 클래스 변수 vs 인스턴스 변수
```python
class MockDoorLockECU:
    LOCKED = 0x00        # 클래스 변수 - 모든 인스턴스가 공유
    def __init__(self, bus):
        self.state = MockDoorLockECU.LOCKED   # 인스턴스 변수 - 인스턴스마다 별도
```
클래스 바디 최상단에는 `self`가 없음 (클래스 정의 시점에는 아직 만들어진 인스턴스가 없으니까). `self`는 메서드 안에서만 의미 있음.

### 8. mutable(가변) vs immutable(불변) — 왜 `state`를 정수로 저장해야 하나
- 정수(int)는 **불변 객체**: `self.state = self.LOCKED`를 해도 `LOCKED` 원본은 절대 안 바뀜. 나중에 `self.state = 0x99`로 재할당해도, 이건 "새 정수 객체 생성 + 재바인딩"일 뿐 원본과 무관함.
- `bytearray`는 **가변 객체**: 만약 `state`를 bytearray로 저장했다면, `ecu.state[0] = 0x99`처럼 **내용을 직접 수정**할 수 있음. `self.state = self.LOCKED`는 값 복사가 아니라 "같은 객체를 가리키는 참조"를 만드는 거라서, 한 인스턴스에서 `state`를 수정하면 클래스 변수 `LOCKED` 자체가 오염되는 심각한 버그가 생길 수 있음.
- 결론: 내부 상태는 정수로 저장, CAN으로 전송할 때만 리스트로 감싸서 보냄 (`[self.state]`)

### 9. `send_message`에 데이터 넘길 때 왜 `bytearray`로 안 감싸도 되나
`send_message(bus, arbitration_id, data)`는 내부에서 `can.Message(data=data, ...)`로 그대로 넘김. python-can이 리스트/bytearray 등 여러 형태를 다 받아주므로, `[self.state]`(리스트)로 충분함.

**단, 받은 값을 검증(비교)할 때는 다름.** `sent.data`처럼 라이브러리가 리턴하는 값은 이미 `bytearray`로 고정되어 있어서, `sent.data == [0x01]`처럼 리스트와 비교하면 타입이 달라 실패함 → `sent.data == bytearray([0x01])`로 맞춰야 함.
(→ "넣을 때는 관대함, 나올 때는 고정된 타입")

### 10. `import can_handler` vs `from can_handler import 함수들`
- 실행 속도 차이 없음. 둘 다 내부적으로 `can_handler.py` 전체를 로드하는 과정은 동일.
- 차이는 오직 "함수를 어떤 이름으로 부르냐"뿐: `can_handler.send_message(...)` vs `send_message(...)`
- `can_handler.py` 안에서 이미 `import can`이 되어 있으므로, `mock_ecu.py`에서 따로 `import can`을 또 할 필요 없음 (함수 내부 구현은 그 함수를 정의한 파일의 책임)

### 11. bash에서 `&&`의 의미
`git add ... && git commit ... && git push`
`&&`는 "왼쪽 명령어가 성공(exit code 0)했을 때만 오른쪽 명령어 실행". 중간에 실패하면 그 뒤 명령어는 실행 안 됨 → 빈 커밋이나 잘못된 push를 방지.

### 12. CAN 물리 계층 vs 논리적 ID
- CAN_H, CAN_L 2가닥 전선이 **한 쌍으로 묶여 "버스 하나"**를 이룸 (차동 신호 방식, 노이즈에 강함)
- 이 버스 하나 위에 0x300, 0x301 같은 여러 ID의 메시지가 시간차를 두고 순차적으로 흘러다님
- 비유: 버스(전선 쌍) = 도로 하나, ID = 그 위를 지나다니는 차량 번호판
- `vcan0`은 이 물리적 버스를 소프트웨어로 흉내낸 가상 버스

### 13. CAN ID(0x300/0x301) 설계 원리 — 왜 명령/응답을 다른 ID로 나누나
- 0x300(명령)과 0x301(상태 응답)은 서로 다른 장치가 아니라, **같은 도어락에 대한 요청-응답 한 쌍**
- 실제 차량 CAN 설계에서도 "명령"과 "상태 피드백"을 별도 ID로 분리하는 게 관례
  - 이유 1: 버스 위 여러 메시지를 ID로만 구분 가능
  - 이유 2: 상태(0x301)는 여러 다른 ECU(계기판 등)가 동시에 구독할 수 있음. 명령과 같은 ID였다면 이 구분이 불가능해짐

### 14. blocking receive(`bus.recv(timeout=1.0)`)의 실무적 한계
- `bus.recv()`는 블로킹 함수 — 메시지 오거나 timeout(1초)까지 그 스레드가 멈춤
- 실제 차량 ECU는 실시간성이 중요해서 인터럽트 기반 수신을 씀 (블로킹 방식은 다른 이벤트 처리를 막을 위험)
- 지금 프로젝트는 "검증 시나리오"가 목적이라 순차 실행(blocking)이어도 로직 검증에는 문제없음 — 단, 이 한계를 알고 있다는 걸 README에 기록해두는 게 중요 (기술 부채를 "인지하고 기록하며 관리"하는 것 자체가 엔지니어링 판단력으로 평가받음)

### 15. `parsed["data"][0]`은 왜 첫 바이트만 꺼내나
CAN 데이터 필드는 원래 최대 8바이트까지 담을 수 있는 구조. `data[0]`은 "이 리스트의 0번째 자리가 명령값이라는 스펙 약속"에 따라 꺼내는 것이지, 잉여 데이터 방어가 주 목적은 아님 (부수 효과로 여러 바이트가 와도 첫 바이트만 안전하게 골라내는 효과는 있음).

---

## 다음 할 일
- `tests/test_mock_ecu.py` 테스트 시나리오 5개 작성
  1. LOCK 명령 → LOCKED 응답
  2. UNLOCK 명령 → UNLOCKED 응답
  3. LOCK→UNLOCK 연속 전송 → 최종 상태 확인
  4. 정의되지 않은 명령값 → 응답 없음
  5. 동일 명령 반복 전송 → 상태 유지(idempotency)
- 이후 GitHub Actions CI/CD, README 정리 (Limitations 섹션 포함: blocking receive 한계 등)
