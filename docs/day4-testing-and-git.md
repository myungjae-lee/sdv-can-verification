# Day 4 (계속) - test_mock_ecu.py 작성 및 Git/GitHub 개념 정리

## 오늘 한 것
- `tests/test_mock_ecu.py` 시나리오 1(LOCK → LOCKED) 작성 및 통과 확인
- import 경로 버그(`src.` 누락) 발견 및 수정
- Git/GitHub 관련 개념 질의응답
- CAN ID 분리 vs 버스 분리 개념 재확인

---

## Q&A 정리

### 1. Git과 GitHub의 차이
- **Git** = 프로그램(도구). 네 컴퓨터(WSL2 Ubuntu)에 설치되어 로컬에서 버전 관리를 수행
- **GitHub** = 웹사이트/서비스. Git 저장소를 인터넷에 올려두고 공유하는 플랫폼
- 비유: Git = 워드 프로그램, GitHub = 그 문서를 올려두는 구글 드라이브
- `git add`, `git commit`, `git push`는 전부 **Git 명령어**이며, 전부 터미널(로컬)에서 실행하는 것. `git push`를 실행하는 순간에만 인터넷을 통해 GitHub 서버로 데이터가 전송됨

### 2. `git add` → `git commit` → `git push`의 각 단계
```
[Working Directory] → [Staging Area] → [Local Repository] → [Remote(GitHub)]
       (수정 중)         git add            git commit           git push
```
- **`git add`**: "이 변경사항을 다음 커밋에 포함시킬 준비를 해라" (스테이징). `git status`로 스테이징 여부 확인 가능
- **`git commit -m "메시지"`**: 스테이징된 것들을 하나의 확정된 스냅샷으로 로컬 저장소(.git)에 기록. **아직 GitHub엔 안 올라감**
- **`git push`**: 로컬에 쌓인 커밋들을 GitHub 서버로 전송. 이게 끝나야 GitHub 웹페이지에서 보임
- `add`와 `commit`을 나누는 이유: 여러 파일을 고쳤을 때 관련 있는 것만 골라 하나의 의미 있는 커밋으로 묶기 위해서

### 3. bash `&&`의 의미
`git add ... && git commit ... && git push`
- "왼쪽 명령어가 성공(exit code 0)했을 때만 오른쪽 명령어 실행"
- 중간에 실패하면 뒤 명령어는 실행 안 됨 → 빈 커밋이나 잘못된 push 방지

### 4. `git log --oneline -3` 결과 해석
```
eacf57a (HEAD -> main, origin/main, origin/HEAD) Add MockDoorLockECU class...
```
- `HEAD -> main` = 로컬 브랜치 현재 위치
- `origin/main`, `origin/HEAD` = GitHub(원격) 저장소가 가리키는 지점
- 이 둘이 같은 커밋을 가리키면 → **로컬과 원격이 동기화됨(push 성공)**
- GitHub 웹 화면은 캐싱 때문에 최신 상태가 바로 안 보일 수 있음 → 터미널에서 `git log`로 확인하는 게 더 확실함

### 5. CAN ID 분리(0x300/0x301) vs 버스 분리(ecu_bus/test_bus) — 서로 다른 층위의 문제
처음엔 "0x300은 도어락 담당, 0x301은 라이트 담당"처럼 오해했었는데, 여러 차례 정정을 거쳐 최종 정리:

| 구분 | 목적 | 실제 차량에서도 통용되나 |
|---|---|---|
| **ID 분리** (0x300=명령, 0x301=상태) | 다른 ECU가 필요한 정보(상태)만 ID 기반으로 선택 구독 가능하게 함 | ✅ 통용됨 (실제 CAN 설계 관례) |
| **버스 분리** (`ecu_bus`, `test_bus`) | SocketCAN의 loopback(자기가 보낸 메시지가 자기한테도 들리는 현상) 회피 | ❌ 통용 안 됨 (python-can + vcan0 테스트 환경의 특수한 제약) |

**ID 분리 이유 - 왜 "속도 향상"이 아닌가:**
- 만약 0x300 하나로 명령/상태를 합쳤다면(flag 바이트 추가), 프레임이 1바이트 늘어나는 정도의 전송 시간 차이는 있지만 무의미한 수준
- 진짜 단점은 "연산 부담 증가": CAN 컨트롤러(하드웨어)는 보통 ID 기반 필터를 지원해서, ID만으로 불필요한 메시지를 하드웨어 단계에서 걸러낼 수 있음. ID를 합치면 이 하드웨어 필터링이 불가능해지고, **CPU(소프트웨어)가 매 메시지마다 flag를 직접 열어봐야 하는 부담**이 생김 — 이게 ID를 분리하는 실질적 이유

**버스 분리 이유 - loopback 문제:**
- 각 bus 객체는 여전히 각자 loopback을 일으킴 (분리해도 없어지지 않음)
- 하지만 "자기가 보낸 걸 자기가 다시 읽으려는 코드가 없으면" 실질적으로 문제 없음
- 지금 구조: `test_bus`로 0x300 보냄(loopback 발생하지만 아무도 안 읽음) → `ecu.process_command()`가 `ecu_bus`로 수신(다른 소켓이라 loopback과 무관) → `test_bus`로 0x301 수신(이번엔 ecu가 새로 보낸 것을 받는 것, loopback 아님)
- **실제 차량에서는 이런 고민 자체가 없음.** 도어락 ECU와 명령을 보내는 장치는 원래부터 서로 다른 물리적 장치니까, "내가 보낸 걸 내가 또 받는" 문제가 이렇게 부각되지 않음
- 지금 프로젝트에서 버스를 2개 쓴 이유: 하나의 Python 프로세스 안에서 "ECU 역할"과 "테스트(외부 장치) 역할"을 동시에 흉내내야 했기 때문. 즉 "기능 하나에 버스 2개가 항상 필요하다"는 결론은 틀림 — 필요한 건 "코드 안에서 흉내내는 역할 수만큼 연결을 나누는 것"

**이 구분에 의미가 있는 이유:**
- 검증하려는 핵심 로직("명령을 보내면 정확한 응답이 오는가")은 실제 차량 검증과 본질적으로 동일
- "왜 이렇게 설계했는지" 원인(loopback)과 해결(소켓 분리)의 인과관계를 정확히 설명할 수 있다는 것 자체가, 시뮬레이션 환경의 한계를 이해하고 우회한 엔지니어링 판단력을 보여줌

### 6. 모듈 import 경로 에러 (`ModuleNotFoundError: No module named 'can_handler'`)
**증상:** `test_mock_ecu.py`에서 `pytest tests/test_mock_ecu.py -v` 실행 시 `can_handler` 모듈을 못 찾는다는 에러 발생

**원인:** 실행 위치(`pwd` = 프로젝트 루트) 자체는 문제가 아니었음. **import 문에 파일의 실제 하위 폴더 경로를 안 적은 것**이 원인:
```python
# 문제였던 코드 (test_mock_ecu.py, src/mock_ecu.py 둘 다)
from can_handler import create_bus, ...   # src 폴더 안에 있는데 경로 명시 안 함

# 정상 동작하던 코드 (test_can_handler.py)
from src.can_handler import create_bus, ...   # src 폴더 경로를 정확히 명시
```
- `can_handler.py`는 실제로 `src/can_handler.py`에 위치
- pytest를 프로젝트 루트에서 실행하니, Python이 모듈을 찾는 기준점도 루트가 됨
- `src` 접두어 없이 `can_handler`만 쓰면 "루트 바로 밑"에서 찾다가 못 찾음 → `src.can_handler`로 정확한 경로를 명시해야 함

**고친 곳 2군데:**
1. `tests/test_mock_ecu.py` — `from src.can_handler import ...`, `from src.mock_ecu import ...`
2. `src/mock_ecu.py` 자체 내부에서도 `from can_handler import ...` → `from src.can_handler import ...`로 수정 (mock_ecu.py도 src 폴더 안에 있으니 같은 원리 적용)

**교훈:** 같은 폴더 구조를 가진 파일이라도, 파일마다 import 문에 경로를 일관되게 명시해야 함. 한 파일(`test_can_handler.py`)이 통과했다고 다른 파일도 같은 방식일 거라 가정하면 안 되고, 실제로 열어서 비교해봐야 원인을 정확히 찾을 수 있음.

---

## 완성된 테스트 (시나리오 1/5)

```python
import pytest
from src.can_handler import create_bus, send_message, receive_message, parse_message
from src.mock_ecu import MockDoorLockECU


def test_lock_command_returns_locked_status():
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()

    raw_msg = receive_message(test_bus)
    assert raw_msg.data == bytearray([0x00])
```

---

## 다음 할 일 (9/14~)
- 시나리오 2: UNLOCK 명령 → UNLOCKED 응답
- 시나리오 3: LOCK→UNLOCK 연속 전송 → 최종 상태 확인
- 시나리오 4: 정의되지 않은 명령값 → 응답 없음
- 시나리오 5: 동일 명령 반복 전송 → 상태 유지(idempotency)
- 이후 GitHub Actions CI/CD, README 정리
