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
            read_value = self.bus.read_byte_data(addr, 0)
            values.append(read_value)

            for i in range(1, max_addr + 1):
                read_value = self.bus.read_byte(addr)
                values.append(read_value)

        except Exception as ex:
            print(f"ERROR::SFP_I2C_BUS::_dump() trying to read from {hex(addr)}")
            print(ex)
            values = [-1] * max_addr

            raise Exception("Remote I/O error communicating with SFP")

        #print(f"Received {len(values)} values from SFP")
        #print(f"_dump() OK, got {values}")

        return values

    def dumpA0(self) -> List[int]:
        return self._dump(self.INFO_ADDR, 0xFF)

    def dumpA2(self) -> List[int]:
        return self._dump(self.DDM_ADDR, 0xFF)

    def read_param_registers(self) -> List[int]:
        ''' 
        Reads the parameter registers of the SFP.
        addr 0xA2, registers 96->105 
        '''

        addr = [i for i in range(96, 105 + 1)]

        return self.read_info_registers(addr)

    def read_registers_from_page(self, registers: List[int], page_num: int):

        read_values = []

        if page_num != 0x50 and page_num != 0x51:
            raise ValueError("Page number not supported")
        else:
            for reg_num in registers:
                read_val = self.bus.read_byte_data(page_num, reg_num)
                read_values.append(read_val)

        return read_values

    def read_info_registers(self, registers: List[int]) -> List[int]:
        '''
        Returns a list of values read from the SFP given a list
        of values indicating register number/location.
        '''
        vals = []

        for reg in registers:
            if reg < 0 or reg > 255:
                raise Exception("Invalid register number. Valid register numbers are 0-255")
            else:
                vals.append(self.bus.read_byte_data(self.INFO_ADDR, reg))
        
        return vals

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
