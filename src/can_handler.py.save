import can

def create_bus(channel="vcan0", interface="socketcan"):
    """Connect to the CAN bus"""
    return can.interface.Bus(channel=channel, interface=interface)

def send_message(bus, arbitration_id, data):
    """Send a CAN message"""
    msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
    bus.send(msg)
    return msg

def receive_message(bus, timeout=1.0):
    """Receive a CAN message, waiting up to timeout seconds"""
    return bus.recv(timeout=timeout)

def parse_message(msg):
    """Extract ID and data from a received message"""
    if msg is None:
        return None
    return {"id": msg.arbitration_id, "data": list(msg.data)}
