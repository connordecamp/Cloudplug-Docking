from dataclasses import dataclass
import struct
from enum import Enum

class MessageCode(Enum):
    DISCOVER = 0
    DOCK_DISCOVER_ACK = 100
    CLOUDPLUG_DISCOVER_ACK = 200

@dataclass
class Message:
    code: int
    data: str
    

    def to_network_message(self):
        return struct.pack('!H254s', self.code, str.encode(self.data))

    