# Day 1-2: Environment Setup and CAN Basics

## 오늘까지 한 일 (큰 그림)

1. 리눅스(WSL/Ubuntu)를 윈도우 안에 설치
2. Git 설치 및 GitHub 레포 연동
3. 파이썬 도구(python-can, pytest) 설치
4. 가상 CAN 버스(vcan0) 생성
5. candump/cansend로 실제 메시지 송수신 실습

---

## 1. 리눅스 설치 (WSL/Ubuntu)

```bash
wsl --install -d Ubuntu
```

윈도우 안에 Ubuntu(리눅스)를 설치. CAN 시뮬레이션은 리눅스 전용 기능이라 필요했음.

---

## 2. Git 설치 및 GitHub 연동

| 명령어 | 의미 |
|---|---|
| `sudo apt install git -y` | Git 설치 |
| `git config --global user.name "..."` | 커밋 기록에 남길 작성자 이름 설정 |
| `git config --global user.email "..."` | 작성자 이메일 설정 |
| `git clone https://github.com/myungjae-lee/sdv-can-verification.git` | GitHub 레포를 내 컴퓨터로 복사 |
| `cd sdv-can-verification` | 그 폴더로 이동 |

**겪었던 문제**: 처음에 `/mnt/c/Windows/system32`(윈도우 영역)에서 clone을 시도해 권한 오류 발생.
`cd ~`로 리눅스 홈 디렉토리(`/home/inka`)로 이동한 후 재시도하여 해결.

---

## 3. 파이썬 도구 설치

```bash
pip install python-can pytest --break-system-packages
```

- `python-can`: CAN 통신을 파이썬으로 다루게 해주는 라이브러리
- `pytest`: 코드 동작을 자동으로 검사하는 테스트 도구
- `--break-system-packages`: 시스템 파이썬 보호 설정을 우회하는 옵션 (개인 개발 환경에서는 안전)

---

## 4. 가상 CAN 버스 생성

```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

- `modprobe vcan`: 리눅스 커널에 가상 CAN 기능을 켜라는 지시
- `ip link add dev vcan0 type vcan`: `vcan0`이라는 가상 CAN 통신선 생성
- `ip link set up vcan0`: 생성한 통신선을 활성화(전원 ON)

**확인**: `ip link show vcan0` 결과에 `UP` 상태가 보이면 성공.

**주의**: 컴퓨터/WSL을 재시작하면 vcan0 설정이 초기화되므로, 다음 작업 시작 시 위 3줄을 다시 입력해야 함.

---

## 5. CAN 메시지 실습 (candump / cansend)

### 도구 설치

```bash
sudo apt install can-utils -y
```

### 기본 개념

- `candump vcan0`: vcan0에 도착하는 메시지를 계속 지켜보며 화면에 출력 (터미널 창 하나 필요)
- `cansend vcan0 <ID>#<데이터>`: vcan0으로 메시지 전송 (다른 터미널 창에서 실행)

### 실습 1: 메시지 전송 및 수신 확인

터미널 A: `candump vcan0` 실행 후 대기
터미널 B: `cansend vcan0 123#DEADBEEF` 실행

터미널 A에 아래처럼 출력됨:
```
vcan0  123   [4]  DE AD BE EF
```

- `123`: CAN ID
- `[4]`: 데이터 길이 4바이트
- `DE AD BE EF`: 실제 전송된 데이터

### 실습 2: 다양한 ID/데이터 길이 관찰

```bash
cansend vcan0 456#11223344
cansend vcan0 100#FF
cansend vcan0 7FF#0102030405060708
```

**관찰 결과**: ID와 데이터 길이가 각각 다르게 표시됨 (`[1]`, `[4]`, `[8]`).
→ CAN 메시지는 "ID + 가변 길이 데이터"로 구성된다는 것을 확인.

### 실습 3: 같은 ID로 여러 번 전송

```bash
cansend vcan0 300#01
cansend vcan0 300#02
cansend vcan0 300#01
```

**관찰 결과**: candump 화면에 순서대로 3줄이 기록됨.
→ 같은 ID라도 데이터 값이 다르면 별개의 메시지로 기록된다는 것을 확인.
→ 프로젝트에서 `0x300`을 도어락 명령 ID로 쓸 계획이므로, LOCK(01)/UNLOCK(02) 명령을 이 방식으로 보낼 예정.

### 타임스탬프 확인 (추가 학습)

기본 `candump vcan0`에는 시간 정보가 안 보임. 아래 옵션으로 확인 가능:

```bash
candump -tz vcan0
```

`-tz`: candump 시작 시점을 0초로 해서 경과 시간을 표시.

---

## 아직 세팅되지 않은 것 (오해 방지용 메모)

`0x300`, `0x301` ID는 Mock ECU 설계 단계에서 "이렇게 쓰기로 계획한 것"일 뿐,
아직 그 메시지를 받아서 실제로 반응하는 프로그램(Mock ECU)은 코드로 작성하지 않았다.
지금까지는 "메시지가 물리적으로 전달되는지"만 확인한 단계이고,
"메시지를 받으면 상태가 바뀌는 로직"은 다음 단계(Python 스크립트 작성)에서 만든다.

---

## 완료 체크리스트

- [x] WSL/Ubuntu 설치
- [x] Git 설치 및 GitHub 레포 연동
- [x] Python, python-can, pytest 설치
- [x] 가상 CAN 버스(vcan0) 생성 및 활성화
- [x] can-utils 설치
- [x] cansend/candump로 메시지 송수신 실습 (ID/데이터 길이 다양하게)
- [x] 같은 ID 반복 전송 시 기록 순서 확인

## 다음 단계 (3일차 예고)

Python으로 CAN 메시지를 직접 만들고 받는 스크립트(`can_handler.py`) 작성.
지금까지 터미널 명령어로 손으로 했던 것을, 코드로 자동화하는 단계.
