# sdv-can-verification

Mini project simulating a door lock ECU over a virtual CAN bus with automated test verification (pytest, CI).

## Purpose

To understand and practice the concepts behind "SIL (Software-In-the-Loop) verification," "Plant Model
development," and "Test Case development" mentioned in SDV integration verification job postings, this
project implements a small-scale CAN communication verification environment using a personal PC and
virtual CAN (vcan).

## Status: Core Verification Complete

All 5 planned test scenarios for the Mock Door Lock ECU are implemented and passing (9/9 tests total).
See `docs/` for detailed learning notes on each development step.

## Structure

```
sdv-can-verification/
├── src/
│   ├── can_handler.py       # CAN bus connection, send/receive/parse functions
│   └── mock_ecu.py          # Mock door lock ECU (state machine)
├── tests/
│   ├── test_can_handler.py  # CAN communication unit tests (4)
│   └── test_mock_ecu.py     # ECU behavior/verification scenarios (5)
├── docs/                    # Development log and concept notes per step
├── .github/workflows/       # CI: syntax check + test collection
└── README.md
```

## Environment

- Python 3, python-can, pytest
- Linux virtual CAN (vcan0) via SocketCAN
- Developed on WSL2 Ubuntu

## CAN Message Spec

| ID | Direction | Meaning |
|---|---|---|
| 0x300 | Test → ECU | Command (LOCK=0x01, UNLOCK=0x02) |
| 0x301 | ECU → Test | Status response (LOCKED=0x00, UNLOCKED=0x01) |

## Test Scenarios (Mock ECU)

1. LOCK command → LOCKED status response
2. UNLOCK command → UNLOCKED status response
3. Consecutive LOCK → UNLOCK → final state check
4. Undefined command value → no response (fault case)
5. Repeated identical command → idempotent state

```bash
pytest -v
# 9 passed
```

## CI

GitHub Actions runs on every push to `main`. Because vcan requires a Linux kernel module that
isn't available in cloud runner containers, the pipeline does not execute the CAN tests directly.
Instead it checks:

- Python syntax (`py_compile`)
- Test collection / import integrity (`pytest --collect-only`)

Actual test execution (`pytest -v`, including vcan-dependent scenarios) is run locally.
This split reflects a common real-world constraint: hardware/kernel-dependent tests often can't
run on generic CI infrastructure and need a dedicated runner or local/target environment instead.

## Design Notes

- **CAN ID separation (0x300 command / 0x301 status)**: lets other ECUs subscribe only to the
  IDs they need via hardware ID filtering, instead of every node parsing every frame.
- **Two separate bus handles in tests (`ecu_bus`, `test_bus`)**: works around SocketCAN loopback
  (a process hears its own sent frames) in this single-process test setup. This is a test-harness
  detail, not a real-vehicle constraint — on a real bus, the ECU and the commanding device are
  separate physical nodes.

## How to Run

```bash
# Set up virtual CAN interface (Linux)
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Install dependencies
pip install python-can pytest --break-system-packages

# Run tests
pytest -v
```
