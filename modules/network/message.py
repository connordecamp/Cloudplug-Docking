from dataclasses import dataclass
import struct
from enum import Enum

class MessageCode(Enum):
    DISCOVER = 0

    # Docking Station Codes
    DOCK_DISCOVER_ACK = 100
    
    CLONE_SFP_MEMORY = 101
    CLONE_SFP_MEMORY_ERROR = 102
    CLONE_SFP_MEMORY_SUCCESS = 103

    # Cloudplug Codes
    CLOUDPLUG_DISCOVER_ACK = 200

@dataclass
class Message:
    code: MessageCode
    data: str
    

    def to_network_message(self) -> bytes:
        return struct.pack('!H254s', self.code.value, str.encode(self.data))

def unpackRawBytes(raw_msg: bytes) -> Message:
    code, data = struct.unpack('!H254s', raw_msg)
    code = MessageCode(code)
    sent_cmd = Message(code, str(data, 'utf-8').strip('\x00'))

    return sent_cmd
    