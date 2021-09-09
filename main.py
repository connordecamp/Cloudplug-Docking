import smbus2
from typing import List
import time
from modules.sfp import SFP

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


def main():
    
    

    '''DEVICE_BUS = 1
    # Really 0xA0 = 0x10100000,
    # but we need to use 0x50 since the last bit
    # is the read/write bit. The I2c addresses are
    # 7 bit binary numbers with the last being the
    # read or write bit
    DEVICE_ADDR = 0x50

    i2c_bus = smbus2.SMBus(DEVICE_BUS)

    bus_dump = []

    for i in range(0xFF + 1):

        res = i2c_bus.read_byte_data(DEVICE_ADDR, i)
        bus_dump.append(res)
        print(format(res, '02X'), end=' ')

        if (i + 1) % 16 == 0:
            print()

    i2c_bus.close()'''

    sfp_bus = SFP_I2C_Bus()

    a0_dump = sfp_bus.dumpA0()
    a2_dump = sfp_bus.dumpA2()

    sfp = SFP(a0_dump, a2_dump)

    print(sfp.get_diagnostic_monitoring_type())

    # Read temperature every 0.5 seconds
    
    print("{:<20} {:<20} {:<30} {:<30} {:<30}".format("Temperature (C)", "Voltage (100 uV)", "TX Bias Current (2 uA)", "TX Power (0.1 uW)", "RX Power (0.1 uW)"))
    # print(sfp.get_voltage_slope())
    #print(sfp.get_voltage_offset())
    while True:

        print("{:<20.5f} {:<20} {:<30} {:<30} {:<30.5f}".format(sfp.get_temperature(), 
            sfp.get_vcc(), 
            sfp.get_tx_bias_current(), 
            sfp.get_tx_power(), 
            sfp.get_rx_power())
        )

        a2_dump = sfp_bus.dumpA2()
        sfp.page_a2 = a2_dump
        time.sleep(0.5)

    return

    while True:
        

        '''
        for idx, num in enumerate(bus_dump):

            if num >= 32 and num <= 126:
                print(chr(num), end='')
            else:
                print('.', end='')

            if (idx + 1) % 16 == 0:
                print()
        '''

        a2_dump = sfp_bus.dumpA2()
        sfp.page_a2 = a2_dump

        print('\n')
        time.sleep(5)

    sfp_bus.end_communication()
    
    
if __name__ == '__main__':
    main()