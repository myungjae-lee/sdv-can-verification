import can

def create_bus(channel="vcan0", interface="socketcan"):
    """가상 CAN 버스에 연결한다"""
    return can.interface.Bus(channel=channel, interface=interface)

def send_message(bus, arbitration_id, data):
    """CAN 메시지를 전송한다"""
    msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
    bus.send(msg)
    return msg

def receive_message(bus, timeout=1.0):
    """CAN 메시지를 수신한다 (timeout 초 동안 기다리고, 없으면 None 반환)"""
    return bus.recv(timeout=timeout)

def parse_message(msg):
    """수신한 메시지에서 ID와 데이터를 꺼낸다"""
    if msg is None:
        return None
    return {"id": msg.arbitration_id, "data": list(msg.data)}
