import pytest
from src.can_handler import create_bus, send_message, receive_message, parse_message
from src.mock_ecu import MockDoorLockECU


def test_lock_command_returns_locked_status():
    """Sending LOCK_CMD (0x300) should update ECU state and respond with LOCKED (0x301)."""
    ecu_bus = create_bus()    # Bus used by the ECU (receives commands, sends status)
    test_bus = create_bus()   # Bus used by the test (sends commands, receives status)
    ecu = MockDoorLockECU(ecu_bus)

    send_message(test_bus, 0x300, [0x01])   # Send LOCK command
    ecu.process_command()                    # ECU processes it and responds

    raw_msg = receive_message(test_bus)
    assert raw_msg.data == bytearray([0x00])   # Expect LOCKED response
