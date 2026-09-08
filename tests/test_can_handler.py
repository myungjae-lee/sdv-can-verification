from src.can_handler import create_bus, send_message

def test_send_message_has_correct_id():
    bus = create_bus()
    sent = send_message(bus, 0x300, [0x01])
    assert sent.arbitration_id == 0x300
    assert sent.data == bytearray([0x01])

