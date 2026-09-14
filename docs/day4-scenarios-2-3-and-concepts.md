# Day 4 (계속, 9/14) - 시나리오 2·3 구현 및 CAN/Git 개념 정리

## 오늘 한 것
- `tests/test_mock_ecu.py` 시나리오 2(UNLOCK → UNLOCKED), 시나리오 3(LOCK→UNLOCK 연속 전송 → 최종 상태) 작성 및 통과 확인 (누적 3/5)
- README 초안 발견 및 정리 방향 결정 (Git 이력 확인)
- CAN 프로토콜 배경지식(토폴로지, 물리 계층, 프레임 구조, ID 마스킹) 질의응답
- pytest assert와 실제 ECU 펌웨어의 차이 정리

---

## 구현 내용

### 시나리오 2: UNLOCK → UNLOCKED
```python
def test_unlock_command_returns_unlocked_status():
    """Sending UNLOCK_CMD (0x300) should update ECU state and respond with UNLOCKED (0x301)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x02])
    ecu.process_command()

    raw_msg = receive_message(test_bus)
    assert raw_msg.data == bytearray([0x01])
```
- 처음엔 `[0x02]`(UNLOCK_CMD)와 `[0x02]`(잘못된 상태값)를 혼동 — 명령값(UNLOCK_CMD=0x02)과 상태값(UNLOCKED=0x01)은 다른 스펙이라는 걸 다시 확인함

### 시나리오 3: 연속 전송 → 최종 상태 확인
```python
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
    raw_msg = receive_message(test_bus)   # Check the final response

    assert raw_msg.data == bytearray([0x01])   # Final state should be UNLOCKED
    assert ecu.state == MockDoorLockECU.UNLOCKED  # Double-check internal state directly
```
- 이 시나리오의 목적: "한 번의 명령"만 테스트해서는 못 잡는, **연속 호출에서만 드러나는 버그**(예: 두 번째 호출부터 상태 갱신이 씹히는 경우)를 검증하기 위함
- 중간 LOCK 응답은 `receive_message`로 비워내기만 하고 검증 안 함(이미 시나리오 1에서 확인됨) — 이 시나리오는 "최종 상태"에만 집중해 중복 검증을 피함
- 응답 메시지(`raw_msg.data`)와 내부 상태(`ecu.state`)를 이중으로 확인 — 서로 다른 것을 검증하므로(통신 계층 vs 내부 로직) 의미 있는 이중 확인임

---

## Q&A 정리

### 1. `assert`(테스트 검증 코드)가 실제 ECU 성능에 영향을 주는가
- **아니다.** `assert`는 `pytest`가 테스트를 실행할 때만 도는 코드지, `MockDoorLockECU` 클래스(시뮬레이션되는 "ECU 로직") 안에 포함되는 게 아님
- 비유: 공장 품질 검사(테스트) vs 출고된 제품(실제 펌웨어) — 검사 장비가 제품 안에 들어있지 않듯, 테스트 코드도 실제 배포 코드에 포함 안 됨
- **실제 양산 ECU(C/C++ 임베디드 펌웨어)라면 다름:** 검증 코드를 펌웨어에 넣지 않는 게 원칙이며, 개발 단계에서 별도 테스트 환경(HIL 등)으로 검증 후 검증된 로직만 최종 펌웨어에 포함시킴. 최소한의 런타임 안전 체크가 필요한 경우에도 저용량 환경에서는 자원 제약을 고려해 최소화해야 함
- 결론: 지금은 "무엇을, 왜 검증해야 하는지"를 배우는 단계이고, "어떻게 자원 효율적으로 실제 임베디드 환경에 이식할지"는 완전히 별개의 과제

### 2. README 파일이 갑자기 길어져 있던 이유
- `git diff README.md`로 확인한 결과, GitHub에 커밋되어 있던 원래 README는 한 줄짜리 소개문뿐이었음
- 로컬 파일에 있던 긴 버전(Purpose, Structure, Completed So Far 등)은 예전에 다른 탭에서 작성해 로컬에 저장만 해두고 아직 커밋하지 않은 상태였음
- **커밋 타이밍 판단:** 지금 바로 README를 고쳐서 커밋하기보다("Next Steps"에 이미 완료된 Mock ECU 구현이 여전히 "예정"으로 잘못 적혀있었음), 오늘 예정된 나머지 작업(시나리오 2, 3)까지 다 끝낸 뒤 최종 상태를 한 번에 반영해서 커밋하는 것이 더 나은 방향으로 결정함 — 같은 파일을 하루에 여러 번 고쳐 커밋하는 것보다, 완결된 시점에 한 번에 정리하는 게 히스토리가 깔끔함

### 3. `__init__.py`의 역할 재확인
- `src/__init__.py`와 `tests/__init__.py`는 각자 자기 폴더를 "패키지"로 표시하는 역할 — 서로 다른 파일이지만 하는 일은 동일
- GitHub에서 파일을 열면 "0 lines, 0 Bytes"로 보이는 게 정상 — 빈 파일인 게 의도된 것이며 코드를 채울 필요 없음

### 4. WSL 재부팅 후 다시 해야 하는 것
```bash
sudo ip link add dev vcan0 type vcan   # vcan0은 재부팅하면 사라짐
sudo ip link set up vcan0
cd ~/sdv-can-verification
git status                              # 로컬/원격 동기화 상태 확인 습관
git log --oneline -3
```

### 5. CAN-FD로 프로젝트 방향을 바꿀 필요가 있는가
- 결론: 바꿀 필요 없음. 이 프로젝트의 목적은 "CAN-FD라는 최신 규격 자체"가 아니라 "CAN 통신 검증 방법론"(ID 기반 명령/응답 분리, 상태 관리, pytest 자동 검증) 습득이며, 이는 Classic CAN이든 CAN-FD든 거의 동일하게 적용됨
- python-can은 CAN-FD도 지원해 나중에 확장이 쉬움 (`is_fd=True` 옵션 추가 정도)
- 실무에서도 바디 제어(도어락 등) 저속 신호는 Classic CAN을 그대로 쓰는 경우가 많아 주제 자체가 부적절하지 않음
- README "Future Improvements"에 "CAN-FD 확장 가능성 인지" 정도만 한 줄 언급하는 것으로 충분

### 6. CAN 네트워크 토폴로지 - Bus 방식
- CAN은 여러 네트워크 구조(Bus, Ring, Star, Tree) 중 **Bus 토폴로지**를 사용 — 하나의 공통 선(버스)에 여러 노드가 나란히 연결되는 구조
- `vcan0`이 이 "공통 버스"에 해당하며, `ecu_bus`/`test_bus`는 같은 버스에 연결된 서로 다른 참가자(노드)
- CAN 미적용 시 각 장치를 개별 배선(point-to-point)으로 연결해야 했던 것을, CAN 적용으로 하나의 공용 버스에 묶어 배선을 단순화함

### 7. CAN_High/Low 선을 꼬아놓는(twisted pair) 이유
- CAN은 차동 신호(differential signaling) 방식 — 두 선의 "전압 차이"로 데이터를 표현
- 두 선을 꼬아놓으면 외부 전자기 노이즈가 양쪽 선에 거의 동일하게 유도되어, 전압 차이(신호) 자체는 상쇄되지 않고 노이즈만 상쇄되는 효과
- 안 꼬면 두 선이 노이즈원으로부터 비대칭적 영향을 받을 수 있음

### 8. CAN 메시지 프레임 구조 - 프로토콜 표준 vs SocketCAN
- SOF, ID(12bit), Control(DLC 포함), Data(최대 8byte), CRC, ACK, EOF로 구성된 프레임 구조는 **CAN 프로토콜 표준 자체**이며 모든 CAN 구현체(운영체제/라이브러리 무관)에 공통 적용됨
- SocketCAN(리눅스 커널)이나 python-can은 이 표준 위에서 동작하는 소프트웨어 계층 — CRC 계산, ACK 확인 같은 저수준 디테일을 자동으로 처리해주기 때문에, 우리 코드에서는 ID와 Data만 다루면 됨

### 9. ID 마스킹(masking) - 하드웨어 필터
- CAN 컨트롤러가 "필터 ID + 마스크"로 특정 비트만 비교해서 관련된 ID 대역을 한 번에 걸러내는 필터링 방식 (예: 마스크로 하위 비트를 무시하면 0x300~0x30F까지 한 번에 필터링 가능)
- 지금 프로젝트는 이 하드웨어 마스킹을 쓰지 않고, `receive_message`로 모든 메시지를 받은 뒤 `parse_message` 이후 소프트웨어(`if parsed["id"] == 0x300`)로 직접 걸러내는 방식 — 이전에 정리한 "ID 분리로 인한 소프트웨어 필터링 부담"이 실제로 이렇게 구현되어 있음
- README "Future Improvements"에 "하드웨어 ID 마스킹 필터 적용 시 CPU 부담 감소 가능" 언급할 만한 포인트

### 10. CAN의 보안 구조적 한계 (참고 수준)
- CAN은 인증(authentication) 메커니즘이 기본적으로 없어, 버스에 물리적으로 접근 가능하면 누구나 임의 ID로 메시지를 보낼 수 있는 구조적 특성이 있음
- 구체적인 공격 기법은 다루지 않되, "인증 계층 부재"라는 구조적 한계는 README "Limitations"에 언급 가능한 포인트 (예: 실제 환경에서는 SecOC 같은 보안 계층이 별도로 필요)

---

## 커밋 이력 (오늘)
```
Add UNLOCK command test scenario
Add consecutive LOCK-UNLOCK test scenario
```

## 다음 할 일
- 시나리오 4: 정의되지 않은 명령값 → 응답 없음
- 시나리오 5: 동일 명령 반복 전송 → 상태 유지(idempotency)
- 전체 시나리오 완료 후 README를 최신 상태로 한 번에 정리 (Completed So Far, Next Steps 갱신 + Limitations/Future Improvements 섹션에 오늘 정리한 CAN-FD, 마스킹, blocking receive, 보안 한계 등 반영)
- 이후 GitHub Actions CI/CD 파이프라인 구축
