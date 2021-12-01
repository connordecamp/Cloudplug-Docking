from dataclasses import dataclass
import struct
from enum import Enum
from typing import List

class MessageCode(Enum):
    DISCOVER = 0

    # Docking Station Codes
    DOCK_DISCOVER_ACK           = 100
    CLONE_SFP_MEMORY            = 101
    CLONE_SFP_MEMORY_ERROR      = 102
    CLONE_SFP_MEMORY_SUCCESS    = 103
    READ_SFP_REGISTERS          = 125
    READ_SFP_REGISTERS_ACK      = 126
    DIAGNOSTIC_INIT_A0          = 127
    DIAGNOSTIC_INIT_A0_ACK      = 128
    DIAGNOSTIC_INIT_A2          = 129
    DIAGNOSTIC_INIT_A2_ACK      = 130
    REAL_TIME_REFRESH           = 131
    REAL_TIME_REFRESH_ACK       = 132
    I2C_ERROR                   = 150

    # Cloudplug Codes
    CLOUDPLUG_DISCOVER_ACK = 200

MESSAGE_BYTES = 256
SIZEOF_H = 2

@dataclass
class Message:
    code: MessageCode
    data_str: str

    def to_network_message(self) -> bytes:
        return struct.pack('!H254s', self.code.value, str.encode(self.data_str))

@dataclass
class ReadRegisterMessage(Message):
    page_number:      int
    register_numbers: List[int]

    def to_network_message(self) -> bytes:
        num_registers_to_request = len(self.register_numbers)
        format_str = f"!HHH{num_registers_to_request}B{MESSAGE_BYTES - 3 * SIZEOF_H - num_registers_to_request}x"
        
        return struct.pack(format_str, self.code.value, self.page_number, num_registers_to_request, *self.register_numbers)

def bytesToReadRegisterMessage(raw_msg: bytes):
    code, page_num, arr_len, *garbage = struct.unpack(f"!HHH{MESSAGE_BYTES - 3 * SIZEOF_H}x", raw_msg)
    format_str = f"!HHH{arr_len}B{MESSAGE_BYTES - 3 * SIZEOF_H - arr_len}x"

    code, page_num, arr_len, *data = struct.unpack(format_str, raw_msg)
    code = MessageCode(code)

    msg = ReadRegisterMessage(code, "", page_num, data)
    return msg

class MeasurementMessage:
    code: MessageCode
    data: List[int]

    def __init__(self, code=None, data=None):
        self.code=code
        self.data=data

    def to_network_message(self) -> bytes:
        num_bytes_to_send = len(self.data)
        num_pad_bytes = MESSAGE_BYTES - 2 * SIZEOF_H - num_bytes_to_send
        return struct.pack(f'!HH{num_bytes_to_send}B{num_pad_bytes}x', self.code.value, num_bytes_to_send, *self.data)




def unpackRawBytes(raw_msg: bytes) -> Message:
    code, data = struct.unpack('!H254s', raw_msg)
    code = MessageCode(code)
    sent_cmd = Message(code, str(data, 'utf-8').strip('\x00'))

    return sent_cmd

def unpackMeasurementMessageBytes(raw_msg: bytes) -> MeasurementMessage:
    code, arr_len, *garbage = struct.unpack(f"!HH{MESSAGE_BYTES - 2 * SIZEOF_H}x", raw_msg)
    int_code, arr_len, *data = struct.unpack(f"!HH{arr_len}B{MESSAGE_BYTES - 2 * SIZEOF_H - arr_len}x", raw_msg)

    sent_cmd = MeasurementMessage(int_code, data)

    return sent_cmd