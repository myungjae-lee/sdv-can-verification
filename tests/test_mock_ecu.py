import pytest
from src.can_handler import create_bus, send_message, receive_message, parse_message
from src.mock_ecu import MockDoorLockECU


def test_lock_command_returns_locked_status():
    """Sending LOCK_CMD (0x300) should update ECU state and respond with LOCKED (0x301)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()

    raw_msg = receive_message(test_bus)
    assert raw_msg.data == bytearray([0x00])


def test_unlock_command_returns_unlocked_status():
    """Sending UNLOCK_CMD (0x300) should update ECU state and respond with UNLOCKED (0x301)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x02])
    ecu.process_command()

    raw_msg = receive_message(test_bus)
    assert raw_msg.data == bytearray([0x01])

def test_consecutive_lock_unlock_final_state():
    """Sending LOCK then UNLOCK consecutively should result in final state UNLOCKED."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    # LOCK
    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()
    receive_message(test_bus)   # Consume LOCK response, not checked here

    # UNLOCK
    send_message(test_bus, 0x300, [0x02])
    ecu.process_command()
    raw_msg = receive_message(test_bus)   # Check the final response

    assert raw_msg.data == bytearray([0x01])   # Final state should be UNLOCKED
    assert ecu.state == MockDoorLockECU.UNLOCKED  # Double-check internal state directly


def test_undefined_command_produces_no_response():
    """Sending an undefined command value should not produce any response (fault case)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x99])
    ecu.process_command()

    raw_msg = receive_message(test_bus, timeout=0.1)
    assert raw_msg is None


def test_repeated_lock_command_is_idempotent():
    """Sending LOCK_CMD twice in a row should keep the state as LOCKED (idempotency)."""
    ecu_bus = create_bus()
    test_bus = create_bus()
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()
    raw_msg1 = receive_message(test_bus)   # First response
    assert raw_msg1.data == bytearray([0x00])

    send_message(test_bus, 0x300, [0x01])
    ecu.process_command()
    raw_msg2 = receive_message(test_bus)   # Second response (should be identical)
    assert raw_msg2.data == bytearray([0x00])
