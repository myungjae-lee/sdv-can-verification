# Day 3 (계속): First pytest test — assert, bytearray, ModuleNotFoundError

## 오늘 이어서 한 일

`send_message` 함수가 실제로 의도한 대로 동작하는지 pytest로 자동 검증하는
첫 테스트를 작성했다. 정답을 받지 않고 힌트만으로 직접 짜면서, 중간에
막힌 부분(assert 개념, 자료형 불일치, 모듈 인식 에러)을 하나씩 스스로 확인했다.

---

## 개념 1: assert의 정확한 동작

`assert 조건`은 "조건이 참이면 통과, 거짓이면 즉시 에러를 내고 멈춘다"는 명령어다.

```python
assert 1 == 1   # 통과, 다음 줄로 넘어감
assert 1 == 2   # AssertionError 발생, 프로그램 중단
```

`if`와의 차이:
- `if`는 조건이 거짓이어도 그냥 다음 줄로 넘어간다 (선택지를 만드는 것)
- `assert`는 조건이 거짓이면 그 자리에서 즉시 멈춘다 (반드시 이래야 한다고 못 박는 것)

테스트에서 `assert`를 쓰는 이유: 사람이 눈으로 매번 확인하지 않아도,
"내가 의도한 값이 실제로 나왔는지"를 기계가 자동으로 걸러내게 하기 위함.

---

## 개념 2: 테스트가 "당연한 것"까지 확인하는 이유

`send_message(bus, 0x300, [0x01])`를 호출한 뒤
`assert sent.arbitration_id == 0x300`으로 확인하는 것을 두고,
"내가 이미 0x300을 넣었으니 당연히 0x300이 나오는 거 아닌가?"라는 의문이 들었다.

답: 당연해 보이지만, 함수 내부에 실수(오타, 잘못된 로직)가 있으면
넣은 값과 실제 결과가 달라질 수 있다. 이런 실수를 사람이 눈으로
매번 놓치지 않고 기계가 자동으로 잡아내게 하는 것이 테스트의 목적이다.

또한 이 테스트는 "0x300만 취급하는 함수"를 검증하는 게 아니라,
"이번 테스트 케이스에서 0x300이라는 값을 넣었을 때 제대로 반영되는지"를
확인하는 것이다. 함수 자체는 어떤 ID를 넣어도 동작하는 범용 함수다.

---

## 개념 3: bytearray 자료형 실험

### 실험 배경

`sent.data == [0x01]`로 비교했더니 실패했다. 이유를 확인하기 위해
`type(sent.data)`를 직접 실행해보니 `<class 'bytearray'>`가 나왔다.
즉 `send_message`가 보낸 데이터는 리스트가 아니라 bytearray 타입으로
저장된다는 것을 실험으로 확인했다.

### bytearray()의 입력값에 따른 동작 차이

`bytearray()`는 입력 자료형에 따라 완전히 다르게 동작한다.

```python
bytearray(0x01)      # 결과: bytearray(b'\x00')
bytearray([0x01])    # 결과: bytearray(b'\x01')
```

- 정수를 넣으면: "그 숫자만큼의 크기를 가진, 0으로 채워진 빈 바이트 묶음을 만들어라"는 뜻
  (예: `bytearray(3)` → 크기 3짜리, 전부 0인 바이트 묶음)
- 리스트를 넣으면: "리스트 안의 값들을 그대로 채워 넣어라"는 뜻

`0x01`은 16진수로 쓴 정수 1일 뿐이라, `bytearray(0x01)`은 `bytearray(1)`과 같고
"내용값 1"이 아니라 "크기 1"로 해석되어 예상과 다른 결과(0으로 채워짐)가 나온다.

에러 없이 조용히 다른 결과를 내기 때문에, 이런 실수는 assert로 자동 검증하지
않으면 놓치기 쉽다는 것을 직접 확인한 사례.

### 최종 올바른 비교

```python
assert sent.data == bytearray([0x01])
```

양쪽을 같은 자료형(bytearray)으로 맞춰야 값 비교가 정확히 이루어진다.

---

## 개념 4: ModuleNotFoundError 디버깅 과정

### 증상

파이썬 대화형 모드(`python3`)에서는 `from src.can_handler import ...`가
문제없이 작동했는데, pytest로 같은 import문이 든 테스트 파일을 실행하니
`ModuleNotFoundError: No module named 'src'` 에러가 발생했다.

### 해결 과정

`src` 폴더와 `tests` 폴더에 각각 빈 파일 `__init__.py`를 추가하니 해결됨.

```bash
touch src/__init__.py
touch tests/__init__.py
```

`__init__.py`가 있으면 파이썬(및 pytest)이 해당 폴더를 "패키지"로 인식해서
`src.can_handler`처럼 점(.)으로 경로를 지정하는 import가 가능해진다.
대화형 모드는 이 파일이 없어도 현재 작업 폴더 기준으로 알아서 찾아주지만,
pytest는 더 엄격하게 패키지 구조를 요구한다는 것을 실전에서 확인함.

---

## 완성된 첫 테스트

```python
from src.can_handler import create_bus, send_message

def test_send_message_has_correct_id():
    bus = create_bus()
    sent = send_message(bus, 0x300, [0x01])
    assert sent.arbitration_id == 0x300
    assert sent.data == bytearray([0x01])
```

실행 결과:

```
tests/test_can_handler.py::test_send_message_has_correct_id PASSED [100%]
1 passed in 0.03s
```

---

## 오늘 완료 체크리스트

- [x] assert의 정확한 동작 원리 이해 (if와의 차이)
- [x] "당연해 보이는 것도 검증해야 하는 이유" 스스로 정리
- [x] bytearray(정수) vs bytearray(리스트) 차이를 직접 실험으로 확인
- [x] ModuleNotFoundError를 `__init__.py` 추가로 직접 해결
- [x] 첫 pytest 테스트 작성 및 통과 확인, GitHub 커밋

## 다음 단계 (예고)

`receive_message` 함수에 대한 테스트도 같은 방식으로 작성.
이후 정상 케이스 외에 실패/이상 케이스(잘못된 ID, timeout 등) 테스트 추가 예정.
