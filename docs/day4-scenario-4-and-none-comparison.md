# Day 4 (계속, 9/15) - 시나리오 4 구현 및 None/is 비교 개념 정리

## 오늘 한 것
- `tests/test_mock_ecu.py` 시나리오 4(정의되지 않은 명령값 → 응답 없음) 작성 및 통과 확인 (누적 4/5)
- WSL2 프로젝트 폴더를 Windows 탐색기에서 여는 방법 확인
- `None` 비교(`is` vs `==`), 테스트에서의 timeout 사용 이유, CPython 정수 캐싱 등 개념 정리

---

## 구현 내용

### 시나리오 4: 정의되지 않은 명령값 → 응답 없음
```python
def test_undefined_command_produces_no_response():
    """Sending an undefined command value should not produce any response (fault case)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x99])
    ecu.process_command()

    raw_msg = receive_message(test_bus, timeout=0.1)
    assert raw_msg is None
```
- `mock_ecu.py`의 `process_command`에서 정의 안 된 명령값이 들어오면 `else: return`으로 응답 전송 없이 종료하는 분기를 검증
- timeout을 짧게(`0.1`) 설정한 이유: "응답이 없다"를 확인하려면 어느 정도 기다려봐야 하지만, 테스트 실행 속도를 위해 기본값(1.0초)보다 짧게 줌

---

## Q&A 정리

### 1. 테스트 코드에서 짧은 timeout을 쓰는 것 vs 실제 ECU의 blocking 문제 — 다른 맥락
- 이전에 지적했던 "blocking이 문제"라는 건 **실제 ECU 펌웨어**(`process_command`)가 매번 오래 기다리면 다른 이벤트 처리를 못 한다는 우려였음
- 지금 테스트 코드에서 짧은 timeout을 쓰는 건 **검증 목적**으로, "응답이 안 온다"를 확인하려면 어쩔 수 없이 조금은 기다려봐야 하기 때문 — 대신 너무 길게 기다리지 않도록 시간을 짧게 설정하는 것뿐
- 실제 배포 로직에 blocking을 쓰는 것과, 테스트 코드에서 검증용으로 짧은 timeout을 쓰는 것은 완전히 다른 층위의 이야기

### 2. `bytearray(None)`과 `raw_msg.data` 접근이 왜 잘못됐는가
- `bytearray(None)`은 그 자체로 `TypeError` — `bytearray()`는 숫자/리스트/바이트 문자열 등을 받지 `None`은 받을 수 없음
- `raw_msg`가 `None`인 상태에서 `raw_msg.data`에 접근하면 `AttributeError` 발생 — "raw_msg.data가 None이 된다"가 아니라, "None에는 애초에 `.data`라는 속성 자체가 없어서 접근 시도 자체가 실패하고 프로그램이 멈추는 것"이 정확한 인과관계
- 올바른 형태: 응답이 아예 안 왔다면 `raw_msg` 자체가 `None`이므로, `raw_msg is None`으로 직접 확인해야 함

### 3. `is`와 `==`의 차이
- `==`: 값이 같은지 비교
- `is`: 완전히 같은 객체(메모리상 동일한 참조)를 가리키는지 비교 — "같은 포인터를 가리키는가"와 같은 개념
- `None`은 파이썬에서 프로그램 전체에 걸쳐 **언어 명세로 유일성이 보장되는 단 하나의 객체**이므로, `is None` 비교가 항상 안전하고 관례적으로 권장됨

### 4. "값이 같으면 항상 같은 객체를 가리키는가?" - 아니다 (CPython 정수 캐싱은 예외적 최적화)
- `a = 1; b = 1`일 때 `a is b`가 `True`로 나오는 건, CPython이 -5~256 범위의 작은 정수를 미리 만들어두고 재사용(캐싱)하는 **구현체 최적화**일 뿐
- `a = 1000; b = 1000`처럼 캐싱 범위를 벗어나면 `a == b`는 `True`지만 `a is b`는 `False` — 값은 같아도 서로 다른 객체로 생성됨
- 리스트처럼 가변 객체는 내용이 같아도(`[1,2,3] == [1,2,3]`) 항상 별개의 객체(`is`는 `False`)
- 결론: "값이 같으면 같은 객체"라는 규칙은 파이썬 언어가 보장하는 게 아니라 특정 타입에 대한 구현 세부사항일 뿐이므로, `None`처럼 언어가 유일성을 보장하는 값이 아니면 `is`로 값 비교를 하면 안 됨

### 5. WSL2 프로젝트 폴더를 Windows 탐색기에서 여는 방법
- 탐색기 주소창에 `\\wsl.localhost\Ubuntu\home\사용자명\프로젝트명` 입력
- 또는 최신 Windows라면 탐색기 왼쪽 사이드바의 "Linux" → "Ubuntu" → home → 사용자명 순으로 진입 가능
- 한 번 들어간 폴더는 즐겨찾기에 고정해두면 다음부터 바로 접근 가능

### 6. timeout 값(1.0초 vs 0.1초)을 각각 그렇게 정한 이유
- `receive_message`의 기본값 `timeout=1.0`: 정상적인 상황에서 실제로 메시지가 도착하길 기다리는 용도. 너무 짧으면 정상 통신 지연도 놓칠 위험, 너무 길면 불필요하게 오래 멈춤 — 1초는 통신 지연을 충분히 커버하면서 무난한 관례적 기본값
- 시나리오 4의 `timeout=0.1`: "응답이 없다"를 확인하는 용도라 애초에 응답이 안 올 걸 알고 있는 상황. 짧게 잡아 테스트 실행 속도를 높이는 게 목적. 다만 극단적으로 짧으면(예: 0.001초) 정상적인 처리 지연 때문에 실제 응답을 놓칠 위험이 있어 피해야 함
- 결론: 두 값 다 "반드시 이래야 하는" 절대적 정답은 없고, 상황의 목적(정상 대기 vs 결함 확인)에 맞춘 실용적 선택

---

## 커밋 이력 (오늘)
```
Add fault case test for undefined command
```

## 다음 할 일
- 시나리오 5: 동일 명령 반복 전송 → 상태 유지(idempotency) (누적 5/5 예정)
- 전체 시나리오 완료 후 README 최종 정리
- GitHub Actions CI/CD 파이프라인 구축
