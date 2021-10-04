from typing import List
import smbus2

class SFP_I2C_Bus:

    # Raspberry Pi uses bus 1 for I2C
    DEVICE_BUS = 1

    # Page 0xA0 of the SFP, stores identifier information
    INFO_ADDR = 0x50

    # Page 0xA2 of the SFP for digital diagnostics monitoring (DDM)
    # Would be 1010 0010, but we ignore the last bit since R/W
    # So we get 101 0001, which is 0x51
    DDM_ADDR = 0x51

    def __init__(self):
        self.bus = smbus2.SMBus(self.DEVICE_BUS)


    def _dump(self, addr: int, max_addr: int) -> List[int]:
        values = []

        try:
            for i in range(max_addr + 1):
                read_value = self.bus.read_byte_data(addr, i)
                values.append(read_value)

        except Exception as ex:
            print("ERROR::SFP_I2C_BUS::_dump()")
            print(ex)
            values = [-1] * max_addr

            raise Exception("Remote I/O error communicating with SFP")

        return values

    def dumpA0(self) -> List[int]:
        return self._dump(self.INFO_ADDR, 0xFF)

    def dumpA2(self) -> List[int]:
        return self._dump(self.DDM_ADDR, 0xFF)


    def end_communication(self):
        self.bus.close()


def print_bus_dump(bus_dump: List[int], ascii: bool) -> None:

    # Print header
    if ascii:
        print(f'0123456789ABCDEF')
    else:
        print('{:>6}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}{:>3}'.format('0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F'))

    for idx, num in enumerate(bus_dump):

        if ascii:
            if num >= 32 and num <= 126:
                print(chr(num), end='')
            else:
                print('.', end='')
        else:
            if idx % 16 == 0:
                print(format(idx, '02X') + ':', end=' ')

            print(format(num, '02X'), end=' ')
            

        if (idx + 1) % 16 == 0:
            print()
