import pytest
from src.can_handler import create_bus, send_message, receive_message


def test_send_message_has_correct_id():
    """send_message should set the correct arbitration ID and data."""
    bus = create_bus()
    sent = send_message(bus, 0x300, [0x01])
    assert sent.arbitration_id == 0x300
    assert sent.data == bytearray([0x01])


def test_receive_message_matches_sent():
    """A message received on one bus should match what was sent on another (avoids loopback)."""
    sender_bus = create_bus()
    receiver_bus = create_bus()
    send_message(sender_bus, 0x300, [0x02])
    received = receive_message(receiver_bus)
    assert received.arbitration_id == 0x300
    assert received.data == bytearray([0x02])


def test_receive_message_returns_none_when_nothing_sent():
    """receive_message should return None if no message arrives within timeout."""
    bus = create_bus()
    received = receive_message(bus, timeout=0.01)
    assert received is None


def test_send_message_rejects_out_of_range_byte():
    """CAN data bytes must be 0-255; out-of-range values should raise ValueError."""
    bus = create_bus()
    with pytest.raises(ValueError):
        send_message(bus, 0x300, [0x123])
