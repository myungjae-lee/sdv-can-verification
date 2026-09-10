from src.can_handler import create_bus, send_message, receive_message, parse_message


class MockDoorLockECU:
    """Simulated door lock ECU that responds to CAN commands."""

    # Status values (sent in 0x301 response)
    LOCKED = 0x00
    UNLOCKED = 0x01

    # Command values (received in 0x300 request)
    LOCK_CMD = 0x01
    UNLOCK_CMD = 0x02

    def __init__(self, bus):
        self.state = MockDoorLockECU.LOCKED  # Default state: locked (fail-safe)
        self.bus = bus

    def process_command(self):
        """Receive a command (0x300), update state, and send a status response (0x301)."""
        raw_msg = receive_message(self.bus)
        parsed = parse_message(raw_msg)

        if parsed is None:
            return  # No message received within timeout

        if parsed["id"] == 0x300:
            cmd = parsed["data"][0]

            if cmd == MockDoorLockECU.LOCK_CMD:
                self.state = MockDoorLockECU.LOCKED
            elif cmd == MockDoorLockECU.UNLOCK_CMD:
                self.state = MockDoorLockECU.UNLOCKED
            else:
                return  # Undefined command - no response sent (fault case)

            send_message(self.bus, 0x301, [self.state])
