from src.can_handler import create_bus, send_message, receive_message

def test_send_message_has_correct_id():
    bus = create_bus()
    sent = send_message(bus, 0x300, [0x01])
    assert sent.arbitration_id == 0x300
    assert sent.data == bytearray([0x01])

def test_receive_message_matches_sent():
    sender_bus = create_bus()
    receiver_bus = create_bus()
    send_message(sender_bus, 0x300, [0x02])
    received = receive_message(receiver_bus)
    assert received.arbitration_id == 0x300
    assert received.data == bytearray([0x02])

def test_receive_message_returns_none_when_nothing_sent():
    bus = create_bus()
    received = receive_message(bus, timeout=0.01)
    assert received is None
